import pytest
from unittest.mock import MagicMock, patch
import sys


@pytest.fixture(autouse=True)
def prevent_browser_launch():
    """Previene que se abra el navegador al importar main"""
    # Mockear las clases ANTES de importar main
    with patch("src.idu_service.IduService") as mock_idu_cls, \
         patch("src.sheet_service.SheetService") as mock_sheet_cls, \
         patch("src.idu_config.IduConfig.load_config") as mock_config:
        
        # Configurar que retornen mocks en lugar de instancias reales
        mock_idu_cls.return_value = MagicMock()
        mock_sheet_cls.return_value = MagicMock()
        mock_config.return_value = MagicMock()
        
        # Limpiar el módulo main si ya fue importado
        if 'main' in sys.modules:
            del sys.modules['main']
        
        yield
        
        # Limpiar después del test
        if 'main' in sys.modules:
            del sys.modules['main']


def test_main_sin_datos():
    """Test cuando no hay datos"""
    mock_sheet = MagicMock()
    mock_idu = MagicMock()
    mock_logger = MagicMock()
    
    mock_sheet.read_sheet.return_value = []
    
    with patch("main.sheet_service", mock_sheet), \
         patch("main.idu_service", mock_idu), \
         patch("main.logger", mock_logger):
        
        from main import main
        main()
        
        mock_logger.warning.assert_called_once_with(
            "No se encontraron datos para procesar, fin del proceso."
        )
        mock_sheet.validate_missing_files.assert_not_called()


def test_main_con_datos():
    """Test con datos válidos"""
    mock_sheet = MagicMock()
    mock_idu = MagicMock()
    mock_logger = MagicMock()
    
    datos = [["colA", "colB"], ["A", "B"], ["C", "D"]]
    
    mock_sheet.read_sheet.return_value = datos
    mock_sheet.validate_missing_files.return_value = (2, ["chip1", "chip2"], 3)
    mock_sheet.agrupar_chips_sin_estado.return_value = MagicMock()
    
    with patch("main.sheet_service", mock_sheet), \
         patch("main.idu_service", mock_idu), \
         patch("main.logger", mock_logger):
        
        from main import main
        main()
        
        mock_sheet.read_sheet.assert_called_once()
        mock_sheet.validate_missing_files.assert_called_once_with(datos)


def test_main_data_none():
    """Test cuando read_sheet retorna None"""
    mock_sheet = MagicMock()
    mock_idu = MagicMock()
    mock_logger = MagicMock()
    
    mock_sheet.read_sheet.return_value = None
    
    with patch("main.sheet_service", mock_sheet), \
         patch("main.idu_service", mock_idu), \
         patch("main.logger", mock_logger):
        
        from main import main
        main()
        
        mock_logger.warning.assert_called_once_with(
            "No se encontraron datos para procesar, fin del proceso."
        )
        mock_sheet.validate_missing_files.assert_not_called()