from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class TestNewTest:
    def setup_method(self, method):
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-features=Translate,BackForwardCache")

        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.automatic_downloads": 1
        }
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def teardown_method(self, method):
        self.driver.quit()

    def wait_page_ready(self):
        WebDriverWait(self.driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def scroll_top(self):
        self.driver.execute_script("window.scrollTo(0, 0);")

    def esperar_carregamento_sumir(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element((By.XPATH, "//div[contains(@class,'x-mask-msg')]"))
            )
        except:
            pass  # às vezes não aparece

    def clicar_com_retry(self, by, locator, tentativas=3, tempo_espera=2):
        for _ in range(tentativas):
            try:
                el = WebDriverWait(self.driver, tempo_espera).until(EC.element_to_be_clickable((by, locator)))
                self.driver.execute_script("arguments[0].click();", el)
                time.sleep(1)  # Adicionando intervalo de 1 segundo após cada clique
                return True
            except:
                time.sleep(0.2)
        return False

    def test_newTest(self):
        self.driver.get("http://10.100.21.48")
        self.wait_page_ready()
        self.scroll_top()
        print('Página carregada!')
        time.sleep(1)  # Intervalo para garantir o carregamento completo da página

        # LOGIN
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'loginUsername')]"))).send_keys("admin")
        self.driver.find_element(By.XPATH, "//input[contains(@id, 'loginPassword')]").send_keys("@1234567", Keys.ENTER)
        time.sleep(1)  # Intervalo após o envio do login
        self.esperar_carregamento_sumir()

        # MENU > REDE > TCP/IP
        print("Iniciando teste TCP/IP e DNS")
        self.clicar_com_retry(By.XPATH, "//a[.//span[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'menu principal']]")
        time.sleep(1)
        self.clicar_com_retry(By.XPATH, "//*[text()='Rede']")
        time.sleep(1)
        self.clicar_com_retry(By.XPATH, "//*[text()='TCP/IP']")
        time.sleep(1)

        # Editar configuração
        self.clicar_com_retry(By.CSS_SELECTOR, ".editIcon")
        time.sleep(1)

        self.clicar_com_retry(By.XPATH, "//span[contains(.,'Estático')]")
        time.sleep(1)

        # TAB até campo e digita "1"
        for _ in range(5):
            self.driver.switch_to.active_element.send_keys(Keys.TAB)
            time.sleep(1)  # Intervalo após cada TAB
        self.driver.switch_to.active_element.send_keys("1")
        time.sleep(1)  # Intervalo após digitar "1"
        # Botão "Teste"
        self.clicar_com_retry(By.XPATH, "//a[contains(@class, 'button_green')]//span[normalize-space()='Teste']")
        time.sleep(1)
        # Espera por mensagem de conflito
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Conflito de IP')]")))
        time.sleep(1)
        # Seleciona opção DHCP
        self.clicar_com_retry(By.XPATH, "//label[contains(@class,'radio-label') and contains(normalize-space(text()), 'DHCP')]")
        self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        time.sleep(1)
        # Força o clique direto no SPAN também (garantia)
        dhcp_span = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[t='net.DHCP']")))
        self.driver.execute_script("arguments[0].click()", dhcp_span)
        time.sleep(2)


        #####>>>> AUTO REGISTRO <<<<#####
        print("Iniciando teste de Auto Registro")
        registrar_span = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[t='sys.AutoRegister']")))
        self.driver.execute_script("arguments[0].click()", registrar_span)
        time.sleep(1)
        habilitar_span = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[t='com.Enable']")))
        self.driver.execute_script("arguments[0].click()", habilitar_span)
        time.sleep(1)
        # Endereço do Servidor
        servidor_span = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Endereço do Servidor']")))
        servidor_span.click()
        time.sleep(1)
        # Espera o campo ativar e digita
        WebDriverWait(self.driver, 5).until(lambda d: d.switch_to.active_element.tag_name == "input")
        campo = self.driver.switch_to.active_element
        campo.send_keys(Keys.CONTROL, "a")
        campo.send_keys("10.100.20.101", Keys.TAB)
        self.driver.switch_to.active_element.send_keys("9500", Keys.TAB)
        self.driver.switch_to.active_element.send_keys("lucas")
        time.sleep(1)  # Intervalo final após digitar no campo


        ##### EMAIL
        print("Testando email!")
        self.clicar_com_retry(By.XPATH, "//span[contains(text(), 'E-mail')]")
        time.sleep(1)
        #habilitar
        self.clicar_com_retry(By.XPATH, "//span[@t='com.Enable' and contains(text(), 'Habilitar')]")
        time.sleep(1)
        self.driver.switch_to.active_element.send_keys(Keys.TAB * 2)
        self.driver.switch_to.active_element.send_keys("smtp.gmail.com")
        self.driver.switch_to.active_element.send_keys(Keys.TAB)
        self.driver.switch_to.active_element.send_keys("587")
        self.driver.switch_to.active_element.send_keys(Keys.TAB * 2)
        self.driver.switch_to.active_element.send_keys("grupo.hdcvi2@gmail.com")
        self.driver.switch_to.active_element.send_keys(Keys.TAB)
        self.driver.switch_to.active_element.send_keys("ugsxpwybyrxtxeqt")
        self.driver.switch_to.active_element.send_keys(Keys.TAB)
        self.driver.switch_to.active_element.send_keys("grupo.hdcvi2@gmail.com")
        self.driver.switch_to.active_element.send_keys(Keys.TAB * 4)
        self.driver.switch_to.active_element.send_keys("grupo.hdcvi2@gmail.com")
        time.sleep(0.5)
        self.driver.switch_to.active_element.send_keys(Keys.TAB)
        self.driver.switch_to.active_element.send_keys(Keys.ENTER)
        self.clicar_com_retry(By.XPATH, "//span[normalize-space(text())='Salvar']")
        self.clicar_com_retry(By.XPATH, "//a[.//span[normalize-space(text())='Teste']]")
        time.sleep(7)


        ### DDNS
        print("Testando DDNS")
        self.clicar_com_retry(By.XPATH, "//span[contains(text(), 'DDNS')]")
        time.sleep(1)
        self.clicar_com_retry(By.XPATH, "//span[@t='com.Enable' and contains(text(), 'Habilitar')]")
        self.driver.switch_to.active_element.send_keys(Keys.TAB * 2)
        self.driver.switch_to.active_element.send_keys("lucas.oliveira@intelbras.com.br")
        self.driver.switch_to.active_element.send_keys(Keys.TAB)
        self.driver.switch_to.active_element.send_keys("teste456")
        self.clicar_com_retry(By.XPATH, "//span[normalize-space(text())='Salvar']")
        time.sleep(5)


        

        ### FTP
        self.clicar_com_retry(By.XPATH, "//span[contains(text(), 'FTP')]")
        time.sleep(1)
        self.clicar_com_retry(By.XPATH, "//span[@t='com.Enable' and contains(text(), 'Habilitar')]")
        self.driver.switch_to.active_element.send_keys(Keys.TAB)
        self.driver.switch_to.active_element.send_keys(Keys.ENTER * 2)
        self.clicar_com_retry(By.XPATH, "//span[normalize-space(text())='Endereço do Servidor']")
        self.driver.switch_to.active_element.send_keys("10.100.22.102")
        self.driver.switch_to.active_element.send_keys(Keys.TAB)
        self.driver.switch_to.active_element.send_keys("2222")
        self.driver.switch_to.active_element.send_keys(Keys.TAB)
        self.driver.switch_to.active_element.send_keys("admin")
        self.driver.switch_to.active_element.send_keys(Keys.TAB)
        self.driver.switch_to.active_element.send_keys("@1234567")


        ##### PORTAS #####
        self.clicar_com_retry(By.XPATH, "//span[contains(text(), 'Porta')]")

if __name__ == "__main__":
    test = TestNewTest()
    test.setup_method(None)
    try:
        test.test_newTest()
    finally:
        input("Pressione Enter para sair e fechar o navegador...")
        test.teardown_method(None)
