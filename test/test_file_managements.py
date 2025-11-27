import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.file_managements import FileManagements


class TestDeleteFiles(unittest.TestCase):

    @patch('src.file_managements.logger')
    @patch('src.file_managements.os.remove')
    @patch('src.file_managements.os.path.isfile')
    @patch('src.file_managements.os.path.join')
    @patch('src.file_managements.os.listdir')
    @patch('src.file_managements.os.path.exists')
    @patch('src.file_managements.SheetService')
    @patch('src.file_managements.IduConfig')
    def test_carpeta_no_existe(self, mock_idu_config, mock_sheet_service, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger):
        """Retorna False cuando la carpeta no existe"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service.return_value = MagicMock()
        
        instancia = FileManagements()
        ruta = '/carpeta/inexistente'
        mock_exists.return_value = False

        # Act
        resultado = instancia.delete_files(ruta)

        # Assert
        assert resultado is False
        mock_exists.assert_called_once_with(ruta)
        mock_logger.warning.assert_called_once()
        mock_listdir.assert_not_called()
        mock_remove.assert_not_called()

    @patch('src.file_managements.logger')
    @patch('src.file_managements.os.remove')
    @patch('src.file_managements.os.path.isfile')
    @patch('src.file_managements.os.path.join')
    @patch('src.file_managements.os.listdir')
    @patch('src.file_managements.os.path.exists')
    @patch('src.file_managements.SheetService')
    @patch('src.file_managements.IduConfig')
    def test_elimina_archivos_correctamente(self, mock_idu_config, mock_sheet_service, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger):
        """Elimina todos los archivos de la carpeta exitosamente"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service.return_value = MagicMock()
        
        instancia = FileManagements()
        ruta = '/carpeta/test'
        archivos = ['archivo1.txt', 'archivo2.pdf', 'archivo3.jpg']
        
        mock_exists.return_value = True
        mock_listdir.return_value = archivos
        mock_join.side_effect = lambda x, y: f"{x}/{y}"
        mock_isfile.return_value = True

        # Act
        resultado = instancia.delete_files(ruta)

        # Assert
        assert resultado is True
        assert mock_remove.call_count == 3
        mock_remove.assert_any_call('/carpeta/test/archivo1.txt')
        mock_remove.assert_any_call('/carpeta/test/archivo2.pdf')
        mock_remove.assert_any_call('/carpeta/test/archivo3.jpg')
        assert mock_logger.info.call_count == 4

    @patch('src.file_managements.logger')
    @patch('src.file_managements.os.remove')
    @patch('src.file_managements.os.path.isfile')
    @patch('src.file_managements.os.path.join')
    @patch('src.file_managements.os.listdir')
    @patch('src.file_managements.os.path.exists')
    @patch('src.file_managements.SheetService')
    @patch('src.file_managements.IduConfig')
    def test_ignora_subdirectorios(self, mock_idu_config, mock_sheet_service, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger):
        """Solo elimina archivos, ignora subdirectorios"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service.return_value = MagicMock()
        
        instancia = FileManagements()
        ruta = '/carpeta/test'
        elementos = ['archivo.txt', 'subcarpeta', 'otro_archivo.doc']
        
        mock_exists.return_value = True
        mock_listdir.return_value = elementos
        mock_join.side_effect = lambda x, y: f"{x}/{y}"
        mock_isfile.side_effect = [True, False, True]

        # Act
        resultado = instancia.delete_files(ruta)

        # Assert
        assert resultado is True
        assert mock_remove.call_count == 2
        mock_remove.assert_any_call('/carpeta/test/archivo.txt')
        mock_remove.assert_any_call('/carpeta/test/otro_archivo.doc')

    @patch('src.file_managements.logger')
    @patch('src.file_managements.os.remove')
    @patch('src.file_managements.os.path.isfile')
    @patch('src.file_managements.os.path.join')
    @patch('src.file_managements.os.listdir')
    @patch('src.file_managements.os.path.exists')
    @patch('src.file_managements.SheetService')
    @patch('src.file_managements.IduConfig')
    def test_carpeta_vacia(self, mock_idu_config, mock_sheet_service, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger):
        """Cuando la carpeta está vacía, retorna True"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service.return_value = MagicMock()
        
        instancia = FileManagements()
        ruta = '/carpeta/vacia'
        
        mock_exists.return_value = True
        mock_listdir.return_value = []

        # Act
        resultado = instancia.delete_files(ruta)

        # Assert
        assert resultado is True
        mock_remove.assert_not_called()
        mock_logger.info.assert_called_with("Todos los archivos han sido eliminados")

    @patch('src.file_managements.logger')
    @patch('src.file_managements.os.remove')
    @patch('src.file_managements.os.path.isfile')
    @patch('src.file_managements.os.path.join')
    @patch('src.file_managements.os.listdir')
    @patch('src.file_managements.os.path.exists')
    @patch('src.file_managements.SheetService')
    @patch('src.file_managements.IduConfig')
    def test_error_al_eliminar_archivo(self, mock_idu_config, mock_sheet_service, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger):
        """Cuando ocurre error al eliminar, retorna False y registra error"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service.return_value = MagicMock()
        
        instancia = FileManagements()
        ruta = '/carpeta/test'
        
        mock_exists.return_value = True
        mock_listdir.return_value = ['archivo.txt']
        mock_join.return_value = '/carpeta/test/archivo.txt'
        mock_isfile.return_value = True
        mock_remove.side_effect = PermissionError("Permiso denegado")

        # Act
        resultado = instancia.delete_files(ruta)

        # Assert
        assert resultado is False
        mock_logger.error.assert_called_once()

    @patch('src.file_managements.logger')
    @patch('src.file_managements.os.remove')
    @patch('src.file_managements.os.path.isfile')
    @patch('src.file_managements.os.path.join')
    @patch('src.file_managements.os.listdir')
    @patch('src.file_managements.os.path.exists')
    @patch('src.file_managements.SheetService')
    @patch('src.file_managements.IduConfig')
    def test_error_al_listar_carpeta(self, mock_idu_config, mock_sheet_service, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger):
        """Cuando ocurre error al listar la carpeta"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service.return_value = MagicMock()
        
        instancia = FileManagements()
        ruta = '/carpeta/test'
        
        mock_exists.return_value = True
        mock_listdir.side_effect = OSError("Error de lectura")

        # Act
        resultado = instancia.delete_files(ruta)

        # Assert
        assert resultado is False
        mock_logger.error.assert_called_once()
        mock_remove.assert_not_called()


