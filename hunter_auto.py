import sys
import socket
import struct
import time
from ctypes import *
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMessageBox, QTableWidgetItem,
    QDialog, QVBoxLayout, QGroupBox, QTableWidget, QPushButton,
    QLabel, QLineEdit, QHBoxLayout, QProgressBar
)
from PyQt5.QtGui import QFont, QPalette, QColor

from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Enum import EM_SEND_SEARCH_TYPE
from NetSDK.SDK_Struct import *
from PyQt5.QtWidgets import QMenu
from queue import Queue  # Importa a classe Queue
from pylau import AdapterSelectionDialog

# Se o atributo UNICAST não existir, define-o (valor arbitrário diferente do MULTICAST_AND_BROADCAST)
if not hasattr(EM_SEND_SEARCH_TYPE, 'UNICAST'):
    EM_SEND_SEARCH_TYPE.UNICAST = 2

# Configuração de estilo global (pode ser ajustada)
STYLE_SHEET = """
    QWidget {
        background-color: rgba(0, 50, 0, 0.7); /* Verde escuro semi-transparente */
        color: #ecf0f1;
        font-family: 'Segoe UI';
        font-size: 12px;
        font-weight: bold;
    }

    QGroupBox {
        border: 2px solid #3498db;
        border-radius: 5px;
        margin-top: 20px;
        padding-top: 15px;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        color: #3498db;
        font-weight: bold;
    }

    QTableWidget {
        background-color: #34495e;
        gridline-color: #7f8c8d;
        selection-background-color: #3498db;
        border: none;
        border-radius: 3px;
    }

    QHeaderView::section {
        background-color: #3498db;
        color: white;
        padding: 4px;
        border: none;
    }

    QPushButton {
        background-color: #27ae60;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 3px;
        min-width: 80px;
        font-weight: bold;
    }

    QPushButton:hover {
        background-color: #219a52;
    }

    QPushButton:pressed {
        background-color: #1d8348;
    }

    QLineEdit {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid #7f8c8d;
        border-radius: 3px;
        padding: 5px;
        color: white;
        font-weight: bold;
    }
    QLineEdit:focus {
        border: 2px solid #3498db;
    }

    QProgressBar {
        border: 1px solid #34495e;
        border-radius: 3px;
        text-align: center;
        background-color: #2c3e50;
    }

    QProgressBar::chunk {
        background-color: #27ae60;
        border-radius: 2px;
    }

    QDialogButtonBox QPushButton {
        background-color: rgba(0, 100, 0, 0.7);
        color: white;
        border: 1px solid rgba(0, 200, 0, 0.7);
        border-radius: 4px;
        padding: 6px 12px;
        font-weight: bold;
        min-width: 70px;
    }

    QDialogButtonBox QPushButton:hover {
        background-color: rgba(0, 150, 0, 0.8);
    }
    QDialogButtonBox QPushButton:pressed {
        background-color: rgba(0, 120, 0, 0.9);
    }
    QLabel {
        color: white;
        font-weight: bold;
    }
"""

class InitDevAccountDialog(QDialog):  # Diálogo simplificado
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inicialização do Dispositivo")
        self.setFixedSize(400, 300)
        # self.setStyleSheet(STYLE_SHEET)  # Não é mais necessário, usar estilo global

        layout = QVBoxLayout(self)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Usuário")  # Adiciona placeholder
        self.password = QLineEdit()
        self.password.setPlaceholderText("Senha")  # Adiciona placeholder
        self.password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirmar Senha")  # Adiciona placeholder
        self.confirm_password.setEchoMode(QLineEdit.Password)

        form_layout = QVBoxLayout()  # Alterado para QVBoxLayout
        form_layout.addWidget(QLabel("Usuário:"))
        form_layout.addWidget(self.username)
        form_layout.addWidget(QLabel("Senha:"))
        form_layout.addWidget(self.password)
        form_layout.addWidget(QLabel("Confirmar Senha:"))
        form_layout.addWidget(self.confirm_password)

        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept)  # Conecta ao slot accept

        layout.addLayout(form_layout)  # Adiciona o layout do formulário ao layout principal
        layout.addWidget(self.btn_ok)  # Adiciona o botão ao layout principal

class FtpCredentialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações de FTP")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout(self)

        self.username = QLineEdit("admin")  # Preenchido com "admin"
        self.password = QLineEdit("@1234567")  # Preenchido com "@1234567"
        self.password.setEchoMode(QLineEdit.Password)

        layout.addWidget(QLabel("Usuário:"))
        layout.addWidget(self.username)
        layout.addWidget(QLabel("Senha:"))
        layout.addWidget(self.password)

        self.adapter_selection_button = QPushButton("Selecionar Adaptador de Rede")
        self.adapter_selection_button.clicked.connect(self.open_adapter_selection)

        layout.addWidget(self.adapter_selection_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.selected_adapter = None

    def open_adapter_selection(self):
        dialog = AdapterSelectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_adapter = dialog.selected_adapter
            print(f"Adaptador selecionado: {self.selected_adapter}")  # Para depuração

class FtpAutomationThread(QThread):
    finished = pyqtSignal()  # Sinal para indicar que a automação foi concluída
    error = pyqtSignal(str)  # Sinal para indicar um erro

    def __init__(self, full_url, username, password, selected_adapter):
        super().__init__()
        self.full_url = full_url
        self.username = username
        self.password = password
        self.selected_adapter = selected_adapter

    def run(self):
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys
        import time

        # ========== CONFIG ========== 
        BASE_URL = self.full_url  # Use a URL completa (IP:Porta)

        # ========== CHROME ========== 
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)
        driver.get(BASE_URL)

        try:
            # Campo usuário com múltiplas opções de placeholder
            campo_usuario = wait.until(EC.presence_of_element_located((
                By.XPATH,
                '//input[@placeholder="Nomeutilizador" or @placeholder="Usuário" or @placeholder="Username"]'
            )))
            campo_usuario.send_keys(self.username)  # Usa o nome de usuário do diálogo

            # Campo senha com múltiplas opções de placeholder
            campo_senha = wait.until(EC.presence_of_element_located((
                By.XPATH,
                '//input[@placeholder="Palavra-Passe" or @placeholder="Senha" or @placeholder="Password"]'
            )))
            for char in self.password:  # Usa a senha do diálogo
                campo_senha.send_keys(char)
                time.sleep(0.1)

            # Pressiona Enter no campo de senha
            campo_senha.send_keys(Keys.RETURN)

            # Aguarda o redirecionamento
            # wait.until(EC.url_contains("#/index"))
            # time.sleep(1)

            # Clicar em "CONFIG." ou "Menu Principal"
            config_tab = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                '//span[@class="ui5-tab-item-text" and text()="CONFIG."] | '  # opção 1
                '//a[.//span[@t="com.CONFIGTITLE" and contains(text(), "Configurações")]]'  # opção 2
            )))
            config_tab.click()
            time.sleep(0.5)

            # Clicar em "STORAGE"
            storage_div = wait.until(EC.element_to_be_clickable((
                By.XPATH, 
                '//div[@class="ui5-grid-item-title text-ellipsis" and @title="STORAGE"] | '
                '//div[contains(@class,"x-menu-item") and .//span[@t="net.NetworkSet" and contains(text(),"Rede")]]'
            )))
            storage_div.click()
            time.sleep(0.5)

            # Clicar em "FTP"
            ftp_div = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                '//div[@title="FTP"]//a[text()="FTP"] | '  # Opção 1 (interface clássica)
                '//tr[contains(@class,"x-grid-row") and .//span[@t="com.FTP" and contains(text(),"FTP")]]'  # Opção 2 (tabela com <tr>)
            )))
            ftp_div.click()
            time.sleep(0.5)
            
            # Clicar no label que contém "FTP"
            label_ftp = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                '//label[contains(@class, "ant-radio-wrapper") and .//div[text()="FTP"]] | '  # Opção 1 (ant-radio)
                '//label[@class="radio-label radio-label-after" and .//span[@t="com.FTP" and contains(text(),"FTP")]]'  # Opção 2 (x-form label direto)
            )))
            driver.execute_script("arguments[0].click();", label_ftp)
            time.sleep(0.5)
            
            # Aguardar e clicar no botão OK da caixa de diálogo de confirmação ou no botão "Salvar"
            botao_modal_ok = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                '//div[@class="ant-modal-confirm-btns"]//button[span[text()="OK"]] | '  # Opção 1: modal OK
                '//span[@id="button-1005-btnIconEl"]'   # Opção 2: botão Salvar
            )))
            botao_modal_ok.click()
            time.sleep(0.5)

            # Encontra o label pelo texto "Habilitar"
            label = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                '//label[span[text()="Habilitar"]]'
            )))

            # Clica no label
            label.click()

            # Preencher IP
            campo_ip = wait.until(EC.presence_of_element_located((
                By.XPATH,
                '//div[contains(@class,"label-custom-wrapper")]//input[@type="text"] | '  # Opção 1
                '//input[@type="text" and @id="textfield-1392-inputEl"]'  # Opção 2 corrigida
            )))
            campo_ip.clear()
            campo_ip.send_keys(self.selected_adapter)  # Aqui você pode usar o IP do adaptador selecionado, se necessário
            time.sleep(0.5)
            # Pressionar TAB para ir para o campo Porta
            campo_ip.send_keys(Keys.TAB)

            # Preencher Porta (evitando deixar vazio)
            webdriver.ActionChains(driver).send_keys(Keys.BACKSPACE).perform()  # Remove um dígito se necessário
            webdriver.ActionChains(driver).send_keys("2222").perform()  # Usa a porta HTTP
            time.sleep(0.5)
            webdriver.ActionChains(driver).send_keys(Keys.TAB).perform()

            # Preencher Nomeutilizador
            time.sleep(0.5)
            webdriver.ActionChains(driver).send_keys(self.username).perform()  # Usa o nome de usuário do diálogo
            time.sleep(0.5)
            webdriver.ActionChains(driver).send_keys(Keys.TAB).perform()

            # Preencher Palavra-Passe
            time.sleep(0.5)
            webdriver.ActionChains(driver).send_keys(self.password).perform()  # Usa a senha do diálogo
            time.sleep(0.5)

            print("✅ Campos preenchidos com sucesso!")

        except Exception as e:
            self.error.emit(f"❌ Erro: {e}")

        finally:
            driver.quit()
            self.finished.emit()  # Emite o sinal de que a automação foi concluída


