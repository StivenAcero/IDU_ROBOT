from src.email_drive import EmailDrive


etiquetar_correos = EmailDrive()

def main():
    etiquetar_correos.label_idu_emails_per_month()
if __name__ == "__main__":
    main()
    
 