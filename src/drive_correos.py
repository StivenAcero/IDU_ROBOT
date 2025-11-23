import os
from datetime import date
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from email.utils import parsedate_to_datetime

# Constante para nombres de meses en español
MESES_ESPANOL = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


def get_credentials(scopes, root_path='config/'):
    creds = None
    if os.path.exists(root_path + 'token.json'):
        creds = Credentials.from_authorized_user_file(root_path + 'token.json', scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                root_path + 'credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        with open(root_path + 'token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def get_gmail_service(creds):
    """Crea el servicio de Gmail."""
    return build('gmail', 'v1', credentials=creds)


def obtener_id_etiqueta(service, nombre_etiqueta):
    """Obtiene el ID de una etiqueta por su nombre."""
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        for label in labels:
            if label['name'] == nombre_etiqueta:
                print(f"✓ Etiqueta '{nombre_etiqueta}' encontrada")
                return label['id']
        
        print(f"✗ No se encontró la etiqueta '{nombre_etiqueta}'")
        return None
    except Exception as e:
        print(f"✗ Error al buscar etiqueta: {e}")
        return None


def buscar_correos_dia_actual(service, remitente=None, asunto=None, max_resultados=100):
    """
    Busca correos por remitente y/o asunto SOLO del día actual.
    Retorna lista única de IDs.
    """
    all_messages = []
    fecha_hoy = date.today().strftime('%Y/%m/%d')
    
    # Construir query base con filtro de fecha
    query_base = f"after:{fecha_hoy}"
    
    if remitente:
        try:
            query = f"{query_base} from:{remitente}"
            print(f"🔍 Buscando correos de: {remitente} (fecha: {fecha_hoy})")
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_resultados
            ).execute()
            messages = results.get('messages', [])
            all_messages.extend([msg['id'] for msg in messages])
            print(f"✓ {len(messages)} correos del remitente hoy")
        except Exception as e:
            print(f"✗ Error al buscar por remitente: {e}")
    
    if asunto:
        try:
            query = f'{query_base} subject:"{asunto}"'
            print(f"🔍 Buscando correos con asunto: {asunto} (fecha: {fecha_hoy})")
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_resultados
            ).execute()
            messages = results.get('messages', [])
            all_messages.extend([msg['id'] for msg in messages])
            print(f"✓ {len(messages)} correos con el asunto hoy")
        except Exception as e:
            print(f"✗ Error al buscar por asunto: {e}")
    
    # Eliminar duplicados
    unique_messages = list(set(all_messages))
    print(f"\n📊 Total de correos únicos del día actual: {len(unique_messages)}")
    
    return unique_messages


def gestionar_etiquetas_correos(service, message_ids, label_ids, verificar=True):
    """
    Agrega etiquetas a correos, opcionalmente verificando si ya las tienen.
    """
    if not message_ids:
        return 0
    
    correos_a_etiquetar = message_ids
    
    if verificar:
        correos_a_etiquetar = []
        for msg_id in message_ids:
            try:
                message = service.users().messages().get(
                    userId='me', 
                    id=msg_id, 
                    format='minimal'
                ).execute()
                
                existing_labels = set(message.get('labelIds', []))
                if not all(label_id in existing_labels for label_id in label_ids):
                    correos_a_etiquetar.append(msg_id)
            except Exception as e:
                print(f"⚠ Error al verificar correo {msg_id}: {e}")
    
    if not correos_a_etiquetar:
        print("✓ Todos los correos ya están etiquetados")
        return 0
    
    try:
        print(f"🏷️ Etiquetando {len(correos_a_etiquetar)} correos...")
        service.users().messages().batchModify(
            userId='me',
            body={'ids': correos_a_etiquetar, 'addLabelIds': label_ids}
        ).execute()
        print(f"✓ {len(correos_a_etiquetar)} correos etiquetados")
        return len(correos_a_etiquetar)
    except Exception as e:
        print(f"✗ Error al etiquetar: {e}")
        return 0


def crear_etiqueta_anidada(service, nombre_padre, nombre_hijo):
    """Crea una etiqueta anidada (Padre/Hijo)."""
    nombre_completo = f"{nombre_padre}/{nombre_hijo}"
    
    # Verificar si ya existe
    label_id = obtener_id_etiqueta(service, nombre_completo)
    if label_id:
        return label_id
    
    try:
        print(f"📋 Creando etiqueta: {nombre_completo}")
        created_label = service.users().labels().create(
            userId='me',
            body={
                'name': nombre_completo,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
        ).execute()
        print(f"✓ Etiqueta creada")
        return created_label['id']
    except Exception as e:
        if 'already exists' in str(e).lower():
            return obtener_id_etiqueta(service, nombre_completo)
        print(f"✗ Error al crear etiqueta: {e}")
        return None


def obtener_fecha_correo(service, message_id):
    """Obtiene el año y mes de un correo."""
    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='metadata',
            metadataHeaders=['Date']
        ).execute()
        
        headers = message.get('payload', {}).get('headers', [])
        for header in headers:
            if header['name'].lower() == 'date':
                fecha = parsedate_to_datetime(header['value'])
                return fecha.year, fecha.month
        
        return None, None
    except Exception as e:
        return None, None


