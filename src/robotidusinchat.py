import os
import json
import time
import pandas as pd
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import re  # Importar módulo para trabajar con expresiones regulares
import shutil

chromedriver_autoinstaller.install()

def configurar_navegador():
    print("Configurando el navegador...")
    chrome_options = Options()
    # Solo las opciones necesarias para Mac
    chrome_options.add_argument("--window-size=1200,800")
    #chrome_options.add_argument("--headless=new")  # Descomenta si quieres headless
    # Elimina opciones que pueden causar conflicto en Mac
    #chrome_options.add_argument("--no-sandbox")
    #chrome_options.add_argument("--disable-dev-shm-usage")
    #chrome_options.add_argument('--disable-gpu')
    #chrome_options.add_argument("--allow-running-insecure-content")
    #chrome_options.add_argument("--disable-web-security")
    #chrome_options.add_argument("--disable-site-isolation-trials")
    #chrome_options.add_argument("--ignore-certificate-errors")
    #chrome_options.add_argument("--log-level=3")
    #chrome_options.add_argument("--disable-logging")
    #chrome_options.add_argument("--disable-software-rasterizer")
    #chrome_options.add_argument("--disable-webgl")
    #chrome_options.add_argument("--disable-webgl2")

    # Directorio de descargas para Mac
    downloads_path = os.path.expanduser("~/Downloads")
    prefs = {
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "safebrowsing.disable_download_protection": True,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "download.default_directory": downloads_path
    }
    chrome_options.add_experimental_option("prefs", prefs)

    try:
        chrome_service = Service()
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        print("Navegador abierto correctamente.")
        return driver
    except Exception as e:
        print(f"Error al abrir el navegador: {e}")
        raise

