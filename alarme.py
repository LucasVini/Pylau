from PyQt5.QtWidgets import QMainWindow, QMessageBox, QHeaderView, QAbstractItemView, QApplication, QGroupBox, QMenu,QTableWidgetItem
from PyQt5.QtCore import Qt,QThread,pyqtSignal
import sys
import datetime
import types
import time

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'AlarmListenUI.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Struct import *
from NetSDK.SDK_Enum import *
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect, CB_FUNCTYPE



from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(804, 615)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 531, 101))
        self.groupBox.setObjectName("groupBox")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(3, 30, 61, 20))
        self.label.setObjectName("label")
        self.IP_lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.IP_lineEdit.setGeometry(QtCore.QRect(110, 30, 121, 20))
        self.IP_lineEdit.setObjectName("IP_lineEdit")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(250, 30, 61, 20))
        self.label_2.setObjectName("label_2")
        self.Port_lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.Port_lineEdit.setGeometry(QtCore.QRect(320, 30, 113, 20))
        self.Port_lineEdit.setObjectName("Port_lineEdit")
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(3, 60, 101, 20))
        self.label_3.setObjectName("label_3")
        self.Username_lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.Username_lineEdit.setGeometry(QtCore.QRect(110, 60, 121, 20))
        self.Username_lineEdit.setObjectName("Username_lineEdit")
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_4.setGeometry(QtCore.QRect(230, 60, 91, 20))
        self.label_4.setObjectName("label_4")
        self.Password_lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.Password_lineEdit.setGeometry(QtCore.QRect(320, 60, 113, 20))
        self.Password_lineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.Password_lineEdit.setObjectName("Password_lineEdit")
        self.Login_pushButton = QtWidgets.QPushButton(self.groupBox)
        self.Login_pushButton.setGeometry(QtCore.QRect(440, 20, 91, 31))
        self.Login_pushButton.setObjectName("Login_pushButton")
        self.Logout_pushButton = QtWidgets.QPushButton(self.groupBox)
        self.Logout_pushButton.setGeometry(QtCore.QRect(440, 60, 91, 31))
        self.Logout_pushButton.setObjectName("Logout_pushButton")
        self.Alarmlisten_tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.Alarmlisten_tableWidget.setGeometry(QtCore.QRect(10, 120, 791, 441))
        self.Alarmlisten_tableWidget.setObjectName("Alarmlisten_tableWidget")
        self.Alarmlisten_tableWidget.setColumnCount(5)
        self.Alarmlisten_tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(9)
        item.setFont(font)
        self.Alarmlisten_tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.Alarmlisten_tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.Alarmlisten_tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.Alarmlisten_tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.Alarmlisten_tableWidget.setHorizontalHeaderItem(4, item)
        self.Alarmlisten_tableWidget.horizontalHeader().setDefaultSectionSize(150)
        self.Alarmlisten_tableWidget.horizontalHeader().setMinimumSectionSize(50)
        self.Alarmlisten_tableWidget.horizontalHeader().setStretchLastSection(False)
        self.Alarmlisten_tableWidget.verticalHeader().setVisible(False)
        self.Alarmlisten_tableWidget.verticalHeader().setSortIndicatorShown(False)
        self.Alarmlisten_tableWidget.verticalHeader().setStretchLastSection(False)
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setGeometry(QtCore.QRect(540, 10, 261, 101))
        self.groupBox_2.setObjectName("groupBox_2")
        self.Alarmlisten_pushButton = QtWidgets.QPushButton(self.groupBox_2)
        self.Alarmlisten_pushButton.setGeometry(QtCore.QRect(60, 20, 161, 31))
        self.Alarmlisten_pushButton.setObjectName("Alarmlisten_pushButton")
        self.Stopalarmlisten_pushButton = QtWidgets.QPushButton(self.groupBox_2)
        self.Stopalarmlisten_pushButton.setGeometry(QtCore.QRect(60, 60, 161, 31))
        self.Stopalarmlisten_pushButton.setObjectName("Stopalarmlisten_pushButton")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 804, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Eventos de Alarme"))
        self.groupBox.setTitle(_translate("MainWindow", "(Login no Gravador)"))
        self.label.setText(_translate("MainWindow", "(IP)"))
        self.label_2.setText(_translate("MainWindow", "(Porta)"))
        self.label_3.setText(_translate("MainWindow", "(Usuário)"))
        self.label_4.setText(_translate("MainWindow", "(Senha)"))
        self.Login_pushButton.setText(_translate("MainWindow", "(Login)"))
        self.Logout_pushButton.setText(_translate("MainWindow", "(Logout)"))
        item = self.Alarmlisten_tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "(Nº.)"))
        item = self.Alarmlisten_tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "(Tempo)"))
        item = self.Alarmlisten_tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "(Canal)"))
        item = self.Alarmlisten_tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "(Tipo de Alarme)"))
        item = self.Alarmlisten_tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "(Status)"))
        self.groupBox_2.setTitle(_translate("MainWindow", "(Seguir)"))
        self.Alarmlisten_pushButton.setText(_translate("MainWindow", "(Seguir Alarme)"))
        self.Stopalarmlisten_pushButton.setText(_translate("MainWindow", "(Parar de Seguir)"))



