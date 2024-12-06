import os
import sys
import logging
import socket
import cv2
import subprocess
import psutil
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QTextEdit, QHBoxLayout, QLabel, QDialog, QFormLayout, QLineEdit, QDialogButtonBox)
from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QMovie, QImage, QPixmap
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QPlainTextEdit, QDialog, QListWidget, QInputDialog
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QPushButton, QInputDialog, QMessageBox

import paramiko
import socket
import time
import argparse
import threading
import ctypes



# Configuração do logger
logger = logging.getLogger("SFTPServerLogger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[%(levelname)s %(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S")



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

    
class SFTPServerThread(QThread):
    def __init__(self, host='0.0.0.0', port=3373, keyfile=None, level='INFO', logger=None):
        super().__init__()
        self.host = host
        self.port = port
        self.keyfile = keyfile
        self.level = level
        self.logger = logger

    def run(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            server_socket.bind((self.host,
 self.port))
            server_socket.listen(10)


            self.logger.info(f"Servidor SFTP aguardando conexões em {self.host}:{self.port}")

            while True:
                conn, addr = server_socket.accept()
                # ... (restante do código do sftp.py)  # Replace with the actual implementation from sftp.py

        except Exception as e:
            self.logger.error(f"Erro ao iniciar o servidor SFTP: {str(e)}")
            # Add logic to handle the error, e.g., restart the server or notify the user

        finally:
            if server_socket:
                server_socket.close()

    def stop(self):
        # Implement logic to stop the SFTP server (if necessary)
        pass
    
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
                    result += f"❌Porta {port} - <span style='color: red;'>Fechada</span><br>"


        self.scan_finished.emit(result)

class PortCheckerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Layout principal
        layout = QVBoxLayout(self)
        
        # Botão de fechar
        fechar_btn = QPushButton("Fechar", self)
        fechar_btn.setStyleSheet("background-color: red; color: white; font-weight: bold; border: none;")
        fechar_btn.clicked.connect(self.close)

        # Layout para alinhar o botão de fechar à direita
        top_layout = QHBoxLayout()
        top_layout.addWidget(fechar_btn, alignment=Qt.AlignRight)
        layout.addLayout(top_layout)

        # Texto de ajuda
        ajuda_texto = QPlainTextEdit(self)
        ajuda_texto.setReadOnly(True)
        ajuda_texto.setPlainText("""\
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
        """)
        ajuda_texto.setStyleSheet("color: white; background: transparent; font-size: 14px;")
        
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
                        timeout=120
                    )
                    if "TTL=" in resposta.stdout.decode('latin1'):  # Resposta positiva
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

class AlarmThread(QThread):
    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path

    def run(self):
        # Executa o outro script Python
        subprocess.run(['python', self.script_path], check=True)

class iaThread(QThread):
    def __init__(self, script_path):
        super().__init__()
        self.script_path = script_path

    def run(self):
        # Executa o outro script Python
        subprocess.run(['python', self.script_path], check=True)

