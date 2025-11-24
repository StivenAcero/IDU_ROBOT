import pytest
import pandas as pd
from typing import cast
from unittest.mock import Mock, patch,MagicMock
from src.idu_service import IduService


@patch('src.idu_service.SheetService')
@patch('src.idu_service.IduConfig.load_config')
@patch('src.idu_service.IduNavigator')
@patch('src.idu_service.logger')
class TestIduServiceProcesarChipSinEstado:
    """Pruebas unitarias para IduService.procesar_chip_sin_estado"""

    @pytest.fixture
    def mock_config(self):
        """Configuración mock para las pruebas"""
        config = Mock()
        config.target_url = "https://ejemplo.com"
        config.user_name = "Usuario Test"
        config.request_email = "test@ejemplo.com"
        config.spreadsheet_id = "spreadsheet_123"
        return config

    @pytest.fixture
    def encabezado(self):
        """Encabezado de ejemplo"""
        return ["chips", "nombre", "estado"]

    @pytest.fixture
    def df_con_datos(self):
        """DataFrame con solicitudes sin estado"""
        return pd.DataFrame({
            'chips': ['CHIP001', 'CHIP002'],
            'nombre': ['Solicitud 1', 'Solicitud 2'],
            'estado': [None, None]
        })

    def test_dataframe_vacio_no_procesa(
        self, mock_logger, mock_navigator, mock_config_load, mock_sheet_service, 
        mock_config, encabezado
    ):
        """Cuando el DataFrame está vacío, no procesa nada"""
        # Arrange
        mock_config_load.return_value = mock_config
        service = IduService()
        df_vacio = pd.DataFrame()

        # Act
        service.procesar_chip_sin_estado(df_vacio, encabezado)

        # Assert
        mock_logger.info.assert_called_once_with("Todos los registros tienen ESTADO asignado")
        service._driver = cast(MagicMock, service._driver)
        service._driver.navegar_a_url.assert_not_called()# pylint: disable=no-member

    def test_procesa_solicitud_exitosamente(
        self, mock_logger, mock_navigator, mock_config_load, mock_sheet_service,
        mock_config, encabezado, df_con_datos
    ):
        """Procesa una solicitud exitosamente y actualiza el estado"""
        # Arrange
        mock_config_load.return_value = mock_config
        mock_driver = Mock()
        mock_navigator.return_value = mock_driver
        mock_sheet = Mock()
        mock_sheet_service.return_value = mock_sheet
        
        tabla_form_mock = Mock()
        mock_driver.preparar_formulario.return_value = (None, tabla_form_mock, None)
        mock_driver.rellenar_formulario_usuario.return_value = True
        mock_driver.rellenar_campo_mensaje_solicitud.return_value = True
        mock_driver.click_iniciar_chat.return_value = True
        
        service = IduService()
        df_una_solicitud = df_con_datos.iloc[[0]]

        # Act
        service.procesar_chip_sin_estado(df_una_solicitud, encabezado)

        # Assert
        mock_driver.navegar_a_url.assert_called_once_with(mock_config.target_url)
        mock_driver.realizar_clicks_secuenciales.assert_called_once()
        mock_driver.rellenar_formulario_usuario.assert_called_once()
        mock_driver.click_iniciar_chat.assert_called_once()
        mock_sheet.actualizar_estado_chips.assert_called_once_with(
            mock_config.spreadsheet_id,
            encabezado,
            'CHIP001',
            'Solicitado chat IDU'
        )
        mock_driver.reiniciar_navegador.assert_called_once()

    def test_error_al_preparar_formulario(
        self, mock_logger, mock_navigator, mock_config_load, mock_sheet_service,
        mock_config, encabezado, df_con_datos
    ):
        """Cuando falla la preparación del formulario, registra error y salta a la siguiente iteración"""
        # Arrange
        mock_config_load.return_value = mock_config
        mock_driver = Mock()
        mock_navigator.return_value = mock_driver
        mock_sheet = Mock()
        mock_sheet_service.return_value = mock_sheet
        
        mock_driver.preparar_formulario.return_value = (None, None, None)
        
        service = IduService()
        df_una_solicitud = df_con_datos.iloc[[0]]

        # Act
        service.procesar_chip_sin_estado(df_una_solicitud, encabezado)

        # Assert
        mock_logger.error.assert_called()
        # Con el continue, no debe intentar rellenar el formulario
        mock_driver.rellenar_formulario_usuario.assert_not_called()
        mock_driver.rellenar_campo_mensaje_solicitud.assert_not_called()
        mock_driver.click_iniciar_chat.assert_not_called()
        # No debe actualizar estado si falló
        mock_sheet.actualizar_estado_chips.assert_not_called()
        # Pero sí debe reiniciar el navegador
        mock_driver.reiniciar_navegador.assert_called_once()

    def test_error_al_rellenar_formulario_usuario(
        self, mock_logger, mock_navigator, mock_config_load, mock_sheet_service,
        mock_config, encabezado, df_con_datos
    ):
        """Cuando falla el llenado de usuario, no continúa"""
        # Arrange
        mock_config_load.return_value = mock_config
        mock_driver = Mock()
        mock_navigator.return_value = mock_driver
        mock_sheet = Mock()
        mock_sheet_service.return_value = mock_sheet
        
        tabla_form_mock = Mock()
        mock_driver.preparar_formulario.return_value = (None, tabla_form_mock, None)
        mock_driver.rellenar_formulario_usuario.return_value = False
        
        service = IduService()
        df_una_solicitud = df_con_datos.iloc[[0]]

        # Act
        service.procesar_chip_sin_estado(df_una_solicitud, encabezado)

        # Assert
        mock_driver.click_iniciar_chat.assert_not_called()
        mock_sheet.actualizar_estado_chips.assert_not_called()

    def test_error_al_rellenar_mensaje(
        self, mock_logger, mock_navigator, mock_config_load, mock_sheet_service,
        mock_config, encabezado, df_con_datos
    ):
        """Cuando falla el llenado del mensaje, no continúa"""
        # Arrange
        mock_config_load.return_value = mock_config
        mock_driver = Mock()
        mock_navigator.return_value = mock_driver
        mock_sheet = Mock()
        mock_sheet_service.return_value = mock_sheet
        
        tabla_form_mock = Mock()
        mock_driver.preparar_formulario.return_value = (None, tabla_form_mock, None)
        mock_driver.rellenar_formulario_usuario.return_value = True
        mock_driver.rellenar_campo_mensaje_solicitud.return_value = False
        
        service = IduService()
        df_una_solicitud = df_con_datos.iloc[[0]]

        # Act
        service.procesar_chip_sin_estado(df_una_solicitud, encabezado)

        # Assert
        mock_driver.click_iniciar_chat.assert_not_called()
        mock_sheet.actualizar_estado_chips.assert_not_called()

    def test_error_al_iniciar_chat(
        self, mock_logger, mock_navigator, mock_config_load, mock_sheet_service,
        mock_config, encabezado, df_con_datos
    ):
        """Cuando falla el inicio del chat, lanza excepción"""
        # Arrange
        mock_config_load.return_value = mock_config
        mock_driver = Mock()
        mock_navigator.return_value = mock_driver
        mock_sheet = Mock()
        mock_sheet_service.return_value = mock_sheet
        
        tabla_form_mock = Mock()
        mock_driver.preparar_formulario.return_value = (None, tabla_form_mock, None)
        mock_driver.rellenar_formulario_usuario.return_value = True
        mock_driver.rellenar_campo_mensaje_solicitud.return_value = True
        mock_driver.click_iniciar_chat.return_value = False
        
        service = IduService()
        df_una_solicitud = df_con_datos.iloc[[0]]

        # Act
        service.procesar_chip_sin_estado(df_una_solicitud, encabezado)

        # Assert
        mock_logger.error.assert_called()
        mock_sheet.actualizar_estado_chips.assert_not_called()

    def test_procesa_multiples_solicitudes(
        self, mock_logger, mock_navigator, mock_config_load, mock_sheet_service,
        mock_config, encabezado, df_con_datos
    ):
        """Procesa múltiples solicitudes correctamente"""
        # Arrange
        mock_config_load.return_value = mock_config
        mock_driver = Mock()
        mock_navigator.return_value = mock_driver
        mock_sheet = Mock()
        mock_sheet_service.return_value = mock_sheet
        
        tabla_form_mock = Mock()
        mock_driver.preparar_formulario.return_value = (None, tabla_form_mock, None)
        mock_driver.rellenar_formulario_usuario.return_value = True
        mock_driver.rellenar_campo_mensaje_solicitud.return_value = True
        mock_driver.click_iniciar_chat.return_value = True
        
        service = IduService()

        # Act
        service.procesar_chip_sin_estado(df_con_datos, encabezado)

        # Assert
        assert mock_driver.realizar_clicks_secuenciales.call_count == 2
        assert mock_sheet.actualizar_estado_chips.call_count == 2
        assert mock_driver.reiniciar_navegador.call_count == 2

    def test_excepcion_general_durante_procesamiento(
        self, mock_logger, mock_navigator, mock_config_load, mock_sheet_service,
        mock_config, encabezado, df_con_datos
    ):
        """Cuando ocurre una excepción general, la captura y registra"""
        # Arrange
        mock_config_load.return_value = mock_config
        mock_driver = Mock()
        mock_navigator.return_value = mock_driver
        mock_sheet = Mock()
        mock_sheet_service.return_value = mock_sheet
        
        mock_driver.realizar_clicks_secuenciales.side_effect = Exception("Error inesperado")
        
        service = IduService()
        df_una_solicitud = df_con_datos.iloc[[0]]

        # Act
        service.procesar_chip_sin_estado(df_una_solicitud, encabezado)

        # Assert
        mock_logger.error.assert_called()
        mock_sheet.actualizar_estado_chips.assert_not_called()
        mock_driver.reiniciar_navegador.assert_called_once()

    def test_una_solicitud_exitosa_y_una_fallida(
        self, mock_logger, mock_navigator, mock_config_load, mock_sheet_service,
        mock_config, encabezado, df_con_datos
    ):
        """Procesa correctamente cuando una solicitud falla y otra tiene éxito"""
        # Arrange
        mock_config_load.return_value = mock_config
        mock_driver = Mock()
        mock_navigator.return_value = mock_driver
        mock_sheet = Mock()
        mock_sheet_service.return_value = mock_sheet
        
        tabla_form_mock = Mock()
        mock_driver.preparar_formulario.return_value = (None, tabla_form_mock, None)
        mock_driver.rellenar_formulario_usuario.return_value = True
        mock_driver.rellenar_campo_mensaje_solicitud.return_value = True
        # Primera llamada falla, segunda tiene éxito
        mock_driver.click_iniciar_chat.side_effect = [False, True]
        
        service = IduService()

        # Act
        service.procesar_chip_sin_estado(df_con_datos, encabezado)

        # Assert
        # Solo la segunda solicitud debe actualizar estado
        assert mock_sheet.actualizar_estado_chips.call_count == 1
        mock_sheet.actualizar_estado_chips.assert_called_with(
            mock_config.spreadsheet_id,
            encabezado,
            'CHIP002',
            'Solicitado chat IDU'
        )