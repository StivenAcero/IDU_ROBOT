import time
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from src.idu_config import IduConfig
import logging
logger = logging.getLogger(__name__)


class IduNavigator:

    def __init__(self):
        config = IduConfig.load_config()
        chromedriver_autoinstaller.install()
        self._chrome_options = Options()
        self._chrome_options.add_argument("--window-size=1200,800")
        self._chrome_options.add_experimental_option("prefs", config.prefs)
        self._chrome_service = Service()
        self._driver = webdriver.Chrome(
            service=self._chrome_service, options=self._chrome_options
        )
        self._logger = logging.getLogger(__name__)
    def navegar_a_url(self, url):
        try:
            self._driver.get(url)
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("Página cargada correctamente.")
        except TimeoutException:
            logger.error("Error: Tiempo de espera agotado al cargar la página.")
            self._driver.quit()
            raise
        except Exception as e:
            logger.error(f"Error al navegar a la URL: {e}")
            self._driver.quit()
            raise

    def realizar_clicks_secuenciales(self, num_clicks=4, timeout=15):

        wait = WebDriverWait(self._driver, timeout)

        for i in range(num_clicks):
            try:
                boton = wait.until(EC.element_to_be_clickable((By.ID, "end")))
                logger.info("realizando click")
                boton.click()
                time.sleep(1)  # Pausa entre clicks
            except Exception as e:
                logging.error(f" Error en click #{i+1}: {e}")
                raise

        print(f"✓ Se completaron {num_clicks} clicks exitosamente")

    def buscar_iframe_chat(self, timeout=15):
        print("Buscando iframes en la página...")

        try:
            # Esperar a que haya iframes disponibles
            WebDriverWait(self._driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )

            iframes = self._driver.find_elements(By.TAG_NAME, "iframe")
            print(f"✓ Cantidad de iframes encontrados: {len(iframes)}")

            # Mostrar información de cada iframe
            for idx, iframe in enumerate(iframes):
                name = iframe.get_attribute("name")
                iframe_id = iframe.get_attribute("id")
                src = iframe.get_attribute("src")
                print(f"  Iframe {idx+1}: name={name}, id={iframe_id}, src={src}")

            # Buscar el iframe correcto por src
            for iframe in iframes:
                src = iframe.get_attribute("src")
                if src and "chat_valorizacion/chat" in src:
                    print("✓ Iframe del chat encontrado. Cambiando al iframe...")
                    self._driver.switch_to.frame(iframe)
                    return True

            print(
                "⚠ No se encontró el iframe del chat. Continuando en el DOM principal..."
            )
            return False

        except Exception as e:
            print(f"❌ Error al buscar iframes: {e}")
            return False

    def buscar_tabla_formulario(self, timeout=15):

        try:
            tabla_form = WebDriverWait(self._driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.form"))
            )
            print("✓ Tabla con class='form' encontrada")
            return tabla_form

        except Exception as e:
            print(f"❌ No se encontró la tabla con class='form': {e}")
            return None

    def buscar_input_username(self, tabla_form=None, timeout=15):

        print("Buscando el input para colocar el nombre de usuario...")

        try:
            if tabla_form:
                # Buscar dentro de la tabla
                input_username = WebDriverWait(self._driver, timeout).until(
                    lambda d: tabla_form.find_element(
                        By.CSS_SELECTOR, 'input.username[name="name"]'
                    )
                )
            else:
                # Buscar en el contexto actual
                input_username = WebDriverWait(self._driver, timeout).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'input.username[name="name"]')
                    )
                )

            print("✓ Input de usuario encontrado")
            return input_username

        except Exception as e:
            print(f"❌ No se encontró el input de usuario: {e}")
            return None

    def preparar_formulario(self, timeout=15):

        en_iframe_chat = self.buscar_iframe_chat(timeout)
        tabla_form = self.buscar_tabla_formulario(timeout)

        if not tabla_form:
            print("⚠ No se puede continuar sin la tabla del formulario")
            return None, None, en_iframe_chat

        # 3. Buscar el input de usuario dentro de la tabla
        input_username = self.buscar_input_username(tabla_form, timeout)

        if input_username:
            print("✓ Formulario preparado exitosamente")
        else:
            print("⚠ Formulario encontrado pero sin input de usuario")

        return input_username, tabla_form, en_iframe_chat

    def rellenar_campo_nombre(self, tabla_form, name_user, timeout=15):

        print(f"Buscando campo de nombre...")

        try:
            if tabla_form:
                input_name = WebDriverWait(self._driver, timeout).until(
                    lambda d: tabla_form.find_element(
                        By.CSS_SELECTOR, 'input.username[name="name"]'
                    )
                )
            else:
                print("⚠ No se proporcionó la tabla del formulario")
                return False

            print(f"✓ Campo de nombre encontrado. Escribiendo '{name_user}'...")
            input_name.clear()
            input_name.send_keys(name_user)
            print(f"✓ Se escribió '{name_user}' en el campo de nombre")
            return True

        except Exception as e:
            print(f"❌ Error al rellenar campo de nombre: {e}")
            return False

    def rellenar_campo_email(self, tabla_form, email_user, timeout=15):

        print(f"Buscando campo de email...")

        try:
            if tabla_form:
                input_email = WebDriverWait(self._driver, timeout).until(
                    lambda d: tabla_form.find_element(
                        By.CSS_SELECTOR, 'input.username[name="email"]'
                    )
                )
            else:
                print("⚠ No se proporcionó la tabla del formulario")
                return False

            print(f"✓ Campo de email encontrado. Escribiendo '{email_user}'...")
            input_email.clear()
            input_email.send_keys(email_user)
            print(f"✓ Se escribió '{email_user}' en el campo de email")
            return True

        except Exception as e:
            print(f"❌ Error al rellenar campo de email: {e}")
            return False

    def rellenar_formulario_usuario(
        self, tabla_form, name_user, email_user, timeout=15
    ):

        nombre_ok = self.rellenar_campo_nombre(tabla_form, name_user, timeout)
        email_ok = self.rellenar_campo_email(tabla_form, email_user, timeout)

        return nombre_ok and email_ok

    def rellenar_campo_mensaje_solicitud(self, tabla_form, solicitud_row, timeout=15):
        try:
            if tabla_form:
                textarea_message = WebDriverWait(self._driver, timeout).until(
                    lambda d: tabla_form.find_element(
                        By.CSS_SELECTOR, 'textarea[name="message"]'
                    )
                )
            else:
                print("⚠ No se proporcionó la tabla del formulario")
                return False

            print("✓ Textarea de mensaje encontrado. Construyendo mensaje...")
            chips = solicitud_row.get("chips", "")
            mensaje = f"Solicitud de paz y salvo de estos chips: {chips}"

            textarea_message.clear()
            textarea_message.send_keys(mensaje)
            print("✓ Se escribió el mensaje en el textarea")
            return True

        except Exception as e:
            print(f"❌ Error al rellenar campo de mensaje: {e}")
            return False

    def click_iniciar_chat(self, timeout=15):
        try:
            boton_iniciar = WebDriverWait(self._driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a#submit-survey"))
            )
            boton_iniciar.click()
            self._driver.switch_to.default_content()
            time.sleep(2)  # Esperar un momento para asegurar que el chat se inicie
            return True

        except Exception as e:
            print(f"❌ No se encontró o no se pudo hacer click en 'Iniciar Chat': {e}")
            # Intentar volver al contexto principal de todas formas
            try:
                self._driver.switch_to.default_content()
            except:
                pass
            return False

    def reiniciar_navegador(self, url):
        print("\n🔄 Reiniciando navegador...")
        # Cerrar navegador anterior
        try:
            if self._driver:
                self._driver.quit()
                print("✓ Navegador cerrado")
        except Exception as e:
            print(f"⚠ Error al cerrar navegador: {e}")
        time.sleep(2) 
        max_intentos = 3
        for intento in range(max_intentos):
            try:
                self._driver = webdriver.Chrome(
                    service=self._chrome_service, 
                    options=self._chrome_options
                )
                print(f"✓ Nuevo navegador creado (intento {intento + 1})")
                self._driver.get(url)
                WebDriverWait(self._driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("✓ Navegador reiniciado y página cargada correctamente")
                return 
            except Exception as e:
                print(f"⚠ Error en intento {intento + 1}: {e}")
                if intento < max_intentos - 1:
                    time.sleep(3)
                else:
                    print("❌ No se pudo reiniciar el navegador después de 3 intentos")
                    raise
        