class SearchDeviceWidget(QWidget):
    update_table = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Buscador de Dispositivos")
        self.setFixedSize(900, 700)

        self.sdk = NetClient()
        self.sdk.InitEx(None, 0)

        self.init_ui()
        self.search_thread = None

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Campo de busca para filtrar a tabela
        search_layout = QHBoxLayout()
        lbl_search = QLabel("Pesquisar:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Digite para buscar...")
        self.search_edit.textChanged.connect(self.filter_table)
        search_layout.addWidget(lbl_search)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Tabela de dispositivos
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Nº", "Status", "IP", "Porta",
            "MAC", "Tipo", "Detalhes", "HTTP"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Configuração de IP para busca unicast
        ip_layout = QHBoxLayout()
        self.start_ip = QLineEdit()
        self.start_ip.setPlaceholderText("IP Inicial")
        self.end_ip = QLineEdit()
        self.end_ip.setPlaceholderText("IP Final")
        ip_layout.addWidget(QLabel("IP Inicial:"))
        ip_layout.addWidget(self.start_ip)
        ip_layout.addWidget(QLabel("IP Final:"))
        ip_layout.addWidget(self.end_ip)
        layout.addLayout(ip_layout)

        # Botões de controle
        btn_layout = QHBoxLayout()
        self.btn_multicast = QPushButton("Buscar na Rede")
        self.btn_unicast = QPushButton("Buscar por IP")
        self.btn_init = QPushButton("Inicializar")
        self.btn_clear = QPushButton("Limpar")  # Novo botão "Limpar"
        self.btn_clear.setStyleSheet("background-color: #e67e22; color: white;")  # Estilo laranja
        btn_layout.addWidget(self.btn_multicast)
        btn_layout.addWidget(self.btn_unicast)
        btn_layout.addWidget(self.btn_init)
        btn_layout.addWidget(self.btn_clear)  # Adiciona o botão "Limpar"
        layout.addLayout(btn_layout)

        # Conexões
        self.btn_multicast.clicked.connect(self.start_multicast_search)
        self.btn_unicast.clicked.connect(self.start_unicast_search)
        self.btn_init.clicked.connect(self.init_device)
        self.btn_clear.clicked.connect(self.clear_table)  # Conecta o botão "Limpar" ao método
        self.update_table.connect(self.update_device_table)

         # Conectar o campo de IP ao método de busca
        self.end_ip.returnPressed.connect(self.start_unicast_search)  # Conecta o Enter ao método de busca

        # Barra de progresso
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)

        # Conectar o sinal de clique com o botão direito
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        """Exibe o menu de contexto ao clicar com o botão direito na tabela."""
        menu = QMenu(self)

        # Adiciona a ação para executar a automação
        action_run_automation = menu.addAction("Ativar FTP")
        action_run_automation2 = menu.addAction("Ativar SFTP")
        action_run_automation3 = menu.addAction("Testar DHCP")
        action_run_automation4 = menu.addAction("Ativar E-mail")
        action_run_automation.triggered.connect(self.run_automation)

        # Exibe o menu no local do clique
        menu.exec_(self.table.viewport().mapToGlobal(pos))

    def run_automation(self):
        """Executa a automação com o IP e a porta do dispositivo selecionado."""
        current_row = self.table.currentRow()
        if current_row >= 0:  # Verifica se uma linha está selecionada
            ip_item = self.table.item(current_row, 2)  # Coluna do IP
            http_port_item = self.table.item(current_row, 7)  # Coluna da Porta HTTP
            if ip_item and http_port_item:
                ip_address = ip_item.text()
                http_port = http_port_item.text()
                full_url = f"http://{ip_address}:{http_port}"  # Formata a URL

                # Abre o diálogo de credenciais
                credentials_dialog = FtpCredentialsDialog(self)
                if credentials_dialog.exec_() == QDialog.Accepted:
                    username = credentials_dialog.username.text()
                    password = credentials_dialog.password.text()
                    selected_adapter = credentials_dialog.selected_adapter

                    # Inicia a thread de automação
                    self.ftp_thread = FtpAutomationThread(full_url, username, password, selected_adapter)
                    self.ftp_thread.finished.connect(self.on_automation_finished)
                    self.ftp_thread.error.connect(self.on_automation_error)
                    self.ftp_thread.start()

    def on_automation_finished(self):
        """Método chamado quando a automação é concluída."""
        QMessageBox.information(self, "Concluído", "A automação FTP foi concluída com sucesso!")

    def on_automation_error(self, error_message):
        """Método chamado quando ocorre um erro na automação."""
        QMessageBox.critical(self, "Erro", error_message)

    def clear_table(self):
        """Limpa a tabela de dispositivos."""
        self.table.setRowCount(0)  # Remove todas as linhas da tabela

    def showEvent(self, event):
        super().showEvent(event)
        self.set_title_bar_color()

    def set_title_bar_color(self):
        """
        Utiliza DwmSetWindowAttribute para alterar a cor da barra de título e do texto
        na janela nativa do Windows 11.
        """
        try:
            from ctypes import windll, byref, c_int, sizeof
            # Constantes para os atributos do DWM
            DWMWA_CAPTION_COLOR = 35
            DWMWA_TEXT_COLOR = 36

            hwnd = int(self.winId())
            # Calcula o COLORREF para a cor verde (RGB(0, 50, 0)):
            caption_color_value = 0 | (50 << 8) | (0 << 16)
            caption_color = c_int(caption_color_value)
            # Define a cor do texto como branco (RGB(255, 255, 255))
            text_color_value = 255 | (255 << 8) | (255 << 16)
            text_color = c_int(text_color_value)

            windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, byref(caption_color), sizeof(caption_color))
            windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_TEXT_COLOR, byref(text_color), sizeof(text_color))
        except Exception as e:
            print(f"Erro ao definir a cor da barra de título: {e}")

    def start_multicast_search(self):
        self.start_search(EM_SEND_SEARCH_TYPE.MULTICAST_AND_BROADCAST)

    def start_unicast_search(self):
        # Verifica se os campos de IP foram preenchidos
        start = self.start_ip.text().strip()
        end = self.end_ip.text().strip()
        
        if not start or not end:
            QMessageBox.warning(self, "Aviso", "Por favor, preencha os campos IP Inicial e IP Final.")
            return

        # Verifica se o campo final contém apenas números
        if not end.isdigit() or not (0 <= int(end) <= 255):
            QMessageBox.warning(self, "Aviso", "Por favor, insira um número válido (0-255) no campo IP Final.")
            return

        # Divide o IP inicial em partes
        ip_parts = start.split('.')
        if len(ip_parts) != 4:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um IP válido no campo IP Inicial.")
            return

        # Constrói o IP final
        final_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{end}"

        # Inicia a busca
        self.start_search(EM_SEND_SEARCH_TYPE.UNICAST, start, final_ip)

    def validate_ips(self, start, end):
        # TODO: Implementar uma validação adequada de IPs
        return True

    def start_search(self, search_type, start=None, end=None):
        if self.search_thread:
            self.search_thread.stop()  # Para qualquer busca existente

        self.search_thread = SearchThread(
            self, self.sdk, search_type, start, end  # Adiciona self
        )
        self.search_thread.found_device.connect(self.update_table.emit)  # Conecta o sinal de dispositivos encontrados
        self.search_thread.finished_search.connect(self.search_finished)  # Conecta sinal de término da busca
        self.search_thread.start()
        self.progress.show()  # Mostra a barra de progresso
        self.progress.setRange(0, 0)  # Indeterminado

    def search_finished(self):
        self.progress.setRange(0, 1)  # Reseta a barra de progresso
        self.progress.setValue(1)
        self.progress.hide()

    def update_device_table(self, device_info):
        row = self.table.rowCount()
        self.table.insertRow(row)

        status = "✅" if device_info[0] else "❌"  # Usa marca de verificação ou X para status
        self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.table.setItem(row, 1, QTableWidgetItem(status))
        self.table.setItem(row, 2, QTableWidgetItem(device_info[2]))
        self.table.setItem(row, 3, QTableWidgetItem(str(device_info[3])))
        self.table.setItem(row, 4, QTableWidgetItem(device_info[4]))
        self.table.setItem(row, 5, QTableWidgetItem(device_info[5]))
        self.table.setItem(row, 6, QTableWidgetItem(device_info[6]))
        self.table.setItem(row, 7, QTableWidgetItem(str(device_info[7])))

    def filter_table(self, text):
        """Filtra as linhas da tabela com base no texto digitado."""
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def init_device(self):
        dialog = InitDevAccountDialog(self)  # Passa 'self' como pai
        if dialog.exec_():
            # TODO: Implementar lógica de inicialização
            pass