### AQUI FICA A DEFINIÇÃO DA PARTE VISUAL DA JANELA PRINCIPAL
class Pylau(QWidget):
    def __init__(self):

        super().__init__()

        self.init_ui()
        self.create_tray_icon()
        self.ftp_server_thread = None
        self.sftp_server_thread = None
        self.rtsp_stream_thread = None
        self.port_checker_thread = None
        self.sftp_running = False

        # Logger
        self.logger = logging.getLogger("SFTPServerLogger")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(levelname)s %(asctime)s] %(message)s", "%d-%m-%Y %H:%M:%S")
        text_edit_logger = QTextEditLogger(self.log_console)
        text_edit_logger.setFormatter(formatter)
        self.logger.addHandler(text_edit_logger)
        
        self.logger.info("Aplicativo PyLau iniciado. 💙\n Registros:")

    def init_ui(self):
        self.setWindowIcon(QIcon(resource_path('icone.ico')))
        self.setWindowTitle('PyLau - Python Local Access Utility')
        self.tray_icon = QSystemTrayIcon(QIcon(resource_path('icone.ico')), self)
        self.tray_icon.show()
        self.setGeometry(300, 300, 780, 780)

        # Configurando o fundo com um GIF animado
        self.background_label = QLabel(self)
        self.background_label.setGeometry(self.rect())
        gif_path = resource_path("ativo2.png")  # Use o caminho adaptado
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
        self.log_console.setStyleSheet("""
            background: transparent;
            color: white;
            font-size: 16pt;
            font-family: 'Impact';
            font-weight: regular;
        """)
        layout.addWidget(self.log_console)

        # Adiciona a QLabel para o stream RTSP
        self.rtsp_label = QLabel(self)
        layout.addWidget(self.rtsp_label)

        # Layout para os botões em colunas
        button_layout = QHBoxLayout()

        # Coluna da esquerda
        left_column_layout = QVBoxLayout()
        self.start_ftp_button = QPushButton('👁️‍🗨️ Iniciar Servidor FTP', self)
        self.start_sftp_button = QPushButton('👁️ Iniciar Servidor SFTP', self)
        self.rtsp_button = QPushButton('📹 RTSP', self)
        left_column_layout.addWidget(self.start_ftp_button)
        left_column_layout.addWidget(self.start_sftp_button)
        left_column_layout.addWidget(self.rtsp_button)

        # Coluna da direita
        right_column_layout = QVBoxLayout()
        self.check_ports_button = QPushButton('🔍 Checar Portas', self)
        self.reset_button = QPushButton("⚙️Padrão de Fáb.", self)
        self.stop_button = QPushButton('⛔ Parar', self)
        self.ajuda_button = QPushButton('❓ Ajuda', self)
        self.alarm_button = QPushButton('📢 Alarme', self)
        self.ia_button = QPushButton('🤖 I.A', self)

        right_column_layout.addWidget(self.check_ports_button)
        right_column_layout.addWidget(self.reset_button)
        right_column_layout.addWidget(self.stop_button)
        right_column_layout.addWidget(self.alarm_button)
        right_column_layout.addWidget(self.ia_button)
        right_column_layout.addWidget(self.ajuda_button)

        # Adiciona transparência aos botões
        button_style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 204); /* Preto com 80% de opacidade */
                color: white;
                font-size: 14pt;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(50, 50, 50, 204); /* Leve destaque no hover */
            }
        """
        for button in [
            self.start_ftp_button, self.start_sftp_button, self.rtsp_button,
            self.check_ports_button, self.reset_button, self.stop_button,
            self.alarm_button, self.ia_button, self.ajuda_button
        ]:
            button.setStyleSheet(button_style)

        # Adiciona as colunas ao layout horizontal
        button_layout.addLayout(left_column_layout)
        button_layout.addLayout(right_column_layout)

        # Adiciona o layout de botões ao layout principal
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Conectar os botões às funções correspondentes
        self.start_ftp_button.clicked.connect(self.iniciar_ftp_server)
        self.start_sftp_button.clicked.connect(self.start_sftp_server)
        self.rtsp_button.clicked.connect(self.configurar_rtsp)
        self.check_ports_button.clicked.connect(self.abrir_port_checker_dialog)
        self.reset_button.clicked.connect(self.reset_dvr)
        self.stop_button.clicked.connect(self.parar_servidores)
        self.alarm_button.clicked.connect(self.start_alarm)
        self.ia_button.clicked.connect(self.start_ia)
        self.ajuda_button.clicked.connect(self.abrir_ajuda)
        def resizeEvent(self, event):
            self.background_label.setGeometry(self.rect())
            self.movie.setScaledSize(self.size())
            super().resizeEvent(event)

    def start_alarm(self):
        # Caminho para o script alarme.py
        script_path = "alarme.py"

        # Inicia o script em uma thread separada
        self.alarm_thread = AlarmThread(script_path)
        self.alarm_thread.start()

    def start_ia(self):
        # Caminho para o script genia.py
        script_path = "genia.py"

        # Inicia o script em uma thread separada
        self.ia_thread = iaThread(script_path)
        self.ia_thread.start()

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(QIcon('icone.ico'), self)
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
        if not self.ftp_server_thread:
            self.ftp_server_thread = FTPServerThread()
            self.ftp_server_thread.start()


    def start_sftp_server(self):
        if not self.sftp_running:
            self.logger.info("Iniciando o servidor SFTP...")
            try:
                self.sftp_server_thread = SFTPServerThread(
                    host='0.0.0.0', 
                    port=3373, 
                    keyfile='id_rsa', 
                    logger=self.logger
                )
                self.sftp_server_thread.start()
                self.sftp_running = True
                self.start_sftp_button.setText("👁️ Parar Servidor SFTP")
                self.logger.info("Servidor SFTP iniciado.")
            except Exception as e:
                self.logger.error(f"Erro ao iniciar o servidor SFTP: {str(e)}")
        else:
            self.logger.info("Parando o servidor SFTP...")
            try:
                if self.sftp_server_thread:
                    self.sftp_server_thread.terminate()  # Finaliza o thread
                    self.sftp_server_thread = None
                self.sftp_running = False
                self.start_sftp_button.setText("👁️ Iniciar Servidor SFTP")
                self.logger.info("Servidor SFTP parado.")
            except Exception as e:
                self.logger.error(f"Erro ao parar o servidor SFTP: {str(e)}")

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
            self.log_console.append('📺Abrindo transmissão')
            rtsp_stream_thread.start()

    # Método closeEvent ajustado na RTSPWindow
    def closeEvent(self, event):
        # Verifica se o thread de transmissão RTSP existe e está rodando
        if hasattr(self, 'rtsp_stream_thread') and self.rtsp_stream_thread is not None:
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


    
    ### AUTOMAÇÃO DE PADRÃO DE FÁBRICA

    def reset_dvr(self):
        ip, ok_ip = QInputDialog.getText(self, "IP do Alvo", "Digite o IP alvo:")
        if ok_ip and ip:
            senha, ok_senha = QInputDialog.getText(self, "Senha do Alvo", "Digite a senha do alvo:")
            if ok_senha and senha:
                QMessageBox.information(self, "Iniciado", "O produto será restaurado para o padrão de fábrica.\nDeseja continuar com o processo?")
                threading.Thread(target=self.run_selenium_script, args=(ip, senha)).start()

    def run_selenium_script(self, ip, senha):
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.action_chains import ActionChains
            import time

            # Inicialize o navegador e use o IP passado
            driver = webdriver.Chrome()
            driver.get(f"http://{ip}")

            # Login usando o IP e senha fornecidos
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "loginUsername-inputEl"))
            )
            username_input.send_keys("admin")
            # Localizar o campo de senha e inserir a senha
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "loginPassword-inputEl"))
            )
            password_input.send_keys(senha)

            submit_button = driver.find_element(By.ID, "loginButton-btnWrap")
            submit_button.click()

            # Continuação da sequência de reset
            try:
                configuracoes = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "button-1045-btnEl"))
                )
                configuracoes.click()
                time.sleep(2)
                
                    # Depois, localize e clique em "Sistema"
                reset = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'SYSTEM') or contains(text(), 'Sistema')]"))
                )
                reset.click()
                time.sleep(2)

                    # Após clicar em "Sistema" e "Padrão"
                reset_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Default') or contains(text(), 'Padrão') or contains(text(), 'Predeterminado')]"))
                )
                reset_link.click()
                time.sleep(2)

                    # Localizar e clicar no botão "Padrão de fábrica"
                reset_button = None
                titles = ["Factory Defaults", "Padrão de fábrica", "Estándar de fábrica"]

                for title in titles:
                    reset_button = driver.execute_script(
                        f"return document.querySelector(\"a[title='{title}']\")"
                    )
                    if reset_button:
                        driver.execute_script("arguments[0].click();", reset_button)
                        break

                if not reset_button:
                    print("Nenhum botão encontrado com os títulos especificados.")
                time.sleep(2)

                    # Aguarda o botão "Salvar" ficar clicável e clica nele
                save_button = None
                titles = ["Save", "Salvar", "Guardar"]

                for title in titles:
                    # Executa o script para encontrar o botão com o texto "Save"
                    save_button = driver.execute_script(
                        f"return document.querySelector('span.x-btn-inner span[t=\"com.Save\"]')"
                    )
                    if save_button:
                        driver.execute_script("arguments[0].click();", save_button)
                        break

                if not save_button:
                    print("Nenhum botão 'Save' ou 'Salvar' encontrado.")
                time.sleep(2)

                # Localizar o campo de senha pelo tipo do input
                password_field = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//input[@type='password']")
                    )
                )

                # Focar no campo e preencher a senha
                password_field.click()  # Focar no campo
                password_field.send_keys("@1234567")  # Inserir a senha
                time.sleep(2)
                                



            except Exception as e:
                print("Ocorreu um erro:", e)

        except Exception as e:
            print("Erro ao resetar DVR:", e)

    
    ###     VERIFICADOR DE PORTAS ABERTAS
        
    def checar_portas(self, ip):
        ports_to_check = [21, 22, 80, 443, 554, 37777]  # Lista de portas para verificar

        self.port_checker_thread = PortCheckerThread(ip, ports_to_check)
        self.port_checker_thread.scan_finished.connect(self.mostrar_resultado_portas)
        self.port_checker_thread.start()
        self.log_console.append('🔍Verificando')

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
