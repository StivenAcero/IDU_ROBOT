import pytest
from unittest.mock import MagicMock, patch
import sys


@pytest.fixture(autouse=True)
def prevent_services_init():
    """Previene la inicialización real de servicios"""
    with patch("src.email_drive.EmailDrive"), \
         patch("src.download_files_emails.FileDrive"), \
         patch("src.file_managements.FileManagements"), \
         patch("src.upload_drive.UploadDrive"), \
         patch("src.idu_config.IduConfig"):
        
        if 'main_correos' in sys.modules:
            del sys.modules['main_correos']
        
        yield
        
        if 'main_correos' in sys.modules:
            del sys.modules['main_correos']


@pytest.fixture
def mocks():
    """Fixture que crea todos los mocks necesarios"""
    return {
        'email': MagicMock(),
        'downloader': MagicMock(),
        'list_mgr': MagicMock(),
        'upload': MagicMock(),
        'config': MagicMock(download_path="/fake/path"),
        'logger': MagicMock()
    }


def test_main_sin_correos(mocks):
    """Test cuando no hay correos para procesar"""
    mocks['email'].label_idu_emails_per_month.return_value = 0
    mocks['list_mgr'].delete_files.return_value = 5
    
    with patch("main_correos.etiquetar_correos", mocks['email']), \
         patch("main_correos.downloader", mocks['downloader']), \
         patch("main_correos.list_manager", mocks['list_mgr']), \
         patch("main_correos.uploadDrive_instance", mocks['upload']), \
         patch("main_correos.config", mocks['config']), \
         patch("main_correos.logger", mocks['logger']), \
         patch("main_correos.os.path.exists", return_value=True):
        
        from main_correos import main
        main()
        
        mocks['logger'].warning.assert_called_once_with(
            "No hay correos para procesar. Finalizando ejecución."
        )
        mocks['downloader'].download_files.assert_not_called()


def test_main_con_correos(mocks):
    """Test del flujo completo cuando hay correos"""
    mock_df = MagicMock()
    
    mocks['email'].label_idu_emails_per_month.return_value = 5
    mocks['list_mgr'].delete_files.return_value = 3
    mocks['downloader'].download_files.return_value = 5
    mocks['upload'].upload_files.return_value = 5
    mocks['list_mgr'].list_files_to_dataframe.return_value = mock_df
    mocks['list_mgr'].actualizar_estado_descargado.return_value = 5
    
    with patch("main_correos.etiquetar_correos", mocks['email']), \
         patch("main_correos.downloader", mocks['downloader']), \
         patch("main_correos.list_manager", mocks['list_mgr']), \
         patch("main_correos.uploadDrive_instance", mocks['upload']), \
         patch("main_correos.config", mocks['config']), \
         patch("main_correos.logger", mocks['logger']), \
         patch("main_correos.os.path.exists", return_value=True):
        
        from main_correos import main
        main()
        
        mocks['email'].label_idu_emails_per_month.assert_called_once()
        mocks['downloader'].download_files.assert_called_once()
        mocks['upload'].upload_files.assert_called_once()
        mocks['list_mgr'].actualizar_estado_descargado.assert_called_once_with(mock_df)


def test_main_directorio_no_existe(mocks):
    """Test cuando el directorio de descarga no existe"""
    mocks['email'].label_idu_emails_per_month.return_value = 5
    mocks['downloader'].download_files.return_value = 5
    mocks['upload'].upload_files.return_value = 5
    mocks['list_mgr'].list_files_to_dataframe.return_value = MagicMock()
    mocks['list_mgr'].actualizar_estado_descargado.return_value = 5
    
    with patch("main_correos.etiquetar_correos", mocks['email']), \
         patch("main_correos.downloader", mocks['downloader']), \
         patch("main_correos.list_manager", mocks['list_mgr']), \
         patch("main_correos.uploadDrive_instance", mocks['upload']), \
         patch("main_correos.config", mocks['config']), \
         patch("main_correos.logger", mocks['logger']), \
         patch("main_correos.os.path.exists", return_value=False):
        
        from main_correos import main
        main()
        
        mocks['list_mgr'].delete_files.assert_not_called()
        mocks['downloader'].download_files.assert_called_once()