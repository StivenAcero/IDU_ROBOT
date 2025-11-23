import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


class GoogleCredentials:

    @staticmethod
    def get_credentials(scopes, root_path='config/'):
        token_api = 'token.json'
        credentials_file = 'credentials.json'
        creds = None
        if os.path.exists(root_path + token_api):
            creds = Credentials.from_authorized_user_file(root_path + token_api, scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    root_path +  credentials_file, scopes)
                creds = flow.run_local_server(port=0)
            with open(root_path + token_api, 'w', encoding='utf-8') as token:
                token.write(creds.to_json())
        return creds
    