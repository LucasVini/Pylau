# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'AlarmListenUI.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

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
        MainWindow.setWindowTitle(_translate("MainWindow", "报警订阅(Alarm Listen)-离线(OffLine)"))
        self.groupBox.setTitle(_translate("MainWindow", "设备登录(Device Login)"))
        self.label.setText(_translate("MainWindow", "IP地址(IP)"))
        self.label_2.setText(_translate("MainWindow", "端口(Port)"))
        self.label_3.setText(_translate("MainWindow", "用户名(Username)"))
        self.label_4.setText(_translate("MainWindow", "密码(Password)"))
        self.Login_pushButton.setText(_translate("MainWindow", "登录(Login)"))
        self.Logout_pushButton.setText(_translate("MainWindow", "登出(Logout)"))
        item = self.Alarmlisten_tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "序号(No.)"))
        item = self.Alarmlisten_tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "时间(Time)"))
        item = self.Alarmlisten_tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "通道(Channel)"))
        item = self.Alarmlisten_tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "报警类型(Alarm Type)"))
        item = self.Alarmlisten_tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "状态(Status)"))
        self.groupBox_2.setTitle(_translate("MainWindow", "报警订阅(Subscribe)"))
        self.Alarmlisten_pushButton.setText(_translate("MainWindow", "报警订阅(Subscribe Alarm)"))
        self.Stopalarmlisten_pushButton.setText(_translate("MainWindow", "停止订阅(Stop Subscribe)"))