global hwnd

class VideoMotionCallBackAlarmInfo:
    def __init__(self):
        self.time_str = ""
        self.channel_str = ""
        self.alarm_type = ""
        self.status_str = ""

    def get_alarm_info(self, alarm_info):
        self.time_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        self.channel_str = str(alarm_info.nChannelID)
        self.alarm_type = '（Evento VideoMotion)'
        if (alarm_info.nEventAction == 0):
            self.status_str = '(Pulse)'
        elif (alarm_info.nEventAction == 1):
            self.status_str = '(Iniciar)'
        elif (alarm_info.nEventAction == 2):
            self.status_str = '(Parar)'

class BackUpdateUIThread(QThread):
    # 通过类成员对象定义信号
    update_date = pyqtSignal(int, object)

    # 处理业务逻辑
    def run(self):
        pass

@CB_FUNCTYPE(None, c_long, C_LLONG, POINTER(c_char), C_DWORD, POINTER(c_char), c_long, c_int, c_long, C_LDWORD)
def MessCallback(lCommand, lLoginID, pBuf, dwBufLen ,pchDVRIP, nDVRPort, bAlarmAckFlag, nEventID, dwUser):
    if(lLoginID != hwnd.loginID):
        return
    if(lCommand == SDK_ALARM_TYPE.EVENT_MOTIONDETECT):
        print('Enter MessCallback')
        alarm_info = cast(pBuf, POINTER(ALARM_MOTIONDETECT_INFO)).contents
        show_info = VideoMotionCallBackAlarmInfo()
        show_info.get_alarm_info(alarm_info)
        hwnd.backthread.update_date.emit(lCommand, show_info)

