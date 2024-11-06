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
        Bem-vindo ao PyLau (Python Local Access Utillity)
        
        Este aplicativo foi desenvolvido para permitir a transferência de arquivos utilizando protocolo FTP e SFTP hospedando servidor localmente.
        
        Funcionalidades:
        - ✅Iniciar Servidor FTP 
        - ❗️Iniciar Servidor SFTP: (em desenvolvimento). 
        - ✅Visualização RTSP: Acesse de forma simplificada uma visualização de stream RTSP. 
        
        Se você precisar de mais assistência, consulte a documentação ou entre em contato com Lucas Vinicius de Oliveira.
        
        Obrigado por usar PyLau!
        
        Lucas V.
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

        # Logger
        self.logger = logging.getLogger("SFTPServerLogger")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(levelname)s %(asctime)s] %(message)s", "%d-%m-%Y %H:%M:%S")
        text_edit_logger = QTextEditLogger(self.log_console)
        text_edit_logger.setFormatter(formatter)
        self.logger.addHandler(text_edit_logger)
        
        self.logger.info("Aplicativo PyLau iniciado. 💙\n Registros:")

    def init_ui(self):
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

        # Layout principal
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Console de log
        self.log_console = QTextEdit(self)
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("""
            background: transparent;
            color: white;
            font-size: 12pt;
            font-family: 'Arial';
            font-weight: bold;
        """)
        layout.addWidget(self.log_console)

        # Adiciona a QLabel para o stream RTSP
        self.rtsp_label = QLabel(self)
        layout.addWidget(self.rtsp_label)

        # Layout dos botões
        button_layout = QHBoxLayout()
        self.start_ftp_button = QPushButton('👁️‍🗨️ Iniciar Servidor FTP', self)
        self.start_sftp_button = QPushButton('👁️ Iniciar Servidor SFTP', self)
        self.rtsp_button = QPushButton('📹 Configurar RTSP', self)
        self.check_ports_button = QPushButton('🔍 Checar Portas', self)  # Novo botão para checar portas
        self.reset_button = QPushButton("⚙️Padrão de Fáb.", self)
        self.reset_button.clicked.connect(self.reset_dvr)
        layout.addWidget(self.reset_button)  # Adiciona ao layout
        self.stop_button = QPushButton('⛔ Parar', self)

        self.ajuda_button = QPushButton('❓ Ajuda', self)
        button_layout.addWidget(self.start_ftp_button)
        button_layout.addWidget(self.start_sftp_button)
        button_layout.addWidget(self.rtsp_button)
        button_layout.addWidget(self.check_ports_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.ajuda_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Conectar os botões às funções correspondentes
        self.start_ftp_button.clicked.connect(self.iniciar_ftp_server)
        self.start_sftp_button.clicked.connect(self.iniciar_sftp_server)  # Conectando corretamente o botão SFTP
        self.rtsp_button.clicked.connect(self.configurar_rtsp)
        self.check_ports_button.clicked.connect(self.abrir_port_checker_dialog)
        self.stop_button.clicked.connect(self.parar_servidores)
        self.ajuda_button.clicked.connect(self.abrir_ajuda)

    def resizeEvent(self, event):
        self.background_label.setGeometry(self.rect())
        self.movie.setScaledSize(self.size())
        super().resizeEvent(event)

    def create_tray_icon(self):
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
        if not self.ftp_server_thread:
            self.ftp_server_thread = FTPServerThread()
            self.ftp_server_thread.start()


    def iniciar_sftp_server(self):
        if not self.sftp_server_thread:
            # Launch the SFTP server code in a separate process using subprocess
            import subprocess

            # Ensure the sftp.py file is in the same directory as this script
            sftp_script_path = os.path.join(os.path.dirname(__file__), "sftp.py")

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
            import time

            # Inicialize o navegador e use o IP passado
            driver = webdriver.Chrome()
            driver.get(f"http://{ip}")

            # Login usando o IP e senha fornecidos
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ant-input"))
            )
            username_input.send_keys("admin")
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Senha']"))
            )
            password_input.send_keys(senha)


            submit_button = driver.find_element(By.CLASS_NAME, "login-button")
            submit_button.click()

            # Continuação da sequência de reset, igual ao script que você compartilhou

            try:
                configuracoes = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[text()='Configurações']"))
                )
                configuracoes.click()
                time.sleep(2)
                
                    # Depois, localize e clique em "Sistema"
                reset = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[text()='Sistema']"))
                )
                reset.click()

                    # Após clicar em "Sistema" e "Padrão"
                reset_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[@href='#/index/SysConfig/defaultConfig']"))
                )
                reset_link.click()

                            # Aguarda o botão "Padrão de fábrica" ficar clicável e, em seguida, clica nele
                padrao_fabrica_botao = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'labelText-wrapper') and text()='Padrão de fábrica']"))
                )
                padrao_fabrica_botao.click()

                        # Aguarda o botão "OK" ficar clicável e clica nele
                ok_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'ant-btn-primary') and span[text()='OK']]"))
                )
                ok_button.click()

                password_field = driver.find_element(By.XPATH, "//input[@class='ant-input false' and @placeholder='Senha']")
                password_field.send_keys("adminadmin12345")

                        # Localiza e clica no botão "OK"
                ok_button = driver.find_element(By.XPATH, "//div[@class='labelText-wrapper labelText undefined' and text()='OK']")
                ok_button.click()

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
