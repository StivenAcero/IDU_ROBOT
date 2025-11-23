from src.idu_config import IduConfig
from src.idu_service import IduService
from src.sheet_service import SheetService
import logging
from src.logs import setup_logging

logger = logging.getLogger(__name__)

config = IduConfig.load_config('config/config.json')
sheet_service = SheetService()
idu_service = IduService()

def main():
    setup_logging() 
    data = sheet_service.read_sheet(config.spreadsheet_id, config.range_name)
    encabezado = data[0] if data else []
    if not data:
        logger.warning("No se encontraron datos para procesar, fin del proceso.")
        return 
    _, registros_sin_estado, _ = sheet_service.validate_missing_files(data)
    df_solicitudes = sheet_service.agrupar_chips_sin_estado(registros_sin_estado, max_por_grupo=5)
    idu_service.procesar_chip_sin_estado(df_solicitudes,encabezado)
    
if __name__ == "__main__":
    main()