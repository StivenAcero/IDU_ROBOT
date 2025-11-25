import sys
import os
import unittest
import json
from unittest.mock import patch, mock_open
from src.idu_config import IduConfig
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestIduConfigInit(unittest.TestCase):
    """Tests para el constructor __init__"""
    def test_init_default_values(self):
        """Verifica que IduConfig inicializa con valores por defecto correctos"""
        config = IduConfig()
            
            # Verificar strings vacíos
        self.assertEqual(config.spreadsheet_id, '')
        self.assertEqual(config.range_name, '')
        self.assertEqual(config.target_url, '')
        self.assertEqual(config.user_name, '')
        self.assertEqual(config.request_email, '')
        self.assertEqual(config.download_path, '')
        self.assertEqual(config.drive_folder_id, '')
        self.assertEqual(config.label_email, '')
        self.assertEqual(config.mailer_idu, '')
        self.assertEqual(config.email_subject, '')
        self.assertIsInstance(config.scopes, list)
        self.assertEqual(config.scopes, [])
        self.assertIsInstance(config.prefs, dict)
        self.assertEqual(config.prefs, {})
        self.assertEqual(config.max_results_email, 500)

class TestIduConfigFromDict(unittest.TestCase):
    
    def setUp(self):
        self.config_data = {
            "spreadsheet_id": "test_spreadsheet_id",  # minúsculas
            "range_name": "Sheet1!A1:D10",  # minúsculas
            "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],  # minúsculas
            "url_chat": "https://example.com/api",
            "name_user": "test_user",  # minúsculas con guion bajo
            "mail_requests": "example@example.com",  # Nombre correcto
            "prefs": {"pref1": "value1", "pref2": "value2"}
        }
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.idu_config.json.load')
    def test_load_config_success(self, mock_json_load, mock_file):
        """Prueba exitosa: load_config carga correctamente"""
        mock_json_load.return_value = self.config_data
        
        config = IduConfig.load_config('config/config.json')
        
        self.assertEqual(config.spreadsheet_id, 'test_spreadsheet_id')
        self.assertEqual(config.range_name, 'Sheet1!A1:D10')
        self.assertEqual(config.scopes, ['https://www.googleapis.com/auth/spreadsheets.readonly'])
        self.assertEqual(config.target_url, 'https://example.com/api')
        self.assertEqual(config.user_name, 'test_user')
        self.assertEqual(config.request_email, 'example@example.com')
        self.assertEqual(config.prefs, {'pref1': 'value1', 'pref2': 'value2'})
        mock_file.assert_called_once_with('config/config.json', 'r', encoding='utf-8')
        
    def test_load_config_file_not_found_with_path(self):
        """Prueba: valida que el path aparece en el mensaje de error"""
        test_path = 'config/inexistente.json'
        
        with patch('builtins.open', side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError) as context:
                IduConfig.load_config(test_path)
            self.assertIn(test_path, str(context.exception))
            
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_json_decode_error_with_message(self, mock_file):
        """Prueba: JSON inválido con validación del mensaje personalizado"""
        mock_file.return_value.__enter__.return_value.read.return_value = "{"
        with self.assertRaises(json.JSONDecodeError) as context:
            IduConfig.load_config('config/config.json')
        exception = context.exception
        self.assertIn("configuración no es un JSON válido", str(exception))