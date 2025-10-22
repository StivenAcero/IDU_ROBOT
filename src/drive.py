import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request



def get_credentials(root_path='config/'):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly','https://www.googleapis.com/auth/drive']
    creds = None
    if os.path.exists(root_path + 'token.json'):
        creds = Credentials.from_authorized_user_file(root_path + 'token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                root_path + 'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(root_path + 'token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

creds = get_credentials('config/')

def get_sheets_service(creds):
    """Crear el servicio de Google Sheets"""
    return build('sheets', 'v4', credentials=creds)

def read_sheet(service, spreadsheet_id, range_name):
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        return values
    except Exception as e:
        print(f"Error al leer la hoja: {e}")
        return None