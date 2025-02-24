import sys
import datetime
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QWidget, QGroupBox, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Struct import *
from NetSDK.SDK_Enum import *
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect, CB_FUNCTYPE

# Global para acesso nos callbacks (não é o ideal, mas preserva a lógica)
global hwnd

################################################################
# Interface (UI) – construída como um QWidget com layouts
################################################################

class Ui_AlarmWidget(object):
    def setupUi(self, AlarmWidget):
        AlarmWidget.setObjectName("AlarmWidget")
        AlarmWidget.setFixedSize(800, 600)
        
        # Layout principal vertical
        self.mainLayout = QVBoxLayout(AlarmWidget)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(10)
        
        # --- Layout Superior: dois group boxes em linha ---
        self.topLayout = QHBoxLayout()
        self.topLayout.setSpacing(10)
        
        # GroupBox de Conexão
        self.groupBoxConexao = QGroupBox("Login no Gravador", AlarmWidget)
        self.groupBoxConexao.setObjectName("groupBoxConexao")
        self.groupBoxConexao.setMinimumWidth(500)
        formLayout = QFormLayout(self.groupBoxConexao)
        formLayout.setContentsMargins(10, 10, 10, 10)
        formLayout.setSpacing(8)
        
        self.IP_lineEdit = QLineEdit(self.groupBoxConexao)
        self.IP_lineEdit.setObjectName("IP_lineEdit")
        formLayout.addRow("IP:", self.IP_lineEdit)
        
        self.Port_lineEdit = QLineEdit(self.groupBoxConexao)
        self.Port_lineEdit.setObjectName("Port_lineEdit")
        formLayout.addRow("Porta:", self.Port_lineEdit)
        
        self.Username_lineEdit = QLineEdit(self.groupBoxConexao)
        self.Username_lineEdit.setObjectName("Username_lineEdit")
        formLayout.addRow("Usuário:", self.Username_lineEdit)
        
        self.Password_lineEdit = QLineEdit(self.groupBoxConexao)
        self.Password_lineEdit.setEchoMode(QLineEdit.Password)
        self.Password_lineEdit.setObjectName("Password_lineEdit")
        formLayout.addRow("Senha:", self.Password_lineEdit)
        
        # Layout horizontal para botões de login/logout
        btnLayoutLogin = QHBoxLayout()
        self.Login_pushButton = QPushButton("(Login)", self.groupBoxConexao)
        self.Login_pushButton.setObjectName("Login_pushButton")
        self.Logout_pushButton = QPushButton("(Logout)", self.groupBoxConexao)
        self.Logout_pushButton.setObjectName("Logout_pushButton")
        btnLayoutLogin.addWidget(self.Login_pushButton)
        btnLayoutLogin.addWidget(self.Logout_pushButton)
        formLayout.addRow("", btnLayoutLogin)
        
        self.topLayout.addWidget(self.groupBoxConexao)
        
        # GroupBox de Controle de Alarme
        self.groupBoxControl = QGroupBox("Controles", AlarmWidget)
        self.groupBoxControl.setObjectName("groupBoxControl")
        vboxControl = QVBoxLayout(self.groupBoxControl)
        vboxControl.setContentsMargins(10, 10, 10, 10)
        vboxControl.setSpacing(10)
        self.Alarmlisten_pushButton = QPushButton("Monitorar Alarme", self.groupBoxControl)
        self.Alarmlisten_pushButton.setObjectName("Alarmlisten_pushButton")
        self.Stopalarmlisten_pushButton = QPushButton("Parar de Monitorar", self.groupBoxControl)
        self.Stopalarmlisten_pushButton.setObjectName("Stopalarmlisten_pushButton")
        vboxControl.addWidget(self.Alarmlisten_pushButton)
        vboxControl.addWidget(self.Stopalarmlisten_pushButton)
        self.topLayout.addWidget(self.groupBoxControl)
        
        self.mainLayout.addLayout(self.topLayout)
        
        # --- Tabela de Alarmes ---
        self.Alarmlisten_tableWidget = QTableWidget(self)
        self.Alarmlisten_tableWidget.setObjectName("Alarmlisten_tableWidget")
        self.Alarmlisten_tableWidget.setColumnCount(5)
        self.Alarmlisten_tableWidget.setRowCount(0)
        headers = ["Nº.", "Horário", "Canal", "Tipo de Alarme", "Status"]
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(headers)
        self.Alarmlisten_tableWidget.horizontalHeader().setDefaultSectionSize(150)
        self.Alarmlisten_tableWidget.horizontalHeader().setMinimumSectionSize(50)
        self.Alarmlisten_tableWidget.verticalHeader().setVisible(False)
        self.mainLayout.addWidget(self.Alarmlisten_tableWidget)
        
        self.retranslateUi(AlarmWidget)
        QtCore.QMetaObject.connectSlotsByName(AlarmWidget)
        self.apply_stylesheet(AlarmWidget)
        
    def retranslateUi(self, AlarmWidget):
        _translate = QtCore.QCoreApplication.translate
        AlarmWidget.setWindowTitle(_translate("AlarmWidget", "Eventos de Alarme"))
        
    def apply_stylesheet(self, AlarmWidget):
        """Estilo moderno: fundo verde escuro, fontes brancas e botões modernos.
        Também define que tudo selecionado (itens da tabela e textos em campos) tenha fundo verde."""
        style = """
        QWidget {
            background-color: #004000;
            color: white;
            font-family: 'Segoe UI';
            font-weight: bold;
        }
        QGroupBox {
            border: 2px solid #3CB371;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 14px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
        }
        QLabel {
            font-size: 12px;
            color: white;
        }
        QLineEdit {
            background-color: #2E8B57;
            color: white;
            border: 1px solid #3CB371;
            border-radius: 4px;
            padding: 4px;
        }
        QLineEdit::selection {
            background-color: #228B22;
            color: white;
        }
        QPushButton {
            background-color: #3CB371;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #2E8B57;
        }
        QPushButton:pressed {
            background-color: #228B22;
        }
        QTableWidget {
            background-color: #002200;
            color: white;
            gridline-color: #3CB371;
            font: bold 10px;
        }
        QTableWidget::item:selected {
            background-color: #228B22;
            color: white;
        }
        QHeaderView::section {
            background-color: #3CB371;
            color: white;
            padding: 4px;
            font-weight: bold;
        }
        """
        AlarmWidget.setStyleSheet(style)