class TestListFilesToDataframe(unittest.TestCase):

    @patch('src.file_managements.logger')
    @patch('src.file_managements.os.path.isfile')
    @patch('src.file_managements.os.listdir')
    @patch('src.file_managements.os.path.exists')
    @patch('src.file_managements.SheetService')
    @patch('src.file_managements.IduConfig')
    def test_carpeta_no_existe(self, mock_idu_config, mock_sheet_service, mock_exists, mock_listdir, mock_isfile, mock_logger):
        """Retorna DataFrame vacío cuando la carpeta no existe"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service.return_value = MagicMock()
        
        instancia = FileManagements()
        ruta = '/carpeta/inexistente'
        mock_exists.return_value = False

        # Act
        resultado = instancia.list_files_to_dataframe(ruta)

        # Assert
        assert resultado.empty
        assert list(resultado.columns) == ['archivos']
        mock_logger.warning.assert_called_once()

    @patch('src.file_managements.logger')
    @patch('src.file_managements.os.path.isfile')
    @patch('src.file_managements.os.listdir')
    @patch('src.file_managements.os.path.exists')
    @patch('src.file_managements.SheetService')
    @patch('src.file_managements.IduConfig')
    def test_lista_archivos_correctamente(self, mock_idu_config, mock_sheet_service, mock_exists, mock_listdir, mock_isfile, mock_logger):
        """Lista todos los archivos sin extensión correctamente"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service.return_value = MagicMock()
        
        instancia = FileManagements()
        ruta = '/carpeta/test'
        elementos = ['archivo1.txt', 'archivo2.pdf', 'archivo3.jpg']
        
        mock_exists.return_value = True
        mock_listdir.return_value = elementos
        mock_isfile.return_value = True

        # Act
        resultado = instancia.list_files_to_dataframe(ruta)

        # Assert
        assert not resultado.empty
        assert len(resultado) == 3
        assert resultado['archivos'].tolist() == ['archivo1', 'archivo2', 'archivo3']
        mock_logger.info.assert_called_once()

    @patch('src.file_managements.logger')
    @patch('src.file_managements.os.path.isfile')
    @patch('src.file_managements.os.listdir')
    @patch('src.file_managements.os.path.exists')
    @patch('src.file_managements.SheetService')
    @patch('src.file_managements.IduConfig')
    def test_ignora_directorios(self, mock_idu_config, mock_sheet_service, mock_exists, mock_listdir, mock_isfile, mock_logger):
        """Solo lista archivos, ignora subdirectorios"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service.return_value = MagicMock()
        
        instancia = FileManagements()
        ruta = '/carpeta/test'
        elementos = ['archivo.txt', 'subcarpeta', 'otro_archivo.doc']
        
        mock_exists.return_value = True
        mock_listdir.return_value = elementos
        mock_isfile.side_effect = [True, False, True]

        # Act
        resultado = instancia.list_files_to_dataframe(ruta)

        # Assert
        assert len(resultado) == 2
        assert resultado['archivos'].tolist() == ['archivo', 'otro_archivo']

    @patch('src.file_managements.logger')
    @patch('src.file_managements.os.path.isfile')
    @patch('src.file_managements.os.listdir')
    @patch('src.file_managements.os.path.exists')
    @patch('src.file_managements.SheetService')
    @patch('src.file_managements.IduConfig')
    def test_carpeta_vacia(self, mock_idu_config, mock_sheet_service, mock_exists, mock_listdir, mock_isfile, mock_logger):
        """Retorna DataFrame vacío cuando la carpeta está vacía"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service.return_value = MagicMock()
        
        instancia = FileManagements()
        ruta = '/carpeta/vacia'
        
        mock_exists.return_value = True
        mock_listdir.return_value = []

        # Act
        resultado = instancia.list_files_to_dataframe(ruta)

        # Assert
        assert resultado.empty
        assert list(resultado.columns) == ['archivos']

    @patch('src.file_managements.logger')
    @patch('src.file_managements.os.path.isfile')
    @patch('src.file_managements.os.listdir')
    @patch('src.file_managements.os.path.exists')
    @patch('src.file_managements.SheetService')
    @patch('src.file_managements.IduConfig')
    def test_error_listando_carpeta(self, mock_idu_config, mock_sheet_service, mock_exists, mock_listdir, mock_isfile, mock_logger):
        """Retorna DataFrame vacío cuando ocurre error al listar"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service.return_value = MagicMock()
        
        instancia = FileManagements()
        ruta = '/carpeta/test'
        
        mock_exists.return_value = True
        mock_listdir.side_effect = OSError("Error de lectura")

        # Act
        resultado = instancia.list_files_to_dataframe(ruta)

        # Assert
        assert resultado.empty
        mock_logger.error.assert_called_once()


@patch('src.file_managements.logger')
@patch('src.file_managements.SheetService')
@patch('src.file_managements.IduConfig')
class TestActualizarEstadoDescargado(unittest.TestCase):

    @patch('src.file_managements.logging.getLogger')
    def test_dataframe_vacio(self, mock_get_logger, mock_idu_config, mock_sheet_service, mock_module_logger):
        """Retorna 0 cuando el DataFrame está vacío"""
        # Arrange
        mock_idu_config.load_config.return_value = MagicMock()
        mock_sheet_service_inst = MagicMock()
        mock_sheet_service.return_value = mock_sheet_service_inst
        
        mock_logger_inst = MagicMock()
        mock_get_logger.return_value = mock_logger_inst
        
        instancia = FileManagements()
        df_vacio = pd.DataFrame(columns=['archivos'])

        # Act
        resultado = instancia.actualizar_estado_descargado(df_vacio)

        # Assert
        assert resultado == 0
        mock_logger_inst.warning.assert_called_once()

    @patch('src.file_managements.logging.getLogger')
    def test_actualiza_estados_correctamente(self, mock_get_logger, mock_idu_config, mock_sheet_service, mock_module_logger):
        """Actualiza correctamente los estados a DESCARGADO"""
        # Arrange
        mock_config = MagicMock()
        mock_config.spreadsheet_id = 'test_id'
        mock_idu_config.load_config.return_value = mock_config
        
        mock_sheet_service_inst = MagicMock()
        mock_sheet_service.return_value = mock_sheet_service_inst
        
        data = [
            ['CHIPS', 'NOMBRE', 'ESTADO'],
            ['CHIP001', 'Archivo1', 'PENDIENTE'],
            ['CHIP002', 'Archivo2', 'PENDIENTE'],
            ['CHIP003', 'Archivo3', 'PENDIENTE']
        ]
        mock_sheet_service_inst.read_sheet.return_value = data
        mock_sheet_service_inst.obtener_letra_columna.return_value = 'C'
        
        mock_values = MagicMock()
        mock_batch = MagicMock()
        mock_values.batchUpdate.return_value = mock_batch
        mock_batch.execute.return_value = {'replies': []}
        mock_sheet_service_inst._spreadsheets.values.return_value = mock_values
        
        mock_logger_inst = MagicMock()
        mock_get_logger.return_value = mock_logger_inst
        
        instancia = FileManagements()
        df_archivos = pd.DataFrame({'archivos': ['CHIP001', 'CHIP002']})

        # Act
        resultado = instancia.actualizar_estado_descargado(df_archivos)

        # Assert
        assert resultado == 2
        mock_values.batchUpdate.assert_called_once()

    @patch('src.file_managements.logging.getLogger')
    def test_no_hay_datos_en_hoja(self, mock_get_logger, mock_idu_config, mock_sheet_service, mock_module_logger):
        """Retorna 0 cuando no hay datos en la hoja"""
        # Arrange
        mock_config = MagicMock()
        mock_idu_config.load_config.return_value = mock_config
        
        mock_sheet_service_inst = MagicMock()
        mock_sheet_service.return_value = mock_sheet_service_inst
        mock_sheet_service_inst.read_sheet.return_value = []
        
        mock_logger_inst = MagicMock()
        mock_get_logger.return_value = mock_logger_inst
        
        instancia = FileManagements()
        df_archivos = pd.DataFrame({'archivos': ['CHIP001']})

        # Act
        resultado = instancia.actualizar_estado_descargado(df_archivos)

        # Assert
        assert resultado == 0
        mock_logger_inst.error.assert_called_once()

    @patch('src.file_managements.logging.getLogger')
    def test_columna_estado_no_encontrada(self, mock_get_logger, mock_idu_config, mock_sheet_service, mock_module_logger):
        """Retorna 0 cuando no encuentra la columna ESTADO"""
        # Arrange
        mock_config = MagicMock()
        mock_idu_config.load_config.return_value = mock_config
        
        mock_sheet_service_inst = MagicMock()
        mock_sheet_service.return_value = mock_sheet_service_inst
        
        data = [
            ['CHIPS', 'NOMBRE'],
            ['CHIP001', 'Archivo1']
        ]
        mock_sheet_service_inst.read_sheet.return_value = data
        mock_sheet_service_inst.obtener_letra_columna.return_value = None
        
        mock_logger_inst = MagicMock()
        mock_get_logger.return_value = mock_logger_inst
        
        instancia = FileManagements()
        df_archivos = pd.DataFrame({'archivos': ['CHIP001']})

        # Act
        resultado = instancia.actualizar_estado_descargado(df_archivos)

        # Assert
        assert resultado == 0
        mock_logger_inst.error.assert_called_once()

    @patch('src.file_managements.logging.getLogger')
    def test_error_actualizando(self, mock_get_logger, mock_idu_config, mock_sheet_service, mock_module_logger):
        """Retorna 0 y registra error cuando ocurre excepción"""
        # Arrange
        mock_config = MagicMock()
        mock_config.spreadsheet_id = 'test_id'
        mock_idu_config.load_config.return_value = mock_config
        
        mock_sheet_service_inst = MagicMock()
        mock_sheet_service.return_value = mock_sheet_service_inst
        
        data = [
            ['CHIPS', 'NOMBRE', 'ESTADO'],
            ['CHIP001', 'Archivo1', 'PENDIENTE']
        ]
        mock_sheet_service_inst.read_sheet.return_value = data
        mock_sheet_service_inst.obtener_letra_columna.return_value = 'C'
        
        mock_logger_inst = MagicMock()
        mock_get_logger.return_value = mock_logger_inst
        
        mock_values = MagicMock()
        mock_values.batchUpdate.side_effect = Exception("Error de API")
        mock_sheet_service_inst._spreadsheets.values.return_value = mock_values
        
        instancia = FileManagements()
        df_archivos = pd.DataFrame({'archivos': ['CHIP001']})

        # Act
        resultado = instancia.actualizar_estado_descargado(df_archivos)

        # Assert
        assert resultado == 0
        mock_logger_inst.critical.assert_called_once()

    @patch('src.file_managements.logging.getLogger')
    def test_no_coincidencias_para_actualizar(self, mock_get_logger, mock_idu_config, mock_sheet_service, mock_module_logger):
        """Retorna 0 cuando no hay coincidencias para actualizar"""
        # Arrange
        mock_config = MagicMock()
        mock_config.spreadsheet_id = 'test_id'
        mock_idu_config.load_config.return_value = mock_config
        
        mock_sheet_service_inst = MagicMock()
        mock_sheet_service.return_value = mock_sheet_service_inst
        
        data = [
            ['CHIPS', 'NOMBRE', 'ESTADO'],
            ['CHIP001', 'Archivo1', 'PENDIENTE'],
            ['CHIP002', 'Archivo2', 'PENDIENTE']
        ]
        mock_sheet_service_inst.read_sheet.return_value = data
        mock_sheet_service_inst.obtener_letra_columna.return_value = 'C'
        
        mock_logger_inst = MagicMock()
        mock_get_logger.return_value = mock_logger_inst
        
        instancia = FileManagements()
        df_archivos = pd.DataFrame({'archivos': ['CHIP999']})

        # Act
        resultado = instancia.actualizar_estado_descargado(df_archivos)

        # Assert
        assert resultado == 0
        mock_logger_inst.warning.assert_called_with("No se encontraron coincidencias para actualizar")

    @patch('src.file_managements.logging.getLogger')
    def test_error_valor_columna(self, mock_get_logger, mock_idu_config, mock_sheet_service, mock_module_logger):
        """Retorna 0 cuando hay error de ValueError"""
        # Arrange
        mock_config = MagicMock()
        mock_idu_config.load_config.return_value = mock_config
        
        mock_sheet_service_inst = MagicMock()
        mock_sheet_service.return_value = mock_sheet_service_inst
        
        data = [
            ['NOMBRE', 'ESTADO'],
            ['Archivo1', 'PENDIENTE']
        ]
        mock_sheet_service_inst.read_sheet.return_value = data
        
        mock_logger_inst = MagicMock()
        mock_get_logger.return_value = mock_logger_inst
        
        instancia = FileManagements()
        df_archivos = pd.DataFrame({'archivos': ['CHIP001']})

        # Act
        resultado = instancia.actualizar_estado_descargado(df_archivos)

        # Assert
        assert resultado == 0
        mock_logger_inst.error.assert_called_once()