import os
import sys
import time
import logging
import socket
import threading
import ctypes
import argparse

import cv2
import psutil
import paramiko
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QMovie, QImage, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit,
    QHBoxLayout, QLabel, QDialog, QFormLayout, QLineEdit,
    QDialogButtonBox, QSystemTrayIcon, QMenu, QAction,
    QPlainTextEdit, QListWidget
)



#### Implementação dos efeitos Blur

# Estruturas e funções para o efeito blur
class ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ACCENTPOLICY)),
        ("SizeOfData", ctypes.c_size_t)
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



## SFTP
# Configuração dos diretórios para o SFTP
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIVED_DIR = os.path.join(BASE_DIR, 'SFTP_RECEBIDO')
if not os.path.exists(RECEIVED_DIR):
    os.makedirs(RECEIVED_DIR)

# Configuração do logger
logger = logging.getLogger("SFTPServerLogger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[%(levelname)s %(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S")


# Configurando o adaptador ETHERNET
def get_first_ethernet_ip():
    """Obtém o IP do primeiro adaptador Ethernet ativo."""
    for interface, addrs in psutil.net_if_addrs().items():
        # Procura por interfaces Ethernet (nome geralmente contém "Ethernet" ou "eth")
        if "Ethernet" in interface or "eth" in interface.lower():
            for addr in addrs:
                if addr.family == socket.AF_INET:  # Apenas endereços IPv4
                    return addr.address
    return "127.0.0.1"  # Fallback para localhost caso não encontre adaptador Ethernet
    
# Classe StubServer para autenticação básica
class StubServer(paramiko.ServerInterface):
    def check_auth_password(self, username, password):
        if username == "admin" and password == "@1234567":
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED

# Classe StubSFTPServer para manipulação dos arquivos
class StubSFTPServer(paramiko.SFTPServerInterface):
    ROOT = RECEIVED_DIR

    def _realpath(self, path):
        return os.path.join(self.ROOT, path.lstrip('/'))

    def open(self, path, flags, attr):
        path = self._realpath(path)
        try:
            return open(path, 'wb' if flags & os.O_WRONLY else 'rb')
        except IOError:
            return paramiko.SFTP_PERMISSION_DENIED

# Classe para rodar o servidor SFTP em uma thread separada
class SFTPServerThread(QThread):
    update_status = pyqtSignal(str)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True

    def run(self):
        self.update_status.emit(f"Iniciando servidor SFTP em {self.host}:{self.port}")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(10)
        
        while self.running:
            conn, _ = server_socket.accept()
            try:
                host_key = paramiko.RSAKey.generate(2048)
                transport = paramiko.Transport(conn)
                transport.add_server_key(host_key)
                transport.set_subsystem_handler("sftp", paramiko.SFTPServer, StubSFTPServer)
                transport.start_server(server=StubServer())
                while self.running and transport.is_active():
                    self.sleep(1)
            except Exception as e:
                self.update_status.emit(f"Erro no servidor: {e}")

        server_socket.close()
        self.update_status.emit("Servidor SFTP parado.")

    def stop(self):
        self.running = False
    
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
                    result += f"Porta {port} aberta✅\n"
                except (socket.timeout, ConnectionRefusedError):
                    result += f"Porta {port} fechada❌\n"
        self.scan_finished.emit(result)

class PortCheckerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Checar Portas")
        self.setGeometry(400, 300, 300, 150)

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
        layout.addLayout(button_layout)  # Adicionar o layout dos botões ao layout principal

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
    def __init__(self, host='0.0.0.0', porta=2222, usuario='admin', senha='@1234567', diretorio='./FTP_RECEBIDO'):
        super().__init__()
        self.host = host
        self.porta = porta
        self.usuario = usuario
        self.senha = senha
        self.diretorio = diretorio
        self.server = None

    def run(self):
        if not os.path.exists(self.diretorio):
            os.makedirs(self.diretorio)

        # Descobrir o IPv4 real do host
        self.host = self.get_ipv4_address()

        authorizer = DummyAuthorizer()
        authorizer.add_user(self.usuario, self.senha, self.diretorio, perm='elradfmw')

        handler = FTPHandler
        handler.authorizer = authorizer

        self.server = FTPServer((self.host, self.porta), handler)
        logger.info(f""">>> Servidor FTP iniciado\n---------------------\nIP = {self.host}:{self.porta}, 
Utilize o seguinte login no gravador:\n\nUsuário: {self.usuario},\nSenha: {self.senha},\npid={os.getpid()} <<<""")

        self.server.serve_forever()

    def stop(self):
        if self.server:
            self.server.close_all()
            logger.info("Servidor FTP parado.")
            self.quit()

    @staticmethod
    def get_ipv4_address():
        """Obtém o endereço IPv4 real do host."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
        except Exception:
            ip_address = "127.0.0.1"
        finally:
            s.close()
        return ip_address

class AjudaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajuda")
        self.setGeometry(400, 400, 500, 300)

        layout = QVBoxLayout(self)

        # Criar o QPlainTextEdit antes de aplicar o estilo
        ajuda_texto = QPlainTextEdit(self)
        ajuda_texto.setReadOnly(True)
        ajuda_texto.setPlainText("""
        Bem-vindo ao PyLau (Python Local Access Utility)

        Este aplicativo foi desenvolvido para permitir a transferência de arquivos utilizando protocolo FTP e SFTP hospedando servidor localmente.

        Funcionalidades:
        - ✅Iniciar Servidor FTP 
        - ❗️Iniciar Servidor SFTP: (em desenvolvimento). 
        - ✅Visualização RTSP: Acesse de forma simplificada uma visualização de stream RTSP. 

        Se você precisar de mais assistência, consulte a documentação ou entre em contato com Lucas Vinicius de Oliveira.

        Obrigado por usar PyLau!

        Lucas V.
        """)

        # Definir o fundo transparente e a cor do texto
        ajuda_texto.setStyleSheet("background: transparent; color: white; font-size: 14px;")
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
        self.setGeometry(400, 400, 300, 200)

        self.layout = QFormLayout(self)
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
        self.varredura_btn = QPushButton("Varredura", self)
        self.varredura_btn.clicked.connect(self.abrir_janela_varredura)
        ip_layout.addWidget(self.varredura_btn)

        self.layout.addRow("IP:", ip_layout)
        self.layout.addRow("Porta:", self.porta)

        # Botão para preencher os campos com valores padrão
        self.preencher_btn = QPushButton("Auto Preencher", self)
        self.preencher_btn.clicked.connect(self.preencher_campos)
        self.layout.addWidget(self.preencher_btn)

        # Adicionando o QDialogButtonBox com botões OK e Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)  # Conectar o botão OK para aceitar o diálogo
        self.button_box.rejected.connect(self.reject)  # Conectar o botão Cancelar para rejeitar o diálogo
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
            'usuario': self.usuario.text(),
            'senha': self.senha.text(),
            'ip': self.ip.text(),
            'porta': self.porta.text(),
        }


class PingThread(QThread):
    """Thread para realizar a varredura de IPs."""
    progress = pyqtSignal(str)

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
                        timeout=120
                    )
                    if "TTL=" in resposta.stdout.decode('latin1'):  # Resposta positiva
                        self.progress.emit(ip)
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
                    base_ip = ".".join(ip_local.split(".")[:-1]) + "."  # Extrai o base IP
                    if base_ip not in adaptadores_ips:
                        adaptadores_ips.append(base_ip)  # Adiciona o base IP se ainda não estiver na lista

        return adaptadores_ips

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
        self.thread.progress.connect(self.adicionar_ip_na_lista)
        self.thread.start()

    def adicionar_ip_na_lista(self, ip):
        """Adiciona um IP à lista de dispositivos encontrados."""
        self.ip_list_widget.addItem(ip)

    def selecionar_ip(self, item):
        """Preenche o campo de IP no diálogo principal com o IP selecionado."""
        ip_selecionado = item.text()
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
                q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                
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



class Pylau(QWidget):
    def __init__(self):
        super().__init__()

        # Inicialização da interface e configuração do ícone da bandeja
        self.logger = logging.getLogger("SFTPServerLogger")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(levelname)s %(asctime)s] %(message)s", "%d-%m-%Y %H:%M:%S")

        # Inicializa o logger para o console
        self.log_console = QTextEdit(self)
        self.log_console.setReadOnly(True)
        text_edit_logger = QTextEditLogger(self.log_console)
        text_edit_logger.setFormatter(formatter)
        self.logger.addHandler(text_edit_logger)

        self.init_ui()  # Inicializa a interface após configurar o logger
        self.create_tray_icon()

        # Inicialização das threads
        self.ftp_server_thread = None
        self.sftp_server_thread = None
        self.sftp_running = False  # Flag para controle do estado do servidor SFTP
        self.rtsp_stream_thread = None
        self.port_checker_thread = None

        self.logger.info("Aplicativo PyLau iniciado. 💙\n Registros:")
    
    def init_ui(self):
        # Configurações da janela principal
        self.setWindowIcon(QIcon('pylau.ico'))
        self.setWindowTitle('PyLau - Python Local Access Utility')
        self.setGeometry(300, 300, 600, 400)

        # Configurando o fundo com um GIF animado
        self.background_label = QLabel(self)
        self.background_label.setGeometry(self.rect())
        self.movie = QMovie("fundo.gif")
        self.movie.setScaledSize(self.size())
        self.background_label.setMovie(self.movie)
        self.movie.start()

        # Criação do contêiner de widgets
        self.foreground_widget = QWidget(self)
        self.foreground_widget.setGeometry(self.rect())
        foreground_layout = QVBoxLayout(self.foreground_widget)
        foreground_layout.setContentsMargins(0, 0, 0, 0)

        # Console de log com fundo sólido e selecinável
        self.log_console.setStyleSheet("""
            background-color: rgba(30, 30, 30, 0);  /* fundo escuro semi-transparente */
            color: white;
            font-size: 12pt;
            font-family: 'Arial';
            font-weight: bold;
            border: none;
        """)
        self.log_console.setReadOnly(False)  # Permite a seleção de texto
        foreground_layout.addWidget(self.log_console)

        # Adiciona a QLabel para o stream RTSP
        self.rtsp_label = QLabel(self)
        foreground_layout.addWidget(self.rtsp_label)

        # Layout dos botões
        self.init_buttons_layout(foreground_layout)

        self.setLayout(foreground_layout)

    def resizeEvent(self, event):
        """Redimensiona o fundo do GIF e o contêiner de widgets ao ajustar a janela."""
        self.background_label.setGeometry(self.rect())
        self.foreground_widget.setGeometry(self.rect())
        self.movie.setScaledSize(self.size())
        super().resizeEvent(event)



    def init_buttons_layout(self, layout):
        """Inicializa o layout dos botões na interface."""
        button_layout = QHBoxLayout()
        self.start_ftp_button = QPushButton('👁️‍🗨️ Iniciar Servidor FTP', self)
        self.iniciar_sftp_paramiko_button = QPushButton('👁️ Iniciar Servidor SFTP', self)
        self.rtsp_button = QPushButton('📹 Configurar RTSP', self)
        self.check_ports_button = QPushButton('🔍 Checar Portas', self)
        self.stop_button = QPushButton('⛔ Parar', self)
        self.ajuda_button = QPushButton('❓ Ajuda', self)

        # Conecta os botões às funções correspondentes
        self.start_ftp_button.clicked.connect(self.iniciar_ftp_server)
        self.iniciar_sftp_paramiko_button.clicked.connect(self.iniciar_sftp_paramiko_server)
        self.rtsp_button.clicked.connect(self.configurar_rtsp)
        self.check_ports_button.clicked.connect(self.abrir_port_checker_dialog)
        self.stop_button.clicked.connect(self.parar_servidores)
        self.ajuda_button.clicked.connect(self.mostrar_ajuda)

        # Adiciona os botões ao layout
        button_layout.addWidget(self.start_ftp_button)
        button_layout.addWidget(self.iniciar_sftp_paramiko_button)
        button_layout.addWidget(self.rtsp_button)
        button_layout.addWidget(self.check_ports_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.ajuda_button)
        layout.addLayout(button_layout)

    def resizeEvent(self, event):
        """Redimensiona o fundo do GIF ao ajustar a janela."""
        self.background_label.setGeometry(self.rect())
        self.movie.setScaledSize(self.size())
        super().resizeEvent(event)

    def create_tray_icon(self):
        """Cria o ícone na bandeja do sistema."""
        self.tray_icon = QSystemTrayIcon(QIcon('pylau.ico'), self)
        tray_menu = QMenu(self)

        abrir_acao = QAction("Abrir", self)
        sair_acao = QAction("Sair", self)
        tray_menu.addAction(abrir_acao)
        tray_menu.addAction(sair_acao)

        abrir_acao.triggered.connect(self.show)
        sair_acao.triggered.connect(self.close)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def iniciar_ftp_server(self):
        """Inicia o servidor FTP."""
        if not self.ftp_server_thread:
            self.ftp_server_thread = FTPServerThread()
            self.ftp_server_thread.start()

    def iniciar_sftp_paramiko_server(self):
        """Inicia ou para o servidor SFTP usando Paramiko."""
        if not self.sftp_running:
            # Obter o IP do primeiro adaptador Ethernet
            local_ip = get_first_ethernet_ip()
            
            # Iniciar o servidor SFTP
            self.sftp_server_thread = SFTPServerThread(host=local_ip, port=2222)
            self.sftp_server_thread.update_status.connect(self.update_status)
            self.sftp_server_thread.start()
            
            # Atualizar a interface para refletir o status do servidor
            self.iniciar_sftp_paramiko_button.setText("Parar SFTP")
            self.sftp_running = True
            self.logger.info(f"Servidor SFTP iniciado no IP {local_ip} na porta 2222.")
        else:
            # Parar o servidor SFTP
            if self.sftp_server_thread:
                self.sftp_server_thread.stop()
                self.sftp_server_thread.wait()  # Espera a thread encerrar
            self.iniciar_sftp_paramiko_button.setText("Iniciar SFTP")
            self.sftp_running = False
            self.logger.info("Servidor SFTP parado.")

    def update_status(self, message):
        """Atualiza o console de log com mensagens do servidor."""
        self.log_console.append(message)

    def configurar_rtsp(self):
        """Configura a transmissão RTSP e a janela correspondente."""
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
            self.log_console.append('📺 Abrindo transmissão')
            rtsp_stream_thread.start()

    def closeEvent(self, event):
        """Lida com o fechamento da janela, parando a transmissão RTSP se necessário."""
        if hasattr(self, 'rtsp_stream_thread') and self.rtsp_stream_thread is not None:
            self.rtsp_stream_thread.stop()  # Para o thread de stream
            self.rtsp_stream_thread.wait()  # Espera o thread finalizar

        event.accept()  # Fecha a janela normalmente

    def abrir_port_checker_dialog(self):
        """Abre o diálogo para verificar portas."""
        dialog = PortCheckerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            ip = dialog.get_ip()
            if ip:
                self.checar_portas(ip)
            else:
                QMessageBox.warning(self, "Erro", "Endereço IP não pode ser vazio!")

    def checar_portas(self, ip):
        """Verifica as portas especificadas no IP fornecido."""
        ports_to_check = [21, 22, 80, 443, 554, 2222, 37777]  # Lista de portas para verificar

        self.port_checker_thread = PortCheckerThread(ip, ports_to_check)
        self.port_checker_thread.scan_finished.connect(self.mostrar_resultado_portas)
        self.port_checker_thread.start()
        self.log_console.append('🔍 Verificando portas...')

    def mostrar_resultado_portas(self, resultado):
        """Exibe o resultado da verificação das portas."""
        self.log_console.append(resultado)

    def parar_servidores(self):
        """Para os servidores FTP e RTSP se estiverem em execução."""
        if self.ftp_server_thread:
            self.ftp_server_thread.stop()
            self.ftp_server_thread = None
            self.logger.info("Servidor FTP parado.")
        if self.rtsp_stream_thread:
            self.rtsp_stream_thread.stop()
            self.rtsp_stream_thread = None
            self.logger.info("Servidor RTSP parado.")

    def mostrar_ajuda(self):
        """Abre o diálogo de ajuda."""
        dialog = AjudaDialog()
        dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Pylau()
    main_window.show()
    sys.exit(app.exec_())
