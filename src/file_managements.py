import os
import logging
from src.idu_config import IduConfig

logger = logging.getLogger(__name__)


class FileManagements:
    
    def __init__(self):
        self._config = IduConfig.load_config('config/config.json')
        
    def create_folder_if_not_exists(self, ruta_carpeta):
        try:
            if not os.path.exists(ruta_carpeta):
                os.makedirs(ruta_carpeta)
                logger.info("Carpeta creada: %s", ruta_carpeta)
            else:
                logger.info("La carpeta ya existe: %s", ruta_carpeta)
            return True

        except Exception as e:
            logger.error("Error al crear la carpeta %s: %s", ruta_carpeta, e)
            return False

    def delete_files(self, ruta_carpeta):
        try:
            if not os.path.exists(ruta_carpeta):
                logger.warning("La carpeta %s no existe", ruta_carpeta)
                return False

            for elemento in os.listdir(ruta_carpeta):
                ruta_completa = os.path.join(ruta_carpeta, elemento)

                if os.path.isfile(ruta_completa):
                    os.remove(ruta_completa)
                    logger.info("Archivo eliminado: %s", elemento)

            logger.info("Todos los archivos han sido eliminados")
            return True
        except Exception as e:
            logger.error("Error al eliminar archivos en %s: %s", ruta_carpeta, e)
            return False

