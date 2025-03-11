import sys
import os
import logging
import socket
import subprocess
import ctypes
import time  # Usado em FTPServerThread e potencialmente em outros lugares

# Módulos externos
import cv2  # Usado para RTSP
import psutil  # Usado para obter informações de rede
import paramiko  # Para SFTP (e possivelmente SSH, se você usar)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests  # Para requisições HTTP (reset de fábrica)

# PyQt5 - Agrupando imports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit,
    QHBoxLayout, QLabel, QDialog, QFormLayout, QLineEdit,
    QDialogButtonBox, QSystemTrayIcon, QMenu, QAction,
    QPlainTextEdit, QListWidget, QInputDialog, QMessageBox,
    QMainWindow, QRadioButton, QButtonGroup, QFileDialog,
    QGraphicsBlurEffect
)
from PyQt5.QtCore import (
    QThread, QTimer, Qt, pyqtSignal, QPoint, QRect
)
from PyQt5.QtGui import (
    QMovie, QImage, QPixmap, QIcon, QPalette, QColor, QFont
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QOpenGLWidget, QWidget, QLabel,
    QPushButton, QVBoxLayout, QDialog
)
from PyQt5.QtGui import QOpenGLShader, QOpenGLShaderProgram, QPixmap
from PyQt5.QtCore import QTimer, Qt
from OpenGL.GL import *
import math

# pyftpdlib - Agrupando imports
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

# paramiko - Agrupando (se você realmente usar todos)
import paramiko.kex_group14
import paramiko.kex_group16
import paramiko.kex_ecdh_nist
import paramiko.kex_gss
import paramiko.packet
import paramiko.primes
import paramiko.rsakey
import paramiko.ecdsakey

# NetSDK - Organizando (se você usar todos)
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect
from NetSDK.SDK_Enum import EM_DEV_CFG_TYPE, EM_LOGIN_SPAC_CAP_TYPE
from NetSDK.SDK_Struct import (
    LOG_SET_PRINT_INFO, NET_TIME, C_LDWORD, C_LLONG,
    NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY, NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY,
    CB_FUNCTYPE
)

# módulos/classes
from sftpapp import SFTPApplication
from tempo import TimeSyncDialog
from hunter import SearchDeviceWidget
from alarme import StartListenWidget

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QPointF, QVariantAnimation, QEasingCurve, Qt
from PyQt5.QtGui import QPainter, QRadialGradient, QColor, QPen


class RadialGlowButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMouseTracking(True)
        self.hovered = False
        self._mouse_pos = QPointF()  # Posição do mouse
        # Ponto distante (fora da janela).  Use um valor grande.
        self.distant_point = QPointF(10000, 10000)

        # Animação para a intensidade do brilho
        self.intensity_animation = QVariantAnimation(self)
        self.intensity_animation.setDuration(200)
        self.intensity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.intensity_animation.valueChanged.connect(self.update)

        self.base_color = QColor(0, 0, 0, 150)
        self.glow_color = QColor(50, 200, 50, 200)
        self.border_color = QColor(133, 196, 120, 255)
        self.text_color = Qt.white

        self.max_glow_radius = 0.8
        self.min_glow_radius = 0.0
        self.current_glow_radius = self.min_glow_radius
        self.glow_intensity = 0.7
        self.current_intensity = 0.0  # Começa com intensidade 0

    def enterEvent(self, event):
        self.hovered = True
        self.intensity_animation.setStartValue(self.current_intensity)
        self.intensity_animation.setEndValue(self.glow_intensity)
        self.intensity_animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.intensity_animation.setStartValue(self.current_intensity)
        self.intensity_animation.setEndValue(0.0)  # Volta para intensidade 0
        self.intensity_animation.start()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        if self.hovered:
            self._mouse_pos = event.localPos()
            self.update()
        super().mouseMoveEvent(event)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)

        # --- Gradiente Radial ---
        # Usa o ponto distante se o mouse não estiver sobre o botão.
        gradient_center = self.distant_point if not self.hovered else self._mouse_pos
        gradient_radius = min(rect.width(), rect.height()) / 0.2

        gradient = QRadialGradient(gradient_center, gradient_radius)


        # Calcula o raio baseado na intensidade
        if self.intensity_animation.state() == QVariantAnimation.Running:
            self.current_intensity = self.intensity_animation.currentValue()
        current_radius = self.min_glow_radius + (self.max_glow_radius - self.min_glow_radius) * self.current_intensity

        # Cores do gradiente
        gradient.setColorAt(0, QColor(self.glow_color.red(), self.glow_color.green(), self.glow_color.blue(), int(self.glow_color.alpha()* self.current_intensity))) #Usa current_intensity

        gradient.setColorAt(current_radius, QColor(self.glow_color.red(), self.glow_color.green(), self.glow_color.blue(), int(self.glow_color.alpha()* self.current_intensity)))
        gradient.setColorAt(1, self.base_color)

        painter.setBrush(gradient)
        painter.setPen(QPen(self.border_color, 1))
        painter.drawRoundedRect(rect, 10, 10)

        # Desenha o texto
        painter.setPen(self.text_color)
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignCenter, self.text())

        
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
        super().__init__(parent)  # Importante: passe 'parent' para o construtor da classe base
        self.oldPos = None
        self.init_ui()


    def init_ui(self):
        self.setWindowTitle("Checar Portas")
        self.setGeometry(400, 200, 300, 150)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        layout = QVBoxLayout(self)
        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText("Digite o endereço IP")
        self.ip_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 30);
                color: white;
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 4px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.ip_input)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK", self)
        self.cancel_button = QPushButton("Cancelar", self)
        button_style = """
            QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """
        self.ok_button.setStyleSheet(button_style)
        self.cancel_button.setStyleSheet(button_style)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_ip(self):
        return self.ip_input.text()

    def showEvent(self, event):
        """Aplica o blur e centraliza a janela."""
        super().showEvent(event)
        hwnd = int(self.winId())
        enable_blur_effect(hwnd)
        self.center()  # Chama a função center() para centralizar

    def center(self):
        """Centraliza o diálogo em relação à janela pai (se houver)."""
        if self.parentWidget():  # Verifica se existe uma janela pai
            parent_rect = self.parentWidget().geometry()  # Geometria da janela pai
            dialog_rect = self.geometry()  # Geometria do diálogo

            # Calcula a posição central
            center_x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            center_y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2

            self.move(center_x, center_y)  # Move o diálogo para o centro
        else:
            # Se não houver pai, centraliza na tela
            screen = QApplication.primaryScreen().availableGeometry()
            self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None