################################################################
# Lógica do programa – funcionalidades e callbacks
################################################################

class VideoMotionCallBackAlarmInfo:
    def __init__(self):
        self.time_str = ""
        self.channel_str = ""
        self.alarm_type = ""
        self.status_str = ""

    def get_alarm_info(self, alarm_info):
        self.time_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        self.channel_str = str(alarm_info.nChannelID)
        self.alarm_type = 'Evento - Video Motion'
        if alarm_info.nEventAction == 0:
            self.status_str = '(Pulse)'
        elif alarm_info.nEventAction == 1:
            self.status_str = '(Iniciar)'
        elif alarm_info.nEventAction == 2:
            self.status_str = '(Parar)'

class BackUpdateUIThread(QThread):
    update_date = pyqtSignal(int, object)
    def run(self):
        # Sua lógica de atualização – se necessário
        pass

@CB_FUNCTYPE(None, 
             c_long,       # lCommand
             C_LLONG,      # lLoginID
             POINTER(c_char),  # pBuf
             c_uint,       # dwBufLen
             POINTER(c_char),  # pchDVRIP
             c_long,       # nDVRPort
             c_int,        # bAlarmAckFlag
             c_long,       # nEventID
             C_LDWORD)     # dwUser
def MessCallback(lCommand, lLoginID, pBuf, dwBufLen, pchDVRIP, nDVRPort, bAlarmAckFlag, nEventID, dwUser):
    if lLoginID != hwnd.loginID:
        return
    if lCommand == SDK_ALARM_TYPE.EVENT_MOTIONDETECT:
        print('Enter MessCallback')
        alarm_info = cast(pBuf, POINTER(ALARM_MOTIONDETECT_INFO)).contents
        show_info = VideoMotionCallBackAlarmInfo()
        show_info.get_alarm_info(alarm_info)
        hwnd.backthread.update_date.emit(lCommand, show_info)


################################################################
# Widget Principal – substituindo QMainWindow por QWidget
################################################################

