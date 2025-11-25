import logging
from datetime import date
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import build
from src.google_credentials import GoogleCredentials
from src.idu_config import IduConfig


MESES_ESPANOL = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


class EmailDrive:
    def __init__(self):
        self._config = IduConfig.load_config('config/config.json')
        self._creds = GoogleCredentials.get_credentials(self._config.scopes, root_path='config/')
        self._service = build('gmail', 'v1', credentials=self._creds)
        self._logger = logging.getLogger(__name__)
    
    def get_or_create_label(self, label_name: str | None = None) -> str:
        """Obtiene o crea una etiqueta."""
        label_name = label_name or self._config.label_email
        
        try:
             # pylint: disable=maybe-no-member
            results = self._service.users().labels().list(userId='me').execute()
            for lbl in results.get('labels', []):
                if lbl['name'] == label_name:
                    return lbl['id']
            
            self._logger.info("Creando etiqueta: %s", label_name)
             # pylint: disable=maybe-no-member
            created = self._service.users().labels().create(
                userId='me',
                body={
                    'name': label_name,
                    'labelListVisibility': 'labelShow',
                    'messageListVisibility': 'show'
                }
            ).execute()
            return created['id']
            
        except Exception as e:
            if 'already exists' in str(e).lower():
                return self.get_or_create_label(label_name)
            self._logger.error("Error con etiqueta '%s': %s", label_name, e)
            return ''
    
    def search_emails_today(self) -> list[str]:
        """Busca correos del día actual."""
        fecha_hoy = date.today().strftime('%Y/%m/%d')
        all_emails = []
        
        for subject in [self._config.mailer_idu, self._config.email_subject]:
            if subject:
                all_emails.extend(self._search_by_subject(subject, fecha_hoy))
        
        unique_emails = list(set(all_emails))
        self._logger.info("Correos encontrados: %d", len(unique_emails))
        return unique_emails
    
    def _search_by_subject(self, subject: str, fecha: str) -> list[str]:
        """Busca correos por asunto y fecha."""
        try:
             # pylint: disable=maybe-no-member
            results = self._service.users().messages().list(
                userId='me',
                q=f"subject:{subject} after:{fecha}",
                maxResults=self._config.max_results_email
            ).execute()
            return [msg['id'] for msg in results.get('messages', [])]
        except Exception as e:
            self._logger.error("Error buscando '%s': %s", subject, e)
            return []
    
    def add_label_to_emails(self, message_ids: list, label_ids: list, verificar: bool = True) -> dict:
        """Agrega etiquetas a correos."""
        if not message_ids:
            return {'labeled': 0, 'failed': 0}
        
        emails_to_tag = self._filter_emails_to_tag(message_ids, label_ids) if verificar else message_ids
        
        if not emails_to_tag:
            return {'labeled': 0, 'failed': 0}
        
        return self._batch_modify_labels(emails_to_tag, label_ids)
    
    def _filter_emails_to_tag(self, message_ids: list, label_ids: list) -> list:
        """Filtra correos que necesitan etiquetas."""
        emails_to_tag = []
        for msg_id in message_ids:
            try:
                 # pylint: disable=maybe-no-member
                message = self._service.users().messages().get(
                    userId='me', id=msg_id, format='metadata'
                ).execute()
                existing = message.get('labelIds', [])
                if not all(label in existing for label in label_ids):
                    emails_to_tag.append(msg_id)
            except Exception as e:
                self._logger.error("Error verificando correo %s: %s", msg_id, e)
        return emails_to_tag
    
    def _batch_modify_labels(self, message_ids: list, label_ids: list) -> dict:
        """Aplica etiquetas en batch."""
        try:
             # pylint: disable=maybe-no-member
            self._service.users().messages().batchModify(
                userId='me',
                body={'ids': message_ids, 'addLabelIds': label_ids}
            ).execute()
            return {'labeled': len(message_ids), 'failed': 0}
        except Exception as e:
            self._logger.error("Error etiquetando: %s", e)
            return {'labeled': 0, 'failed': len(message_ids)}
    
    def get_email_date(self, message_id: str) -> tuple:
        """Obtiene año y mes del correo."""
        try:
             # pylint: disable=maybe-no-member
            message = self._service.users().messages().get(
                userId='me', id=message_id, format='metadata', metadataHeaders=['Date']
            ).execute()
            
            for header in message.get('payload', {}).get('headers', []):
                if header['name'] == 'Date':
                    fecha = parsedate_to_datetime(header['value'])
                    return (fecha.year, fecha.month)
        except Exception as e:
            self._logger.error("Error obteniendo fecha %s: %s", message_id, e)
        
        return (None, None)
    
    def _group_emails_by_month(self, message_ids: list) -> tuple[dict, list]:
        """Agrupa correos por mes y separa los sin fecha."""
        correos_por_mes = {}
        correos_sin_fecha = []
        
        for msg_id in message_ids:
            anio, mes = self.get_email_date(msg_id)
            if anio and mes:
                correos_por_mes.setdefault((anio, mes), []).append(msg_id)
            else:
                correos_sin_fecha.append(msg_id)
        
        return correos_por_mes, correos_sin_fecha
    
    def _process_monthly_emails(self, correos_por_mes: dict, label_padre_id: str) -> tuple[dict, int]:
        """Procesa y etiqueta correos agrupados por mes."""
        estadisticas = {}
        total_etiquetados = 0
        
        for (anio, mes), message_ids in sorted(correos_por_mes.items()):
            nombre_mes = MESES_ESPANOL.get(mes, str(mes))
            label_mes = f"{self._config.label_email}/{nombre_mes} {anio}"
            label_mes_id = self.get_or_create_label(label_mes)
            
            if label_mes_id:
                resultado = self.add_label_to_emails(message_ids, [label_padre_id, label_mes_id])
                total_etiquetados += resultado['labeled']
                estadisticas[f"{nombre_mes} {anio}"] = {
                    'total': len(message_ids),
                    'nuevos': resultado['labeled']
                }
        
        return estadisticas, total_etiquetados
    
    def _process_dateless_emails(self, correos_sin_fecha: list, label_padre_id: str) -> tuple[dict, int]:
        """Procesa correos sin fecha."""
        if not correos_sin_fecha:
            return {}, 0
        
        resultado = self.add_label_to_emails(correos_sin_fecha, [label_padre_id])
        estadisticas = {
            'Sin fecha': {
                'total': len(correos_sin_fecha),
                'nuevos': resultado['labeled']
            }
        }
        return estadisticas, resultado['labeled']
    
    def label_idu_emails_per_month(self) -> dict:
        """Etiqueta correos IDU del día actual por mes."""
        self._logger.info("Iniciando etiquetado - Día: %s", date.today().strftime('%d/%m/%Y'))
        
        # Validar etiqueta padre
        label_padre_id = self.get_or_create_label()
        if not label_padre_id:
            return {'exitoso': False, 'error': 'No se pudo crear etiqueta padre'}
        
        # Buscar correos
        correos = self.search_emails_today()
        if not correos:
            return {'exitoso': True, 'total_encontrados': 0, 'procesados': 0}
        
        # Agrupar por mes
        correos_por_mes, correos_sin_fecha = self._group_emails_by_month(correos)
        
        # Procesar correos
        estadisticas_mes, total_mes = self._process_monthly_emails(correos_por_mes, label_padre_id)
        estadisticas_sin, total_sin = self._process_dateless_emails(correos_sin_fecha, label_padre_id)
        
        # Combinar resultados
        estadisticas = {**estadisticas_mes, **estadisticas_sin}
        total_etiquetados = total_mes + total_sin
        
        self._logger.info("Resumen - Total: %d, Etiquetados: %d", len(correos), total_etiquetados)
        
        return {
            'exitoso': True,
            'total_encontrados': len(correos),
            'procesados': total_etiquetados,
            'por_mes': estadisticas
        }