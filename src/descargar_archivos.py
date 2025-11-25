import base64
from pathlib import Path
from datetime import date
from src.drive_correos import obtener_id_etiqueta

def crear_carpeta_destino(carpeta_destino):
    """Crea la carpeta de destino si no existe."""
    Path(carpeta_destino).mkdir(parents=True, exist_ok=True)
    print(f"📁 Carpeta de destino: {carpeta_destino}")


def obtener_correos_por_etiqueta_dia_actual(service, label_id, max_resultados=500):
    try:
        fecha_hoy = date.today().strftime('%Y/%m/%d')
        query = f"after:{fecha_hoy}"
        
        print(f"📅 Fecha de búsqueda: {fecha_hoy}")
        
        results = service.users().messages().list(
            userId='me',
            labelIds=[label_id],
            q=query,
            maxResults=max_resultados
        ).execute()
        
        messages = results.get('messages', [])
        print(f"✓ {len(messages)} correos encontrados del día actual")
        return messages
        
    except Exception as e:
        print(f"✗ Error al buscar correos: {e}")
        return None


def obtener_informacion_correo(service, msg_id):
    """
    Obtiene la información básica de un correo (asunto, fecha).
    
    Returns:
        dict: {'asunto': str, 'fecha': str, 'payload': dict}
    """
    try:
        msg_detail = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        
        headers = msg_detail['payload'].get('headers', [])
        asunto = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'Sin asunto')
        fecha = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Sin fecha')
        
        return {
            'asunto': asunto,
            'fecha': fecha,
            'payload': msg_detail['payload']
        }
    except Exception as e:
        print(f"   ✗ Error al obtener información del correo: {e}")
        return None


def generar_nombre_archivo_unico(carpeta_destino, nombre_archivo):
    """
    Genera un nombre de archivo único si ya existe.
    
    Returns:
        Path: Ruta del archivo (única)
    """
    filepath = Path(carpeta_destino) / nombre_archivo
    contador = 1
    
    while filepath.exists():
        nombre_base = Path(nombre_archivo).stem
        extension = Path(nombre_archivo).suffix
        filepath = Path(carpeta_destino) / f"{nombre_base}_{contador}{extension}"
        contador += 1
    
    return filepath


def descargar_adjunto(service, msg_id, attachment_id, filename, carpeta_destino):
    """
    Descarga un adjunto específico y lo guarda en disco.
    
    Returns:
        tuple: (bool exito, str nombre_archivo, int tamaño_bytes)
    """
    try:
        # Descargar el adjunto
        attachment = service.users().messages().attachments().get(
            userId='me',
            messageId=msg_id,
            id=attachment_id
        ).execute()
        
        # Decodificar datos
        file_data = base64.urlsafe_b64decode(
            attachment['data'].encode('UTF-8')
        )
        
        # Generar nombre único
        filepath = generar_nombre_archivo_unico(carpeta_destino, filename)
        
        # Guardar archivo
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        print(f"   ✓ Descargado: {filepath.name} ({len(file_data):,} bytes)")
        return True, filepath.name, len(file_data)
        
    except Exception as e:
        print(f"   ⚠ Error al descargar '{filename}': {e}")
        return False, filename, 0


def procesar_parte_mensaje(service, part, msg_id, carpeta_destino):
    """
    Procesa una parte del mensaje buscando adjuntos.
    
    Returns:
        int: Número de archivos descargados
    """
    archivos_descargados = 0
    
    # Si tiene subpartes, procesarlas recursivamente
    if 'parts' in part:
        for subpart in part['parts']:
            archivos_descargados += procesar_parte_mensaje(
                service, subpart, msg_id, carpeta_destino
            )
        return archivos_descargados
    
    # Verificar si es un adjunto
    filename = part.get('filename', '')
    if not filename:
        return 0
    
    body = part.get('body', {})
    attachment_id = body.get('attachmentId')
    
    if attachment_id:
        exito, _, _ = descargar_adjunto(
            service, msg_id, attachment_id, filename, carpeta_destino
        )
        if exito:
            archivos_descargados += 1
    
    return archivos_descargados


def extraer_adjuntos_correo(service, msg_id, payload, carpeta_destino):
    """
    Extrae todos los adjuntos de un correo.
    
    Returns:
        int: Número de archivos descargados
    """
    archivos_descargados = 0
    
    # Caso 1: Mensaje con partes múltiples
    if 'parts' in payload:
        for part in payload['parts']:
            archivos_descargados += procesar_parte_mensaje(
                service, part, msg_id, carpeta_destino
            )
    
    # Caso 2: Mensaje simple con adjunto directo
    else:
        filename = payload.get('filename', '')
        if filename:
            body = payload.get('body', {})
            attachment_id = body.get('attachmentId')
            
            if attachment_id:
                exito, _, _ = descargar_adjunto(
                    service, msg_id, attachment_id, filename, carpeta_destino
                )
                if exito:
                    archivos_descargados += 1
    
    return archivos_descargados