class StartListenWnd(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(StartListenWnd, self).__init__()
        self.setupUi(self)
        # 界面初始化
        self.init_ui()

        # NetSDK用到的相关变量和回调
        self.loginID = C_LLONG()
        self.m_DisConnectCallBack = fDisConnect(self.DisConnectCallBack)
        self.m_ReConnectCallBack = fHaveReConnect(self.ReConnectCallBack)

        # 获取NetSDK对象并初始化
        self.sdk = NetClient()
        self.sdk.InitEx(self.m_DisConnectCallBack)
        self.sdk.SetAutoReconnect(self.m_ReConnectCallBack)

        #设置报警回调函数
        self.sdk.SetDVRMessCallBackEx1(MessCallback,0)

        # 创建线程
        self.backthread = BackUpdateUIThread()
        # 连接信号
        self.backthread.update_date.connect(self.update_ui)
        self.thread = QThread()
        self.backthread.moveToThread(self.thread)
        # 开始线程
        self.thread.started.connect(self.backthread.run)
        self.thread.start()


    def init_ui(self):
        self.IP_lineEdit.setText('10.100.x.x')
        self.Port_lineEdit.setText('37777')
        self.Username_lineEdit.setText('admin')
        self.Password_lineEdit.setText('@1234567')
        self.Login_pushButton.clicked.connect(self.login_btn_onclick)
        self.Logout_pushButton.clicked.connect(self.logout_btn_onclick)

        self.Alarmlisten_pushButton.clicked.connect(self.attach_btn_onclick)
        self.Stopalarmlisten_pushButton.clicked.connect(self.detach_btn_onclick)
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(False)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.row = 0
        self.column = 0

    def login_btn_onclick(self):
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['(Nº)', ')', '(Canal)', '(Tipo de Alarme)', '(Status)'])
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
            self.setWindowTitle('(Alarm Listen)-(OnLine)')
            self.Login_pushButton.setEnabled(False)
            self.Logout_pushButton.setEnabled(True)
            if (int(device_info.nChanNum) > 0):
                self.Alarmlisten_pushButton.setEnabled(True)
        else:
            QMessageBox.about(self, '(prompt)', error_msg)

    def logout_btn_onclick(self):
        # 登出
        if (self.loginID == 0):
            return
        # 停止报警订阅
        self.sdk.StopListen(self.loginID)
        #登出
        result = self.sdk.Logout(self.loginID)
        self.Login_pushButton.setEnabled(True)
        self.Logout_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(False)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.setWindowTitle("(Alarm Listen)-(OffLine)")
        self.loginID = 0
        self.row = 0
        self.column = 0
        self.Alarmlisten_tableWidget.clear()
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['(Nº.)', '(Tempo)', '(Canal)', '(Tipo de Alarme)', '(Status)'])

    def attach_btn_onclick(self):
        self.row = 0
        self.column = 0
        self.Alarmlisten_tableWidget.clear()
        self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(['(Nº.)', '(Tempo)', '(Canal)', '(Tipo de Alarme)', '(Status)'])
        result = self.sdk.StartListenEx(self.loginID)
        if result:
            QMessageBox.about(self, '(prompt)', "(Subscribe alarm success)")
            self.Stopalarmlisten_pushButton.setEnabled(True)
            self.Alarmlisten_pushButton.setEnabled(False)
        else:
            QMessageBox.about(self, '(prompt)', 'erro:' + str(self.sdk.GetLastError()))

    def detach_btn_onclick(self):
        if (self.loginID > 0):
            self.sdk.StopListen(self.loginID)
        self.Stopalarmlisten_pushButton.setEnabled(False)
        self.Alarmlisten_pushButton.setEnabled(True)

    # 关闭主窗口时清理资源
    def closeEvent(self, event):
        event.accept()
        if self.loginID:
            self.sdk.StopListen(self.loginID)
            self.sdk.Logout(self.loginID)
            self.loginID = 0
        self.sdk.Cleanup()
        self.Alarmlisten_tableWidget.clear()


    def update_ui(self, lCommand, show_info):
        if (lCommand == SDK_ALARM_TYPE.EVENT_MOTIONDETECT):
            if (self.row > 499):
                self.Alarmlisten_tableWidget.clear()
                self.Alarmlisten_tableWidget.setRowCount(0)
                self.Alarmlisten_tableWidget.setHorizontalHeaderLabels(
                    ['(Nº.)', '(Tempo)', '(Canal)', '(Tipo de Alarme)', '(Status)'])
                self.row = 0
                self.Alarmlisten_tableWidget.viewport().update()
            self.Alarmlisten_tableWidget.setRowCount(self.row + 1)
            item = QTableWidgetItem(str(self.row + 1))
            self.Alarmlisten_tableWidget.setItem(self.row, self.column, item)
            item1 = QTableWidgetItem(show_info.time_str)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 1, item1)
            item2 = QTableWidgetItem(show_info.channel_str)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 2, item2)
            item3 = QTableWidgetItem(show_info.alarm_type)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 3, item3)
            item4 = QTableWidgetItem(show_info.status_str)
            self.Alarmlisten_tableWidget.setItem(self.row, self.column + 4, item4)
            self.row += 1
                # ui更新
            self.Alarmlisten_tableWidget.update()
            self.Alarmlisten_tableWidget.viewport().update()


    # 实现断线回调函数功能
    def DisConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle("报警订阅(Alarm Listen)-离线(OffLine)")

    # 实现断线重连回调函数功能
    def ReConnectCallBack(self, lLoginID, pchDVRIP, nDVRPort, dwUser):
        self.setWindowTitle('报警订阅(Alarm Listen)-在线(OnLine)')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wnd = StartListenWnd()
    hwnd = wnd
    wnd.show()
    sys.exit(app.exec_())
