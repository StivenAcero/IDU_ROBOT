from src.drive import get_credentials, get_sheets_service, read_sheet
import json
import os

def load_config(config_path='config.json'):
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: El archivo {config_path} no tiene formato JSON válido")
        print(f"Detalle: {e.msg} en línea {e.lineno}, columna {e.colno}")
        return None

def main():
    
    config = load_config('config/config.json')
    if not config:
        print("No se pudo cargar la configuración")
        return
    
    SPREADSHEET_ID = config['SPREADSHEET_ID']
    RANGE_NAME = 'SIN_IDENTIFICAR!A1:B'
    
    # 1. Obtener credenciales
    print("Obteniendo credenciales...")
    creds = get_credentials('config/')
    
    # 2. Crear servicio de Sheets
    print("Creando servicio de Google Sheets...")
    sheets_service = get_sheets_service(creds)
    
    # 3. Leer datos
    print(f"Leyendo datos del rango {RANGE_NAME}...")
    data = read_sheet(sheets_service, SPREADSHEET_ID, RANGE_NAME)
    
    # 4. Procesar datos
    if data:
        print(f"\n✓ Se encontraron {len(data)} filas")
        print("\nDatos:")
        for i, row in enumerate(data, 1):
            print(f"Fila {i}: {row}")
    else:
        print("✗ No se encontraron datos.")


if __name__ == "__main__":
    main()