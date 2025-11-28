from src.email_drive import EmailDrive
from src.download_files_emails import FileDrive
from src.file_managements import FileManagements
from src.idu_config import IduConfig
from src.upload_drive import UploadDrive
import os 
import logging
from datetime import datetime
# ===========================
# CONFIGURACIÓN DEL LOGGER
# ===========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(BASE_DIR, "logs")
os.makedirs(logs_dir, exist_ok=True)

log_filename = os.path.join(
    logs_dir,
    "idu_robot_%s.log" % datetime.now().strftime("%Y-%m-%d")
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
etiquetar_correos = EmailDrive()
downloader = FileDrive()
list_manager = FileManagements()
uploadDrive_instance = UploadDrive()
config = IduConfig()



# FUNCIÓN PRINCIPAL
def main():
    
    logger.info("==== Inicio ejecución IDU Robot correos ====")
    # Eliminar archivos locales previos
    if os.path.exists(config.download_path):
        eliminar_archivos = list_manager.delete_files(config.download_path)
        logger.info("Archivos locales eliminados: %s", eliminar_archivos)
    else:
        logger.info("El directorio %s no existe. No hay archivos para eliminar.", config.download_path)
    # Etiquetar correos
    etiqueta = etiquetar_correos.label_idu_emails_per_month()
    logger.info("Correos etiquetados por mes: %s", etiqueta)
    # Validar si hay correos para procesar
    if not etiqueta or etiqueta == 0:
        logger.warning("No hay correos para procesar. Finalizando ejecución.")
        logger.info("==== Fin ejecución IDU Robot ====")
        return
    # Continuar con el resto del proceso solo si hay correos
    download = downloader.download_files()
    logger.info("Archivos descargados: %s", download)

    subir = uploadDrive_instance.upload_files()
    logger.info("Archivos subidos: %s", subir)

    listar = list_manager.actualizar_estado_descargado(
        list_manager.list_files_to_dataframe()
    )
    logger.info("Cantidad de chips actualizados: %s", listar)

    logger.info("==== Fin ejecución IDU Robot correos ====")

if __name__ == "__main__":
    main()
