
from src.idu_config import IduConfig
from src.upload_drive import UploadDrive
from src.file_managements import FileManagements
import logging

logger = logging.getLogger(__name__)


def main():
    config = IduConfig.load_config('config/config.json')

    fm = FileManagements()
    
    if not fm.create_folder_if_not_exists(config.dowload_path):
        logger.error("No se pudo crear o verificar la carpeta de descarga.")
        return
    if not fm.delete_files(config.dowload_path):
        logger.error("No se pudieron eliminar los archivos previos.")
        return
    uploader = UploadDrive()
    month_folder_id = uploader.get_current_month_folder(config.drive_folder_id)

    if not month_folder_id:
        logger.error("No se pudo encontrar la carpeta del mes actual en Google Drive.")
        return

    # Subir archivos
    result = uploader.upload_files(config.dowload_path, month_folder_id)

    logger.info("Archivos subidos con éxito: %s", result['success'])
    logger.info("Archivos que fallaron al subir: %s", result['failed'])
    
if __name__ == "__main__":
    main()