import logging
import os
import time
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from src.google_credentials import GoogleCredentials
from src.idu_config import IduConfig


class UploadDrive:
    def __init__(self):
        self._config = IduConfig.load_config('config/config.json')
        self._creds = GoogleCredentials.get_credentials(self._config.scopes, root_path='config/')
        self._service = build('drive', 'v3', credentials=self._creds)
        self._max_retries = 5
        self._logger = logging.getLogger(__name__)

    def get_current_year_folder(self) -> str | None:
        """
        Busca la carpeta del año actual dentro de la carpeta raíz configurada.
        
        Returns:
            str | None: ID de la carpeta del año o None si no existe
        """
        current_year = datetime.now().strftime('%Y')
        query = (
            f"name = '{current_year}' and "
            f"'{self._config.drive_folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"trashed=false"
        )
        
        try:
            # pylint: disable=maybe-no-member
            results = self._service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            folders = results.get('files', [])
            if folders:
                year_folder = folders[0]
                self._logger.info(
                    "Carpeta año encontrada: %s (ID: %s)", 
                    year_folder['name'], 
                    year_folder['id']
                )
                return year_folder['id']
            
            self._logger.warning("Carpeta del año '%s' no encontrada", current_year)
            return None
            
        except HttpError as error:
            self._logger.error("Error al buscar carpeta del año: %s", error)
            return None

    def get_current_month_folder(self, year_folder_id: str) -> str | None:
        """
        Busca la carpeta del mes actual dentro de la carpeta del año.
        
        Args:
            year_folder_id: ID de la carpeta del año
            
        Returns:
            str | None: ID de la carpeta del mes o None si no existe
        """
        current_month = datetime.now().strftime('%m')
        query = (
            f"name contains '{current_month}' and "
            f"'{year_folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"trashed=false"
        )
        
        try:
            # pylint: disable=maybe-no-member
            results = self._service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            folders = results.get('files', [])
            for folder in folders:
                if folder['name'].startswith(current_month):
                    self._logger.info(
                        "Carpeta mes encontrada: %s (ID: %s)", 
                        folder['name'], 
                        folder['id']
                    )
                    return folder['id']
            
            self._logger.warning("Carpeta que empiece con '%s' no encontrada", current_month)
            return None
            
        except HttpError as error:
            self._logger.error("Error al buscar carpeta del mes: %s", error)
            return None

    def _validate_folders(self) -> tuple[str, str, str] | None:
        """
        Valida la existencia de carpetas (año, mes, local).
        
        Returns:
            tuple[str, str, str] | None: (year_folder_id, month_folder_id, local_folder) o None si falla
        """
        year_folder_id = self.get_current_year_folder()
        if not year_folder_id:
            self._logger.error("No se encontró la carpeta del año actual en Drive")
            return None
        
        month_folder_id = self.get_current_month_folder(year_folder_id)
        if not month_folder_id:
            self._logger.error("No se encontró la carpeta del mes actual en Drive")
            return None
        
        local_folder = self._config.download_path
        if not os.path.exists(local_folder):
            self._logger.error("La carpeta local %s no existe", local_folder)
            return None
        
        return year_folder_id, month_folder_id, local_folder

    def _upload_single_file(self, file_path: str, filename: str, month_folder_id: str) -> dict | None:
        """
        Sube un archivo individual a Drive con reintentos.
        
        Args:
            file_path: Ruta completa del archivo local
            filename: Nombre del archivo
            month_folder_id: ID de la carpeta destino en Drive
            
        Returns:
            dict | None: Info del archivo subido o None si falló
        """
        file_metadata = {
            'name': filename,
            'parents': [month_folder_id]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        
        for attempt in range(self._max_retries):
            try:
                # pylint: disable=maybe-no-member
                file = self._service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id',
                    supportsAllDrives=True
                ).execute()
                
                file_id = file.get('id')
                self._logger.info("Archivo %s subido con éxito. ID: %s", filename, file_id)
                return {'filename': filename, 'id': file_id}
                
            except HttpError as error:
                self._logger.error("Error al subir archivo %s: %s", filename, error)
                
                if attempt < self._max_retries - 1:
                    wait_time = 2 ** attempt
                    self._logger.info("Reintentando en %d segundos...", wait_time)
                    time.sleep(wait_time)
                else:
                    self._logger.error("Número máximo de reintentos alcanzado para %s", filename)
                    return None
        
        return None

    def upload_files(self) -> dict:
        """
        Sube archivos de la carpeta local configurada a la carpeta del mes actual en Drive.
        
        Returns:
            dict: Resultado con archivos exitosos y fallidos
        """
        validation_result = self._validate_folders()
        
        if validation_result is None:
            return {'success': [], 'failed': [], 'error': 'Validación de carpetas falló'}
        
        year_folder_id, month_folder_id, local_folder = validation_result
        
        uploaded_files = []
        failed_files = []
        
        for filename in os.listdir(local_folder):
            file_path = os.path.join(local_folder, filename)
            
            if not os.path.isfile(file_path):
                continue
            
            result = self._upload_single_file(file_path, filename, month_folder_id)
            
            if result:
                uploaded_files.append(result)
            else:
                failed_files.append(filename)
        
        self._logger.info("Archivos subidos exitosamente: %d", len(uploaded_files))
        self._logger.info("Archivos fallidos: %d", len(failed_files))
        
        return {
            'success': uploaded_files,
            'failed': failed_files
        }
