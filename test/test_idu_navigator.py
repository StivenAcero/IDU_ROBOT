import pytest
from unittest.mock import MagicMock, patch
from selenium.common.exceptions import TimeoutException
from src.idu_navigator import IduNavigator


# -------------------------------------------------------------
# DummyDriver: Simula un driver REAL sin abrir Chrome
# -------------------------------------------------------------
class DummyDriver:
    def __init__(self):
        self.log = []
        self.switch_to = MagicMock()
        self.switch_to.frame = MagicMock()
        self.switch_to.default_content = MagicMock()

    def get(self, url):
        self.log.append(f"GET:{url}")

    def quit(self):
        self.log.append("QUIT")

    def find_element(self, *args, **kwargs):
        if "FAIL" in self.log:
            raise Exception("not found")
        return MagicMock()

    def find_elements(self, *args, **kwargs):
        return []

    # simulate click element
    def click(self):
        return None


# -------------------------------------------------------------
# FIXTURE GLOBAL: Mock completo de Selenium
# -------------------------------------------------------------
@pytest.fixture
def navigator():

    with patch("src.idu_navigator.chromedriver_autoinstaller.install", return_value=None), \
         patch("src.idu_navigator.Options") as mock_options_cls, \
         patch("src.idu_navigator.Service") as mock_service_cls, \
         patch("src.idu_navigator.webdriver.Chrome") as mock_chrome_cls, \
         patch("src.idu_navigator.IduConfig.load_config",
               return_value=MagicMock(prefs={})), \
         patch("src.idu_navigator.WebDriverWait") as mock_wait_cls:

        dummy = DummyDriver()
        mock_chrome_cls.return_value = dummy

        mock_options_cls.return_value = MagicMock()
        mock_service_cls.return_value = MagicMock()

        mock_wait = MagicMock()
        mock_wait.until.return_value = MagicMock()
        mock_wait_cls.return_value = mock_wait

        nav = IduNavigator()
        # pylint: disable=maybe-no-member
        nav._driver = dummy 
        return nav


# -------------------------------------------------------------
# Tests: navegar_a_url
# -------------------------------------------------------------
def test_navegar_a_url(navigator):
    navigator.navegar_a_url("http://example.com")
    assert "GET:http://example.com" in navigator._driver.log


def test_navegar_a_url_timeout(navigator):
    with patch("src.idu_navigator.WebDriverWait") as mock_wait:
        mock = MagicMock()
        mock.until.side_effect = TimeoutException()
        mock_wait.return_value = mock
        with pytest.raises(TimeoutException):
            navigator.navegar_a_url("http://example.com")


def test_navegar_a_url_error_general(navigator):
    """Test error general en navegación"""
    with patch.object(navigator._driver, 'get', side_effect=Exception("boom")):
        with pytest.raises(Exception):
            navigator.navegar_a_url("http://example.com")


# -------------------------------------------------------------
# Tests: realizar_clicks_secuenciales
# -------------------------------------------------------------
def test_realizar_clicks_secuenciales(navigator):

    # Creamos un botón clickeable
    button = MagicMock()
    button.click.return_value = None

    navigator._driver.find_element = MagicMock(return_value=button)

    # Mock para element_to_be_clickable
    with patch("src.idu_navigator.EC.element_to_be_clickable",
               return_value=lambda d: button):

        navigator.realizar_clicks_secuenciales(num_clicks=2)
        assert button.click.call_count == 2


def test_realizar_clicks_secuenciales_sin_elementos(navigator):

    navigator._driver.find_element = MagicMock(side_effect=Exception("not found"))

    with patch("src.idu_navigator.EC.element_to_be_clickable",
               return_value=lambda d: (_ for _ in ()).throw(Exception("not found"))):

        with pytest.raises(Exception):
            navigator.realizar_clicks_secuenciales(1)


def test_realizar_clicks_secuenciales_error_click(navigator):
    """Test error durante el click"""
    mock_button = MagicMock()
    mock_button.click.side_effect = Exception("bad click")
    
    with patch("src.idu_navigator.WebDriverWait") as mock_wait:
        mock_wait.return_value.until.return_value = mock_button
        with pytest.raises(Exception):
            navigator.realizar_clicks_secuenciales(num_clicks=1)


