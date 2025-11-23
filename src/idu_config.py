import json
from typing import Dict, Any


class IduConfig:
    def __init__(self):
        self.spreadsheet_id = None
        self.range_name = None
        self.scopes = None
        self.target_url = None
        self.user_name = None
        self.request_email = None
        self.prefs: Dict[str, Any] = {}
        self.dowload_path = None
        self.drive_folder_id = None

    @staticmethod
    def load_config(config_path="config/config.json"):
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config_data = json.load(file)

            config = IduConfig()
            config.spreadsheet_id = config_data.get("spreadsheet_id")
            config.range_name = config_data.get("range_name")
            config.scopes = config_data.get("scopes")
            config.target_url = config_data.get("url_chat")
            config.user_name = config_data.get("name_user")
            config.request_email = config_data.get("mail_requests")
            config.prefs = config_data.get("prefs", {})
            config.dowload_path = config_data.get("download_path")
            config.drive_folder_id = config_data.get("drive_folder_id")
            
            return config
        except FileNotFoundError as e:
            raise FileNotFoundError(f"No se encontró el archivo {config_path}") from e
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                "El archivo de configuración no es un JSON válido.",
                e.doc,
                e.pos
            ) from e