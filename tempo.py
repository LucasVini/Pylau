import os
import sys
from ctypes import *
from datetime import datetime, timedelta

import ntplib  # Certifique-se de ter o ntplib instalado (pip install ntplib)
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QDialog, QPushButton, QVBoxLayout, QGroupBox, QLabel,
    QLineEdit, QDateTimeEdit, QFormLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime
from PyQt5.QtGui import QFont
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect
from NetSDK.SDK_Enum import EM_DEV_CFG_TYPE, EM_LOGIN_SPAC_CAP_TYPE
from NetSDK.SDK_Struct import (
    LOG_SET_PRINT_INFO, NET_TIME, C_LDWORD, C_LLONG,
    NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY, NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY, CB_FUNCTYPE,
)

# Variável global para log (não mais utilizado, pois a seção de logs foi removida)
file = os.path.join(os.getcwd(), "sdk_log.log")

@CB_FUNCTYPE(c_int, c_char_p, c_uint, C_LDWORD)
def SDKLogCallBack(szLogBuffer, nLogSize, dwUser):
    try:
        with open(file, "a") as f:
            f.write(szLogBuffer.decode())
    except Exception as e:
        print(e)
    return 1

class Ui_TimeSyncDialog(object):
    def setupUi(self, TimeSyncDialog):
        TimeSyncDialog.setObjectName("TimeSyncDialog")
        TimeSyncDialog.resize(600, 400)
        
        # Layout principal vertical
        self.mainLayout = QVBoxLayout(TimeSyncDialog)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(10)
        
        # --- GroupBox Conexão ---
        self.groupBoxConexao = QGroupBox(TimeSyncDialog)
        self.groupBoxConexao.setObjectName("groupBoxConexao")
        conexaoLayout = QFormLayout(self.groupBoxConexao)
        conexaoLayout.setContentsMargins(10, 10, 10, 10)
        conexaoLayout.setSpacing(8)
        
        self.IP_lineEdit = QLineEdit(self.groupBoxConexao)
        self.IP_lineEdit.setObjectName("IP_lineEdit")
        conexaoLayout.addRow("Endereço IP:", self.IP_lineEdit)
        
        self.Port_lineEdit = QLineEdit(self.groupBoxConexao)
        self.Port_lineEdit.setObjectName("Port_lineEdit")
        conexaoLayout.addRow("Porta:", self.Port_lineEdit)
        
        self.Name_lineEdit = QLineEdit(self.groupBoxConexao)
        self.Name_lineEdit.setObjectName("Name_lineEdit")
        conexaoLayout.addRow("Usuário:", self.Name_lineEdit)
        
        self.Pwd_lineEdit = QLineEdit(self.groupBoxConexao)
        self.Pwd_lineEdit.setEchoMode(QLineEdit.Password)
        self.Pwd_lineEdit.setObjectName("Pwd_lineEdit")
        conexaoLayout.addRow("Senha:", self.Pwd_lineEdit)
        
        self.Login_pushButton = QPushButton(self.groupBoxConexao)
        self.Login_pushButton.setObjectName("Login_pushButton")
        conexaoLayout.addRow("", self.Login_pushButton)
        
        # --- GroupBox Sincronização de Horário ---
        self.groupBoxHorario = QGroupBox(TimeSyncDialog)
        self.groupBoxHorario.setObjectName("groupBoxHorario")
        horarioLayout = QFormLayout(self.groupBoxHorario)
        horarioLayout.setContentsMargins(10, 10, 10, 10)
        horarioLayout.setSpacing(8)
        
        self.Time_dateTimeEdit = QDateTimeEdit(self.groupBoxHorario)
        # Aumenta o tamanho e torna a fonte em negrito
        self.Time_dateTimeEdit.setMinimumHeight(50)
        self.Time_dateTimeEdit.setFont(QFont("Arial", 16, QFont.Bold))
        self.Time_dateTimeEdit.setDateTime(QDateTime(QDate.currentDate(), QTime.currentTime()))
        self.Time_dateTimeEdit.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        horarioLayout.addRow("Horário do Gravador:", self.Time_dateTimeEdit)
        
        btnLayoutHorario = QHBoxLayout()
        self.GetTime_pushButton = QPushButton(self.groupBoxHorario)
        self.GetTime_pushButton.setObjectName("GetTime_pushButton")
        self.SetTime_pushButton = QPushButton(self.groupBoxHorario)
        self.SetTime_pushButton.setObjectName("SetTime_pushButton")
        self.SyncNTP_pushButton = QPushButton(self.groupBoxHorario)
        self.SyncNTP_pushButton.setObjectName("SyncNTP_pushButton")
        btnLayoutHorario.addWidget(self.GetTime_pushButton)
        btnLayoutHorario.addWidget(self.SetTime_pushButton)
        btnLayoutHorario.addWidget(self.SyncNTP_pushButton)
        horarioLayout.addRow("", btnLayoutHorario)
        
        # --- GroupBox Reinicialização ---
        self.groupBoxRestart = QGroupBox(TimeSyncDialog)
        self.groupBoxRestart.setObjectName("groupBoxRestart")
        restartLayout = QHBoxLayout(self.groupBoxRestart)
        restartLayout.setContentsMargins(10, 10, 10, 10)
        self.Restart_pushButton = QPushButton(self.groupBoxRestart)
        self.Restart_pushButton.setObjectName("Restart_pushButton")
        restartLayout.addWidget(self.Restart_pushButton)
        
        # Adiciona os group boxes ao layout principal (removida a seção de logs)
        self.mainLayout.addWidget(self.groupBoxConexao)
        self.mainLayout.addWidget(self.groupBoxHorario)
        self.mainLayout.addWidget(self.groupBoxRestart)
        
        self.retranslateUi(TimeSyncDialog)
        QtCore.QMetaObject.connectSlotsByName(TimeSyncDialog)
        self.apply_stylesheet(TimeSyncDialog)
    
    def retranslateUi(self, TimeSyncDialog):
        _translate = QtCore.QCoreApplication.translate
        TimeSyncDialog.setWindowTitle(_translate("TimeSyncDialog", "Time Sync"))
        self.groupBoxConexao.setTitle(_translate("TimeSyncDialog", "Conexão com o Gravador"))
        self.Login_pushButton.setText(_translate("TimeSyncDialog", "Login"))
        self.groupBoxHorario.setTitle(_translate("TimeSyncDialog", "Sincronização de Horário"))
        self.GetTime_pushButton.setText(_translate("TimeSyncDialog", "Obter Horário"))
        self.SetTime_pushButton.setText(_translate("TimeSyncDialog", "Definir Horário"))
        self.SyncNTP_pushButton.setText(_translate("TimeSyncDialog", "Sincronizar NTP"))
        self.groupBoxRestart.setTitle(_translate("TimeSyncDialog", "Reinicialização Remota"))
        self.Restart_pushButton.setText(_translate("TimeSyncDialog", "Reiniciar Gravador"))
    
    def apply_stylesheet(self, TimeSyncDialog):
        """Aplica um stylesheet com tema verde escuro, fontes brancas e botões no estilo anterior."""
        style = """
        QDialog {
            background-color: #004000;
            color: white;
        }
        QGroupBox {
            border: 2px solid #3CB371;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 14px;
            font-weight: bold;
            color: white;
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
        QLineEdit, QDateTimeEdit {
            background-color: #3CB371;
            color: white;
            border: 1px solid #2E8B57;
            border-radius: 4px;
            padding: 4px;
            font-size: 12px;
        }
        /* Botões com estilo conforme programa anterior */
        QPushButton {
            background-color: #3CB371;
            color: white;
            border: 1px solid #2E8B57;
            border-radius: 4px;
            padding: 6px 12px;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #2E8B57;
        }
        QPushButton:pressed {
            background-color: #228B22;
        }
        """
        TimeSyncDialog.setStyleSheet(style)

