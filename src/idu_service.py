
from src.idu_config import IduConfig
from src.sheet_service import SheetService
from src.idu_navigator import IduNavigator
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class IduService:

    def __init__(self):
        self._driver = IduNavigator()
        self._config = IduConfig.load_config("config/config.json")
        self._sheet_service = SheetService()

    def procesar_chip_sin_estado(self, df_solicitudes: pd.DataFrame,encabezado: list):
        if df_solicitudes.empty:
            logger.info("Todos los registros tienen ESTADO asignado")
            return
        self._driver.navegar_a_url(self._config.target_url)
        solicitudes_exitosas = []

        for idx, solicitud_row in df_solicitudes.iterrows():
            solicitud_exitosa = False

            try:
                self._driver.realizar_clicks_secuenciales()
                _, tabla_form, _ = (
                    self._driver.preparar_formulario()
                )

                if not tabla_form:
                    logger.error("No se pudo preparar el formulario para la solicitud %s", idx)

                name_and_email_ok = self._driver.rellenar_formulario_usuario(
                    tabla_form, self._config.user_name, self._config.request_email
                )

                mensaje_ok = self._driver.rellenar_campo_mensaje_solicitud(
                    tabla_form, solicitud_row
                )

                if not name_and_email_ok or not mensaje_ok:
                    logger.error("Solicitud {idx} completada con errores")
                    continue
                chat_iniciado = self._driver.click_iniciar_chat()
                
                # time.sleep(5)  # Esperar un momento para asegurar que el chat se inicie

                if not chat_iniciado:
                    raise ValueError("No se pudo iniciar el chat: parámetros inválidos")
      
                logger.info("Solicitud {idx} procesada exitosamente")
                solicitud_exitosa = True
                solicitudes_exitosas.append(solicitud_row)

            except Exception as e:
                logger.error("Error procesando solicitud %s: %s", idx, e)

            if solicitud_exitosa:
                self._sheet_service.actualizar_estado_chips(
                    self._config.spreadsheet_id,
                    encabezado,
                    solicitud_row["chips"],
                    "Solicitado chat IDU",
                )

            self._driver.reiniciar_navegador(url=self._config.target_url)
