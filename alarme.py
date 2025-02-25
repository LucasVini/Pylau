import sys
import os
import time
import http.server
import socketserver
import threading
import requests
import socket
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QFormLayout, QMessageBox, QDialogButtonBox,
    QWidget, QGroupBox, QDateTimeEdit, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime, QPoint, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QPalette, QColor
from ctypes import *
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect
from NetSDK.SDK_Enum import EM_DEV_CFG_TYPE, EM_LOGIN_SPAC_CAP_TYPE, SDK_ALARM_TYPE
from NetSDK.SDK_Struct import (
    LOG_SET_PRINT_INFO,
    NET_TIME,
    C_LDWORD,
    C_LLONG,
    NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY,
    NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY,
    CB_FUNCTYPE,
    ALARM_MOTIONDETECT_INFO
)
from PyQt5 import QtCore, QtGui, QtWidgets  # Import QtWidgets
import datetime  # Import the datetime module


# --- Blur Effect Structures (Windows) ---
# (Keep the blur effect code if you intend to use it on other dialogs,
#  but it's not directly used by StartListenWidget anymore)
class ACCENTPOLICY(Structure):
    _fields_ = [
        ("AccentState", c_int),
        ("AccentFlags", c_int),
        ("GradientColor", c_uint),
        ("AnimationId", c_int),
    ]

class WINDOWCOMPOSITIONATTRIBDATA(Structure):
    _fields_ = [
        ("Attribute", c_int),
        ("Data", POINTER(ACCENTPOLICY)),
        ("SizeOfData", c_size_t),
    ]

def enable_blur_effect(hwnd):
    accent = ACCENTPOLICY()
    accent.AccentState = 4  # ACRYLICBLURBEHIND
    accent.GradientColor = 0x99000000  # Cor e opacidade
    accent.AccentFlags = 2
    accent_data = pointer(accent)
    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = 19
    data.Data = accent_data
    data.SizeOfData = sizeof(accent)
    ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, byref(data))


# No longer a global variable
# global wnd

# Removed Ui_TimeSyncDialog, as it's not relevant to this specific file.


class VideoMotionCallBackAlarmInfo:  # Corrected class name
    def __init__(self):
        self.time_str = ""
        self.channel_str = ""
        self.alarm_type = ""
        self.status_str = ""

    def get_alarm_info(self, alarm_info):
        self.time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.channel_str = str(alarm_info.nChannelID)  # Access nChannelID
        self.alarm_type = 'Evento - Video Motion'
        if alarm_info.nEventAction == 0:  # Use nEventAction
            self.status_str = '(Pulse)'
        elif alarm_info.nEventAction == 1:
            self.status_str = '(Iniciar)'
        elif alarm_info.nEventAction == 2:
            self.status_str = '(Parar)'

class AlarmUpdateThread(QThread):
    update_signal = pyqtSignal(int, object)  # Signal to send updates to the main thread

    def __init__(self, sdk, loginID):
        super().__init__()
        self.sdk = sdk
        self.loginID = loginID
        self.running = True

    def run(self):
        # Callback function *must* be defined *inside* the run method (or be a method of the class)
        @WINFUNCTYPE(None, C_LLONG, C_LLONG, POINTER(c_char), c_uint, POINTER(c_char), c_long, c_int, c_long, C_LDWORD)
        def MessCallback(lCommand, lLoginID, pBuf, dwBufLen, pchDVRIP, nDVRPort, bAlarmAckFlag, nEventID, dwUser):
            #print("Received alarm event!") # Debug print.  VERY IMPORTANT.
            if lLoginID != self.loginID:  # Verify that this message is for our logged in device.
                return

            if lCommand == SDK_ALARM_TYPE.EVENT_MOTIONDETECT: #Motion Detect
               # print("Motion detect event received!") #Debug
                try:
                    alarm_info = cast(pBuf, POINTER(ALARM_MOTIONDETECT_INFO)).contents
                    show_info = VideoMotionCallBackAlarmInfo() # Create object
                    show_info.get_alarm_info(alarm_info)
                    self.update_signal.emit(lCommand, show_info)  #Emit signal

                except Exception as e:
                    print(f"Erro ao processar o evento de detecção de movimento: {e}") #Translated


        # Set the message callback.  *MUST* be done inside the thread.
        self.sdk.SetDVRMessCallBackEx1(MessCallback, 0)

        # Start listening.  *MUST* be done after setting the callback
        self.sdk.StartListenEx(self.loginID)
        print("Ouvindo alarmes...") #Translated


        while self.running:
            time.sleep(0.1)  # Short sleep to prevent busy-waiting

    def stop(self):
        self.running = False
        self.wait()