# -------------------------------------------------------------
# Tests: buscar_iframe_chat
# -------------------------------------------------------------
def test_buscar_iframe_chat(navigator):

    iframe1 = MagicMock()
    iframe1.get_attribute.return_value = "chat_valorizacion/chat"

    navigator._driver.find_elements = MagicMock(return_value=[iframe1])

    result = navigator.buscar_iframe_chat()
    assert result is True
    navigator._driver.switch_to.frame.assert_called_once_with(iframe1)


def test_buscar_iframe_chat_no_encontrado(navigator):

    iframe1 = MagicMock()
    iframe1.get_attribute.return_value = "other"

    navigator._driver.find_elements = MagicMock(return_value=[iframe1])

    result = navigator.buscar_iframe_chat()
    assert result is False


def test_buscar_iframe_chat_excepcion(navigator):
    """Test excepción al buscar iframes"""
    with patch.object(navigator._driver, 'find_elements', side_effect=Exception("bad iframe")):
        result = navigator.buscar_iframe_chat()
        assert result is False


# -------------------------------------------------------------
# buscar_tabla_formulario
# -------------------------------------------------------------
def test_buscar_tabla_formulario(navigator):

    table = MagicMock()
    navigator._driver.find_element = MagicMock(return_value=table)

    result = navigator.buscar_tabla_formulario()
    assert result is not None


def test_buscar_tabla_formulario_no_encontrado(navigator):

    navigator._driver.find_element = MagicMock(side_effect=Exception("no table"))
    result = navigator.buscar_tabla_formulario()

    assert result is None


def test_buscar_tabla_formulario_excepcion(navigator):
    """Test excepción en WebDriverWait"""
    with patch("src.idu_navigator.WebDriverWait") as mock_wait:
        mock_wait.return_value.until.side_effect = Exception("timeout")
        result = navigator.buscar_tabla_formulario()
        assert result is None


# -------------------------------------------------------------
# buscar_input_username
# -------------------------------------------------------------
def test_buscar_input_username(navigator):

    table = MagicMock()
    input_mock = MagicMock()
    table.find_element = MagicMock(return_value=input_mock)

    result = navigator.buscar_input_username(table)
    assert result == input_mock


def test_buscar_input_username_none(navigator):

    table = MagicMock()
    table.find_element = MagicMock(side_effect=Exception("not found"))

    result = navigator.buscar_input_username(table)
    assert result is None


def test_buscar_input_username_error_sin_tabla(navigator):
    """Test buscar input sin tabla (usa WebDriverWait)"""
    with patch("src.idu_navigator.WebDriverWait") as mock_wait:
        mock_wait.return_value.until.side_effect = Exception("no input")
        result = navigator.buscar_input_username(None)
        assert result is None


# -------------------------------------------------------------
# preparar_formulario
# -------------------------------------------------------------
def test_preparar_formulario(navigator):

    table = MagicMock()
    navigator.buscar_iframe_chat = MagicMock(return_value=True)
    navigator.buscar_tabla_formulario = MagicMock(return_value=table)
    navigator.buscar_input_username = MagicMock(return_value=MagicMock())

    iu, tbl, flag = navigator.preparar_formulario()

    assert iu is not None
    assert tbl == table
    assert flag is True


def test_preparar_formulario_falla_iframe(navigator):

    navigator.buscar_iframe_chat = MagicMock(return_value=False)
    navigator.buscar_tabla_formulario = MagicMock(return_value=None)

    iu, tbl, flag = navigator.preparar_formulario()

    assert iu is None
    assert tbl is None
    assert flag is False


def test_preparar_formulario_no_input(navigator):
    """Test cuando se encuentra la tabla pero no el input"""
    navigator.buscar_iframe_chat = MagicMock(return_value=True)
    tabla = MagicMock()
    navigator.buscar_tabla_formulario = MagicMock(return_value=tabla)
    navigator.buscar_input_username = MagicMock(return_value=None)

    u, t, inside = navigator.preparar_formulario()
    assert u is None
    assert t == tabla
    assert inside is True


# -------------------------------------------------------------
# rellenar campos
# -------------------------------------------------------------
def test_rellenar_campo_nombre(navigator):

    table = MagicMock()
    input_mock = MagicMock()
    table.find_element = MagicMock(return_value=input_mock)

    assert navigator.rellenar_campo_nombre(table, "Juan") is True
    input_mock.send_keys.assert_called_with("Juan")


def test_rellenar_campo_nombre_sin_tabla(navigator):
    """Test rellenar nombre sin tabla"""
    result = navigator.rellenar_campo_nombre(None, "Juan")
    assert result is False