class StartListenWidget(QWidget, Ui_AlarmWidget):
    def __init__(self):
        super(StartListenWidget, self).__init__()
        self.setupUi(self)
        self.init_ui()
        
        # Variáveis do NetSDK e callbacks
        self.loginID = C_LLONG()
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)
        self.sdk.SetDVRMessCallBackEx1(MessCallback, 0)
        
        # Cria thread para atualização da UI
        self.backthread = BackUpdateUIThread()
        self.backthread.update_date.connect(self.update_ui)
        self.thread = QThread()
        self.backthread.moveToThread(self.thread)
        self.thread.started.connect(self.backthread.run)
        self.thread.start()
        
    def init_ui(self):
        # Valores padrão para os campos de conexão
        self.IP_lineEdit.setText("10.100.")
        self.Port_lineEdit.setText("37777")
        self.Username_lineEdit.setText("admin")
        self.Password_lineEdit.setText("@1234567")
        
        # Conecta os botões
        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.Logout_pushButton.clicked.connect(self.logout_btn_onclick)
        self.Alarmlisten_pushButton.clicked.connect(self.attach_btn_onclick)
        self.Stopalarmlisten_pushButton.clicked.connect(self.detach_btn_onclick)
        
        # Inicialmente, habilita apenas o botão de login
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(False)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.row = 0
        self.column = 0

    def login_btn_onclick(self):
        # Preenche os cabeçalhos da tabela
        headers = ['Nº', 'Horário', 'Canal', 'Tipo de Alarme', 'Status']
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(headers)
        ip = self.IP_lineEdit.text()
        port = int(self.Port_lineEdit.text())
        username = self.Username_lineEdit.text()
        password = self.Password_lineEdit.text()
        
        stuInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stuInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
        stuInParam.szIP = ip.encode()
        stuInParam.nPort = port
        stuInParam.szUserName = username.encode()
        stuInParam.szPassword = password.encode()
        stuInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP
        stuInParam.pCapParam = None
        
        stuOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stuOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)
        
        self.loginID, device_info, error_msg = self.sdk.LoginWithHighLevelSecurity(stuInParam, stuOutParam)
        if self.loginID != 0:
            self.setWindowTitle("(Alarme) - (OnLine)")
            self.Login_pushButton.setEnabled(False)
            self.Logout_pushButton.setEnabled(True)
            if int(device_info.nChanNum) > 0:
                self.Alarmlisten_pushButton.setEnabled(True)
        else:
            QMessageBox.about(self, "(Aviso)", "Falha! Verifique se os dados fornecidos estão corretos.")
    
    def logout_btn_onclick(self):
        if self.loginID == 0:
            return
        self.sdk.StopListen(self.loginID)
        result = self.sdk.Logout(self.loginID)
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(False)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.setWindowTitle("(Alarme) - (OffLine)")
        self.loginID = 0
        self.row = 0
        self.column = 0
        self.Alarmlisten_tableWidget.clear()
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['Nº', 'Horário', 'Canal', 'Tipo de Alarme', 'Status'])
    
    def attach_btn_onclick(self):
        self.row = 0
        self.column = 0
        self.Alarmlisten_tableWidget.clear()
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['Nº', 'Horário', 'Canal', 'Tipo de Alarme', 'Status'])
        result = self.sdk.StartListenEx(self.loginID)
        if result:
            QMessageBox.about(self, "(Aviso)", "Acompanhando Alarmes!")
            self.Stopalarmlisten_pushButton.setEnabled(True)
            self.Alarmlisten_pushButton.setEnabled(False)
        else:
            QMessageBox.about(self, "(Aviso)", "Erro: " + str(self.sdk.GetLastError()))
    
    def detach_btn_onclick(self):
        if self.loginID > 0:
            self.sdk.StopListen(self.loginID)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(True)
    
    def update_ui(self, lCommand, show_info):
        if lCommand == SDK_ALARM_TYPE.EVENT_MOTIONDETECT:
            if self.row > 499:
                self.Alarmlisten_tableWidget.clear()
                self.Alarmlisten_tableWidget.setRowCount(0)
                self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(
                    ['Nº', 'Horário', 'Canal', 'Tipo de Alarme', 'Status']
                )
                self.row = 0
                self.Alarmlisten_tableWidget.viewport().update()
            self.Alarmlisten_tableWidget.setRowCount(self.row + 1)
            item0 = QTableWidgetItem(str(self.row + 1))
            item1 = QTableWidgetItem(show_info.time_str)
            item2 = QTableWidgetItem(show_info.channel_str)
            item3 = QTableWidgetItem(show_info.alarm_type)
            item4 = QTableWidgetItem(show_info.status_str)
            self.Alarmlisten_tableWidget.setItem(self.row, 0, item0)
            self.Alarmlisten_tableWidget.setItem(self.row, 1, item1)
            self.Alarmlisten_tableWidget.setItem(self.row, 2, item2)
            self.Alarmlisten_tableWidget.setItem(self.row, 3, item3)
            self.Alarmlisten_tableWidget.setItem(self.row, 4, item4)
            self.row += 1
            self.Alarmlisten_tableWidget.viewport().update()
    
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("(Alarme) - (OffLine)")
    
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("(Alarme) - (OnLine)")
    
    def closeEvent(self, event):
        event.accept()
        if self.loginID:
            self.sdk.StopListen(self.loginID)
            self.sdk.Logout(self.loginID)
            self.loginID = 0
        self.sdk.Cleanup()
        self.Alarmlisten_tableWidget.clear()

################################################################
# Execução do programa
################################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = StartListenWidget()
    hwnd = widget  # Atribui para uso no callback
    widget.show()
    sys.exit(app.exec_())