class StartListenWidget(QWidget):  # Changed to QWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.init_ui()
        self.sdk = NetClient()
        self.sdk.InitEx(fDisConnect(self.DisConnectCallBack),0)  # Initialize with disconnect callback.
        self.sdk.SetAutoReconnect(fHaveReConnect(self.ReConnectCallBack),0) # Set reconnect callback
        self.loginID = C_LLONG(0)
        self.listening = False
        self.alarm_thread = None
        self.is_logged_in = False #Added to track login
        # self.sdk.SetDVRMessCallBackEx1(MessCallback, 0)  # Callback is set in the thread now.


    def setupUi(self, AlarmWidget):
        AlarmWidget.setObjectName("AlarmWidget")
        # Fixed size is usually a bad idea for main windows.  Consider using layouts to make it resizable.
        AlarmWidget.setFixedSize(800, 600)
        self.mainLayout = QVBoxLayout(AlarmWidget)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(12)
        # GroupBox de Conexão
        self.groupBoxConexao = QGroupBox("Login no Gravador")
        self.groupBoxConexao.setObjectName("groupBoxConexao")
        self.groupBoxConexao.setMinimumWidth(500)  # Set minimum width, no maximum

        formLayout = QFormLayout(self.groupBoxConexao)
        formLayout.setContentsMargins(10, 15, 10, 10)
        formLayout.setSpacing(8)
        self.IP_lineEdit = QLineEdit(self.groupBoxConexao)
        self.IP_lineEdit.setObjectName("IP_lineEdit")
        self.IP_lineEdit.setPlaceholderText("ex: 192.168.1.108")  # Add placeholder
        formLayout.addRow("IP:", self.IP_lineEdit)
        self.Port_lineEdit = QLineEdit(self.groupBoxConexao)
        self.Port_lineEdit.setObjectName("Port_lineEdit")
        self.Port_lineEdit.setPlaceholderText("ex: 37777")  # Add placeholder
        formLayout.addRow("Porta:", self.Port_lineEdit)
        self.Username_lineEdit = QLineEdit(self.groupBoxConexao)
        self.Username_lineEdit.setObjectName("Username_lineEdit")
        self.Username_lineEdit.setPlaceholderText("ex: admin")
        formLayout.addRow("Usuário:", self.Username_lineEdit)
        self.Password_lineEdit = QLineEdit(self.groupBoxConexao)
        self.Password_lineEdit.setEchoMode(QLineEdit.Password)
        self.Password_lineEdit.setObjectName("Password_lineEdit")
        self.Password_lineEdit.setPlaceholderText("Senha")
        formLayout.addRow("Senha:", self.Password_lineEdit)


        # --- Botões de Login e Logout (Horizontal Layout) ---
        btnLayoutLogin = QHBoxLayout()  # Horizontal layout for login/logout buttons
        self.Login_pushButton = QPushButton("Login")
        self.Login_pushButton.setObjectName("Login_pushButton")
        self.Logout_pushButton = QPushButton("Logout")
        self.Logout_pushButton.setObjectName("Logout_pushButton")
        self.Logout_pushButton.setEnabled(False)  # Initially disabled
        btnLayoutLogin.addWidget(self.Login_pushButton)
        btnLayoutLogin.addWidget(self.Logout_pushButton)
        formLayout.addRow(btnLayoutLogin)  # Add the button layout to the form

        # --- GroupBox de Controle de Alarme ---
        self.groupBoxControl = QGroupBox("Controles")
        self.groupBoxControl.setObjectName("groupBoxControl")
        vboxControl = QVBoxLayout(self.groupBoxControl)
        vboxControl.setContentsMargins(10, 15, 10, 10)
        vboxControl.setSpacing(10)

        self.Alarmlisten_pushButton = QPushButton("Monitorar Alarme")
        self.Alarmlisten_pushButton.setObjectName("Alarmlisten_pushButton")
        self.Alarmlisten_pushButton.setEnabled(False) #Disabled by default.

        self.Stopalarmlisten_pushButton = QPushButton("Parar de Monitorar")
        self.Stopalarmlisten_pushButton.setObjectName("Stopalarmlisten_pushButton")
        self.Stopalarmlisten_pushButton.setEnabled(False) #Disabled by default

        vboxControl.addWidget(self.Alarmlisten_pushButton)
        vboxControl.addWidget(self.Stopalarmlisten_pushButton)

        hbox = QHBoxLayout()
        hbox.addWidget(self.groupBoxConexao)
        hbox.addWidget(self.groupBoxControl)
        self.mainLayout.addLayout(hbox)


        # --- Tabela de Alarmes ---
        self.Alarmlisten_tableWidget = QTableWidget(self)
        self.Alarmlisten_tableWidget.setObjectName("Alarmlisten_tableWidget")
        self.Alarmlisten_tableWidget.setColumnCount(5)
        self.Alarmlisten_tableWidget.setRowCount(0)
        headers = ["Nº", "Horário", "Canal", "Tipo de Alarme", "Status"]
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(headers)
        self.Alarmlisten_tableWidget.horizontalHeader().setStretchLastSection(True)  # Stretches last section
        self.mainLayout.addWidget(self.Alarmlisten_tableWidget)

        self.retranslateUi(AlarmWidget)
        QtCore.QMetaObject.connectSlotsByName(AlarmWidget)
        self.apply_stylesheet(AlarmWidget)

        # --- Connect signals and slots ---
        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.Logout_pushButton.clicked.connect(self.logout_btn_onclick)
        self.Alarmlisten_pushButton.clicked.connect(self.attach_btn_onclick)
        self.Stopalarmlisten_pushButton.clicked.connect(self.detach_btn_onclick)


    def retranslateUi(self, AlarmWidget):
      _translate = QtCore.QCoreApplication.translate
      AlarmWidget.setWindowTitle(_translate("AlarmWidget", "Eventos de Alarme"))
      #self.label.setText(_translate("AlarmWidget", "<html><head/><body><p align=\"center\">Serviço de Notificação de Alarmes</p></body></html>"))
      #self.pushButton.setText(_translate("AlarmWidget", "Iniciar"))
      #self.pushButton_2.setText(_translate("AlarmWidget", "Parar"))
      self.groupBoxConexao.setTitle(_translate("AlarmWidget", "Login no Gravador"))
      #self.label_2.setText(_translate("AlarmWidget", "Endereço IP"))
      #self.label_3.setText(_translate("AlarmWidget", "Porta"))
      #self.label_4.setText(_translate("AlarmWidget", "Usuário"))
      #self.label_5.setText(_translate("AlarmWidget", "Senha"))
      self.Login_pushButton.setText(_translate("AlarmWidget", "Login"))
      self.Logout_pushButton.setText(_translate("AlarmWidget", "Logout"))
      self.groupBoxControl.setTitle(_translate("AlarmWidget", "Controles de Alarme"))
      self.Alarmlisten_pushButton.setText(_translate("AlarmWidget", "Monitorar Alarme"))
      self.Stopalarmlisten_pushButton.setText(_translate("AlarmWidget", "Parar Monitoramento"))

    def apply_stylesheet(self, AlarmWidget):
      """Applies a stylesheet for a dark green theme."""
      style = """
      QWidget {
          background-color: #004000; /* Dark green background */
          color: white;              /* White text */
          font-family: 'Segoe UI';
          font-weight: bold;
      }
      QGroupBox {
          border: 2px solid #3CB371; /* Medium sea green border */
          border-radius: 5px;
          margin-top: 10px; /* Space for title */
          font-size: 14px; /* Larger title font */

      }
      QGroupBox::title {
          subcontrol-origin: margin;
          subcontrol-position: top left;
          padding: 0 3px;
          color: white;
      }
      QLabel {
          font-size: 12px;
          color: white;
      }
      QLineEdit {
          background-color: #3CB371; /* Medium sea green */
          color: white;
          border: 1px solid #2E8B57; /* Sea green border*/
          border-radius: 4px;
          padding: 2px;
      }
      QPushButton {
          background-color: #3CB371; /* Medium sea green */
          color: white;
          border: 1px solid #2E8B57;
          border-radius: 4px;
          padding: 5px 10px;
          font-size: 12px;
      }
      QPushButton:hover {
          background-color: #2E8B57; /* Sea green on hover*/
      }
      QPushButton:pressed {
          background-color: #228B22; /* Dark green on press */
      }
        QPushButton:disabled{
          background-color:gray;
          color: darkgray;
          border: 1px solid #2E8B57;
          border-radius: 4px;
          padding: 5px 10px;
          font-size: 12px;
      }
      QTableWidget {
          background-color: #002200;
          color: white;
          gridline-color: #3CB371;
          font: bold 10px;
      }

      QTableWidget::item:selected{
        background-color: #228B22;
        color: white;
      }

      QHeaderView::section {
          background-color: #3CB371; /* Medium sea green */
          color: white;
          padding: 4px;
          font-weight: bold;
      }
      """
      AlarmWidget.setStyleSheet(style)

    def init_ui(self):
      # Placeholder texts and initial button states
      self.IP_lineEdit.setPlaceholderText("e.g., 192.168.1.108")
      self.Port_lineEdit.setPlaceholderText("e.g., 37777")
      self.Username_lineEdit.setPlaceholderText("e.g., admin")
      self.Password_lineEdit.setPlaceholderText("e.g., @1234567")

      self.Login_pushButton.setEnabled(True)
      self.Logout_pushButton.setEnabled(False)
      self.Alarmlisten_pushButton.setEnabled(False)
      self.Stopalarmlisten_pushButton.setEnabled(False)
      self.row = 0
      self.column = 0
      self.Alarmlisten_tableWidget.clear()
      self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['Nº', 'Horário', 'Canal', 'Tipo de Alarme', 'Status'])

      self.setStyleSheet(STYLE_SHEET) #Applying global

    def login_btn_onclick(self):
      if not self.is_logged_in:
        # Login
        ip = self.IP_lineEdit.text().strip()  # Get the IP address from the QLineEdit
        port_str = self.Port_lineEdit.text().strip()
        username = self.Username_lineEdit.text().strip()
        password = self.Password_lineEdit.text().strip()

        if not ip or not port_str or not username or not password:
            QMessageBox.warning(self, "Erro", "Por favor, preencha todos os campos.") # Translated
            return

        try:
            port = int(port_str)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Número de porta inválido.") # Translated
            return

        stuInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stuInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
        stuInParam.szIP = ip.encode('utf-8')  # Encode to bytes
        stuInParam.nPort = port
        stuInParam.szUserName = username.encode('utf-8')
        stuInParam.szPassword = password.encode('utf-8')
        stuInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP
        stuInParam.pCapParam = None

        stuOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stuOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

        self.loginID, device_info, error = self.sdk.LoginWithHighLevelSecurity(stuInParam, stuOutParam)

        if self.loginID:
            self.is_logged_in = True
            self.Login_pushButton.setText("✓ Login")
            self.setWindowTitle("Alarme (Online)")
            self.Login_pushButton.setEnabled(False)
            self.Logout_pushButton.setEnabled(True)
            self.Alarmlisten_pushButton.setEnabled(True)

        else:
            QMessageBox.critical(self, "Falha no Login", f"Não foi possível fazer login. Código de erro: {error}") # Translated

      #Logout isn't required here, but kept for consistency.
      else:
        self.logout_btn_onclick()


    def logout_btn_onclick(self):
        if self.is_logged_in:
            self.detach_btn_onclick()  # Stop alarm monitoring *before* logout
            if self.sdk.Logout(self.loginID):

                self.Login_pushButton.setText("Login")
                self.setWindowTitle("Alarme (Offline)")
                self.Login_pushButton.setEnabled(True)
                self.Logout_pushButton.setEnabled(False)
                self.Alarmlisten_pushButton.setEnabled(False)
                self.Stopalarmlisten_pushButton.setEnabled(False)
                self.is_logged_in = False
                self.loginID = C_LLONG(0) #Reset

                # Clear table
                self.Alarmlisten_tableWidget.clearContents()
                self.Alarmlisten_tableWidget.setRowCount(0)  # Reset row count
                self.row = 0  # Reset row index.
                self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['Nº', 'Horário', 'Canal', 'Tipo de Alarme', 'Status'])
            else:
                QMessageBox.critical(self, "Falha no Logout", "Não foi possível fazer logout.") # Translated

    def attach_btn_onclick(self):
        if not self.listening and self.is_logged_in:
            self.alarm_thread = AlarmUpdateThread(self.sdk, self.loginID)
            self.alarm_thread.update_signal.connect(self.update_ui) #Connect signal to update
            self.alarm_thread.start()
            self.listening = True
            self.Alarmlisten_pushButton.setEnabled(False)
            self.Stopalarmlisten_pushButton.setEnabled(True)
            QMessageBox.information(self, "Monitoramento de Alarme", "Monitoramento de alarmes iniciado.") # Translated
            self.Alarmlisten_tableWidget.clearContents()
            self.Alarmlisten_tableWidget.setRowCount(0) #Reset row count
            self.row = 0

        elif not self.is_logged_in:
            QMessageBox.warning(self, "Não Logado", "Por favor, faça login primeiro.") # Translated

    def detach_btn_onclick(self):
        if self.listening and self.alarm_thread:
            self.sdk.StopListen(self.loginID) # Stop listening on the SDK side.
            self.alarm_thread.stop()  # Stop the thread
            self.alarm_thread = None # Clean up
            self.listening = False
            self.Alarmlisten_pushButton.setEnabled(True)
            self.Stopalarmlisten_pushButton.setEnabled(False)
            QMessageBox.information(self, "Monitoramento de Alarme", "Monitoramento de alarmes parado.") # Translated

    def update_ui(self, lCommand, show_info):
        if lCommand == SDK_ALARM_TYPE.EVENT_MOTIONDETECT:
            if self.row >= 500: #Limit rows to 500
              self.Alarmlisten_tableWidget.clearContents() #Clear contents
              self.Alarmlisten_tableWidget.setRowCount(0) #Reset Row count
              self.row = 0 # Reset row index
            self.Alarmlisten_tableWidget.insertRow(self.row) #Always add to end

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
            self.Alarmlisten_tableWidget.scrollToBottom() # Scroll to the newest item
            self.row += 1


    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("Alarme (Offline)")
        # Handle disconnection (e.g., disable buttons, show a message)
        # You might want to run this on the main thread using a signal/slot
        QMessageBox.warning(self, "Desconectado", "Perda de conexão com o dispositivo.") # Translated
        self.Login_pushButton.setEnabled(True)  # Re-enable login on disconnect
        self.Logout_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(False)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.is_logged_in = False


    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
         self.setWindowTitle("Alarme (Online)")
        # Handle reconnection (e.g., update the UI)
        # You might want to run this on the main thread
         QMessageBox.information(self, "Reconectado", "Reconexão com o dispositivo bem-sucedida.") # Translated


    def closeEvent(self, event):
        self.detach_btn_onclick()  # Stop listening if running
        if self.is_logged_in:
          self.sdk.Logout(self.loginID)
        self.sdk.Cleanup()
        event.accept()


# Global stylesheet
STYLE_SHEET = """
/* Your global stylesheet here */
"""

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app.setStyleSheet(STYLE_SHEET)  # Set the global stylesheet
    widget = StartListenWidget()
    widget.show()
    sys.exit(app.exec_())
