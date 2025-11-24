from googleapiclient.discovery import build
from src.google_credentials import GoogleCredentials
from src.idu_config import IduConfig
import logging
from datetime import date


MESES_ESPANOL = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

class EmailDrive:
    def __init__(self) :
        self._config = IduConfig.load_config('config/config.json')
        self._creds = GoogleCredentials.get_credentials(self._config.scopes, root_path='config/')
        self._service = build('gmail', 'v1', credentials=self._creds)
        self._logger = logging.getLogger(__name__)
    
    def get_id_label(self, label_name: str | None = None) -> str:
        try:
            # Determinar qué etiqueta buscar
            label_to_find = label_name or self._config.label_email
            
            # pylint: disable=maybe-no-member
            results = self._service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            for lbl in labels:
                if lbl['name'] == label_to_find:
                    self._logger.info("Etiqueta encontrada: %s (ID: %s)", 
                                    label_to_find, lbl['id'])
                    return lbl['id']
            
            self._logger.warning("Etiqueta '%s' no encontrada", label_to_find)
            return ''
        except Exception as e:
            self._logger.error("Error al buscar etiqueta: %s", e, exc_info=True)
            return ''
        
    def search_emails_today(self) -> list[str]:
        """Busca correos del día actual según configuración."""
        all_emails = []
        fecha_hoy = date.today().strftime('%Y/%m/%d')
        
        # Búsqueda con mailer_idu
        if self._config.mailer_idu:
            try:
                query = f"subject:{self._config.mailer_idu} after:{fecha_hoy}"
                # pylint: disable=maybe-no-member
                results = self._service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=self._config.max_results_email  # Desde config
                ).execute()
                messages = results.get('messages', [])
                all_emails.extend([msg['id'] for msg in messages])
            except Exception as e:
                self._logger.error(
                    "Error al buscar correos con asunto '%s': %s", 
                    self._config.mailer_idu, 
                    e, 
                    exc_info=True
                )
        
        # Búsqueda con email_subject
        if self._config.email_subject:
            try:
                query = f"subject:{self._config.email_subject} after:{fecha_hoy}"
                # pylint: disable=maybe-no-member
                results = self._service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=self._config.max_results_email  # Desde config
                ).execute()
                messages = results.get('messages', [])
                all_emails.extend([msg['id'] for msg in messages])
            except Exception as e:
                self._logger.error(
                    "Error al buscar correos con asunto '%s': %s", 
                    self._config.email_subject, 
                    e, 
                    exc_info=True
                )
        
        # Eliminar duplicados
        unique_emails = list(set(all_emails))
        self._logger.info(
            "Correos encontrados para el día %s: %d", 
            fecha_hoy, 
            len(unique_emails)
        )
        return unique_emails
    
    def add_label_to_emails(self,message_ids, label_ids, verificar=True) :
        if not message_ids:
            return {'labeled': 0, 'failed': 0}
        emails_to_tag = message_ids
        if verificar:
            emails_to_tag = []
            for msg_id in message_ids:
                try:
                    # pylint: disable=maybe-no-member
                    message = self._service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='metadata',
                        metadataHeaders=[]
                    ).execute()
                    existing_labels = message.get('labelIds', [])
                    if not all(label in existing_labels for label in label_ids):
                        emails_to_tag.append(msg_id)
                except Exception as e:
                    self._logger.error(f"Error al verificar etiquetas del correo {msg_id}: {e}", exc_info=True)
                    
        if not emails_to_tag:
                self._logger.info("No hay correos para etiquetar después de la verificación.")
                return {'labeled': 0, 'failed': 0}
        try:
            self._logger.info(f"Etiquetando {len(emails_to_tag)} correos...")
            self._service.users().messages().batchModify(  # pylint: disable=maybe-no-member
                userId='me',
                body={
                    'ids': emails_to_tag,
                    'addLabelIds': label_ids
                }
            ).execute()
            return {'labeled': len(emails_to_tag), 'failed': 0}
        except Exception as e:
            self._logger.error(f"Error al etiquetar correos: {e}", exc_info=True)
            return {'labeled': 0, 'failed': len(emails_to_tag)}
        
    def create_nested_label(self, parent_label_name: str, new_label_name: str) -> str:
        complete_name = f"{parent_label_name}/{new_label_name}"
        # Verificar si ya existe
        label_id = self.get_id_label(complete_name)
        if label_id:
            self._logger.info("La etiqueta '%s' ya existe con ID: %s", complete_name, label_id)
            return label_id
        try:
            self._logger.info("Creando etiqueta: %s", complete_name)
            # pylint: disable=maybe-no-member
            created_label = self._service.users().labels().create(
                userId='me',
                body={
                    'name': complete_name,
                    'labelListVisibility': 'labelShow',
                    'messageListVisibility': 'show'
                }
            ).execute()
            
            self._logger.info("Etiqueta '%s' creada exitosamente", complete_name)
            return created_label['id']
        except Exception as e:
            # Si la etiqueta ya existe (condición de carrera), intentar obtenerla
            if 'already exists' in str(e).lower():
                self._logger.warning("La etiqueta ya existe, obteniendo ID...")
                return self.get_id_label(complete_name)
            
            self._logger.error("Error al crear etiqueta '%s': %s", complete_name, e, exc_info=True)
            return ''
        
    def get_date_email(self, message_id: str) -> str:
        try:
            # pylint: disable=maybe-no-member
            message = self._service.users().messages().get(
                userId='me',
                id=message_id,
                format='metadata',
                metadataHeaders=['Date']
            ).execute()
                
            headers = message.get('payload', {}).get('headers', [])
            for header in headers:
                if header['name'] == 'Date':
                    return header['value']
            self._logger.warning("Fecha no encontrada en el correo %s", message_id)
            return ''
        except Exception as e:
            self._logger.error(
                "Error al obtener fecha %s: %s", 
                message_id, 
                e, 
                exc_info=True
            )
            return ''
      
    
    def label_idu_emails_per_month(self) -> dict:
        """Etiqueta correos IDU del día actual por mes."""
        self._logger.info("Iniciando etiquetado de correos IDU - Día: %s", 
                        date.today().strftime('%d/%m/%Y'))
        
        # Validar etiqueta padre
        label_padre_id = self.get_id_label()
        if not label_padre_id:
            return self._error_etiqueta_no_existe()
        
        # Buscar correos
        todos_correos = self.search_emails_today()
        if not todos_correos:
            return self._sin_correos_encontrados()
        
        # Agrupar y procesar
        correos_por_mes, correos_sin_fecha = self._agrupar_correos_por_mes(todos_correos)
        estadisticas, total_etiquetados = self._procesar_correos_agrupados(
            correos_por_mes, correos_sin_fecha, label_padre_id
        )
        
        # Log resumen
        self._log_resumen(todos_correos, total_etiquetados, estadisticas)
        
        return {
            'exitoso': True,
            'total_encontrados': len(todos_correos),
            'procesados': total_etiquetados,
            'por_mes': estadisticas
        }


    def _error_etiqueta_no_existe(self) -> dict:
        error_msg = f"La etiqueta '{self._config.label_email}' no existe"
        self._logger.error(error_msg)
        return {'exitoso': False, 'error': error_msg}


    def _sin_correos_encontrados(self) -> dict:
        """Retorna resultado cuando no hay correos."""
        self._logger.warning("No se encontraron correos del día actual")
        return {'exitoso': True, 'total_encontrados': 0, 'procesados': 0}


    def _agrupar_correos_por_mes(self, todos_correos: list[str]) -> tuple[dict, list]:
        """Agrupa correos por año y mes."""
        self._logger.info("Agrupando %d correos por mes", len(todos_correos))
        correos_por_mes = {}
        correos_sin_fecha = []
        
        for msg_id in todos_correos:
            self._clasificar_correo_por_fecha(msg_id, correos_por_mes, correos_sin_fecha)
        
        self._logger.info("Encontrados %d meses diferentes", len(correos_por_mes))
        if correos_sin_fecha:
            self._logger.warning("%d correos sin fecha", len(correos_sin_fecha))
        
        return correos_por_mes, correos_sin_fecha


    def _clasificar_correo_por_fecha(self, msg_id: str, correos_por_mes: dict, 
                                    correos_sin_fecha: list) -> None:
        """Clasifica un correo según su fecha."""
        fecha_str = self.get_date_email(msg_id)
        if not fecha_str:
            correos_sin_fecha.append(msg_id)
            return
        
        anio, mes = self._extraer_anio_mes(fecha_str)
        if anio and mes:
            clave = (anio, mes)
            correos_por_mes.setdefault(clave, []).append(msg_id)
        else:
            correos_sin_fecha.append(msg_id)


    def _procesar_correos_agrupados(self, correos_por_mes: dict, 
                                    correos_sin_fecha: list, 
                                    label_padre_id: str) -> tuple[dict, int]:
        """Procesa correos agrupados y retorna estadísticas."""
        estadisticas = {}
        total_etiquetados = 0
        
        # Procesar correos con fecha
        total_etiquetados += self._procesar_correos_con_fecha(
            correos_por_mes, label_padre_id, estadisticas
        )
        
        # Procesar correos sin fecha
        if correos_sin_fecha:
            total_etiquetados += self._procesar_correos_sin_fecha(
                correos_sin_fecha, label_padre_id, estadisticas
            )
        
        return estadisticas, total_etiquetados


    def _procesar_correos_con_fecha(self, correos_por_mes: dict, 
                                    label_padre_id: str, 
                                    estadisticas: dict) -> int:
        """Procesa correos que tienen fecha válida."""
        total_etiquetados = 0
        
        for (anio, mes), message_ids in sorted(correos_por_mes.items()):
            nombre_mes = MESES_ESPANOL.get(mes, str(mes))
            self._logger.info("Procesando %s %d - %d correos", nombre_mes, anio, len(message_ids))
            
            label_mes_id = self.create_nested_label(
                self._config.label_email, 
                f"{nombre_mes} {anio}"
            )
            
            if not label_mes_id:
                self._logger.error("No se pudo crear etiqueta para %s/%d", mes, anio)
                continue
            
            resultado = self.add_label_to_emails(
                message_ids, 
                [label_padre_id, label_mes_id],
                verificar=True
            )
            
            total_etiquetados += resultado['labeled']
            estadisticas[f"{nombre_mes} {anio}"] = {
                'total': len(message_ids),
                'nuevos': resultado['labeled'],
                'fallidos': resultado['failed']
            }
        
        return total_etiquetados


    def _procesar_correos_sin_fecha(self, correos_sin_fecha: list, 
                                    label_padre_id: str, 
                                    estadisticas: dict) -> int:
        """Procesa correos sin fecha válida."""
        self._logger.info("Procesando %d correos sin fecha", len(correos_sin_fecha))
        
        resultado = self.add_label_to_emails(
            correos_sin_fecha, 
            [label_padre_id],
            verificar=True
        )
        
        estadisticas['Sin fecha'] = {
            'total': len(correos_sin_fecha),
            'nuevos': resultado['labeled'],
            'fallidos': resultado['failed']
        }
        
        return resultado['labeled']


    def _log_resumen(self, todos_correos: list, total_etiquetados: int, 
                    estadisticas: dict) -> None:
        """Registra el resumen del procesamiento."""
        self._logger.info("Resumen - Total correos: %d, Etiquetados: %d", 
                        len(todos_correos), total_etiquetados)
        
        for mes, stats in estadisticas.items():
            self._logger.info("%s: %d/%d nuevos", mes, stats['nuevos'], stats['total'])


    def _extraer_anio_mes(self, fecha_str: str) -> tuple:
        """Extrae año y mes de una fecha RFC 2822."""
        try:
            from email.utils import parsedate_to_datetime
            fecha = parsedate_to_datetime(fecha_str)
            return (fecha.year, fecha.month)
        except Exception as e:
            self._logger.error("Error al parsear fecha '%s': %s", fecha_str, e)
            return (None, None)
