from unittest.mock import Mock, patch, mock_open
from src.google_credentials import GoogleCredentials


@patch('src.google_credentials.InstalledAppFlow.from_client_secrets_file')
@patch('src.google_credentials.Request')
@patch('src.google_credentials.Credentials.from_authorized_user_file')
@patch('builtins.open', new_callable=mock_open)
@patch('src.google_credentials.os.path.exists')

class TestGoogleCredentials:
    def test_token_valido_existente(
        self, mock_exists, mock_file, mock_from_file, mock_request, mock_flow):
        scopes = ['https://www.googleapis.com/auth/calendar']
        mock_creds = Mock()
        mock_creds.valid = True
        mock_exists.return_value = True
        mock_from_file.return_value = mock_creds

        # Act
        result = GoogleCredentials.get_credentials(scopes)

        # Assert
        assert result == mock_creds
        mock_from_file.assert_called_once_with('config/token.json', scopes)
        mock_file.assert_not_called()  # No debe escribir

    def test_token_expirado_se_refresca(self, mock_exists, mock_file, mock_from_file, mock_request, mock_flow ):
        """Cuando el token está expirado, lo refresca"""
        # Arrange
        scopes =  ['https://www.googleapis.com/auth/calendar']
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = 'token123'
        mock_creds.to_json.return_value = '{"refreshed": true}'
        mock_exists.return_value = True
        mock_from_file.return_value = mock_creds

        # Act
        result = GoogleCredentials.get_credentials(scopes)

        # Assert
        assert result == mock_creds
        mock_creds.refresh.assert_called_once()
        mock_file.assert_called_once_with('config/token.json', 'w', encoding='utf-8')

    def test_sin_token_crea_nuevo( self, mock_exists, mock_file, mock_from_file, mock_request, mock_flow):
    
        scopes = ['https://www.googleapis.com/auth/calendar']
        mock_flow_instance = Mock()
        mock_new_creds = Mock()
        mock_new_creds.to_json.return_value = '{"new": true}'
        
        mock_exists.return_value = False
        mock_flow.return_value = mock_flow_instance
        mock_flow_instance.run_local_server.return_value = mock_new_creds

        # Act
        result = GoogleCredentials.get_credentials(scopes)

        # Assert
        assert result == mock_new_creds
        mock_flow.assert_called_once_with('config/credentials.json', scopes)
        mock_flow_instance.run_local_server.assert_called_once_with(port=0)
        mock_file.assert_called_once()

    def test_token_invalido_crea_nuevo(self, mock_exists, mock_file, mock_from_file, mock_request, mock_flow):
   
        scopes = ['https://www.googleapis.com/auth/calendar']
        mock_old_creds = Mock()
        mock_old_creds.valid = False
        mock_old_creds.expired = False
        mock_old_creds.refresh_token = None
        
        mock_flow_instance = Mock()
        mock_new_creds = Mock()
        mock_new_creds.to_json.return_value = '{"new": true}'
        
        mock_exists.return_value = True
        mock_from_file.return_value = mock_old_creds
        mock_flow.return_value = mock_flow_instance
        mock_flow_instance.run_local_server.return_value = mock_new_creds

        # Act
        result = GoogleCredentials.get_credentials(scopes)

        # Assert
        assert result == mock_new_creds
        mock_flow.assert_called_once()

    def test_root_path_personalizado(self, mock_exists, mock_file, mock_from_file, mock_request, mock_flow ):
        # Arrange
        scopes = ['https://www.googleapis.com/auth/calendar']
        custom_path = 'mi/ruta/'
        mock_creds = Mock()
        mock_creds.valid = True
        
        mock_exists.return_value = True
        mock_from_file.return_value = mock_creds

        # Act
        result = GoogleCredentials.get_credentials(scopes, root_path=custom_path)
        assert result is not None 

        # Assert
        mock_exists.assert_called_with('mi/ruta/token.json')
        mock_from_file.assert_called_with('mi/ruta/token.json', scopes)
    