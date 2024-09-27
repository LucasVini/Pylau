import os
import sys
import logging
import socket
import cv2
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QTextEdit, QHBoxLayout, QLabel, QDialog, QFormLayout, QLineEdit, QDialogButtonBox)
from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QMovie, QImage, QPixmap
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QPlainTextEdit, QDialog
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
import paramiko
import socket
import time
import argparse
import threading
# Importar a função para iniciar o servidor SFTP
import sftp  # Importa o arquivo sftp.py


# Configuração do logger
logger = logging.getLogger("SFTPServerLogger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[%(levelname)s %(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S")


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
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
 True)
            server_socket.bind((self.host, self.port))
            server_socket.listen(10)


            self.logger.info(f"Servidor SFTP aguardando conexões em {self.host}:{self.port}")

            while True:
                conn, addr = server_socket.accept()
                # ... (restante do código do sftp.py)
        except Exception as e:
            self.logger.error(f"Erro ao iniciar o servidor SFTP: {str(e)}")
            # Adicionar lógica para lidar com o erro, por exemplo, reiniciar o servidor
        finally:
            if server_socket:
                server_socket.close()

    def stop(self):
        # Implementar lógica para parar o servidor SFTP (se necessário)
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ajuda")
        self.setGeometry(400, 400, 500, 300)

        layout = QVBoxLayout(self)

        ajuda_texto = QPlainTextEdit(self)
        ajuda_texto.setReadOnly(True)
        ajuda_texto.setPlainText("""
        Bem-vindo ao PyLau (Python Local Access Utillity)

        Este aplicativo permite realizar transferência de arquivos utilizando protocolo FTP e SFTP hospedando servidor localmente.

        Funcionalidades:
        - ✅Iniciar Servidor FTP 
        - ❗️Iniciar Servidor SFTP: (em desenvolvimento). 
        - ✅Visualização RTSP: Acesse de forma simplificada uma visualização de stream RTSP. 

        Se você precisar de mais assistência, consulte a documentação ou entre em contato com Lucas Vinicius de Oliveira.

        Obrigado por usar PyLau!

        E lembrem-se de pagar cafézinho para Lucas.
        """)

        layout.addWidget(ajuda_texto)
        self.setLayout(layout)

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
        self.layout.addRow("IP:", self.ip)
        self.layout.addRow("Porta:", self.porta)

        # Adicionando o QDialogButtonBox com botões OK e Cancelar
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)  # Conectar o botão OK para aceitar o diálogo
        self.button_box.rejected.connect(self.reject)  # Conectar o botão Cancelar para rejeitar o diálogo
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

    def get_rtsp_config(self):
        return {
            'usuario': self.usuario.text(),
            'senha': self.senha.text(),
            'ip': self.ip.text(),
            'porta': self.porta.text(),
        }

class RTSPStream(QThread):
    def __init__(self, rtsp_url, label=None, external_window=None):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.label = label
        self.external_window = external_window
        self.capture = None
        self.running = False

    def run(self):
        self.capture = cv2.VideoCapture(self.rtsp_url)
        self.running = True

        while self.running and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)

                if self.external_window:
                    self.external_window.set_video_frame(pixmap)
                elif self.label:
                    self.label.setPixmap(pixmap)
            else:
                logger.warning("Falha na captura de frame RTSP.")
        
        self.capture.release()

    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class RTSPWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stream RTSP")
        self.label = QLabel(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def set_video_frame(self, pixmap):
        self.label.setPixmap(pixmap)
        self.adjustSize()  # Ajusta o tamanho da janela ao tamanho do vídeo

    def closeEvent(self, event):
        if self.parent().rtsp_stream_thread:
            self.parent().rtsp_stream_thread.stop()
        event.accept()


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
            color: black;
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
        self.ajuda_button.clicked.connect(self.mostrar_ajuda)

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
            self.sftp_server_thread = SFTPServerThread(logger=self.logger)
            self.sftp_server_thread.start()
            self.logger.info("Servidor SFTP iniciado.")

    def parar_sftp_server(self):
        # Implementar a lógica para parar o servidor SFTP
        if self.sftp_server_thread:
            self.sftp_server_thread.stop()
            self.sftp_server_thread = None
            self.logger.info("Servidor SFTP parado.")

    

    def configurar_rtsp(self):
        dialog = RTSPDialog()
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_rtsp_config()
            rtsp_url = f"rtsp://{config['usuario']}:{config['senha']}@{config['ip']}:{config['porta']}/"

            self.rtsp_window = RTSPWindow()
            self.rtsp_window.show()

            self.rtsp_stream_thread = RTSPStream(rtsp_url, external_window=self.rtsp_window)
            self.rtsp_stream_thread.start()

    def abrir_port_checker_dialog(self):
        dialog = PortCheckerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            ip = dialog.get_ip()
            if ip:
                self.checar_portas(ip)
            else:
                QMessageBox.warning(self, "Erro", "Endereço IP não pode ser vazio!")

    def checar_portas(self, ip):
        ports_to_check = [21, 22, 80, 443, 554, 37777]  # Lista de portas para verificar

        self.port_checker_thread = PortCheckerThread(ip, ports_to_check)
        self.port_checker_thread.scan_finished.connect(self.mostrar_resultado_portas)
        self.port_checker_thread.start()

    def mostrar_resultado_portas(self, resultado):
        self.log_console.append(resultado)

    def parar_servidores(self):
        if self.ftp_server_thread:
            self.ftp_server_thread.stop()
            self.ftp_server_thread = None
        if self.rtsp_stream_thread:
            self.rtsp_stream_thread.stop()
            self.rtsp_stream_thread = None

    def mostrar_ajuda(self):
        dialog = AjudaDialog()
        dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Pylau()
    main_window.show()
    sys.exit(app.exec_())