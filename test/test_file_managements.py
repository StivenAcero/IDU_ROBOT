import unittest
from unittest.mock import patch
from src.file_managements import FileManagements
@patch('src.file_managements.logger')
@patch('src.file_managements.os.remove')
@patch('src.file_managements.os.path.isfile')
@patch('src.file_managements.os.path.join')
@patch('src.file_managements.os.listdir')
@patch('src.file_managements.os.path.exists')

class TestDeleteFiles (unittest.TestCase):

    def test_carpeta_no_existe(
        self, mock_exists, mock_listdir, mock_join, mock_isfile, mock_remove, mock_logger
    ):
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