class CustomFTPHandler(FTPHandler):
    def __init__(self, *args, main_window=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window  # Referência à janela principal

    def on_connect(self):
        """Chamado quando um cliente se conecta."""
        ip = self.remote_ip
        logger.info(f"✅Dispositivo <span style='color: green;'>conectado</span>: {ip}")
        #logger.info("Servidor FTP <span style='color: red;'>parado</span>")
        # Posta o evento para a janela principal
        if self.main_window:
            QApplication.postEvent(self.main_window, ConnectionEvent(ip))

    def on_disconnect(self):
        """Chamado quando um cliente se desconecta."""
        logger.info(f"⛔️Dispositivo <span style='color: red;'>desconectado</span>: {self.remote_ip}")

    def on_file_received(self, file):
        """Chamado quando um arquivo é recebido."""
        logger.info(f"✅📁Arquivo recebido: {file}")
        if self.main_window:
            # Posta um evento para a thread principal com o nome do arquivo
            QApplication.postEvent(self.main_window, FileReceivedEvent(file))

class FTPServerThread(QThread):
    def __init__(
        self,
        host="0.0.0.0",
        porta=2222,
        usuario="admin",
        senha="@1234567",
        diretorio="./FTP_RECEBIDO",
        parent=None,  # Adicione um argumento parent
    ):
        super().__init__(parent)  # Passe o parent para o construtor da QThread
        self.host = host
        self.porta = porta
        self.usuario = usuario
        self.senha = senha
        self.diretorio = diretorio
        self.server = None


    def run(self):
        if not os.path.exists(self.diretorio):
            os.makedirs(self.diretorio)

        authorizer = DummyAuthorizer()
        authorizer.add_user(self.usuario, self.senha, self.diretorio, perm="elradfmw")

        handler = CustomFTPHandler  # Usa o handler customizado
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
            self.wait()  # Espera a thread terminar


    def event(self, event):
        """Lida com eventos customizados (como o de conexão)."""
        if event.type() == 1000:  # Verifica o tipo do evento
            dialog = AcrylicDialog(event.ip_address, parent=self.parent())  # Passa o parent
            dialog.exec_()  # Mostra o diálogo
            return True  # Indica que o evento foi tratado

        return super().event(event)  # Chama o manipulador de eventos padrão

class AjudaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.oldPos = None  # Para arrastar a janela
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Ajuda")
        self.setGeometry(100, 100, 450, 600)  # Tamanho adequado

        # --- Configuração para Blur e Janela Sem Borda ---
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;") # Garante a transparencia

        layout = QVBoxLayout(self)

        # --- Botão "OK" (em vez de "Fechar") ---
        ok_button = QPushButton("OK", self)
        button_style = """
            QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """
        ok_button.setStyleSheet(button_style)
        ok_button.clicked.connect(self.accept)  # Conecta a self.accept()

        # --- Layout para o botão OK (centralizado) ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Adiciona espaço flexível à esquerda
        button_layout.addWidget(ok_button)
        button_layout.addStretch()  # Adiciona espaço flexível à direita
        layout.addLayout(button_layout)  # Adiciona o layout do botão ao layout principal


        # Texto de ajuda
        ajuda_texto = QPlainTextEdit(self)
        ajuda_texto.setReadOnly(True)
        ajuda_texto.setPlainText(
            """
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
            "color: white; background: transparent; font-size: 14px; border: none;"  # Sem borda
        )
        layout.addWidget(ajuda_texto) # Adicionando antes do botão

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        enable_blur_effect(hwnd)
        self.center()  # Centraliza após aplicar o blur

    def center(self):
        if self.parentWidget():
            parent_rect = self.parentWidget().geometry()
            dialog_rect = self.geometry()
            center_x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            center_y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            self.move(center_x, center_y)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None

         
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
        self.oldPos = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Seleção de Adaptador de Rede")
        self.resize(300, 200)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        layout = QVBoxLayout(self)

        instruction_label = QLabel("Selecione um adaptador de rede:")
        instruction_label.setStyleSheet("color: white;")
        layout.addWidget(instruction_label)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.populate_adapters(layout)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover { background-color: rgba(0, 150, 0, 200); }
        """)
        self.ok_button.clicked.connect(self.confirm_selection)
        layout.addWidget(self.ok_button)

    def populate_adapters(self, layout):
        adapters = self.get_network_adapters()
        if not adapters:
            error_label = QLabel("Nenhum adaptador encontrado.")
            error_label.setStyleSheet("color: white;")
            layout.addWidget(error_label)
            return

        for idx, (name, ip) in enumerate(adapters.items()):
            rb = QRadioButton(f"{name} - {ip}")
            rb.setStyleSheet("""
                QRadioButton { color: white; }
                QRadioButton::indicator { width: 13px; height: 13px; }
                QRadioButton::indicator:checked {
                    background-color: rgba(0, 180, 0, 255);
                    border: 2px solid rgba(0, 100, 0, 255);
                }
                QRadioButton::indicator:unchecked {
                    background-color: rgba(50, 50, 50, 100);
                    border: 2px solid rgba(100, 100, 100, 200);
                }
            """)
            self.button_group.addButton(rb, id=idx)
            layout.addWidget(rb)

    @staticmethod
    def get_network_adapters():
        adapters = {}
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    adapters[interface] = addr.address
        return adapters

    def confirm_selection(self):
        selected_button = self.button_group.checkedButton()
        if selected_button:
            self.selected_adapter = selected_button.text().split(" - ")[1]
            self.accept()
        else:
            # --- Usar show_message para exibir o QMessageBox ---
            self.show_message("Erro", "Por favor, selecione um adaptador de rede.", QMessageBox.Warning)

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        enable_blur_effect(hwnd)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None

    def show_message(self, title, message, icon):
        """Função auxiliar para exibir QMessageBox personalizados."""
        msg_box = QMessageBox(self)  # 'self' como pai
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: rgba(0, 0, 0, 230); /* Preto translúcido */
                color: white; /* Texto branco */
            }
            QLabel{
                color: white; /* Garante texto branco na label */
            }
             QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
                min-width: 60px; /* Largura mínima para os botões */
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }

        """)
        msg_box.exec_()

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

### Classes do RTMP
class RTSPDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.parent_window = parent
        self.oldPos = None
        self.initial_data = initial_data or {}
        self.init_ui()
        self.load_initial_data()

    def load_initial_data(self):
        # Preenche os campos com dados iniciais se existirem
        self.usuario.setText(self.initial_data.get("usuario", ""))
        self.senha.setText(self.initial_data.get("senha", ""))
        self.ip.setText(self.initial_data.get("ip", ""))
        self.porta.setText(self.initial_data.get("porta", ""))
        self.canal.setText(self.initial_data.get("canal", ""))

    def init_ui(self):
        self.setWindowTitle("Configuração RTSP")
        self.setGeometry(400, 400, 350, 280)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        self.layout = QFormLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.usuario = QLineEdit(self)
        self.senha = QLineEdit(self)
        self.senha.setEchoMode(QLineEdit.Password)  # Esconder senha por padrão
        self.ip = QLineEdit(self)
        self.porta = QLineEdit(self)
        self.canal = QLineEdit(self)

        self.usuario.setPlaceholderText("Padrão: admin")
        self.senha.setPlaceholderText("Padrão: @1234567")
        self.ip.setPlaceholderText("Digite o endereço IP do DVR")
        self.porta.setPlaceholderText("Digite a porta para RTSP - Padrão: 554")
        self.canal.setPlaceholderText("Número do Canal (Padrão: 1)")

        line_edit_style = """
            QLineEdit {
                background-color: rgba(255, 255, 255, 30);
                color: white;
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
        """
        self.usuario.setStyleSheet(line_edit_style)
        self.senha.setStyleSheet(line_edit_style)
        self.ip.setStyleSheet(line_edit_style)
        self.porta.setStyleSheet(line_edit_style)
        self.canal.setStyleSheet(line_edit_style)

        self.layout.addRow("Usuário:", self.usuario)
        self.layout.addRow("Senha:", self.senha)

        ip_layout = QHBoxLayout()
        ip_layout.addWidget(self.ip)
        self.varredura_btn = QPushButton("🔍 Varredura", self)

        button_style = """
            QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """
        self.varredura_btn.setStyleSheet(button_style)
        self.varredura_btn.clicked.connect(self.abrir_janela_varredura)
        self.varredura_btn.setFixedWidth(100)
        ip_layout.addWidget(self.varredura_btn)
        self.layout.addRow("IP:", ip_layout)
        self.layout.addRow("Porta:", self.porta)
        self.layout.addRow("Canal:", self.canal)

        self.preencher_btn = QPushButton("Auto Preencher", self)
        self.preencher_btn.setStyleSheet(button_style)
        self.preencher_btn.clicked.connect(self.preencher_campos)
        self.layout.addWidget(self.preencher_btn)

        self.toggle_senha_btn = QPushButton("👁 Mostrar Senha", self)
        self.toggle_senha_btn.setStyleSheet(button_style)
        self.toggle_senha_btn.clicked.connect(self.toggle_senha)
        self.layout.addWidget(self.toggle_senha_btn)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.setStyleSheet("""
            QDialogButtonBox QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
                min-width: 80px;
                font-weight: bold;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """)
        self.layout.addWidget(self.button_box)

    def preencher_campos(self):
        self.usuario.setText("admin")
        self.senha.setText("@1234567")
        self.porta.setText("554")
        self.canal.setText("1")

    def abrir_janela_varredura(self):
        self.varredura_window = VarreduraIPWindow(self)
        self.varredura_window.show()

    def toggle_senha(self):
        if self.senha.echoMode() == QLineEdit.Password:
            self.senha.setEchoMode(QLineEdit.Normal)
            self.toggle_senha_btn.setText("👁 Ocultar Senha")
        else:
            self.senha.setEchoMode(QLineEdit.Password)
            self.toggle_senha_btn.setText("👁 Mostrar Senha")

    def get_rtsp_config(self):
        return {
            "usuario": self.usuario.text(),
            "senha": self.senha.text(),
            "ip": self.ip.text(),
            "porta": self.porta.text(),
            "canal": self.canal.text() or "1",
        }

    def accept(self):
        # Coleta apenas os 3 campos essenciais
        credentials = (
            self.usuario.text() or "admin",
            self.senha.text() or "@1234567",
            self.ip.text()  # Apenas username, password e IP
        )
        
        # Monta a URL com porta e canal separados
        porta = self.porta.text() or "554"
        canal = self.canal.text() or "1"
        rtsp_url = f"rtsp://{credentials[0]}:{credentials[1]}@{credentials[2]}:{porta}/cam/realmonitor?channel={canal}&subtype=0"
        
        rtsp_stream_thread = RTSPStream(rtsp_url)
        self.rtsp_window = RTSPWindow(rtsp_stream_thread, credentials)  # Passando as credenciais
        self.rtsp_window.setAttribute(Qt.WA_DeleteOnClose, False)  # Impede que feche o app principal
        self.rtsp_window.show()
        super().accept()

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        enable_blur_effect(hwnd)
        self.center()

    def center(self):
        if self.parent_window:
            parent_rect = self.parent_window.geometry()
            dialog_rect = self.geometry()
            center_x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            center_y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            self.move(center_x, center_y)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)


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

# Código do shader (ShaderWidget) para o Countdown do RTSP
# -------------------------------------------------
vertex_shader_source = """
#version 330 core
layout (location = 0) in vec2 position;
out vec2 fragCoord;
void main()
{
    fragCoord = position;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

fragment_shader_source = """
#version 330 core
uniform vec2 iResolution;
uniform float iTime;
out vec4 fragColor;

float random(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

float movingNoise(vec2 uv) {
    float noise = 0.0;
    float scale = 0.02;
    float timeOffset = sin(iTime * 0.5) * 0.02;
    for (int i = -1; i <= 1; i++) {
        for (int j = -1; j <= 1; j++) {
            noise += random(uv + vec2(i, j) * scale + timeOffset);
        }
    }
    return noise / 9.0;
}

float lightBeam(vec2 coord, vec2 source, float intensity, float spread) {
    float dist = length(coord - source);
    float attenuation = exp(-dist * spread) * intensity;
    float flicker = 0.5 + 0.5 * sin(iTime * 2.0);
    return attenuation * flicker;
}

void main()
{
    vec2 uv = gl_FragCoord.xy / iResolution.xy;
    vec3 backgroundColor = vec3(0.02, 0.04, 0.02);
    vec2 lightSource = vec2(iResolution.x * 0.5, iResolution.y * 1.1);
    float intensity = 1.0;
    float spread = 0.004;
    float beam = lightBeam(gl_FragCoord.xy, lightSource, intensity, spread);
    vec3 lightEffect = vec3(0.1, 0.8, 0.3) * beam;
    float noise = movingNoise(uv);
    lightEffect *= mix(0.9, 1.1, noise);
    fragColor = vec4(backgroundColor + lightEffect, 1.0);
}
"""

class ShaderWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_time = time.time()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # Aproximadamente 60 FPS

    def initializeGL(self):
        self.program = QOpenGLShaderProgram()
        vertex_shader = QOpenGLShader(QOpenGLShader.Vertex)
        vertex_shader.compileSourceCode(vertex_shader_source)
        self.program.addShader(vertex_shader)
        fragment_shader = QOpenGLShader(QOpenGLShader.Fragment)
        fragment_shader.compileSourceCode(fragment_shader_source)
        self.program.addShader(fragment_shader)
        self.program.link()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        self.program.bind()
        iResolution = self.program.uniformLocation("iResolution")
        iTime = self.program.uniformLocation("iTime")
        self.program.setUniformValue(iResolution, self.width(), self.height())
        self.program.setUniformValue(iTime, float(time.time() - self.start_time))
        glBegin(GL_TRIANGLES)
        glVertex2f(-1, -1)
        glVertex2f(3, -1)
        glVertex2f(-1, 3)
        glEnd()
        self.program.release()

class RTSPWindow(QWidget):
    def __init__(self, rtsp_stream_thread=None, credentials=None, parent_dialog=None):
        super().__init__()
        self.rtsp_stream_thread = rtsp_stream_thread
        self.credentials = credentials
        self.parent_dialog = parent_dialog  # Guarda referência ao diálogo pai
        self.video_received = False  # Flag para indicar se o vídeo já foi recebido
        self.driver = None 
        self.init_ui()
        self.start_countdown()

    def init_ui(self):
        self.setWindowTitle("RTSP Stream")
        self.set_green_titlebar()
        self.setGeometry(200, 200, 640, 480)

        # Label que exibirá os frames do stream
        self.label = QLabel("Conectando ao stream RTSP...", self)
        self.label.setAlignment(Qt.AlignCenter)

        # Botões de funcionalidades
        self.btn_activate = QPushButton("Ativar Máscara", self)
        self.btn_activate.setStyleSheet("background-color: green; color: white; font-size: 14px;")
        self.btn_activate.clicked.connect(self.activate_privacy_masking)

        self.btn_adjust_video = QPushButton("Ajustar Vídeo", self)
        self.btn_adjust_video.setStyleSheet("background-color: blue; color: white; font-size: 14px;")
        self.btn_adjust_video.clicked.connect(self.adjust_video_settings)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.btn_activate)
        layout.addWidget(self.btn_adjust_video)
        self.setLayout(layout)

        # Criação do overlay de carregamento
        self.loading_overlay = QWidget(self)
        self.loading_overlay.setGeometry(self.rect())
        # Faz com que o overlay não capture eventos de mouse (para não atrapalhar os botões quando estiver visível)
        self.loading_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # Adiciona o ShaderWidget como fundo do overlay
        self.shader_widget = ShaderWidget(self.loading_overlay)
        self.shader_widget.setGeometry(self.loading_overlay.rect())

        # Label do contador (centralizado, fonte branca e grande)
        self.countdown_label = QLabel("15", self.loading_overlay)
        self.countdown_label.setStyleSheet("color: white; font-size: 72pt; background: transparent;")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setGeometry(self.loading_overlay.rect())
        self.countdown_label.raise_()  # Garante que o contador fique visível sobre o shader

        # Se houver thread de stream RTSP, conecta o sinal de frame recebido
        if self.rtsp_stream_thread:
            self.rtsp_stream_thread.frame_received.connect(self.update_frame)
            self.rtsp_stream_thread.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Atualiza o tamanho do overlay e de seus filhos em caso de redimensionamento
        self.loading_overlay.setGeometry(self.rect())
        self.shader_widget.setGeometry(self.loading_overlay.rect())
        self.countdown_label.setGeometry(self.loading_overlay.rect())

    def start_countdown(self):
        self.countdown_time = 15  # Tempo inicial de 15 segundos
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # Atualiza a cada 1 segundo

    def update_countdown(self):
        if self.video_received:
            self.countdown_timer.stop()
            self.loading_overlay.hide()
            return
        self.countdown_time -= 1
        if self.countdown_time <= 0:
            self.countdown_timer.stop()
            self.close()  # Fecha a janela se não houver transmissão
        else:
            self.countdown_label.setText(str(self.countdown_time))

    def update_frame(self, q_image):
        """Atualiza a label com o frame do RTSP e esconde o overlay de carregamento."""
        if not self.video_received:
            self.video_received = True
            self.loading_overlay.hide()
        if isinstance(q_image, QPixmap):
            self.label.setPixmap(q_image)
        else:
            pixmap = QPixmap.fromImage(q_image)
            self.label.setPixmap(pixmap)
        
    def activate_privacy_masking(self):
        """Ativa a máscara de privacidade usando Selenium"""
        if self.credentials is None:
            print("Credenciais não foram configuradas!")
            return
            
        # Extrai as credenciais do diálogo
        usuario, senha, ip = self.credentials
        self._execute_api_request(
            endpoint="cgi-bin/PrivacyMasking.cgi?action=setPrivacyMasking"
                     "&channel=1&PrivacyMasking.Index=0&PrivacyMasking.Name=Privacidade%201"
                     "&PrivacyMasking.Enable=1&PrivacyMasking.ShapeType=Rect"
                     "&PrivacyMasking.Rect[0]=0&PrivacyMasking.Rect[1]=0"
                     "&PrivacyMasking.Rect[2]=5000&PrivacyMasking.Rect[3]=5000&PrivacyMasking.Mosaic=16",
            username=usuario,
            password=senha,
            dvr_ip=ip,
            message="Privacidade ativada com sucesso!"
        )

    def adjust_video_settings(self):
        """Ajusta brilho, saturação e contraste, depois restaura os valores originais."""
        if self.credentials is None:
            print("Credenciais não foram configuradas!")
            return

        username, password, dvr_ip = self.credentials

        if not self.credentials:
            self.reopen_dialog()  # Reabre o diálogo se não houver credenciais
        return
        
        # Primeira chamada
        self._execute_api_request(
            endpoint="cgi-bin/configManager.cgi?action=setConfig"
                     "&VideoColor[0][0].Brightness=50"
                     "&VideoColor[0][0].Saturation=0"
                     "&VideoColor[0][0].Contrast=100",
            username=usuario,
            password=senha,
            dvr_ip=ip,
            message="Configurações de vídeo ajustadas!"
        )

        # Aguarda 5 segundos antes de restaurar
        time.sleep(5)

        # Segunda chamada
        self._execute_api_request(
            endpoint="cgi-bin/configManager.cgi?action=setConfig"
                     "&VideoColor[0][0].Brightness=50"
                     "&VideoColor[0][0].Saturation=50"
                     "&VideoColor[0][0].Contrast=50",
            username=username,
            password=password,
            dvr_ip=dvr_ip,
            message="Configurações de vídeo restauradas!"
        )

    def _execute_api_request(self, endpoint, username, password, dvr_ip, message):
        """Versão corrigida com parâmetros corretos"""
        if not all([username, password, dvr_ip]):
            print("Credenciais inválidas ou incompletas!")
            return

        try:
            if not self.driver:
                options = Options()
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_experimental_option("excludeSwitches", ["enable-logging"])
                
                service = Service(
                    ChromeDriverManager().install(),
                    service_log_path=os.devnull
                )
                
                self.driver = webdriver.Chrome(
                    service=service,
                    options=options
                )

            url = f"http://{username}:{password}@{dvr_ip}/{endpoint}"
            self.driver.get(url)
            print(message)

        except Exception as e:
            print(f"Erro na API: {str(e)}")
            self._reset_driver()

    def _reset_driver(self):
        """Reinicialização segura do driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        self.driver = None

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

    def closeEvent(self, event):
        """Fechamento seguro"""
        if self.driver:
            self._reset_driver()
        if self.rtsp_stream_thread:
            self.rtsp_stream_thread.stop()
        event.accept()
        self.deleteLater()  # Garante a destruição da janela

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
        super().__init__(parent)
        self.oldPos = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Opções de Reset")
        self.setGeometry(100, 100, 350, 200)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        layout = QVBoxLayout(self)

        label = QLabel("Selecione uma opção de reset:")
        label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(label)

        button_factory = QPushButton("Padrão de Fábrica", self)
        button_reset = QPushButton("Reiniciar", self)

        button_style = """
            QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """
        button_factory.setStyleSheet(button_style)
        button_reset.setStyleSheet(button_style)

        button_factory.clicked.connect(self.padrao_fabrica)
        button_reset.clicked.connect(self.reset)
        layout.addWidget(button_factory)
        layout.addWidget(button_reset)

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        enable_blur_effect(hwnd)
        self.center()

    def center(self):
        if self.parentWidget():
            parent_rect = self.parentWidget().geometry()
            dialog_rect = self.geometry()
            center_x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            center_y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            self.move(center_x, center_y)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None

    def padrao_fabrica(self):
        ip, ok_ip = self.get_input("Padrão de Fábrica", "Digite o IP do DVR:")
        if ok_ip and ip:
            user, ok_user = self.get_input("Padrão de Fábrica", "Digite o usuário do DVR:")
            if ok_user and user:
                password, ok_password = self.get_input("Padrão de Fábrica", "Digite a senha do DVR:", password=True)
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
                            self.show_message("Sucesso", f"O DVR com IP {ip} foi resetado com sucesso!", QMessageBox.Information)
                        else:
                            self.show_message("Falha", "Falha ao resetar o DVR.", QMessageBox.Warning)
                    except Exception as e:
                         self.show_message("Erro", str(e), QMessageBox.Critical)
                    finally:
                        if driver:
                            driver.quit()

    def reset(self):
        ip, ok_ip = self.get_input("Reiniciar", "Digite o IP do DVR:")
        if ok_ip and ip:
            user, ok_user = self.get_input("Reiniciar", "Digite o usuário do DVR:")
            if ok_user and user:
                password, ok_password = self.get_input("Reiniciar", "Digite a senha do DVR:", password=True)
                if ok_password and password:
                    driver = None
                    try:
                        url = f"http://{user}:{password}@{ip}/cgi-bin/magicBox.cgi?action=reboot"
                        chrome_options = Options()
                        chrome_options.add_argument("--headless")
                        chrome_options.add_argument("--disable-gpu")
                        chrome_options.add_argument("--no-sandbox")
                        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
                        driver.get(url)

                        if "OK" in driver.page_source or "Success" in driver.page_source or "rebooting" in driver.page_source:
                            self.show_message("Sucesso", f"O DVR com IP {ip} foi reiniciado com sucesso!", QMessageBox.Information)
                        else:
                            self.show_message("Falha", f"Falha ao reiniciar o DVR. Resposta: {driver.page_source}", QMessageBox.Warning)
                    except Exception as e:
                        self.show_message("Erro", str(e), QMessageBox.Critical)
                    finally:
                        if driver:
                            driver.quit()

    def get_input(self, title, prompt, password=False):
        dialog = QInputDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLabelText(prompt)
        dialog.setInputMode(QInputDialog.TextInput)
        if password:
            dialog.setTextEchoMode(QLineEdit.Password)

        dialog.setStyleSheet("""
            QInputDialog {
                background-color: rgba(0, 50, 0, 200);
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 30);
                color: white;
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """)

        ok = dialog.exec_()
        text = dialog.textValue()
        return text, ok

    def show_message(self, title, message, icon):
        """Função auxiliar para exibir QMessageBox personalizados."""
        msg_box = QMessageBox(self)  # 'self' como pai
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        # --- Aplica estilo MANUALMENTE ao QMessageBox ---
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: rgba(0, 0, 0, 230); /* Preto translúcido */
                color: white; /* Texto branco */
            }
            QLabel{
                color: white; /* Garante texto branco na label */
            }
             QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
                min-width: 60px; /* Largura mínima para os botões */
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }

        """)
        msg_box.exec_()# --- (dentro de uma janela principal, se necessário) ---


class AtivarLogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.oldPos = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Ativar Log")
        self.setGeometry(100, 100, 400, 250)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self.message_label = QLabel("""
        Primeiramente, plugue o pendrive no gravador. O pendrive deve estar vázio.
        O gravador irá reiniciar após preencher os campos e clicar em OK. 
        Depois, verifique se foi criado no pendrive arquivos como: 
        printf_001.txt, kmsg_xxxx.txt e UsbDebug.txt

        Preencha os campos para ativar o log:""", self)
        self.message_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        layout.addRow(self.message_label)

        self.usuario_input = QLineEdit(self)
        self.usuario_input.setPlaceholderText("Usuário")
        layout.addRow("Usuário:", self.usuario_input)

        self.senha_input = QLineEdit(self)
        self.senha_input.setPlaceholderText("Senha")
        self.senha_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Senha:", self.senha_input)

        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText("Endereço IP")
        layout.addRow("IP:", self.ip_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

        self.set_styles()  # Aplica os estilos

    def set_styles(self):
        line_edit_style = """
            QLineEdit {
                background-color: rgba(255, 255, 255, 30);
                color: white;
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
        """
        self.usuario_input.setStyleSheet(line_edit_style)
        self.senha_input.setStyleSheet(line_edit_style)
        self.ip_input.setStyleSheet(line_edit_style)

        self.button_box.setStyleSheet("""
            QDialogButtonBox QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
                min-width: 70px;
                font-weight: bold;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """)

    def showEvent(self, event):
        super().showEvent(event)
        enable_blur_effect(int(self.winId()))
        self.center()

    def center(self):
        if self.parentWidget():
            parent_rect = self.parentWidget().geometry()
            dialog_rect = self.geometry()
            center_x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            center_y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            self.move(center_x, center_y)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None

    def show_message(self, title, message, icon):
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: rgba(0, 0, 0, 230);
                color: white;
            }
            QLabel{
                color: white;
                font-weight: bold;
            }
             QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
                min-width: 60px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """)
        msg_box.exec_()


    def accept(self):
        """Sobrescreve o método accept() para usar o Selenium."""
        usuario = self.usuario_input.text()
        senha = self.senha_input.text()
        ip = self.ip_input.text()

        if not all([usuario, senha, ip]):
            self.show_message("Erro", "Preencha todos os campos.", QMessageBox.Warning)
            return

        # --- URL para ativar o log ---
        url_config = f"http://{usuario}:{senha}@{ip}/cgi-bin/configManager.cgi?action=setConfig&InterimRDPrint.AlwaysEnable=true"
        # --- URL para reiniciar (reboot) ---
        url_reboot = f"http://{usuario}:{senha}@{ip}/cgi-bin/magicBox.cgi?action=reboot"

        driver = None  # Inicializa o driver
        try:
            # --- Configuração do Selenium ---
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            # --- Primeiro Acesso: Ativar Log ---
            driver.get(url_config)

            if "OK" in driver.page_source:
                self.show_message("Sucesso", "Log ativado com sucesso! Reiniciando...", QMessageBox.Information)

                # --- Segundo Acesso: Reiniciar ---
                driver.get(url_reboot)  # Acessa a URL de reboot *depois* de ativar o log

                #Verifica resposta do reboot (adapte conforme necessário)
                if "OK" in driver.page_source or "rebooting" in driver.page_source.lower():  # Verifica se a resposta contem OK ou rebooting
                  self.show_message("Sucesso", "Dispositivo reiniciando...", QMessageBox.Information)
                  super().accept() #Fecha após o sucesso
                else:
                   self.show_message("Aviso", "Dispositivo pode não ter reiniciado corretamente.", QMessageBox.Warning)
                   super().accept() #Fecha, mesmo com aviso
            else:
                self.show_message("Falha", f"Resposta inesperada ao ativar log: {driver.page_source}", QMessageBox.Warning)

        except Exception as e:
            self.show_message("Erro", str(e), QMessageBox.Critical)

        finally:
            if driver:
                driver.quit()


class RTMPConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.oldPos = None  # Para arrastar a janela
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Configurar RTMP")
        self.setGeometry(100, 100, 450, 400)  # Ajuste o tamanho

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self.message_label = QLabel("Preencha os campos para configurar o RTMP:", self)
        self.message_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        layout.addRow(self.message_label)

        self.usuario_input = QLineEdit(self)
        self.usuario_input.setPlaceholderText("Usuário")
        layout.addRow("Usuário:", self.usuario_input)

        self.senha_input = QLineEdit(self)
        self.senha_input.setPlaceholderText("Senha")
        self.senha_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Senha:", self.senha_input)

        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText("Endereço IP")
        layout.addRow("IP:", self.ip_input)

        self.enable_input = QLineEdit(self)
        self.enable_input.setPlaceholderText("(true/false)")
        layout.addRow("Habilitar:", self.enable_input)

        self.address_input = QLineEdit(self)
        self.address_input.setPlaceholderText("Endereço do Servidor RTMP")
        layout.addRow("Endereço:", self.address_input)

        self.port_input = QLineEdit(self)
        self.port_input.setPlaceholderText("Porta do Servidor RTMP (ex: 1935)")
        layout.addRow("Porta:", self.port_input)

        self.custom_path_input = QLineEdit(self)
        self.custom_path_input.setPlaceholderText("Endereço (ex: rtmp://py...)")
        layout.addRow("Endereço Personalizado:", self.custom_path_input)

        self.stream_path_input = QLineEdit(self)
        self.stream_path_input.setPlaceholderText("Prefix (ex: liveStream)")
        layout.addRow("Endereço da Transmissão:", self.stream_path_input)

        self.key_input = QLineEdit(self)  # Campo para a chave (opcional)
        self.key_input.setPlaceholderText("Chave (opcional)")
        layout.addRow("Chave/Token:", self.key_input)


        # Botões - Criar ANTES de chamar set_styles
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)  # Adicionar ao layout ANTES de set_styles

        self.set_styles()  # Aplica os estilos



    def set_styles(self):
        line_edit_style = """
            QLineEdit {
                background-color: rgba(255, 255, 255, 30);
                color: white;
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            }
        """
        button_style = """
            QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """
         # Aplica os estilos aos QLineEdit
        self.usuario_input.setStyleSheet(line_edit_style)
        self.senha_input.setStyleSheet(line_edit_style)
        self.ip_input.setStyleSheet(line_edit_style)
        self.enable_input.setStyleSheet(line_edit_style)
        self.address_input.setStyleSheet(line_edit_style)
        self.port_input.setStyleSheet(line_edit_style)
        self.custom_path_input.setStyleSheet(line_edit_style)
        self.stream_path_input.setStyleSheet(line_edit_style)
        self.key_input.setStyleSheet(line_edit_style)  # Aplica estilo ao campo da chave


        self.button_box.setStyleSheet("""
            QDialogButtonBox QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
                min-width: 70px;
                font-weight: bold;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """)

    def showEvent(self, event):
        super().showEvent(event)
        enable_blur_effect(int(self.winId()))
        self.center()

    def center(self):
        if self.parentWidget():
            parent_rect = self.parentWidget().geometry()
            dialog_rect = self.geometry()
            center_x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            center_y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            self.move(center_x, center_y)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None


    def show_message(self, title, message, icon):
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: rgba(0, 0, 0, 230);
                color: white;
            }
            QLabel{
                color: white;
                font-weight: bold;
            }
             QPushButton {
                background-color: rgba(0, 100, 0, 150);
                color: white;
                border: 1px solid rgba(0, 150, 0, 255);
                border-radius: 5px;
                padding: 5px 10px;
                min-width: 60px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 150, 0, 200);
            }
        """)
        msg_box.exec_()

    def accept(self):
        """Sobrescreve o método accept() para usar o Selenium."""
        usuario = self.usuario_input.text()
        senha = self.senha_input.text()
        ip = self.ip_input.text()
        enable = self.enable_input.text().lower() == "true"  # Converte para booleano
        address = self.address_input.text()
        port = self.port_input.text()
        custom_path = self.custom_path_input.text()
        stream_path = self.stream_path_input.text()
        key = self.key_input.text()  # Obtém o valor da chave

        #Validação
        if not all([usuario, senha, ip, address, port, custom_path, stream_path]): #key é opcional
            self.show_message("Erro", "Preencha todos os campos obrigatórios.", QMessageBox.Warning)
            return

        try:  #Converte a porta para int
          port_int = int(port)
        except ValueError:
          self.show_message("Erro", "A porta deve ser um número inteiro.", QMessageBox.Warning)
          return

        # --- Construção da URL ---
        # Monta a URL base (sempre presente)
        base_url = f"http://{usuario}:{senha}@{ip}/cgi-bin/configManager.cgi?action=setConfig"
        # Adiciona os parâmetros, um por vez.  Isso é mais fácil de ler e manter.
        url = base_url
        url += f"&RTMP_NVR.Enable={str(enable).lower()}"  # Converte bool para string "true" ou "false"
        url += f"&RTMP_NVR.Address={address}"
        url += f"&RTMP_NVR.Port={port_int}"  # Usa a porta como inteiro
        url += f"&RTMP_NVR.CustomPath={custom_path}"
        url += f"&RTMP_NVR.StreamPath={stream_path}"
        if key:  # Só adiciona a chave se ela tiver sido preenchida
            url += f"&RTMP_NVR.Key={key}"



        driver = None
        try:
            # --- Configuração do Selenium ---
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(url)

            if "OK" in driver.page_source:
                self.show_message("Sucesso", "Configurações RTMP aplicadas com sucesso!", QMessageBox.Information)
                super().accept()
            else:
                self.show_message("Falha", f"Resposta inesperada: {driver.page_source}", QMessageBox.Warning)

        except Exception as e:
            self.show_message("Erro", str(e), QMessageBox.Critical)

        finally:
            if driver:
                driver.quit()



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
        gif_path = resource_path("teste.gif")
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
            font-family: 'System';
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
        # self.start_ftp_button = QPushButton("📁 Iniciar Servidor FTP", self)  # ANTIGO
        self.start_ftp_button = RadialGlowButton("📁 Iniciar Servidor FTP", self)  # NOVO
        self.start_sftp_button = RadialGlowButton("🔐 Iniciar Servidor SFTP", self)
        self.rtsp_button = RadialGlowButton("👀 RTSP", self)
        self.rtmp_button = RadialGlowButton("▶️ RTMP", self)
        self.check_ports_button = RadialGlowButton("🔍 Checar Portas", self)
        self.ativar_log_button = RadialGlowButton("📋 Ativar Log", self)
        self.reset_button = RadialGlowButton("⚙️Padrão de Fáb.", self)
        left_column_layout.addWidget(self.start_ftp_button)
        left_column_layout.addWidget(self.start_sftp_button)
        left_column_layout.addWidget(self.rtsp_button)
        left_column_layout.addWidget(self.rtmp_button)
        left_column_layout.addWidget(self.check_ports_button)
        left_column_layout.addWidget(self.reset_button)
        left_column_layout.addWidget(self.ativar_log_button)

        # Coluna da direita
        right_column_layout = QVBoxLayout()
        self.encontrar_button = RadialGlowButton("🎯 Encontrar", self)
        self.stop_button = RadialGlowButton("⛔ Parar", self)
        self.ajuda_button = RadialGlowButton("❓ Ajuda", self)
        self.alarm_button = RadialGlowButton("📢 Alarme", self)
        self.snmp_button = RadialGlowButton("🩺 SNMP", self)
        self.time_sync_button = RadialGlowButton("⏱ Time Sync", self)
        
        self.ia_button = RadialGlowButton("🤖 I.A", self)

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
        self.rtmp_button.clicked.connect(self.rtmp)
        self.check_ports_button.clicked.connect(self.abrir_port_checker_dialog)
        self.reset_button.clicked.connect(self.reset_dvr)
        self.ativar_log_button.clicked.connect(self.ativar_log)
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
        self.window_alarm = StartListenWidget()  # Armazena a instância como atributo
        self.window_alarm.show()  # Exibe a janela

    def abrir_time_sync(self):
        """Abre o diálogo TimeSyncDialog."""
        dialog = TimeSyncDialog(self)  #
        dialog.exec_() 

    def encontrar(self):
        self.window_encontrar = SearchDeviceWidget()  # ✅ Armazena a referência na instância da classe
        self.window_encontrar.show()


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

    def ativar_log(self):
        """Abre o diálogo para ativar o log."""
        dialog = AtivarLogDialog(self)  # Passa 'self' como pai
        dialog.exec_()

    def configurar_rtsp(self):
        dialog = RTSPDialog(self)  # Passa 'self' como referência à janela principal
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_rtsp_config()
            rtsp_url = (
                f"rtsp://{config['usuario']}:{config['senha']}@{config['ip']}:{config['porta']}"
                f"/cam/realmonitor?channel={config['canal']}&subtype=0"
            )

            # Cria o thread de transmissão RTSP
            rtsp_stream_thread = RTSPStream(rtsp_url)

            # Cria a janela RTSP e associa o thread à janela
            self.rtsp_window = RTSPWindow(rtsp_stream_thread=rtsp_stream_thread)
            self.rtsp_window.show()

            # Inicia o thread de transmissão
            self.log_console.append("📺 Abrindo transmissão")
            rtsp_stream_thread.start()


    # Método closeEvent ajustado na RTSPWindow
    def closeEvent(self, event):
        # Verifica se o thread de transmissão RTSP existe e está rodando
        if hasattr(self, "rtsp_stream_thread") and self.rtsp_stream_thread is not None:
            self.rtsp_stream_thread.stop()  # Para o thread de stream
            self.rtsp_stream_thread.wait()  # Espera o thread finalizar

        event.accept()  # Fecha a janela normalmente

    def rtmp(self):
        dialog = RTMPConfigDialog(self)  # Passa 'self' como pai
        dialog.exec_()
        
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
    main_window = Pylau()
    main_window.show()
    sys.exit(app.exec_())
