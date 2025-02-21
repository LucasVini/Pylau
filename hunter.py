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

from queue import Queue  # Importa a classe Queue

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


class SearchDeviceWidget(QWidget):
    update_table = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Buscador de Dispositivos")
        self.setFixedSize(900, 700)
        # self.setStyleSheet(STYLE_SHEET)  # Aplicar stylesheet. Removido, global é melhor

        self.sdk = NetClient()
        self.sdk.InitEx(None, 0)  # Inicializa o SDK. Não há callback de desconexão necessário aqui.

        self.init_ui()
        self.search_thread = None  # Inicializa a thread de busca

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
        self.table.setColumnCount(8)  # Número reduzido de colunas
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
        btn_layout.addWidget(self.btn_multicast)
        btn_layout.addWidget(self.btn_unicast)
        btn_layout.addWidget(self.btn_init)
        layout.addLayout(btn_layout)

        # Barra de progresso
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)

        # Conexões
        self.btn_multicast.clicked.connect(self.start_multicast_search)
        self.btn_unicast.clicked.connect(self.start_unicast_search)
        self.btn_init.clicked.connect(self.init_device)
        self.update_table.connect(self.update_device_table)

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

        if self.validate_ips(start, end):
            self.start_search(EM_SEND_SEARCH_TYPE.UNICAST, start, end)

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
