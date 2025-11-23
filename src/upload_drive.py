from src.idu_config import IduConfig
from googleapiclient.discovery import build
from src.google_credentials import GoogleCredentials
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import os
import time
from datetime import datetime

class UploadDrive:
    def __init__(self):
        self._config = IduConfig.load_config('config/config.json')
        self._creds = GoogleCredentials.get_credentials(self._config.scopes, root_path='config/')
        self._service = build('drive', 'v3', credentials=self._creds)
        self._max_retries = 5
        self._scope = self._config.scopes
        
    def get_current_month_folder(self, parent_folder_id):
        current_month = datetime.now().strftime('%m')  # Ej: '11'
        query = f"name contains '{current_month}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        try:
            results = self._service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            folders = results.get('files', [])
            
            # Filtrar carpetas que empiecen con el número del mes
            for folder in folders:
                if folder['name'].startswith(current_month):
                    print(f"Carpeta encontrada: {folder['name']} (ID: {folder['id']})")
                    return folder['id']
            
            print(f"Carpeta que empiece con '{current_month}' no encontrada")
            return None
            
        except HttpError as error:
            print(f"Error al buscar carpeta: {error}")
            return None

    def upload_files(self, local_folder, drive_folder_id):
        if not os.path.exists(local_folder):
            print(f"Error: La carpeta {local_folder} no existe")
            return {'success': [], 'failed': []}
        
        uploaded_files = []
        failed_files = []
        
        for filename in os.listdir(local_folder):
            file_path = os.path.join(local_folder, filename)
            
            # Solo procesar archivos (no directorios)
            if not os.path.isfile(file_path):
                continue
            
            file_metadata = {
                'name': filename,
                'parents': [drive_folder_id]
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            for attempt in range(self._max_retries):
                try:
                    file = self._service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id',
                        supportsAllDrives=True
                    ).execute()
                    
                    file_id = file.get('id')
                    print(f"Archivo {filename} subido con éxito. ID: {file_id}")
                    uploaded_files.append({'filename': filename, 'id': file_id})
                    break
                    
                except HttpError as error:
                    print(f"Error al subir archivo {filename}: {error}")
                    
                    if attempt < self._max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"Reintentando en {wait_time} segundos...")
                        time.sleep(wait_time)
                    else:
                        print(f"Número máximo de reintentos alcanzado para {filename}")
                        failed_files.append(filename)
                        break
        print(f"- Archivos subidos exitosamente: {len(uploaded_files)}")
        print(f"- Archivos fallidos: {len(failed_files)}")
        return {
            'success': uploaded_files,
            'failed': failed_files
        }