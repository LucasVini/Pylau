# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'PlayBackUI.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1001, 678)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(20, 10, 961, 61))
        self.groupBox.setObjectName("groupBox")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(10, 30, 61, 16))
        self.label.setObjectName("label")
        self.IP_lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.IP_lineEdit.setGeometry(QtCore.QRect(80, 30, 121, 20))
        self.IP_lineEdit.setObjectName("IP_lineEdit")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(220, 30, 61, 16))
        self.label_2.setObjectName("label_2")
        self.Port_lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.Port_lineEdit.setGeometry(QtCore.QRect(280, 30, 113, 20))
        self.Port_lineEdit.setObjectName("Port_lineEdit")
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(420, 30, 71, 16))
        self.label_3.setObjectName("label_3")
        self.Name_lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.Name_lineEdit.setGeometry(QtCore.QRect(500, 30, 113, 20))
        self.Name_lineEdit.setObjectName("Name_lineEdit")
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_4.setGeometry(QtCore.QRect(640, 30, 61, 16))
        self.label_4.setObjectName("label_4")
        self.Pwd_lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.Pwd_lineEdit.setGeometry(QtCore.QRect(700, 30, 113, 20))
        self.Pwd_lineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.Pwd_lineEdit.setObjectName("Pwd_lineEdit")
        self.Login_pushButton = QtWidgets.QPushButton(self.groupBox)
        self.Login_pushButton.setGeometry(QtCore.QRect(840, 20, 91, 31))
        self.Login_pushButton.setObjectName("Login_pushButton")
        self.PlayBackWnd = QtWidgets.QLabel(self.centralwidget)
        self.PlayBackWnd.setGeometry(QtCore.QRect(10, 80, 691, 551))
        self.PlayBackWnd.setAutoFillBackground(False)
        self.PlayBackWnd.setStyleSheet("background-color: rgb(180, 180, 180);")
        self.PlayBackWnd.setAlignment(QtCore.Qt.AlignCenter)
        self.PlayBackWnd.setObjectName("PlayBackWnd")
        self.SelectDate_calendarWidget = QtWidgets.QCalendarWidget(self.centralwidget)
        self.SelectDate_calendarWidget.setEnabled(False)
        self.SelectDate_calendarWidget.setGeometry(QtCore.QRect(720, 160, 251, 201))
        self.SelectDate_calendarWidget.setSelectedDate(QtCore.QDate(2020, 4, 10))
        self.SelectDate_calendarWidget.setFirstDayOfWeek(QtCore.Qt.Monday)
        self.SelectDate_calendarWidget.setGridVisible(True)
        self.SelectDate_calendarWidget.setSelectionMode(QtWidgets.QCalendarWidget.SingleSelection)
        self.SelectDate_calendarWidget.setHorizontalHeaderFormat(QtWidgets.QCalendarWidget.ShortDayNames)
        self.SelectDate_calendarWidget.setVerticalHeaderFormat(QtWidgets.QCalendarWidget.NoVerticalHeader)
        self.SelectDate_calendarWidget.setNavigationBarVisible(True)
        self.SelectDate_calendarWidget.setDateEditEnabled(True)
        self.SelectDate_calendarWidget.setObjectName("SelectDate_calendarWidget")
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setGeometry(QtCore.QRect(710, 80, 271, 371))
        self.groupBox_2.setObjectName("groupBox_2")
        self.exist_radioButton = QtWidgets.QRadioButton(self.groupBox_2)
        self.exist_radioButton.setGeometry(QtCore.QRect(50, 300, 151, 16))
        self.exist_radioButton.setCheckable(True)
        self.exist_radioButton.setObjectName("exist_radioButton")
        self.Channel_comboBox = QtWidgets.QComboBox(self.groupBox_2)
        self.Channel_comboBox.setEnabled(False)
        self.Channel_comboBox.setGeometry(QtCore.QRect(110, 20, 61, 22))
        self.Channel_comboBox.setObjectName("Channel_comboBox")
        self.Channel_label = QtWidgets.QLabel(self.groupBox_2)
        self.Channel_label.setGeometry(QtCore.QRect(20, 20, 81, 16))
        self.Channel_label.setObjectName("Channel_label")
        self.StreamTyp_comboBox = QtWidgets.QComboBox(self.groupBox_2)
        self.StreamTyp_comboBox.setEnabled(False)
        self.StreamTyp_comboBox.setGeometry(QtCore.QRect(110, 50, 131, 22))
        self.StreamTyp_comboBox.setObjectName("StreamTyp_comboBox")
        self.StreamTyp_comboBox.addItem("")
        self.StreamTyp_comboBox.addItem("")
        self.label_5 = QtWidgets.QLabel(self.groupBox_2)
        self.label_5.setGeometry(QtCore.QRect(20, 50, 71, 16))
        self.label_5.setObjectName("label_5")
        self.Pause_pushbutton = QtWidgets.QPushButton(self.groupBox_2)
        self.Pause_pushbutton.setEnabled(False)
        self.Pause_pushbutton.setGeometry(QtCore.QRect(160, 330, 101, 31))
        self.Pause_pushbutton.setObjectName("Pause_pushbutton")
        self.PlayBack_pushbutton = QtWidgets.QPushButton(self.groupBox_2)
        self.PlayBack_pushbutton.setEnabled(False)
        self.PlayBack_pushbutton.setGeometry(QtCore.QRect(10, 330, 101, 31))
        self.PlayBack_pushbutton.setObjectName("PlayBack_pushbutton")
        self.groupBox_3 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_3.setGeometry(QtCore.QRect(710, 460, 271, 181))
        self.groupBox_3.setObjectName("groupBox_3")
        self.Start_dateTimeEdit = QtWidgets.QDateTimeEdit(self.groupBox_3)
        self.Start_dateTimeEdit.setGeometry(QtCore.QRect(130, 30, 131, 22))
        self.Start_dateTimeEdit.setDateTime(QtCore.QDateTime(QtCore.QDate(2020, 5, 9), QtCore.QTime(0, 0, 0)))
        self.Start_dateTimeEdit.setObjectName("Start_dateTimeEdit")
        self.label_7 = QtWidgets.QLabel(self.groupBox_3)
        self.label_7.setGeometry(QtCore.QRect(10, 30, 121, 16))
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(self.groupBox_3)
        self.label_8.setGeometry(QtCore.QRect(20, 70, 111, 16))
        self.label_8.setObjectName("label_8")
        self.End_dateTimeEdit = QtWidgets.QDateTimeEdit(self.groupBox_3)
        self.End_dateTimeEdit.setGeometry(QtCore.QRect(130, 70, 131, 22))
        self.End_dateTimeEdit.setDateTime(QtCore.QDateTime(QtCore.QDate(2020, 5, 9), QtCore.QTime(0, 22, 0)))
        self.End_dateTimeEdit.setObjectName("End_dateTimeEdit")
        self.Download_pushButton = QtWidgets.QPushButton(self.groupBox_3)
        self.Download_pushButton.setEnabled(False)
        self.Download_pushButton.setGeometry(QtCore.QRect(70, 110, 101, 31))
        self.Download_pushButton.setObjectName("Download_pushButton")
        self.Download_progressBar = QtWidgets.QProgressBar(self.groupBox_3)
        self.Download_progressBar.setGeometry(QtCore.QRect(70, 150, 118, 23))
        self.Download_progressBar.setMaximum(100)
        self.Download_progressBar.setProperty("value", 0)
        self.Download_progressBar.setTextDirection(QtWidgets.QProgressBar.TopToBottom)
        self.Download_progressBar.setObjectName("Download_progressBar")
        self.groupBox_2.raise_()
        self.groupBox.raise_()
        self.PlayBackWnd.raise_()
        self.SelectDate_calendarWidget.raise_()
        self.groupBox_3.raise_()
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1001, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "回放(PlayBack)"))
        self.groupBox.setTitle(_translate("MainWindow", "设备登录(Device Login)"))
        self.label.setText(_translate("MainWindow", "IP地址(IP)"))
        self.label_2.setText(_translate("MainWindow", "端口(Port)"))
        self.label_3.setText(_translate("MainWindow", "用户名(Name)"))
        self.label_4.setText(_translate("MainWindow", "密码(PWD)"))
        self.Login_pushButton.setText(_translate("MainWindow", "登录(Login)"))
        self.PlayBackWnd.setText(_translate("MainWindow", "回放(PlayBack)"))
        self.groupBox_2.setTitle(_translate("MainWindow", "回放操作(PlayBack)"))
        self.exist_radioButton.setText(_translate("MainWindow", "存在录像(exist video)"))
        self.Channel_label.setText(_translate("MainWindow", "通道(channel)"))
        self.StreamTyp_comboBox.setItemText(0, _translate("MainWindow", "主码流(MainStream)"))
        self.StreamTyp_comboBox.setItemText(1, _translate("MainWindow", "辅码流(ExtraStream)"))
        self.label_5.setText(_translate("MainWindow", "码流(Stream)"))
        self.Pause_pushbutton.setText(_translate("MainWindow", "暂停(Pause)"))
        self.PlayBack_pushbutton.setText(_translate("MainWindow", "播放(Play)"))
        self.groupBox_3.setTitle(_translate("MainWindow", "下载(download)"))
        self.Start_dateTimeEdit.setDisplayFormat(_translate("MainWindow", "yyyy/M/d HH:mm:ss"))
        self.label_7.setText(_translate("MainWindow", "起始时间(StartTime)"))
        self.label_8.setText(_translate("MainWindow", "结束时间(EndTime)"))
        self.End_dateTimeEdit.setDisplayFormat(_translate("MainWindow", "yyyy/M/d HH:mm:ss"))
        self.Download_pushButton.setText(_translate("MainWindow", "下载(download)"))

