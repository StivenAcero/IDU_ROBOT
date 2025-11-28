from src.idu_config import IduConfig
from src.idu_service import IduService
from src.sheet_service import SheetService
import logging
import os
from datetime import datetime


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

config = IduConfig.load_config('config/config.json')
sheet_service = SheetService()
idu_service = IduService()

def main(): 
    logger.info("==== Inicio ejecución IDU Robot  ====")
    data = sheet_service.read_sheet()
    encabezado = data[0] if data else []
    if not data:
        logger.warning("No se encontraron datos para procesar, fin del proceso.")
        return 
    _, registros_sin_estado, _ = sheet_service.validate_missing_files(data)
    df_solicitudes = sheet_service.agrupar_chips_sin_estado(registros_sin_estado, max_por_grupo=5)
    idu_service.procesar_chip_sin_estado(df_solicitudes,encabezado)
    logger.info(" Fin ejecución IDU Robot")
if __name__ == "__main__":
    main()