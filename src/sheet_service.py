import logging
from typing import List
import pandas as pd
from googleapiclient.discovery import build, Resource
from src.google_credentials import GoogleCredentials
from src.idu_config import IduConfig

logger = logging.getLogger(__name__)


class SheetService:

    def __init__(self):
        self._config = IduConfig.load_config('config/config.json')
        self._creds = GoogleCredentials.get_credentials(self._config.scopes, root_path='config/')
        self._service: Resource = build('sheets', 'v4', credentials=self._creds)
        self._logger = logging.getLogger(__name__)
        # El método spreadsheets() se agrega dinámicamente a la insancia de _service
        # pylint: disable=maybe-no-member
        self._spreadsheets = self._service.spreadsheets() # pyright: ignore[reportAttributeAccessIssue]

    def read_sheet(self) -> List:
        try:
            # El método spreadsheets() se agrega dinámicamente a la insancia de servicio
            # pylint: disable=maybe-no-member
            result = (
                self._spreadsheets.values()
                .get(
                    spreadsheetId=self._config.spreadsheet_id,
                    range=self._config.range_name,
                )
                .execute()
            )

            values = result.get('values', [])
            return values
        except Exception as e:
            self._logger.error("Error al leer la hoja:  %s", e,  exc_info=True)
            return []

    def validate_missing_files(self, data: List) -> tuple[int, List[dict], int]:
        if not data or len(data) < 2:
            return 0, [], 0

        # Obtener índices de columnas
        try:
            header = data[0]
            indice_chips = header.index('CHIPS')
            indice_estado = header.index('ESTADO')
        except ValueError :
            self._logger.error("Error: No se encontró la columna requerida. %s")
            return 0, [], 0

        registros_sin_estado = [
            self._crear_registro_sin_estado(fila, indice_chips, indice_estado)  # Sin 'i'
            for i, fila in enumerate(data[1:], start=2)
            if self._estado_vacio(fila, indice_estado)
        ]

        return len(registros_sin_estado), registros_sin_estado, len(data) - 1

    def _estado_vacio(self, fila: List, indice_estado: int) -> bool:
        """Verifica si el estado está vacío o no existe."""
        if len(fila) <= indice_estado:
            return True
        estado = fila[indice_estado].strip() if fila[indice_estado] else ''
        return not estado

    def _obtener_chips(self, fila: List, indice_chips: int) -> str:

        return fila[indice_chips] if len(fila) > indice_chips else ''

    def _crear_registro_sin_estado(self, fila: List, numero_fila: int, indice_chips: int,) -> dict:
        return {
            'fila': numero_fila,
            'CHIPS': self._obtener_chips(fila, indice_chips),
            'ESTADO': ''
        }

    def agrupar_chips_sin_estado(self, registros_sin_estado: List, max_por_grupo=5) -> pd.DataFrame:

        if not registros_sin_estado:
            return pd.DataFrame(columns=['solicitud', 'chips'])

        solicitudes = []

        # Dividir en grupos de máximo 5
        for i in range(0, len(registros_sin_estado), max_por_grupo):
            grupo_actual = registros_sin_estado[i:i + max_por_grupo]

            # Extraer solo los CHIPS
            chips_grupo = [reg['CHIPS'] for reg in grupo_actual]

            solicitudes.append({
                'solicitud': len(solicitudes) + 1,
                'chips': chips_grupo
            })

        return pd.DataFrame(solicitudes)

    def obtener_letra_columna(self, encabezado, nombre_columna) -> str:
        try:
            indice = encabezado.index(nombre_columna)
            logger.info(f"Índice columna {nombre_columna}: {indice}")
            return chr(65 + indice)
        except (ValueError, IndexError):
            raise ValueError(f"No se encontró la columna {nombre_columna}")

    def actualizar_estado_chips(self, spreadsheet_id, encabezado, chips_list, nuevo_estado="Solicitado chat IDU"):
        columna_estado = self.obtener_letra_columna(encabezado, 'ESTADO')
        if not columna_estado:
            logger.error("No se pudo encontrar la columna ESTADO")
            return 0
        self._logger.info("Actualizando estados en Google Sheets...")
        try:
            indice_chips = encabezado.index('CHIPS')
        except ValueError:
            self._logger.error("No se encontró la columna CHIPS")
            return 0

        data = self.read_sheet()
        batch_data = []
        chips_actualizados = []
        for chip in chips_list:
            for i, fila in enumerate(data[1:], start=2):
                if len(fila) > indice_chips and fila[indice_chips] == chip:
                    rango = f"{columna_estado}{i}"
                    batch_data.append({
                        'range': rango,
                        'values': [[nuevo_estado]]
                    })
                    chips_actualizados.append(chip)
                    break
        if batch_data:
            try:
                body = {
                    'valueInputOption': 'RAW',
                    'data': batch_data
                }
                self._spreadsheets.values().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=body
                ).execute()
                self._logger.info("Se actualizaron chips exitosamente %s",{len(batch_data)})
                return len(batch_data)
            except Exception as e:
                self._logger.critical("Error en actualización batch: %s", e)
                return 0
        else:
            self._logger.error("No se encontraron chips para actualizar")
            return 0