# --- NUEVO CODIGO PARA ABRIR LA URL SOLICITADA ---
def main():
    print("Iniciando el script...")
    driver = configurar_navegador()
    url = "https://www.idu.gov.co/page/chat-valorizacion"
    print(f"Abriendo la página: {url}")
    driver.get(url)
    print("Buscando el botón 'Siguiente' (id='end')...")
    boton = None
    for i in range(15):
        try:
            boton = driver.find_element(By.ID, "end")
            print(f"Botón encontrado en el segundo {i+1}. Haciendo primer clic...")
            boton.click()
            break
        except Exception:
            print(f"Botón no encontrado aún... ({i+1}s)")
            time.sleep(1)
    time.sleep(1)
    print("Buscando nuevamente el botón 'Siguiente' para segundo clic...")
    boton = None
    for i in range(15):
        try:
            boton = driver.find_element(By.ID, "end")
            print(f"Botón encontrado en el segundo {i+1} (segunda búsqueda). Haciendo segundo clic...")
            boton.click()
            break
        except Exception:
            print(f"Botón no encontrado aún... ({i+1}s) (segunda búsqueda)")
            time.sleep(1)
    time.sleep(1)
    print("Buscando el botón 'Siguiente' con data-step=3 para tercer clic...")
    boton = None
    for i in range(15):
        try:
            boton = driver.find_element(By.CSS_SELECTOR, 'button#end[data-step="3"]')
            print(f"Botón con data-step=3 encontrado en el segundo {i+1}. Haciendo tercer clic...")
            boton.click()
            break
        except Exception:
            print(f"Botón con data-step=3 no encontrado aún... ({i+1}s)")
            time.sleep(1)
    time.sleep(1)
    print("Buscando el botón 'Finalizar' con data-step=complete para cuarto clic...")
    boton = None
    for i in range(15):
        try:
            boton = driver.find_element(By.CSS_SELECTOR, 'button#end[data-step="complete"]')
            print(f"Botón con data-step=complete encontrado en el segundo {i+1}. Haciendo cuarto clic...")
            boton.click()
            break
        except Exception:
            print(f"Botón con data-step=complete no encontrado aún... ({i+1}s)")
            time.sleep(1)
    # Buscar iframes tras los clics
    print("Buscando iframes en la página tras los clics...")
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"Cantidad de iframes encontrados: {len(iframes)}")
    for idx, iframe in enumerate(iframes):
        print(f"Iframe {idx+1}: name={iframe.get_attribute('name')}, id={iframe.get_attribute('id')}, src={iframe.get_attribute('src')}")
    # Buscar el iframe correcto por src
    input_username = None
    chat_iframe = None
    for iframe in iframes:
        src = iframe.get_attribute('src')
        if src and "chat_valorizacion/chat" in src:
            chat_iframe = iframe
            break
    if chat_iframe:
        print("Cambiando al iframe del chat para buscar la tabla e input...")
        driver.switch_to.frame(chat_iframe)
        print("Buscando la tabla con class='form' dentro del iframe del chat...")
        tabla_form = None
        for i in range(15):
            try:
                tabla_form = driver.find_element(By.CSS_SELECTOR, 'table.form')
                print(f"Tabla encontrada en el segundo {i+1} (iframe chat).")
                break
            except Exception:
                print(f"Tabla no encontrada aún en el iframe chat... ({i+1}s)")
                time.sleep(1)
        if tabla_form:
            print("Buscando el input para colocar el nombre dentro de la tabla (iframe chat)...")
            for i in range(15):
                try:
                    input_username = tabla_form.find_element(By.CSS_SELECTOR, 'input.username[name="name"]')
                    print(f"Input encontrado en el segundo {i+1} dentro de la tabla (iframe chat).")
                    break
                except Exception:
                    print(f"Input no encontrado aún en la tabla (iframe chat)... ({i+1}s)")
                    time.sleep(1)
        else:
            print("No se encontró la tabla con class='form' en el iframe chat. No se puede buscar el input.")
    else:
        print("No se encontró el iframe del chat. Se mantiene la búsqueda en el DOM principal.")
        print("Buscando la tabla con class='form' antes de buscar el input...")
        tabla_form = None
        for i in range(15):
            try:
                tabla_form = driver.find_element(By.CSS_SELECTOR, 'table.form')
                print(f"Tabla encontrada en el segundo {i+1}.")
                break
            except Exception:
                print(f"Tabla no encontrada aún... ({i+1}s)")
                time.sleep(1)
        if tabla_form:
            print("Buscando el input para colocar el nombre dentro de la tabla...")
            for i in range(15):
                try:
                    input_username = tabla_form.find_element(By.CSS_SELECTOR, 'input.username[name="name"]')
                    print(f"Input encontrado en el segundo {i+1} dentro de la tabla.")
                    break
                except Exception:
                    print(f"Input no encontrado aún en la tabla... ({i+1}s)")
                    time.sleep(1)
        else:
            print("No se encontró la tabla con class='form'. No se puede buscar el input.")
    if input_username:
        print("Escribiendo 'pedro'...")
        input_username.clear()
        input_username.send_keys("pedro")
        print("Se escribió 'pedro' en el input username.")
        # Buscar y diligenciar el input de email
        try:
            input_email = tabla_form.find_element(By.CSS_SELECTOR, 'input.username[name="email"]')
            print("Input de email encontrado. Escribiendo 'mateo.duquemoya@davivienda.com'...")
            input_email.clear()
            input_email.send_keys("mateo.duquemoya@davivienda.com")
            print("Se escribió el email en el input correspondiente.")
        except Exception as ex:
            print(f"No se pudo encontrar o diligenciar el input de email: {ex}")
        # Buscar y diligenciar el textarea de mensaje
        try:
            textarea_message = tabla_form.find_element(By.CSS_SELECTOR, 'textarea[name="message"]')
            print("Textarea de mensaje encontrado. Escribiendo mensaje...")
            mensaje = "Solicitud de paz y salvo de estos tres chips: AAA0283EWLF,\nAAA0265UABS,\nAAA0074YPDM"
            textarea_message.clear()
            textarea_message.send_keys(mensaje)
            print("Se escribió el mensaje en el textarea.")
        except Exception as ex:
            print(f"No se pudo encontrar o diligenciar el textarea de mensaje: {ex}")
        # Hacer clic en el botón 'Iniciar Chat' buscando en todos los iframes
        boton_iniciar = None
        print("Buscando el botón 'Iniciar Chat' en todos los iframes...")
        driver.switch_to.default_content()
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for idx, iframe in enumerate(iframes):
            driver.switch_to.default_content()
            driver.switch_to.frame(iframe)
            try:
                boton_iniciar = driver.find_element(By.CSS_SELECTOR, 'a#submit-survey')
                print(f"Botón 'Iniciar Chat' encontrado en el iframe {idx+1}. Haciendo clic...")
                boton_iniciar.click()
                print("Se hizo clic en 'Iniciar Chat'.")
                break
            except Exception:
                print(f"No se encontró el botón 'Iniciar Chat' en el iframe {idx+1}.")
        driver.switch_to.default_content()
    else:
        print("No se encontró el input para colocar el nombre en el tiempo esperado.")
        print("Mostrando todos los inputs de tipo text presentes en la página:")
        inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
        for idx, inp in enumerate(inputs):
            print(f"Input {idx+1}: name={inp.get_attribute('name')}, class={inp.get_attribute('class')}, outerHTML={inp.get_attribute('outerHTML')}")
    input("Presiona Enter para cerrar el navegador...")
    driver.quit()
    print("Navegador cerrado.")

if __name__ == "__main__":
    main()