def test_rellenar_campo_email(navigator):

    table = MagicMock()
    input_mock = MagicMock()
    table.find_element = MagicMock(return_value=input_mock)

    assert navigator.rellenar_campo_email(table, "mail@test.com") is True
    input_mock.send_keys.assert_called_with("mail@test.com")


def test_rellenar_campo_email_sin_tabla(navigator):
    """Test rellenar email sin tabla"""
    result = navigator.rellenar_campo_email(None, "mail@x.com")
    assert result is False


def test_rellenar_campo_mensaje_solicitud(navigator):

    table = MagicMock()
    textarea = MagicMock()
    table.find_element = MagicMock(return_value=textarea)

    solicitud = {"chips": "111,222"}
    assert navigator.rellenar_campo_mensaje_solicitud(table, solicitud) is True

    textarea.send_keys.assert_called()


def test_rellenar_campo_mensaje_solicitud_sin_tabla(navigator):
    """Test rellenar mensaje sin tabla"""
    result = navigator.rellenar_campo_mensaje_solicitud(None, {"chips": "111"})
    assert result is False


# -------------------------------------------------------------
# click iniciar chat
# -------------------------------------------------------------
def test_click_iniciar_chat(navigator):

    button = MagicMock()
    navigator._driver.find_element = MagicMock(return_value=button)

    with patch("src.idu_navigator.EC.element_to_be_clickable",
               return_value=lambda d: button):

        assert navigator.click_iniciar_chat() is True
        button.click.assert_called_once()


def test_click_iniciar_chat_falla(navigator):

    navigator._driver.find_element = MagicMock(side_effect=Exception("missing"))

    with patch("src.idu_navigator.EC.element_to_be_clickable",
               return_value=lambda d: (_ for _ in ()).throw(Exception("missing"))):

        assert navigator.click_iniciar_chat() is False


def test_click_iniciar_chat_excepcion_switch(navigator):
    """Test cuando falla el switch_to después de la excepción"""
    with patch("src.idu_navigator.WebDriverWait") as mock_wait:
        mock_wait.return_value.until.side_effect = Exception("boom")
        
        # Mock del switch_to para que también falle
        navigator._driver.switch_to.default_content.side_effect = Exception("bad switch")
        
        result = navigator.click_iniciar_chat()
        assert result is False


# -------------------------------------------------------------
# reiniciar_navegador
# -------------------------------------------------------------
def test_reiniciar_navegador(navigator):

    dummy_old = navigator._driver               # driver inicial
    dummy_old.quit = MagicMock()                # evitar cerrar realmente

    # --- Nuevo driver simulado que reemplaza al anterior ---
    dummy_new = DummyDriver()
    dummy_new.get = MagicMock(return_value=None)

    with patch("src.idu_navigator.webdriver.Chrome", return_value=dummy_new):
        with patch("src.idu_navigator.WebDriverWait") as mock_wait:

            mock_wait_instance = MagicMock()
            mock_wait_instance.until.return_value = True
            mock_wait.return_value = mock_wait_instance

            navigator.reiniciar_navegador("http://example.com")

    # validaciones
    dummy_old.quit.assert_called_once()
    dummy_new.get.assert_called_once_with("http://example.com")


def test_reiniciar_navegador_error_en_cerrar(navigator):
    """Test cuando falla el quit pero continúa"""
    # Guardamos referencia al mock de quit ANTES de que se reemplace el driver
    mock_quit = MagicMock(side_effect=Exception("cant close"))
    navigator._driver.quit = mock_quit
    
    dummy_new = DummyDriver()
    
    with patch("src.idu_navigator.webdriver.Chrome", return_value=dummy_new):
        with patch("src.idu_navigator.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = True
            
            navigator.reiniciar_navegador("http://example.com")
            
            # Verifica que se intentó cerrar usando la referencia guardada
            mock_quit.assert_called_once()


def test_reiniciar_navegador_falla_3_veces(navigator):
    """Test cuando falla 3 veces y lanza excepción"""
    navigator._driver.quit = MagicMock()
    
    dummy_new = DummyDriver()
    
    with patch("src.idu_navigator.webdriver.Chrome", return_value=dummy_new):
        with patch("src.idu_navigator.WebDriverWait") as mock_wait:
            # Simula que falla todas las veces
            mock_wait.return_value.until.side_effect = Exception("no load")
            
            with pytest.raises(Exception):
                navigator.reiniciar_navegador("http://example.com")