class TimeSyncDialog(QDialog, Ui_TimeSyncDialog):
    def __init__(self, parent=None):
        super(TimeSyncDialog, self).__init__(parent)
        self.setupUi(self)
        self._init_ui()
        
        # Variáveis e callbacks do NetSDK
        self.loginID = C_LLONG()
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)
        
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)
        self.is_logged_in = False

    def _init_ui(self):
        # Valores padrão para os campos de conexão
        self.IP_lineEdit.setText("10.100.")
        self.Port_lineEdit.setText("37777")
        self.Name_lineEdit.setText("admin")
        self.Pwd_lineEdit.setText("@1234567")
        
        # Conexões dos botões
        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.GetTime_pushButton.clicked.connect(self.gettime_btn_onclick)
        self.SetTime_pushButton.clicked.connect(self.settime_btn_onclick)
        self.SyncNTP_pushButton.clicked.connect(self.sync_ntp_btn_onclick)
        self.Restart_pushButton.clicked.connect(self.restart_btn_onclick)
        
        # Inicialmente, desabilita os botões que exigem login
        self.enable_buttons(False)
    
    def enable_buttons(self, enable):
        self.GetTime_pushButton.setEnabled(enable)
        self.SetTime_pushButton.setEnabled(enable)
        self.SyncNTP_pushButton.setEnabled(enable)
        self.Restart_pushButton.setEnabled(enable)
    
    def login_btn_onclick(self):
        if not self.is_logged_in:
            ip = self.IP_lineEdit.text().strip()
            port_text = self.Port_lineEdit.text().strip()
            username = self.Name_lineEdit.text().strip()
            password = self.Pwd_lineEdit.text().strip()
            if not ip or not port_text or not username or not password:
                QMessageBox.warning(self, "Aviso", "Preencha todos os campos de conexão.")
                return
            try:
                port = int(port_text)
            except ValueError:
                QMessageBox.warning(self, "Aviso", "Porta inválida.")
                return
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
            
            self.loginID, device_info, error_msg = self.sdk.LoginWithHighLevelSecurity(
                stuInParam, stuOutParam
            )
            if self.loginID != 0:
                self.setWindowTitle("Time Sync - (Online)")
                self.Login_pushButton.setText("Logout")
                self.enable_buttons(True)
                self.is_logged_in = True
            else:
                QMessageBox.about(self, "Aviso", error_msg)
        else:
            result = self.sdk.Logout(self.loginID)
            if result:
                self.setWindowTitle("Time Sync - (Offline)")
                self.Login_pushButton.setText("Login")
                self.loginID = 0
                self.enable_buttons(False)
                self.is_logged_in = False
    
    def gettime_btn_onclick(self):
        device_time = NET_TIME()
        result = self.sdk.GetDevConfig(
            self.loginID, int(EM_DEV_CFG_TYPE.TIMECFG), -1, device_time, sizeof(NET_TIME)
        )
        if not result:
            QMessageBox.about(self, "Aviso", self.sdk.GetLastErrorMessage())
        else:
            dt = QDateTime(
                QDate(device_time.dwYear, device_time.dwMonth, device_time.dwDay),
                QTime(device_time.dwHour, device_time.dwMinute, device_time.dwSecond)
            )
            self.Time_dateTimeEdit.setDateTime(dt)
    
    def settime_btn_onclick(self):
        device_date = self.Time_dateTimeEdit.date()
        device_time = self.Time_dateTimeEdit.time()
        deviceDateTime = NET_TIME()
        deviceDateTime.dwYear = device_date.year()
        deviceDateTime.dwMonth = device_date.month()
        deviceDateTime.dwDay = device_date.day()
        deviceDateTime.dwHour = device_time.hour()
        deviceDateTime.dwMinute = device_time.minute()
        deviceDateTime.dwSecond = device_time.second()
        
        result = self.sdk.SetDevConfig(
            self.loginID, int(EM_DEV_CFG_TYPE.TIMECFG), -1, deviceDateTime, sizeof(NET_TIME)
        )
        if not result:
            QMessageBox.about(self, "Aviso", self.sdk.GetLastErrorMessage())
    
    def sync_ntp_btn_onclick(self):
        try:
            client = ntplib.NTPClient()
            response = client.request('pool.ntp.org')
            # Obtém o horário UTC a partir da resposta
            utc_time = datetime.utcfromtimestamp(response.tx_time)
            # Ajusta para o horário oficial de Brasília (UTC-3)
            brasilia_time = utc_time - timedelta(hours=3)
            qdt = QDateTime(brasilia_time.year, brasilia_time.month, brasilia_time.day,
                            brasilia_time.hour, brasilia_time.minute, brasilia_time.second)
            self.Time_dateTimeEdit.setDateTime(qdt)
            # Envia o horário para o gravador
            self.settime_btn_onclick()
            QMessageBox.information(self, "Sincronização NTP", "Horário sincronizado com o NTP com sucesso.")
        except Exception as e:
            QMessageBox.warning(self, "Erro NTP", f"Falha ao sincronizar horário via NTP: {e}")
    
    def restart_btn_onclick(self):
        result = self.sdk.RebootDev(self.loginID)
        if not result:
            QMessageBox.about(self, "Aviso", self.sdk.GetLastErrorMessage())
        else:
            QMessageBox.about(self, "Aviso", "Reinicialização efetuada com sucesso.")
    
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("Time Sync - (Offline)")
        self.enable_buttons(False)
        self.is_logged_in = False
    
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("Time Sync - (Online)")
        self.enable_buttons(True)
        self.is_logged_in = True
    
    def closeEvent(self, event):
        if self.loginID:
            self.sdk.Logout(self.loginID)
        self.sdk.Cleanup()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = TimeSyncDialog()
    dialog.show()
    sys.exit(app.exec_())
