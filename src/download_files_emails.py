import base64
import logging
import os
from datetime import date
from googleapiclient.discovery import build
from src.google_credentials import GoogleCredentials
from src.idu_config import IduConfig


class FileDrive:
    def __init__(self):
        self._config = IduConfig.load_config('config/config.json')
        self._creds = GoogleCredentials.get_credentials(self._config.scopes, root_path='config/')
        self._gmail_service = build('gmail', 'v1', credentials=self._creds)
        self._logger = logging.getLogger(__name__)
    
    def get_or_create_label(self, label_name: str) -> str:
        try:
            # pylint: disable=maybe-no-member
            results = self._gmail_service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Buscar si la etiqueta ya existe
            for label in labels:
                if label['name'] == label_name:
                    self._logger.info("Etiqueta '%s' encontrada con ID: %s", label_name, label['id'])
                    return label['id']
            
            # Crear la etiqueta si no existe
            self._logger.info("Creando etiqueta '%s'", label_name)
            created_label = self._gmail_service.users().labels().create(
                userId='me',
                body={
                    'name': label_name,
                    'labelListVisibility': 'labelShow',
                    'messageListVisibility': 'show'
                }
            ).execute()
            
            self._logger.info("Etiqueta '%s' creada con ID: %s", label_name, created_label['id'])
            return created_label['id']
            
        except Exception as e:
            self._logger.error("Error al obtener/crear etiqueta '%s': %s", label_name, e, exc_info=True)
            return ''
    
    def search_emails_today_by_label(self) -> list[str]:
        """
        Busca correos del día actual con la etiqueta configurada que NO tengan la etiqueta 'DESCARGADO'.
        
        Returns:
            list[str]: Lista de IDs de correos encontrados
        """
        try:
            fecha_hoy = date.today().strftime('%Y/%m/%d')
            
            # Construir query: buscar por etiqueta, fecha y excluir los que ya tienen DESCARGADO
            query = f"label:{self._config.label_email} after:{fecha_hoy} -label:DESCARGADO"
            
            self._logger.info(
                "Buscando correos del día %s con etiqueta '%s' sin DESCARGADO",
                fecha_hoy,
                self._config.label_email
            )
            
            # pylint: disable=maybe-no-member
            results = self._gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            message_ids = [msg['id'] for msg in messages]
            
            if not message_ids:
                self._logger.warning(
                    "No se encontraron correos nuevos con la etiqueta '%s' para el día %s",
                    self._config.label_email,
                    fecha_hoy
                )
                return []
            
            self._logger.info(
                "Se encontraron %d correo(s) nuevos con la etiqueta '%s'",
                len(message_ids),
                self._config.label_email
            )
            
            return message_ids
            
        except Exception as e:
            self._logger.error(
                "Error al buscar correos con etiqueta '%s': %s",
                self._config.label_email,
                e,
                exc_info=True
            )
            return []
    
    def get_attachments_from_email(self, message_id: str) -> list[dict]:
        try:
            # pylint: disable=maybe-no-member
            message = self._gmail_service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            attachments = []
            
            # Buscar adjuntos en las partes del mensaje
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part.get('filename') and part.get('body', {}).get('attachmentId'):
                        attachments.append({
                            'filename': part['filename'],
                            'mimeType': part.get('mimeType', ''),
                            'attachmentId': part['body']['attachmentId'],
                            'size': part['body'].get('size', 0)
                        })
            
            if attachments:
                self._logger.info(
                    "Correo %s tiene %d adjunto(s)",
                    message_id,
                    len(attachments)
                )
            
            return attachments
            
        except Exception as e:
            self._logger.error(
                "Error al obtener adjuntos del correo %s: %s",
                message_id,
                e,
                exc_info=True
            )
            return []
    
    def download_attachment(self, message_id: str, attachment_id: str, filename: str) -> bool:
        try:
            # Crear directorio si no existe
            os.makedirs(self._config.download_path, exist_ok=True)
            
            # Obtener el adjunto
            # pylint: disable=maybe-no-member
            attachment = self._gmail_service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            # Decodificar datos
            file_data = base64.urlsafe_b64decode(attachment['data'])
            
            # Guardar archivo
            destination_path = os.path.join(self._config.download_path, filename)
            with open(destination_path, 'wb') as f:
                f.write(file_data)
            
            self._logger.info("Archivo descargado exitosamente: %s", destination_path)
            return True
            
        except Exception as e:
            self._logger.error(
                "Error al descargar adjunto %s del correo %s: %s",
                filename,
                message_id,
                e,
                exc_info=True
            )
            return False
    
    def add_downloaded_label(self, message_id: str, label_id: str) -> bool:
        try:
            # pylint: disable=maybe-no-member
            self._gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            
            self._logger.info("Etiqueta DESCARGADO agregada al correo %s", message_id)
            return True
            
        except Exception as e:
            self._logger.error(
                "Error al etiquetar correo %s: %s",
                message_id,
                e,
                exc_info=True
            )
            return False
    
    def download_files(self) -> dict:
    
        label_descargado_id = self.get_or_create_label('DESCARGADO')
        if not label_descargado_id:
            self._logger.error("No se pudo obtener/crear la etiqueta DESCARGADO")
            return {
                'total_correos': 0,
                'total_adjuntos': 0,
                'descargados': 0,
                'fallidos': 0,
                'etiquetados': 0,
                'archivos': []
            }
        
        # Buscar correos del día con la etiqueta (excluyendo los ya descargados)
        message_ids = self.search_emails_today_by_label()
        
        if not message_ids:
            self._logger.info("No hay correos para procesar")
            return {
                'total_correos': 0,
                'total_adjuntos': 0,
                'descargados': 0,
                'fallidos': 0,
                'etiquetados': 0,
                'archivos': []
            }
        
        descargados = 0
        fallidos = 0
        total_adjuntos = 0
        etiquetados = 0
        archivos_info = []
        
        # Procesar cada correo
        for message_id in message_ids:
            self._logger.info("Procesando correo: %s", message_id)
            
            # Obtener adjuntos del correo
            attachments = self.get_attachments_from_email(message_id)
            total_adjuntos += len(attachments)
            
            correo_exitoso = True
            
            # Descargar cada adjunto
            for attachment in attachments:
                filename = attachment['filename']
                attachment_id = attachment['attachmentId']
                
                self._logger.info("Descargando: %s", filename)
                
                if self.download_attachment(message_id, attachment_id, filename):
                    descargados += 1
                    archivos_info.append({
                        'nombre': filename,
                        'correo_id': message_id,
                        'estado': 'exitoso',
                        'tamaño': attachment['size'],
                        'ruta': os.path.join(self._config.download_path, filename)
                    })
                else:
                    fallidos += 1
                    correo_exitoso = False
                    archivos_info.append({
                        'nombre': filename,
                        'correo_id': message_id,
                        'estado': 'fallido'
                    })
            
            # Si todos los adjuntos se descargaron exitosamente, etiquetar el correo
            if correo_exitoso and attachments:
                if self.add_downloaded_label(message_id, label_descargado_id):
                    etiquetados += 1
        
        resultado = {
            'total_correos': len(message_ids),
            'total_adjuntos': total_adjuntos,
            'descargados': descargados,
            'fallidos': fallidos,
            'etiquetados': etiquetados,
            'archivos': archivos_info
        }
        
        self._logger.info(
            "Resumen descarga - Correos: %d, Adjuntos: %d, Exitosos: %d, Fallidos: %d, Etiquetados: %d",
            len(message_ids),
            total_adjuntos,
            descargados,
            fallidos,
            etiquetados
        )
        return resultado