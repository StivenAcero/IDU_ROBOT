from src.drive_correos import (
    get_credentials,
    get_gmail_service,
    etiquetar_correos_idu_por_mes,  # Nueva función
)
from src.descargar_archivos import descargar_adjuntos_correos_idu
from src.config import load_config
from src.file_managements import eliminar_archivos_carpeta

def main():
    
    try:
        # Cargar configuración
        config = load_config('config/config.json')
        if not config:
            print("No se pudo cargar la configuración")
            return
        
        # Scopes específicos para Gmail
        SCOPES_GMAIL = config.get('SCOPES')
        
        # Configuración de etiquetado
        NOMBRE_ETIQUETA = config.get('NOMBRE_ETIQUETA', 'IDU')
        REMITENTE_IDU = config.get('REMITENTE_IDU', 'atencion.valorizacion@idu.gov.co')
        ASUNTO_IDU = config.get('ASUNTO_IDU', 'Certificado de estado de cuenta para trámite notarial (Paz y salvo IDU)')
        MAX_RESULTADOS = config.get('MAX_RESULTADOS_CORREOS', 500)
        
        # Configuración de descarga de adjuntos
        CARPETA_DESCARGAS = config.get('CARPETA_DESCARGAS', 'descargas_idu')
        ARCHIVAR_DESPUES_DESCARGA = config.get('ARCHIVAR_DESPUES_DESCARGA', True)
        print("limpiando caperta de descargas...")
        eliminar_archivos_carpeta(CARPETA_DESCARGAS)
        
        print("Obteniendo credenciales de Google...")
        creds = get_credentials(SCOPES_GMAIL, 'config/')
        
        if not creds:
            print("❌ No se pudieron obtener las credenciales")
            return
        
        print("✓ Credenciales obtenidas exitosamente")
        
        # 2. Crear servicio de Gmail
        print("\nCreando servicio de Gmail...")
        gmail_service = get_gmail_service(creds)
        print("✓ Servicio de Gmail creado exitosamente")
        
        # 3. Etiquetar correos del IDU organizados por mes
        print("\n" + "="*80)
        print("PASO 1: ETIQUETADO DE CORREOS")
        print("="*80)
        
        resultado_etiquetado = etiquetar_correos_idu_por_mes(
            service=gmail_service,
            nombre_etiqueta=NOMBRE_ETIQUETA,
            remitente=REMITENTE_IDU,
            asunto=ASUNTO_IDU,
            max_resultados=MAX_RESULTADOS
        )
        
        if not resultado_etiquetado['exitoso']:
            print(f"\n❌ Error en el etiquetado: {resultado_etiquetado.get('error', 'Error desconocido')}")
            return
        
        print("\n✅ Etiquetado completado exitosamente")
        
        # 4. Descargar adjuntos y archivar correos
        print("\n" + "="*80)
        print("PASO 2: DESCARGA DE ADJUNTOS Y ARCHIVADO")
        print("="*80)
        
        resultado_descarga = descargar_adjuntos_correos_idu(
            service=gmail_service,
            nombre_etiqueta=NOMBRE_ETIQUETA,
            carpeta_destino=CARPETA_DESCARGAS,
            archivar_despues=ARCHIVAR_DESPUES_DESCARGA
        )
        
        if not resultado_descarga['exitoso']:
            print(f"\n❌ Error en la descarga: {resultado_descarga.get('error', 'Error desconocido')}")
            return
        
        print("\n✅ Descarga y archivado completados exitosamente")
        
        # 5. Resumen final
        print("\n" + "="*80)
        print("RESUMEN GENERAL DEL PROCESO")
        print("="*80)
        print(f"\n📋 ETIQUETADO:")
        print(f"   • Correos encontrados: {resultado_etiquetado.get('total_encontrados', 0)}")
        print(f"   • Correos etiquetados: {resultado_etiquetado.get('procesados', 0)}")
        
        print(f"\n💾 DESCARGA:")
        print(f"   • Correos procesados: {resultado_descarga.get('total_correos', 0)}")
        print(f"   • Archivos descargados: {resultado_descarga.get('archivos_descargados', 0)}")
        print(f"   • Correos archivados: {resultado_descarga.get('correos_archivados', 0)}")
        
        print("\n" + "="*80)
        print("✅ PROCESO COMPLETO FINALIZADO")
        print("="*80)
            
    except Exception as e:
        print(f"\n❌ Error en la ejecución: {e}")
        import traceback
        traceback.print_exc()
        raise


def solo_descargar_adjuntos():
    """
    Función alternativa para solo descargar adjuntos sin etiquetar.
    Útil si ya tienes los correos etiquetados.
    """
    try:
        config = load_config('config/config.json')
        if not config:
            print("No se pudo cargar la configuración")
            return
        
        SCOPES_GMAIL = config.get('SCOPES')
        NOMBRE_ETIQUETA = config.get('NOMBRE_ETIQUETA', 'IDU')
        CARPETA_DESCARGAS = config.get('CARPETA_DESCARGAS', 'descargas_idu')
        ARCHIVAR_DESPUES_DESCARGA = config.get('ARCHIVAR_DESPUES_DESCARGA', True)
        
        print("Obteniendo credenciales de Google...")
        creds = get_credentials(SCOPES_GMAIL, 'config/')
        
        if not creds:
            print("❌ No se pudieron obtener las credenciales")
            return
        
        gmail_service = get_gmail_service(creds)
        
        resultado = descargar_adjuntos_correos_idu(
            service=gmail_service,
            nombre_etiqueta=NOMBRE_ETIQUETA,
            carpeta_destino=CARPETA_DESCARGAS,
            archivar_despues=ARCHIVAR_DESPUES_DESCARGA
        )
        
        if resultado['exitoso']:
            print("\n✅ Proceso completado exitosamente")
        else:
            print(f"\n❌ Proceso completado con errores: {resultado.get('error', 'Error desconocido')}")
            
    except Exception as e:
        print(f"\n❌ Error en la ejecución: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Ejecutar proceso completo (etiquetar + descargar + archivar)
    main()
    
 