def etiquetar_correos_idu_por_mes(service, nombre_etiqueta="IDU", 
                                   remitente="atencion.valorizacion@idu.gov.co", 
                                   asunto="Certificado de estado de cuenta para trámite notarial (Paz y salvo IDU)",
                                   max_resultados=100):
    """
    Función principal que busca y etiqueta correos del IDU del día actual,
    organizándolos por mes.
    """
    print("\n" + "="*80)
    print("ETIQUETADO DE CORREOS IDU POR MES - SOLO DÍA ACTUAL")
    print("="*80)
    print(f"📅 Procesando correos de: {date.today().strftime('%d/%m/%Y')}")
    
    # 1. Verificar etiqueta padre
    label_padre_id = obtener_id_etiqueta(service, nombre_etiqueta)
    if not label_padre_id:
        return {'exitoso': False, 'error': f"La etiqueta '{nombre_etiqueta}' no existe"}
    
    # 2. Buscar correos SOLO del día actual
    print(f"\n{'='*80}")
    todos_correos = buscar_correos_dia_actual(service, remitente, asunto, max_resultados)
    
    if not todos_correos:
        print("⚠ No se encontraron correos del día actual")
        return {'exitoso': True, 'total_encontrados': 0, 'procesados': 0}
    
    # 3. Agrupar por mes
    print("\n🗓️ Agrupando por mes...")
    correos_por_mes = {}
    correos_sin_fecha = []
    
    for msg_id in todos_correos:
        anio, mes = obtener_fecha_correo(service, msg_id)
        if anio and mes:
            clave = (anio, mes)
            correos_por_mes.setdefault(clave, []).append(msg_id)
        else:
            correos_sin_fecha.append(msg_id)
    
    print(f"✓ {len(correos_por_mes)} meses diferentes")
    if correos_sin_fecha:
        print(f"⚠ {len(correos_sin_fecha)} correos sin fecha")
    
    # 4. Procesar cada mes
    estadisticas = {}
    total_etiquetados = 0
    
    for (anio, mes), message_ids in sorted(correos_por_mes.items()):
        print(f"\n{'='*80}")
        nombre_mes = MESES_ESPANOL.get(mes, str(mes))
        print(f"📅 {nombre_mes} {anio} - {len(message_ids)} correos")
        
        # Crear/obtener etiqueta del mes
        label_mes_id = crear_etiqueta_anidada(
            service, 
            nombre_etiqueta, 
            f"{nombre_mes} {anio}"
        )
        
        if not label_mes_id:
            print(f"✗ No se pudo crear etiqueta para {mes}/{anio}")
            continue
        
        # Etiquetar con padre y mes
        etiquetados = gestionar_etiquetas_correos(
            service, 
            message_ids, 
            [label_padre_id, label_mes_id],
            verificar=True
        )
        
        total_etiquetados += etiquetados
        estadisticas[f"{nombre_mes} {anio}"] = {
            'total': len(message_ids),
            'nuevos': etiquetados
        }
    
    # 5. Procesar correos sin fecha
    if correos_sin_fecha:
        print(f"\n{'='*80}")
        print(f"📋 Procesando {len(correos_sin_fecha)} correos sin fecha...")
        sin_fecha_etiquetados = gestionar_etiquetas_correos(
            service, 
            correos_sin_fecha, 
            [label_padre_id],
            verificar=True
        )
        estadisticas['Sin fecha'] = {
            'total': len(correos_sin_fecha),
            'nuevos': sin_fecha_etiquetados
        }
        total_etiquetados += sin_fecha_etiquetados
    
    # 6. Resumen
    print("\n" + "="*80)
    print("RESUMEN - DÍA ACTUAL")
    print("="*80)
    print(f"📧 Total correos del día: {len(todos_correos)}")
    print(f"✅ Etiquetados: {total_etiquetados}")
    print(f"\n🗓️ Por mes:")
    for mes, stats in estadisticas.items():
        print(f"   {mes}: {stats['nuevos']}/{stats['total']} nuevos")
    print("="*80)
    
    return {
        'exitoso': True,
        'total_encontrados': len(todos_correos),
        'procesados': total_etiquetados,
        'por_mes': estadisticas
    }