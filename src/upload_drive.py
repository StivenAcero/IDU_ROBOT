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

    def create_year_folder(self) -> str | None:
        current_year = datetime.now().strftime('%Y')

        metadata = {
            'name': current_year,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [self._config.drive_folder_id]
        }

        try:
            # pylint: disable=maybe-no-member
            folder = self._service.files().create(
                body=metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()

            folder_id = folder.get('id')
            self._logger.info("Carpeta de año creada: %s (ID: %s)", current_year, folder_id)
            return folder_id

        except HttpError as error:
            self._logger.error("Error al crear carpeta del año: %s", error)
            return None

    def get_current_year_folder(self) -> str | None:
        current_year = datetime.now().strftime('%Y')

        query = (
            f"name = '{current_year}' and "
            f"'{self._config.drive_folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and trashed=false"
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
                folder = folders[0]
                self._logger.info("Carpeta de año encontrada: %s (ID: %s)", folder['name'], folder['id'])
                return folder['id']

            self._logger.warning("Carpeta año '%s' no encontrada — creando...", current_year)
            return self.create_year_folder()

        except HttpError as error:
            self._logger.error("Error al buscar carpeta del año: %s", error)
            return None

    def create_month_folder(self, year_folder_id: str) -> str | None:
        month_number = datetime.now().strftime('%m')

        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        month_name = meses[int(month_number) - 1]

        folder_name = f"{month_number} {month_name}"

        metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [year_folder_id]
        }

        try:
            # pylint: disable=maybe-no-member
            folder = self._service.files().create(
                body=metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()

            new_id = folder.get('id')
            self._logger.info("Carpeta de mes creada: %s (ID: %s)", folder_name, new_id)
            return new_id

        except HttpError as error:
            self._logger.error("Error al crear carpeta del mes: %s", error)
            return None

    def get_current_month_folder(self, year_folder_id: str) -> str | None:
        month_number = datetime.now().strftime('%m')

        query = (
            f"name contains '{month_number}' and "
            f"'{year_folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and trashed=false"
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
                if folder['name'].startswith(month_number):
                    self._logger.info("Carpeta mes encontrada: %s (ID: %s)", folder['name'], folder['id'])
                    return folder['id']

            self._logger.warning("Carpeta mes '%s' no encontrada — creando...", month_number)
            return self.create_month_folder(year_folder_id)

        except HttpError as error:
            self._logger.error("Error al buscar carpeta del mes: %s", error)
            return None
    def _validate_folders(self) -> tuple[str, str, str] | None:
        year_folder_id = self.get_current_year_folder()
        if not year_folder_id:
            self._logger.error("No se pudo obtener/crear la carpeta del año")
            return None

        month_folder_id = self.get_current_month_folder(year_folder_id)
        if not month_folder_id:
            self._logger.error("No se pudo obtener/crear la carpeta del mes")
            return None

        local_folder = self._config.download_path
        if not os.path.exists(local_folder):
            self._logger.error("La carpeta local %s no existe", local_folder)
            return None

        return year_folder_id, month_folder_id, local_folder
    
    def _upload_single_file(self, file_path: str, filename: str, month_folder_id: str) -> dict | None:
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
                self._logger.info("Archivo %s subido. ID: %s", filename, file_id)
                return {'filename': filename, 'id': file_id}

            except HttpError as error:
                self._logger.error("Error al subir %s: %s", filename, error)

                if attempt < self._max_retries - 1:
                    wait_time = 2 ** attempt
                    self._logger.info("Reintentando en %d segundos...", wait_time)
                    time.sleep(wait_time)
                else:
                    self._logger.error("Falló definitivamente: %s", filename)
                    return None

        return None
    def upload_files(self) -> dict:
        validation = self._validate_folders()

        if validation is None:
            return {'success': [], 'failed': [], 'error': 'Validación de carpetas falló'}

        _, month_folder_id, local_folder = validation

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
