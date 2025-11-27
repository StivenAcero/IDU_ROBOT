from src.email_drive import EmailDrive
from src.download_files_emails import FileDrive
from src.file_managements import FileManagements
from src.idu_config import IduConfig
from src.upload_drive import UploadDrive

etiquetar_correos = EmailDrive()
downloader = FileDrive()
list_manager = FileManagements()
uploadDrive_instance = UploadDrive()
config = IduConfig()

def main():
    subir = uploadDrive_instance.upload_files()
    print("Archivos subidos", subir)
    
    
if __name__ == "__main__":
    main()
    
 