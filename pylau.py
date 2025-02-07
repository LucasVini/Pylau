import os
import sys
import logging
import socket
import cv2
import subprocess
import psutil
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QHBoxLayout,
    QLabel,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
)
from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QMovie, QImage, QPixmap
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
    QAction,
    QPlainTextEdit,
    QDialog,
    QListWidget,
    QInputDialog,
)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QLabel,
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QPushButton, QInputDialog, QMessageBox
from PyQt5.QtWidgets import QPushButton, QGraphicsBlurEffect

import paramiko
import socket
import time
import argparse
import threading
import ctypes

from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QDialog, QRadioButton,
    QButtonGroup, QLabel, QDialogButtonBox, QWidget
)
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget, QInputDialog, QLineEdit


import paramiko.kex_group14
import paramiko.kex_group16
import paramiko.kex_ecdh_nist
import paramiko.kex_gss
import paramiko.packet
import paramiko.primes
import paramiko.rsakey
import paramiko.ecdsakey

# Importações NetSDK (movidas para o topo para melhor organização)
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect
from NetSDK.SDK_Enum import EM_DEV_CFG_TYPE, EM_LOGIN_SPAC_CAP_TYPE
from NetSDK.SDK_Struct import (
    LOG_SET_PRINT_INFO, NET_TIME, C_LDWORD, C_LLONG,
    NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY, NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY,
    CB_FUNCTYPE
)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests

from sftpapp import SFTPApplication  
from tempo import TimeSyncDialog

# Configuração do logger
logger = logging.getLogger("SFTPServerLogger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "[%(levelname)s %(asctime)s] %(message)s", "%d-%m-%Y %H:%M:%S"
)


class QTextEditLogger(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setFormatter(formatter)  # Usar o formatter global

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)

# Configuração do logger principal (para a janela principal)
logger = logging.getLogger("PylauLogger")  # Logger principal
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "[%(levelname)s %(asctime)s] %(message)s", "%d-%m-%Y %H:%M:%S"
)

# Configurar o logging (agora apenas para o console, o QTextEditLogger será adicionado na classe principal)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Logs no console
    ],
)

logging.info("O programa iniciou com sucesso.")


# Classe base para threads que executam scripts
class ScriptThread(QThread):
    def __init__(self, script_name):
        super().__init__()
        self.script_name = script_name

    def run(self):
        # Caminho completo para o script
        script_path = get_script_path(self.script_name)
        if script_path:
            import subprocess

            subprocess.run([sys.executable, script_path], check=True)
        else:
            print(f"Erro: Script {self.script_name} não encontrado.")


# Função para determinar o caminho dos scripts
def get_script_path(script_name):
    # Verifica se o executável está empacotado
    if getattr(sys, "frozen", False):
        # Quando empacotado pelo PyInstaller
        base_path = sys._MEIPASS
    else:
        # Durante o desenvolvimento
        base_path = os.path.dirname(__file__)

    # Retorna o caminho completo do script
    script_path = os.path.join(base_path, script_name)
    return script_path if os.path.exists(script_path) else None


def resource_path(relative_path):
    """Obter o caminho correto do arquivo, tanto no executável quanto no ambiente de desenvolvimento."""
    try:
        # Caminho temporário usado pelo PyInstaller no executável
        base_path = sys._MEIPASS
    except AttributeError:
        # Caminho local usado durante o desenvolvimento
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


### Definindo efeitos Blur


# Estruturas e funções para o efeito blur
class ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int),
    ]


class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ACCENTPOLICY)),
        ("SizeOfData", ctypes.c_size_t),
    ]


def enable_blur_effect(hwnd):
    accent = ACCENTPOLICY()
    accent.AccentState = 3  # Efeito de blur acrílico
    accent.GradientColor = 0xD0000000  # Fundo transparente

    accent_data = ctypes.pointer(accent)
    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = 19
    data.Data = accent_data
    data.SizeOfData = ctypes.sizeof(accent)

    ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))


class PortCheckerThread(QThread):
    scan_finished = pyqtSignal(str)

    def __init__(self, ip, ports_to_check):
        super().__init__()
        self.ip = ip
        self.ports_to_check = ports_to_check

    def run(self):
        result = ""
        for port in self.ports_to_check:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)  # Timeout para cada tentativa de conexão
                try:
                    sock.connect((self.ip, port))
                    result += f"✅Porta {port} - <span style='color: green;'>Aberta</span><br>"
                except (socket.timeout, ConnectionRefusedError):
                    result += (
                        f"❌Porta {port} - <span style='color: red;'>Fechada</span><br>"
                    )

        self.scan_finished.emit(result)


class PortCheckerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #cdffdc;")  ### COR DA JANELA
        self.setWindowTitle("Checar Portas")
        self.setGeometry(400, 200, 200, 80)

        # Layout do diálogo
        layout = QVBoxLayout(self)  # Usar QVBoxLayout para organizar verticalmente

        # Campo de texto para IP
        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText("Digite o endereço IP")  # Texto de sugestão
        layout.addWidget(self.ip_input)  # Adicionar o campo de texto ao layout

        # Botões OK e Cancelar
        button_layout = QHBoxLayout()  # Layout horizontal para os botões
        self.ok_button = QPushButton("OK", self)
        self.cancel_button = QPushButton("Cancelar", self)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(
            button_layout
        )  # Adicionar o layout dos botões ao layout principal

        # Conexão dos botões    
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_ip(self):
        return self.ip_input.text()


class QTextEditLogger(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setFormatter(formatter)

    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)


class FTPServerThread(QThread):
    def __init__(
        self,
        host="0.0.0.0",
        porta=2222,
        usuario="admin",
        senha="@1234567",
        diretorio="./FTP_RECEBIDO",
    ):
        super().__init__()
        self.host = host  # Usar o IP passado
        self.porta = porta
        self.usuario = usuario
        self.senha = senha
        self.diretorio = diretorio
        self.server = None

    def run(self):
        if not os.path.exists(self.diretorio):
            os.makedirs(self.diretorio)

        # Removido self.get_ipv4_address() para respeitar o IP selecionado
        authorizer = DummyAuthorizer()
        authorizer.add_user(self.usuario, self.senha, self.diretorio, perm="elradfmw")

        handler = FTPHandler
        handler.authorizer = authorizer

        self.server = FTPServer((self.host, self.porta), handler)
        logger.info(
            f""">>> <span style="color: white;">Servidor FTP <span style="color: green;">iniciado</span><br>
    ---------------------<br>
    <span style="color: white;">Endereço IP</span> ⟹ <span style="color: green;">{self.host}:<span style="color: white;">{self.porta}</span>, <br><br>
    <span style="color: white;">Utilize o seguinte login no gravador:<br><br>
    <span style="color: white;">Usuário</span>: <span style="color: green;">{self.usuario}</span>,<br>
    <span style="color: white;">Senha</span>: <span style="color: green;">{self.senha}</span>,<br>
    <span style="color: white;">pid</span> = <span style="color: white;">{os.getpid()}</span> <<<"""
        )

        self.server.serve_forever()

    def stop(self):
        if self.server:
            self.server.close_all()
            logger.info("Servidor FTP <span style='color: red;'>parado</span>")
            self.quit()


class AjudaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajuda")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Layout principal
        layout = QVBoxLayout(self)

        # Botão de fechar
        fechar_btn = QPushButton("Fechar", self)
        fechar_btn.setStyleSheet(
            "background-color: red; color: white; font-weight: bold; border: none;"
        )
        fechar_btn.clicked.connect(self.close)

        # Layout para alinhar o botão de fechar à direita
        top_layout = QHBoxLayout()
        top_layout.addWidget(fechar_btn, alignment=Qt.AlignRight)
        layout.addLayout(top_layout)

        # Texto de ajuda
        ajuda_texto = QPlainTextEdit(self)
        ajuda_texto.setReadOnly(True)
        ajuda_texto.setPlainText(
            """\
        Bem-vindo ao PyLau - Python Local Access Utillity - beta (0.9)
        
        Este aplicativo foi desenvolvido inicialmente para permitir a transferência de arquivos utilizando protocolo FTP e SFTP hospedando servidor localmente.
        
        Funcionalidades:
        - ✅Iniciar Servidor FTP 
        - ❗️Iniciar Servidor SFTP: (em testes). 
        - ✅Visualização RTSP: Acesse de forma simplificada uma visualização de stream RTSP. 
        - ✅Verificador de IP's na rede local.
        - ✅Recuperação de Padrão de Fábrica.

        Se você precisar de assistência, consulte a documentação ou entre em contato com Lucas Vinicius de Oliveira (Vinioli).
        
        Obrigado por usar PyLau!
        
        GNU GPL v3

        Os fundamentos da GPL
        Ninguém deve ser restrito pelo software que eles usam. Existem quatro liberdades que todos os usuários devem ter:

        a liberdade de usar o software para qualquer finalidade,
        a liberdade de mudar o software de acordo com suas necessidades,
        a liberdade de compartilhar o software com seus amigos e vizinhos e
        a liberdade de compartilhar as mudanças que você faz.
        """
        )
        ajuda_texto.setStyleSheet(
            "color: white; background: transparent; font-size: 14px;"
        )

        # Adicionando o texto ao layout principal
        layout.addWidget(ajuda_texto)
        self.setLayout(layout)

    def showEvent(self, event):
        # Centralizar a janela em relação à janela principal
        if self.parent():
            main_geometry = self.parent().geometry()
            x = main_geometry.x() + (main_geometry.width() - self.width()) // 2
            y = main_geometry.y() + (main_geometry.height() - self.height()) // 2
            self.move(x, y)

        hwnd = int(self.winId())  # Ativa o efeito de blur
        enable_blur_effect(hwnd)

    # Adicionar funcionalidade de arraste da janela
    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()


class RTSPDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuração RTSP")
        self.setGeometry(400, 400, 350, 250) # Aumentei um pouco a largura

        # Estilo para o diálogo
        self.setStyleSheet("""
            QDialog {
                background-color: #004000; /* Verde escuro */
                color: white;
                font-family: 'Arial', sans-serif;
            }
            QLineEdit {
                background-color: rgba(0, 0, 0, 50);
                color: white;
                border: 1px solid #008000;
                border-radius: 3px;
                padding: 5px;
                selection-background-color: #71ff78;
                selection-color: black;
            }
            QPushButton {
                background-color: #006400;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #008000;
            }
            QPushButton:pressed {
                background-color: #00A000;
            }
            QLabel {
                color: white;
            }
        """)

        self.layout = QFormLayout(self)
        self.layout.setSpacing(10) # Espaçamento entre as linhas
        self.layout.setContentsMargins(10, 10, 10, 10) # Margens

        self.usuario = QLineEdit(self)
        self.senha = QLineEdit(self)
        self.ip = QLineEdit(self)
        self.porta = QLineEdit(self)

        # Adicionando texto de sugestão (placeholder) nos campos
        self.usuario.setPlaceholderText("Padrão: admin")
        self.senha.setPlaceholderText("Padrão: @1234567")
        self.ip.setPlaceholderText("Digite o endereço IP do DVR")
        self.porta.setPlaceholderText("Digite a porta para RTSP - Padrão: 554")

        self.layout.addRow("Usuário:", self.usuario)
        self.layout.addRow("Senha:", self.senha)

        # Criar layout horizontal para o campo de IP e botão de varredura
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(self.ip)

        # Botão para varredura de IP
        self.varredura_btn = QPushButton("🔍 Varredura", self) # Adicionado ícone
        self.varredura_btn.clicked.connect(self.abrir_janela_varredura)
        self.varredura_btn.setFixedWidth(100) # Largura fixa para o botão
        ip_layout.addWidget(self.varredura_btn)

        self.layout.addRow("IP:", ip_layout)
        self.layout.addRow("Porta:", self.porta)

        # Botão para preencher os campos com valores padrão
        self.preencher_btn = QPushButton("Auto Preencher", self)
        self.preencher_btn.clicked.connect(self.preencher_campos)
        self.layout.addWidget(self.preencher_btn)

        # Adicionando o QDialogButtonBox com botões OK e Cancelar
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Estilo para os botões OK e Cancelar
        self.button_box.setStyleSheet("""
            QDialogButtonBox QPushButton {
                min-width: 80px; /* Largura mínima para os botões */
            }
        """)

        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

    def preencher_campos(self):
        """Preenche os campos com valores padrão."""
        self.usuario.setText("admin")
        self.senha.setText("@1234567")
        self.porta.setText("554")

    def abrir_janela_varredura(self):
        """Abre uma janela para varredura de dispositivos na rede."""
        self.varredura_window = VarreduraIPWindow(self)
        self.varredura_window.show()

    def get_rtsp_config(self):
        return {
            "usuario": self.usuario.text(),
            "senha": self.senha.text(),
            "ip": self.ip.text(),
            "porta": self.porta.text(),
        }


class PingThread(QThread):
    """Thread para realizar a varredura de IPs."""

    progress = pyqtSignal(str, str)  # Emite o IP e o nome do dispositivo

    def __init__(self, base_ip):
        super().__init__()
        self.base_ip = base_ip  # Recebe o base_ip como parâmetro no construtor

    def run(self):
        """Varre a rede local em todos os adaptadores de rede."""
        adaptadores_ips = self.get_adaptadores_ips()

        for base_ip in adaptadores_ips:
            for i in range(1, 255):  # Verificando IPs no intervalo de 1 a 254
                ip = base_ip + str(i)
                try:
                    resposta = subprocess.run(
                        ["ping", "-n", "1", "-w", "500", ip],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=120,
                    )
                    if "TTL=" in resposta.stdout.decode("latin1"):  # Resposta positiva
                        # Obtém o nome do dispositivo (hostname) associado ao IP
                        try:
                            hostname = socket.gethostbyaddr(ip)[0]
                        except socket.herror:
                            hostname = "Desconhecido"

                        # Emite o IP e o hostname
                        self.progress.emit(ip, hostname)
                except subprocess.TimeoutExpired:
                    # Se o tempo limite for excedido, passa para o próximo IP
                    continue

    def get_adaptadores_ips(self):
        """Obtém os IPs base (ex.: 192.168.1.) de todos os adaptadores de rede."""
        adaptadores_ips = []  # Inicializa uma lista para armazenar os IPs base

        # Obtém todas as interfaces de rede
        interfaces = psutil.net_if_addrs()

        for interface in interfaces.values():
            for addr in interface:
                if addr.family == socket.AF_INET:  # Verifica se é IPv4
                    ip_local = addr.address
                    base_ip = (
                        ".".join(ip_local.split(".")[:-1]) + "."
                    )  # Extrai o base IP
                    if base_ip not in adaptadores_ips:
                        adaptadores_ips.append(
                            base_ip
                        )  # Adiciona o base IP se ainda não estiver na lista

        return adaptadores_ips

class AdapterSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_adapter = None
        self.oldPos = None  # Para arrastar a janela
        self.init_ui()


    def init_ui(self):
        self.setWindowTitle("Seleção de Adaptador de Rede")
        self.resize(300, 200)

        # --- Configuração para Blur e Janela Sem Borda ---
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)  # Sem borda
        self.setAttribute(Qt.WA_TranslucentBackground)      # Fundo transparente
        self.setStyleSheet("background:transparent;")         # Importante para o blur

        layout = QVBoxLayout(self)

        # Label de instrução
        instruction_label = QLabel("Selecione um adaptador de rede:")
        instruction_label.setStyleSheet("color: white;")  # Texto branco
        layout.addWidget(instruction_label)

        # Grupo de botões para os adaptadores
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        # Obter adaptadores de rede e endereços IP
        self.populate_adapters(layout)

        # Botão "OK"
        self.ok_button = QPushButton("OK", self)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 100, 0, 150); /* Verde com transparência */
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """)
        self.ok_button.clicked.connect(self.confirm_selection)
        layout.addWidget(self.ok_button)



    def populate_adapters(self, layout):
        adapters = self.get_network_adapters()
        if not adapters:
            error_label = QLabel("Nenhum adaptador de rede disponível.")
            error_label.setStyleSheet("color: white;")  # Texto branco
            layout.addWidget(error_label)
            return

        for idx, (name, ip) in enumerate(adapters.items()):
            radio_button = QRadioButton(f"{name} - {ip}")
            radio_button.setStyleSheet("""
                QRadioButton {
                    color: white;
                }
                QRadioButton::indicator {
                    width: 13px;
                    height: 13px;
                }
                QRadioButton::indicator:checked {
                    background-color: rgba(0, 180, 0, 255);  /* Verde mais claro */
                    border: 2px solid rgba(0, 100, 0, 255);  /* Borda verde escura */
                }
                QRadioButton::indicator:unchecked {
                    background-color: rgba(50, 50, 50, 100);  /* Cinza transparente */
                    border: 2px solid rgba(100, 100, 100, 200);
                }

            """)
            self.button_group.addButton(radio_button, id=idx)
            layout.addWidget(radio_button)

    @staticmethod
    def get_network_adapters():
        adapters = {}
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:  # Apenas IPv4
                    adapters[interface] = addr.address
        return adapters

    def confirm_selection(self):
        selected_button = self.button_group.checkedButton()
        if selected_button:
            # Extrair apenas o endereço IP selecionado
            self.selected_adapter = selected_button.text().split(" - ")[1]
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", "Por favor, selecione um adaptador de rede.")

    def showEvent(self, event):
        """Chamado quando a janela é exibida.  Aplica o efeito de blur."""
        super().showEvent(event)
        hwnd = int(self.winId())
        enable_blur_effect(hwnd)  # Aplica o efeito de blur

    # --- Métodos para arrastar a janela (já que não tem barra de título) ---
    def mousePressEvent(self, event):
        """Captura a posição inicial do mouse no clique."""
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        """Move a janela se o botão esquerdo estiver pressionado."""
        if self.oldPos is not None and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        """Reseta a posição antiga quando o botão do mouse é solto."""
        if event.button() == Qt.LeftButton:
            self.oldPos = None

class VarreduraIPWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dispositivos na Rede")
        self.setGeometry(450, 450, 300, 300)

        self.layout = QVBoxLayout(self)

        self.label = QLabel("Dispositivos conectados na rede:")
        self.layout.addWidget(self.label)

        # Lista de IPs encontrados
        self.ip_list_widget = QListWidget(self)
        self.layout.addWidget(self.ip_list_widget)

        # Botão para realizar a varredura
        self.scan_button = QPushButton("Iniciar Varredura", self)
        self.scan_button.clicked.connect(self.iniciar_varredura)
        self.layout.addWidget(self.scan_button)

        # Adicionando um botão para fechar
        self.close_button = QPushButton("Fechar", self)
        self.close_button.clicked.connect(self.close)
        self.layout.addWidget(self.close_button)

        # Conecta o clique no item da lista com o preenchimento do campo IP
        self.ip_list_widget.itemClicked.connect(self.selecionar_ip)

    def iniciar_varredura(self):
        """Inicia a varredura de IPs na rede local."""
        self.ip_list_widget.clear()

        # Obtém o IP local e varre a rede local
        ip_local = socket.gethostbyname(socket.gethostname())
        base_ip = ".".join(ip_local.split(".")[:-1]) + "."

        # Cria e inicia a thread de varredura passando o base_ip
        self.thread = PingThread(base_ip)
        self.thread.progress.connect(self.adicionar_dispositivo_na_lista)
        self.thread.start()

    def adicionar_dispositivo_na_lista(self, ip, dispositivo):
        """Adiciona um dispositivo à lista com IP e descrição."""
        self.ip_list_widget.addItem(f"{ip} - {dispositivo}")

    def selecionar_ip(self, item):
        """Preenche o campo de IP no diálogo principal com o IP selecionado."""
        ip_selecionado = item.text().split(" - ")[0]
        self.parent().ip.setText(ip_selecionado)
        self.close()


class RTSPStream(QThread):
    frame_received = pyqtSignal(QPixmap)  # Sinal para enviar o frame para a janela

    def __init__(self, rtsp_url):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(self.rtsp_url)  # Captura o stream RTSP usando OpenCV
        if not cap.isOpened():
            print("Falha ao conectar no stream RTSP.")
            return

        while self.running:
            ret, frame = cap.read()  # Lê o próximo frame do stream
            if ret:
                # Converte o frame BGR (padrão do OpenCV) para RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Converte o frame para QImage
                height, width, channel = rgb_frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(
                    rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888
                )

                # Converte QImage para QPixmap
                pixmap = QPixmap.fromImage(q_image)

                # Emite o sinal com o QPixmap para a interface gráfica
                self.frame_received.emit(pixmap)

    def stop(self):
        self.running = False
        self.wait()  # Espera o thread finalizar


class RTSPWindow(QWidget):
    def __init__(self, rtsp_stream_thread=None):
        super().__init__()
        self.setWindowTitle("Stream RTSP")
        self.setStyleSheet("background-color: #32CD32;")  ### COR DA JANELA
        self.label = QLabel(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Armazena o thread de stream RTSP na própria janela
        self.rtsp_stream_thread = rtsp_stream_thread

        # Configura o callback para atualizar o vídeo
        if self.rtsp_stream_thread:
            self.rtsp_stream_thread.frame_received.connect(self.set_video_frame)

    def set_video_frame(self, pixmap):
        self.label.setPixmap(pixmap)
        self.adjustSize()  # Ajusta o tamanho da janela ao tamanho do vídeo

    def closeEvent(self, event):
        # Verifica se o thread de transmissão RTSP existe e está rodando
        if self.rtsp_stream_thread is not None:
            self.rtsp_stream_thread.stop()
        event.accept()  # Fecha a janela normalmente


class AlarmThread(QThread):
    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path

    def run(self):
        # Executa o outro script Python
        subprocess.run(["python", self.script_path], check=True)


class encontrarThread(QThread):
    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path

    def run(self):
        # Executa o outro script Python
        subprocess.run(["python", self.script_path], check=True)


class iaThread(QThread):
    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path

    def run(self):
        # Executa o outro script Python
        subprocess.run(["python", self.script_path], check=True)

class ResetDialog(QDialog):
    def __init__(self, parent=None):
        super(ResetDialog, self).__init__(parent)

        self.setWindowTitle("Opções de Reset")

        # Define o tema verde escuro e fonte branca
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 50, 0))  # Verde escuro
        palette.setColor(QPalette.WindowText, Qt.white)  # Branco
        self.setPalette(palette)

        layout = QVBoxLayout(self)

        label = QLabel("Selecione uma opção de reset:")
        layout.addWidget(label)

        button_factory = QPushButton("Padrão de Fábrica")
        button_factory.clicked.connect(self.padrao_fabrica)  # Conecta ao método padrao_fabrica
        layout.addWidget(button_factory)

        button_reset = QPushButton("Reiniciar") # Nome do botão alterado
        button_reset.clicked.connect(self.reset)  # Conecta ao método reset
        layout.addWidget(button_reset)

    def padrao_fabrica(self):
        # Lógica para o reset de fábrica (movida para dentro do diálogo)
        ip, ok_ip = QInputDialog.getText(self, "Padrão de Fábrica", "Digite o IP do DVR:")

        if ok_ip and ip:
            user, ok_user = QInputDialog.getText(self, "Padrão de Fábrica", "Digite o usuário do DVR:")

            if ok_user and user:
                password, ok_password = QInputDialog.getText(self, "Padrão de Fábrica", "Digite a senha do DVR:", QLineEdit.Password)

                if ok_password and password:
                    driver = None

                    try:
                        url = f"http://{user}:{password}@{ip}/cgi-bin/magicBox.cgi?action=resetSystemEx&type=0"

                        chrome_options = Options()
                        chrome_options.add_argument("--headless")
                        chrome_options.add_argument("--disable-gpu")
                        chrome_options.add_argument("--no-sandbox")

                        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
                        driver.get(url)

                        if "OK" in driver.page_source:
                            QMessageBox.information(self, "Sucesso", f"O DVR com IP {ip} foi resetado com sucesso!")
                        else:
                            QMessageBox.warning(self, "Falha", "Falha ao resetar o DVR. Verifique as credenciais e tente novamente.")

                    except Exception as e:
                        QMessageBox.critical(self, "Erro", f"Erro ao acessar o DVR: {str(e)}")
                    finally:
                        if driver:
                            driver.quit()
                else:
                    QMessageBox.information(self, "Cancelado", "A operação foi cancelada.")
            else:
                QMessageBox.information(self, "Cancelado", "A operação foi cancelada.")
        else:
            QMessageBox.information(self, "Cancelado", "A operação foi cancelada.")
        self.accept()  # Fecha o diálogo após o reset (ou cancelamento)

    def reset(self):
         # Lógica para o reset (usando o link de reboot)
        ip, ok_ip = QInputDialog.getText(self, "Reiniciar", "Digite o IP do DVR:")

        if ok_ip and ip:
            user, ok_user = QInputDialog.getText(self, "Reiniciar", "Digite o usuário do DVR:")

            if ok_user and user:
                password, ok_password = QInputDialog.getText(self, "Reiniciar", "Digite a senha do DVR:", QLineEdit.Password)

                if ok_password and password:
                    driver = None

                    try:
                        url = f"http://{user}:{password}@{ip}/cgi-bin/magicBox.cgi?action=reboot"  # URL de reboot

                        chrome_options = Options()
                        chrome_options.add_argument("--headless")
                        chrome_options.add_argument("--disable-gpu")
                        chrome_options.add_argument("--no-sandbox")

                        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
                        driver.get(url)

                        # A resposta do reboot pode variar, adaptamos para procurar um texto comum
                        if "OK" in driver.page_source or "Success" in driver.page_source or "rebooting" in driver.page_source:  # Adapte conforme a resposta do seu DVR
                            QMessageBox.information(self, "Sucesso", f"O DVR com IP {ip} foi reiniciado com sucesso!")
                        else:
                           QMessageBox.warning(self, "Falha", f"Falha ao reiniciar o DVR. Resposta: {driver.page_source}. Verifique as credenciais e tente novamente.")


                    except Exception as e:
                        QMessageBox.critical(self, "Erro", f"Erro ao acessar o DVR: {str(e)}")
                    finally:
                        if driver:
                            driver.quit()
                else:
                    QMessageBox.information(self, "Cancelado", "A operação foi cancelada.")
            else:
                QMessageBox.information(self, "Cancelado", "A operação foi cancelada.")
        else:
            QMessageBox.information(self, "Cancelado", "A operação foi cancelada.")
        self.accept()



### AQUI FICA A DEFINIÇÃO DA PARTE VISUAL DA JANELA PRINCIPAL
class Pylau(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.ftp_server_thread = None
        self.rtsp_stream_thread = None
        self.port_checker_thread = None

        # Inicialize a aplicação SFTP
        self.sftpapp = SFTPApplication([])  # Passa uma lista vazia como argv
        self.sftpapp.log_signal.connect(self.logar_sftp)
        self.sftp_running = False

        # Logger
        self.logger = logging.getLogger("PylauLogger")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(levelname)s %(asctime)s] %(message)s", "%d-%m-%Y %H:%M:%S"
        )
        text_edit_logger = QTextEditLogger(self.log_console)
        text_edit_logger.setFormatter(formatter)
        self.logger.addHandler(text_edit_logger)

        self.logger.info("Aplicativo PyLau iniciado. 💚\n Registros:")

    def logar_sftp(self, message):
        self.logger.info(f"SFTP: {message}")

    def sftp(self):
        if not self.sftp_running:
            self.sftpapp.start_server()
            self.sftpapp.show_window()  # Adicione esta linha para mostrar a janela
            self.start_sftp_button.setText("🔐 Parar Servidor SFTP")
            self.sftp_running = True
        else:
            self.sftpapp.stop_server()
            self.sftpapp.main_window.hide() # Adicione esta linha para esconder a janela
            self.start_sftp_button.setText("🔐 Iniciar Servidor SFTP")
            self.sftp_running = False

    def closeEvent(self, event):
        if self.sftp_running:
            self.sftpapp.stop_server()
            if self.sftpapp.server_thread:
                self.sftpapp.server_thread.wait()
        event.accept()

    def init_ui(self):
        self.setWindowIcon(QIcon(resource_path("icone.ico")))
        self.setWindowTitle("PyLau - Python Local Access Utility")
        self.tray_icon = QSystemTrayIcon(QIcon(resource_path("icone.ico")), self)
        self.tray_icon.show()
        self.set_green_titlebar()

        # Impedir maximização e redimensionamento
        self.setFixedSize(600, 600)

        # Configurando o fundo com um GIF animado
        self.background_label = QLabel(self)
        self.background_label.setGeometry(self.rect())
        gif_path = resource_path("ativo2.png")
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(self.size())
        self.background_label.setMovie(self.movie)
        self.movie.start()

        # Layout principal
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Console de log
        self.log_console = QTextEdit(self)
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet(
            """
            background: transparent;
            color: white;
            font-size: 11pt;
            font-family: 'Impact';
            font-weight: regular;
            selection-background-color: #71ff78;
            selection-color: black;
        """
        )
        layout.addWidget(self.log_console)

        # Adiciona a QLabel para o stream RTSP
        self.rtsp_label = QLabel(self)
        layout.addWidget(self.rtsp_label)

        # Layout para os botões em colunas
        button_layout = QHBoxLayout()

        # Altera aparência do title bar (minimizar fechar)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowTitleHint
            | Qt.CustomizeWindowHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        # Coluna da esquerda
        left_column_layout = QVBoxLayout()
        self.start_ftp_button = QPushButton("📁 Iniciar Servidor FTP", self)
        self.start_sftp_button = QPushButton("🔐 Iniciar Servidor SFTP", self)
        self.rtsp_button = QPushButton("👀 RTSP", self)
        self.rtmp_button = QPushButton("▶️ RTMP", self)
        self.check_ports_button = QPushButton("🔍 Checar Portas", self)
        self.ativar_log_button = QPushButton("📋 Ativar Log", self)
        self.reset_button = QPushButton("⚙️Padrão de Fáb.", self)
        left_column_layout.addWidget(self.start_ftp_button)
        left_column_layout.addWidget(self.start_sftp_button)
        left_column_layout.addWidget(self.rtsp_button)
        left_column_layout.addWidget(self.rtmp_button)
        left_column_layout.addWidget(self.check_ports_button)
        left_column_layout.addWidget(self.reset_button)
        left_column_layout.addWidget(self.ativar_log_button)

        # Coluna da direita
        right_column_layout = QVBoxLayout()
        self.encontrar_button = QPushButton("🎯 Encontrar", self)
        self.stop_button = QPushButton("⛔ Parar", self)
        self.ajuda_button = QPushButton("❓ Ajuda", self)
        self.alarm_button = QPushButton("📢 Alarme", self)
        self.snmp_button = QPushButton("🩺 SNMP", self)
        self.time_sync_button = QPushButton("⏱ Time Sync", self)
        
        self.ia_button = QPushButton("🤖 I.A", self)

        right_column_layout.addWidget(self.encontrar_button)
        right_column_layout.addWidget(self.stop_button)
        right_column_layout.addWidget(self.alarm_button)
        right_column_layout.addWidget(self.time_sync_button)
        right_column_layout.addWidget(self.snmp_button)
        right_column_layout.addWidget(self.ia_button)
        right_column_layout.addWidget(self.ajuda_button)

        # Adiciona transparência aos botões
        button_style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 150); 
                color: white;
                font-size: 11pt;
                font-weight: bold;
                border: 1px solid rgba(133, 196, 120, 255);
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(50, 200, 50, 200);
            }
        """
        for button in [
            self.start_ftp_button,
            self.start_sftp_button,
            self.rtsp_button,
            self.rtmp_button,
            self.check_ports_button,
            self.reset_button,
            self.stop_button,
            self.alarm_button,
            self.ia_button,
            self.ajuda_button,
            self.time_sync_button,
            self.snmp_button,
            self.encontrar_button,
            self.ativar_log_button,
        ]:
            button.setStyleSheet(button_style)

            # Adiciona o efeito de blur no botão
            blur_effect = QGraphicsBlurEffect()
            blur_effect.setBlurRadius(0)
            button.setGraphicsEffect(blur_effect)

        # Adiciona as colunas ao layout horizontal
        button_layout.addLayout(left_column_layout)
        button_layout.addLayout(right_column_layout)

        # Adiciona o layout de botões ao layout principal
        layout.addLayout(button_layout)

        # Criação de um QWidget central
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Conectar os botões às funções correspondentes
        self.start_ftp_button.clicked.connect(self.iniciar_ftp_server)
        self.start_sftp_button.clicked.connect(self.sftp)
        self.rtsp_button.clicked.connect(self.configurar_rtsp)
        self.check_ports_button.clicked.connect(self.abrir_port_checker_dialog)
        self.reset_button.clicked.connect(self.reset_dvr)
        self.encontrar_button.clicked.connect(self.encontrar)
        self.stop_button.clicked.connect(self.parar_servidores)
        self.alarm_button.clicked.connect(self.start_alarm)
        self.ia_button.clicked.connect(self.start_ia)
        self.ajuda_button.clicked.connect(self.abrir_ajuda)
        self.time_sync_button.clicked.connect(self.abrir_time_sync)

    def set_green_titlebar(self):
        hwnd = int(self.winId())
        green_color = 0x014F04  # Verde
        white_color = 0xFFFFFF  # Branco (cor do texto)

        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR = 36

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_CAPTION_COLOR,
            ctypes.byref(ctypes.c_int(green_color)),
            ctypes.sizeof(ctypes.c_int),
        )
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_TEXT_COLOR,
            ctypes.byref(ctypes.c_int(white_color)),
            ctypes.sizeof(ctypes.c_int),
        )

    def resizeEvent(self, event):
        self.background_label.setGeometry(self.rect())
        self.movie.setScaledSize(self.size())
        super().resizeEvent(event)

    def start_alarm(self):
        # Caminho relativo ao executável
        script_path = os.path.join(os.path.dirname(__file__), "alarme.py")
        self.alarm_thread = AlarmThread(script_path)
        self.alarm_thread.start()

    def abrir_time_sync(self):
        """Abre o diálogo TimeSyncDialog."""
        dialog = TimeSyncDialog(self)  #
        dialog.exec_() 

    def encontrar(self):
        script_path = os.path.join(os.path.dirname(__file__), "hunter.py")
        self.encontrar_thread = encontrarThread(script_path)
        self.encontrar_thread.start()

    def start_ia(self): # Função renomeada para refletir o uso
        # Diálogos para obter IP, usuário e senha
        ip, ok_ip = QInputDialog.getText(self, "Atualização de Firmware", "Digite o IP do dispositivo:")
        if ok_ip and ip:
            username, ok_username = QInputDialog.getText(self, "Atualização de Firmware", "Digite o usuário:")
            if ok_username and username:
                password, ok_password = QInputDialog.getText(self, "Atualização de Firmware", "Digite a senha:", QLineEdit.Password)
                if ok_password and password:
                    upgrader = FirmwareUpgrader(self)
                    upgrader.upload_firmware(ip, username, password) # Passa os dados para o upload
                else:
                     QMessageBox.information(self, "Cancelado", "A operação foi cancelada.")
            else:
                 QMessageBox.information(self, "Cancelado", "A operação foi cancelada.")
        else:
             QMessageBox.information(self, "Cancelado", "A operação foi cancelada.")


    def iniciar_ftp_server(self):
        dialog = AdapterSelectionDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_adapter:
            ip_selecionado = dialog.selected_adapter
            logger.info(f"Adaptador de rede selecionado: {ip_selecionado}")
            if not self.ftp_server_thread:
                # Usar o IP selecionado ao inicializar o servidor FTP
                self.ftp_server_thread = FTPServerThread(host=ip_selecionado)
                self.ftp_server_thread.start()

    def reset_dvr(self):
        dialog = ResetDialog(self)
        dialog.exec_()  # Abre o diálogo e aguarda a interação do usuário

    def configurar_rtsp(self):
        dialog = RTSPDialog()
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_rtsp_config()
            rtsp_url = f"rtsp://{config['usuario']}:{config['senha']}@{config['ip']}:{config['porta']}/"

            # Cria o thread de transmissão RTSP
            rtsp_stream_thread = RTSPStream(rtsp_url)

            # Cria a janela RTSP e associa o thread à janela
            self.rtsp_window = RTSPWindow(rtsp_stream_thread=rtsp_stream_thread)
            self.rtsp_window.show()

            # Inicia o thread de transmissão
            self.log_console.append("📺Abrindo transmissão")
            rtsp_stream_thread.start()

    # Método closeEvent ajustado na RTSPWindow
    def closeEvent(self, event):
        # Verifica se o thread de transmissão RTSP existe e está rodando
        if hasattr(self, "rtsp_stream_thread") and self.rtsp_stream_thread is not None:
            self.rtsp_stream_thread.stop()  # Para o thread de stream
            self.rtsp_stream_thread.wait()  # Espera o thread finalizar

        event.accept()  # Fecha a janela normalmente

    def abrir_port_checker_dialog(self):
        dialog = PortCheckerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            ip = dialog.get_ip()
            if ip:
                self.checar_portas(ip)
            else:
                QMessageBox.warning(self, "Erro", "Endereço IP não pode ser vazio!")

    # Verificador de portas abertas
    def checar_portas(self, ip):
        ports_to_check = [21, 22, 80, 443, 554, 37777]  # Lista de portas para verificar

        self.port_checker_thread = PortCheckerThread(ip, ports_to_check)
        self.port_checker_thread.scan_finished.connect(self.mostrar_resultado_portas)
        self.port_checker_thread.start()
        self.log_console.append("🔍Verificando")

    def mostrar_resultado_portas(self, resultado):
        self.log_console.append(resultado)

    def parar_servidores(self):
        if self.ftp_server_thread:
            self.ftp_server_thread.stop()
            self.ftp_server_thread = None
        if self.rtsp_stream_thread:
            self.rtsp_stream_thread.stop()
            self.rtsp_stream_thread = None

        # Botão de ajuda
        ajuda_btn = QPushButton("Ajuda", self)
        ajuda_btn.clicked.connect(self.abrir_ajuda)

        layout = QVBoxLayout()
        layout.addWidget(ajuda_btn)

        central_widget = QWidget()
        central_widget.setLayout(layout)

    def abrir_ajuda(self):
        self.ajuda_dialog = AjudaDialog()
        self.ajuda_dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Pylau()
    main_window.show()
    sys.exit(app.exec_())