class SearchThread(QThread):
    found_device = pyqtSignal(list)
    finished_search = pyqtSignal()

    def __init__(self, main_window, sdk, search_type, start_ip=None, end_ip=None):  # Adiciona main_window
        super().__init__()
        self.main_window = main_window  # Referência à janela principal
        self.sdk = sdk
        self.search_type = search_type
        self.start_ip = start_ip
        self.end_ip = end_ip
        self.running = True
        self.search_handle = 0  # Handle da busca

    def run(self):
        if self.search_type == EM_SEND_SEARCH_TYPE.MULTICAST_AND_BROADCAST:
            self.multicast_search()
        else:  # Se não for multicast, assume unicast
            self.unicast_search()
        # Em vez de atualizar a GUI diretamente, emite-se um sinal para indicar que a busca terminou
        self.finished_search.emit()

    def multicast_search(self):
        # Função de callback para busca de dispositivos (multicast)
        @WINFUNCTYPE(None, C_LLONG, POINTER(DEVICE_NET_INFO_EX2), c_void_p)
        def search_device_callback(lSearchHandle, pDevNetInfo, pUserData):
            try:
                buf = cast(pDevNetInfo, POINTER(DEVICE_NET_INFO_EX2)).contents
                if buf.stuDevInfo.iIPVersion == 4:  # Processa apenas IPv4
                    device_info = [
                        buf.stuDevInfo.byInitStatus,               # 0. Status de inicialização
                        buf.stuDevInfo.iIPVersion,                 # 1. Versão IP
                        buf.stuDevInfo.szIP.decode(),              # 2. Endereço IP
                        buf.stuDevInfo.nPort,                      # 3. Porta
                        buf.stuDevInfo.szMac.decode(),             # 4. Endereço MAC
                        buf.stuDevInfo.szDeviceType.decode('gbk', errors='ignore'),  # 5. Tipo de dispositivo
                        buf.stuDevInfo.szDetailType.decode('gbk', errors='ignore'),  # 6. Detalhes
                        buf.stuDevInfo.nHttpPort,                  # 7. Porta HTTP
                    ]
                    self.found_device.emit(device_info)  # Emite o sinal com as informações do dispositivo
            except Exception as e:
                print(f"Erro no callback: {e}")

        # Configura os parâmetros de busca
        search_in = NET_IN_STARTSERACH_DEVICE()
        search_in.dwSize = sizeof(NET_IN_STARTSERACH_DEVICE)
        search_in.emSendType = self.search_type
        search_in.cbSearchDevices = search_device_callback  # Define a função de callback

        search_out = NET_OUT_STARTSERACH_DEVICE()
        search_out.dwSize = sizeof(NET_OUT_STARTSERACH_DEVICE)

        # Executa a busca
        self.search_handle = self.sdk.StartSearchDevicesEx(search_in, search_out)

        if self.search_handle:
            print("Busca por multicast iniciada...")
            time.sleep(5)  # Aguarda 5 segundos para que os dispositivos respondam
        else:
            print("Falha ao iniciar busca por multicast.")

    def unicast_search(self):
        # Função de callback para busca de dispositivos (unicast)
        @WINFUNCTYPE(None, POINTER(DEVICE_NET_INFO_EX), c_void_p)
        def search_devie_byIp_callback(pDevNetInfo, pUserData):
            try:
                buf = cast(pDevNetInfo, POINTER(DEVICE_NET_INFO_EX)).contents
                if buf.iIPVersion == 4:  # Processa apenas IPv4
                    device_info = [
                        buf.byInitStatus,                        # 0. Status de inicialização
                        buf.iIPVersion,                          # 1. Versão IP
                        buf.szIP.decode(),                       # 2. Endereço IP
                        buf.nPort,                               # 3. Porta
                        buf.szMac.decode(),                      # 4. Endereço MAC
                        buf.szDeviceType.decode('gbk', errors='ignore'),  # 5. Tipo de dispositivo
                        buf.szDetailType.decode('gbk', errors='ignore'),  # 6. Detalhes
                        buf.nHttpPort,                           # 7. Porta HTTP
                    ]
                    self.found_device.emit(device_info)  # Emite o sinal com as informações do dispositivo
            except Exception as e:
                print(f"Erro no callback unicast: {e}")

        # Configura os parâmetros de busca
        start = struct.unpack("!I", socket.inet_aton(self.start_ip))[0]
        end = struct.unpack("!I", socket.inet_aton(self.end_ip))[0]
        if (end - start > 255) or (end < start):
            QMessageBox.warning(None, '(prompt)', "Intervalo de IP inválido (o máximo são 256 endereços IP).")
            return

        searchbyIp_in = DEVICE_IP_SEARCH_INFO()
        searchbyIp_in.dwSize = sizeof(DEVICE_IP_SEARCH_INFO)
        searchbyIp_in.nIpNum = end - start + 1
        for i in range(searchbyIp_in.nIpNum):
            ip = DEVICE_IP_SEARCH_INFO_IP()
            ip.IP = socket.inet_ntoa(struct.pack("!I", start + i)).encode()
            searchbyIp_in.szIP[i] = ip

        wait_time = 3000  # Tempo de espera padrão

        # Corrigido: passa uma string vazia (bytes) para szLocalIp e wait_time no lugar correto
        result = self.sdk.SearchDevicesByIPs(searchbyIp_in, search_devie_byIp_callback, 0, b"", wait_time)

        if result:
            print("Busca por unicast concluída.")
        else:
            print("Busca por unicast falhou.")

    def stop(self):
        self.running = False
        if self.search_handle:
            self.sdk.StopSearchDevices(self.search_handle)
        self.wait()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- Estilo Global ---
    app.setStyle("Fusion")  # Boa prática
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(0, 50, 0))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Button, QColor(0, 80, 0))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.Base, QColor(0, 30, 0))
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Highlight, QColor(0, 120, 0))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    font = QFont()
    font.setBold(True)
    app.setFont(font)
    app.setPalette(palette)

    window = SearchDeviceWidget()  # Cria uma instância de SearchDeviceWidget
    window.show()
    sys.exit(app.exec_())
