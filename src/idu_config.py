import json
from typing import Dict, Any, List


class IduConfig:
    def __init__(self):
        self.spreadsheet_id: str = ''
        self.range_name: str = ''
        self.scopes: List[str] = []
        self.target_url: str = ''
        self.user_name: str = ''
        self.request_email: str = ''
        self.prefs: Dict[str, Any] = {}
        self.download_path: str = ''
        self.drive_folder_id: str = ''
        self.label_email: str = ''  # ← Ahora es str, no None
        self.mailer_idu: str = ''
        self.email_subject: str = ''
        self.max_results_email: int = 500

    @staticmethod
    def load_config(config_path: str = "config/config.json") -> 'IduConfig':
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config_data = json.load(file)

            config = IduConfig()
            config.spreadsheet_id = config_data.get("spreadsheet_id", '')
            config.range_name = config_data.get("range_name", '')
            config.scopes = config_data.get("scopes", [])
            config.target_url = config_data.get("url_chat", '')
            config.user_name = config_data.get("name_user", '')
            config.request_email = config_data.get("mail_requests", '')
            config.prefs = config_data.get("prefs", {})
            config.download_path = config_data.get("download_path", '')
            config.drive_folder_id = config_data.get("drive_folder_id", '')
            config.label_email = config_data.get("label_email", '')
            config.mailer_idu = config_data.get("mailer_idu", '')
            config.email_subject = config_data.get("email_subject", '')
            config.max_results_email = config_data.get("max_results_email")
            
            return config
        except FileNotFoundError as e:
            raise FileNotFoundError(f"No se encontró el archivo {config_path}") from e
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                "El archivo de configuración no es un JSON válido.",
                e.doc,
                e.pos
            ) from e