import unittest
from unittest.mock import patch
from src.file_managements import FileManagements


@patch('src.file_managements.logger')
@patch('src.file_managements.os.makedirs')
@patch('src.file_managements.os.path.exists')
class TestCreateFolderIfNotExists(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial"""
        self.instance = FileManagements()
        self.test_path = '/ruta/test/carpeta'
    
    def test_create_folder_success(self, mock_exists, mock_makedirs, mock_logger):
        """Prueba: Carpeta no existe y se crea exitosamente"""
        mock_exists.return_value = False
        result = self.instance.create_folder_if_not_exists(self.test_path)
        self.assertTrue(result)
        mock_exists.assert_called_once_with(self.test_path)
        mock_makedirs.assert_called_once_with(self.test_path)
        mock_logger.info.assert_called_once_with("Carpeta creada: %s", self.test_path)
    
    def test_folder_already_exists(self, mock_exists, mock_makedirs, mock_logger):
        """Prueba: Carpeta ya existe"""
        mock_exists.return_value = True
        result = self.instance.create_folder_if_not_exists(self.test_path)
        self.assertTrue(result)
        mock_exists.assert_called_once_with(self.test_path)
        mock_makedirs.assert_not_called()
        mock_logger.info.assert_called_once_with("La carpeta ya existe: %s", self.test_path)
        
    
    def test_create_folder_exception_on_exists_check(self, mock_exists, mock_makedirs, mock_logger):
        """Prueba: Error al verificar si la carpeta existe"""
        mock_exists.side_effect = Exception("Unexpected error")
        
        result = self.instance.create_folder_if_not_exists(self.test_path)
        
        self.assertFalse(result)
        mock_exists.assert_called_once_with(self.test_path)
        mock_logger.error.assert_called_once()
        
@patch('src.file_managements.logger')
@patch('src.file_managements.os.remove')
@patch('src.file_managements.os.path.isfile')
@patch('src.file_managements.os.path.join')
@patch('src.file_managements.os.listdir')
@patch('src.file_managements.os.path.exists')

class TestDeleteFiles (unittest.TestCase):
    """Pruebas unitarias para el método delete_files"""

    def test_carpeta_no_existe(
        self, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger
    ):
        """Cuando la carpeta no existe, retorna False y registra warning"""
        # Arrange
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

    def test_elimina_archivos_correctamente(
        self, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger
    ):
        """Elimina todos los archivos de la carpeta exitosamente"""
        # Arrange
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
        assert mock_logger.info.call_count == 4  # 3 archivos + mensaje final

    def test_ignora_subdirectorios(
        self, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger
    ):
        """Solo elimina archivos, ignora subdirectorios"""
        # Arrange
        instancia = FileManagements()
        ruta = '/carpeta/test'
        elementos = ['archivo.txt', 'subcarpeta', 'otro_archivo.doc']
        
        mock_exists.return_value = True
        mock_listdir.return_value = elementos
        mock_join.side_effect = lambda x, y: f"{x}/{y}"
        # archivo.txt y otro_archivo.doc son archivos, subcarpeta no
        mock_isfile.side_effect = [True, False, True]

        # Act
        resultado = instancia.delete_files(ruta)

        # Assert
        assert resultado is True
        assert mock_remove.call_count == 2  # Solo 2 archivos
        mock_remove.assert_any_call('/carpeta/test/archivo.txt')
        mock_remove.assert_any_call('/carpeta/test/otro_archivo.doc')

    def test_carpeta_vacia(
        self, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger
    ):
        """Cuando la carpeta está vacía, retorna True"""
        # Arrange
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

    def test_error_al_eliminar_archivo(
        self, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger
    ):
        """Cuando ocurre error al eliminar, retorna False y registra error"""
        # Arrange
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
        assert "Error al eliminar archivos" in str(mock_logger.error.call_args)

    def test_error_al_listar_carpeta(
        self, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger
    ):
        """Cuando ocurre error al listar la carpeta, retorna False"""
        # Arrange
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


