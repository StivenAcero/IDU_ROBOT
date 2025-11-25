from src.email_drive import EmailDrive
from src.download_files_emails import FileDrive


etiquetar_correos = EmailDrive()
downloader = FileDrive()

def main():
    etiquetar_correos.label_idu_emails_per_month()
    #downloader.download_files()
    
    
if __name__ == "__main__":
    main()
    
 