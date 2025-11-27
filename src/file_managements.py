import os
import logging
import pandas as pd
from src.idu_config import IduConfig
from src.sheet_service import SheetService

logger = logging.getLogger(__name__)


class FileManagements:
    
    def __init__(self):
        self._config = IduConfig.load_config('config/config.json')
        self._logger = logging.getLogger(__name__)
        self._read_sheet = SheetService().read_sheet
        self._obtener_letra_columna = SheetService().obtener_letra_columna
        self._spreadsheets = SheetService()._spreadsheets
        
    def delete_files(self, ruta_carpeta):
        try:
            if not os.path.exists(ruta_carpeta):
                logger.warning("La carpeta %s no existe", ruta_carpeta)
                return False

            for elemento in os.listdir(ruta_carpeta):
                ruta_completa = os.path.join(ruta_carpeta, elemento)

                if os.path.isfile(ruta_completa):
                    os.remove(ruta_completa)
                    logger.info("Archivo eliminado: %s", elemento)

            logger.info("Todos los archivos han sido eliminados")
            return True
        except Exception as e:
            logger.error("Error al eliminar archivos en %s: %s", ruta_carpeta, e)
            return False
    
    def list_files_to_dataframe(self, ruta_carpeta:str | None = None) -> pd.DataFrame:

        ruta = ruta_carpeta or self._config.download_path
        
        try:
            if not os.path.exists(ruta):
                logger.warning("La carpeta %s no existe", ruta)
                return pd.DataFrame(columns=['archivos'])
            
            # Listar solo archivos (no directorios)
            archivos = [
                os.path.splitext(f)[0]  # Obtener nombre sin extensión
                for f in os.listdir(ruta)
                if os.path.isfile(os.path.join(ruta, f))
            ]
            
            df = pd.DataFrame({'archivos': archivos})
            logger.info("Se encontraron %d archivo(s) en %s", len(archivos), ruta)
            
            return df
            
        except Exception as e:
            logger.error("Error al listar archivos en %s: %s", ruta, e)
            return pd.DataFrame(columns=['archivos'])
        
    def actualizar_estado_descargado(self, df_archivos: pd.DataFrame) -> int:
        """
        Actualiza el estado a 'DESCARGADO' para los chips que coinciden con los archivos del DataFrame.
        
        Args:
            df_archivos: DataFrame con columna 'archivos' que contiene los nombres de archivos descargados
            
        Returns:
            int: Cantidad de chips actualizados
        """
        if df_archivos.empty:
            self._logger.warning("DataFrame vacío, no hay archivos para actualizar")
            return 0
        
        try:
            # Leer la hoja
            data = self._read_sheet()
            if not data or len(data) < 2:
                self._logger.error("No hay datos en la hoja")
                return 0
            
            # Obtener índices de columnas
            encabezado = data[0]
            indice_chips = encabezado.index('CHIPS')
            columna_estado = self._obtener_letra_columna(encabezado, 'ESTADO')
            
            if not columna_estado:
                self._logger.error("No se pudo encontrar la columna ESTADO")
                return 0
            
            # Convertir nombres de archivos del DataFrame a lista
            archivos_descargados = df_archivos['archivos'].tolist()
            
            self._logger.info("Actualizando estados a DESCARGADO para %d archivo(s)", len(archivos_descargados))
            
            # Buscar coincidencias y preparar batch
            batch_data = []
            chips_actualizados = []
            
            for archivo in archivos_descargados:
                for i, fila in enumerate(data[1:], start=2):
                    if len(fila) > indice_chips and fila[indice_chips] == archivo:
                        rango = f"{columna_estado}{i}"
                        batch_data.append({
                            'range': rango,
                            'values': [['DESCARGADO']]
                        })
                        chips_actualizados.append(archivo)
                        break
            
            # Actualizar en batch
            if batch_data:
                body = {
                    'valueInputOption': 'RAW',
                    'data': batch_data
                }
                self._spreadsheets.values().batchUpdate(
                    spreadsheetId=self._config.spreadsheet_id,
                    body=body
                ).execute()
                
                self._logger.info("Se actualizaron %d chip(s) a estado DESCARGADO", len(batch_data))
                return len(batch_data)
            else:
                self._logger.warning("No se encontraron coincidencias para actualizar")
                return 0
                
        except ValueError as e:
            self._logger.error("Columna requerida no encontrada: %s", e)
            return 0
        except Exception as e:
            self._logger.critical("Error al actualizar estados: %s", e, exc_info=True)
            return 0