def procesar_correo_individual(service, msg_id, numero, total, carpeta_destino):
    """
    Procesa un correo individual: muestra info y descarga adjuntos.
    
    Returns:
        dict: {'archivos_descargados': int, 'tiene_adjuntos': bool, 'error': bool}
    """
    print(f"\n{'='*80}")
    print(f"📧 Procesando correo {numero}/{total} (ID: {msg_id[:10]}...)")
    
    resultado = {
        'archivos_descargados': 0,
        'tiene_adjuntos': False,
        'error': False
    }
    
    try:
        # Obtener información del correo
        info_correo = obtener_informacion_correo(service, msg_id)
        if not info_correo:
            resultado['error'] = True
            return resultado
        
        print(f"   Asunto: {info_correo['asunto'][:60]}...")
        print(f"   Fecha: {info_correo['fecha'][:30]}...")
        
        # Extraer adjuntos
        archivos_descargados = extraer_adjuntos_correo(
            service, msg_id, info_correo['payload'], carpeta_destino
        )
        
        resultado['archivos_descargados'] = archivos_descargados
        resultado['tiene_adjuntos'] = archivos_descargados > 0
        
        if archivos_descargados == 0:
            print("   ℹ️  Sin adjuntos")
        
        return resultado
        
    except Exception as e:
        print(f"   ✗ Error al procesar correo: {e}")
        resultado['error'] = True
        return resultado


def archivar_correos_batch(service, message_ids):
    """
    Archiva múltiples correos (los quita del INBOX).
    
    Returns:
        bool: True si tuvo éxito, False si hubo error
    """
    if not message_ids:
        return True
    
    try:
        service.users().messages().batchModify(
            userId='me',
            body={
                'ids': message_ids,
                'removeLabelIds': ['INBOX']
            }
        ).execute()
        
        print(f"✓ {len(message_ids)} correos archivados")
        return True
        
    except Exception as e:
        print(f"✗ Error al archivar correos: {e}")
        return False


def mostrar_resumen_proceso(estadisticas):
    """Muestra el resumen final del proceso."""
    print("\n" + "="*80)
    print("RESUMEN - DÍA ACTUAL")
    print("="*80)
    print(f"📧 Total correos procesados: {estadisticas['total_correos']}")
    print(f"📎 Correos con adjuntos: {estadisticas['correos_con_adjuntos']}")
    print(f"💾 Archivos descargados: {estadisticas['archivos_descargados']}")
    print(f"📦 Correos archivados: {estadisticas['correos_archivados']}")
    
    if estadisticas['errores'] > 0:
        print(f"⚠️  Errores: {estadisticas['errores']}")
    
    if estadisticas['correos_sin_adjuntos']:
        print(f"ℹ️  Correos sin adjuntos: {len(estadisticas['correos_sin_adjuntos'])}")
    
    print("="*80)


def descargar_adjuntos_correos_idu(service, nombre_etiqueta="IDU", 
                                    carpeta_destino="descargas_idu",
                                    archivar_despues=True):

    print("\n" + "="*80)
    print("DESCARGA DE ADJUNTOS DE CORREOS IDU - SOLO DÍA ACTUAL")
    print("="*80)
    print(f"📅 Procesando correos de: {date.today().strftime('%d/%m/%Y')}")
    
    # 1. Crear carpeta de destino
    crear_carpeta_destino(carpeta_destino)
    
    # 2. Obtener ID de la etiqueta
    label_id = obtener_id_etiqueta(service, nombre_etiqueta)
    if not label_id:
        return {
            'exitoso': False, 
            'error': f"La etiqueta '{nombre_etiqueta}' no existe"
        }
    
    # 3. Buscar correos con la etiqueta del día actual
    print(f"\n🔍 Buscando correos con etiqueta '{nombre_etiqueta}' del día actual...")
    messages = obtener_correos_por_etiqueta_dia_actual(service, label_id)
    
    if messages is None:
        return {'exitoso': False, 'error': 'Error al buscar correos'}
    
    if not messages:
        print("⚠ No se encontraron correos del día actual")
        return {
            'exitoso': True,
            'total_correos': 0,
            'archivos_descargados': 0,
            'correos_archivados': 0
        }
    
    # 4. Inicializar estadísticas
    estadisticas = {
        'total_correos': len(messages),
        'correos_con_adjuntos': 0,
        'archivos_descargados': 0,
        'correos_archivados': 0,
        'errores': 0,
        'correos_sin_adjuntos': []
    }
    
    correos_para_archivar = []
    
    # 5. Procesar cada correo
    for i, message in enumerate(messages, 1):
        msg_id = message['id']
        
        resultado = procesar_correo_individual(
            service, msg_id, i, len(messages), carpeta_destino
        )
        
        # Actualizar estadísticas
        if resultado['error']:
            estadisticas['errores'] += 1
        elif resultado['tiene_adjuntos']:
            estadisticas['correos_con_adjuntos'] += 1
            estadisticas['archivos_descargados'] += resultado['archivos_descargados']
            correos_para_archivar.append(msg_id)
        else:
            estadisticas['correos_sin_adjuntos'].append(msg_id)
    
    # 6. Archivar correos si se descargaron adjuntos
    if archivar_despues and correos_para_archivar:
        print(f"\n{'='*80}")
        print(f"📦 Archivando {len(correos_para_archivar)} correos...")
        
        if archivar_correos_batch(service, correos_para_archivar):
            estadisticas['correos_archivados'] = len(correos_para_archivar)
    
    # 7. Mostrar resumen
    mostrar_resumen_proceso(estadisticas)
    
    return {
        'exitoso': True,
        **estadisticas
    }


def verificar_archivo_ya_descargado(carpeta_destino, nombre_archivo):
    filepath = Path(carpeta_destino) / nombre_archivo
    return filepath.exists()