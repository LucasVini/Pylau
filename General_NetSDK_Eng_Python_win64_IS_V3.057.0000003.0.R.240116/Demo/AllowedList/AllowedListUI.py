# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'AllowedListUI.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(921, 776)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.Login_groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.Login_groupBox.setGeometry(QtCore.QRect(10, 10, 901, 61))
        self.Login_groupBox.setObjectName("Login_groupBox")
        self.Logout_pushButton = QtWidgets.QPushButton(self.Login_groupBox)
        self.Logout_pushButton.setGeometry(QtCore.QRect(800, 20, 91, 41))
        self.Logout_pushButton.setObjectName("Logout_pushButton")
        self.Login_pushButton = QtWidgets.QPushButton(self.Login_groupBox)
        self.Login_pushButton.setGeometry(QtCore.QRect(700, 20, 91, 41))
        self.Login_pushButton.setObjectName("Login_pushButton")
        self.Pwd_label = QtWidgets.QLabel(self.Login_groupBox)
        self.Pwd_label.setGeometry(QtCore.QRect(510, 30, 91, 20))
        self.Pwd_label.setObjectName("Pwd_label")
        self.User_label = QtWidgets.QLabel(self.Login_groupBox)
        self.User_label.setGeometry(QtCore.QRect(330, 30, 101, 20))
        self.User_label.setObjectName("User_label")
        self.Port_lineEdit = QtWidgets.QLineEdit(self.Login_groupBox)
        self.Port_lineEdit.setGeometry(QtCore.QRect(260, 30, 51, 20))
        self.Port_lineEdit.setObjectName("Port_lineEdit")
        self.User_lineEdit = QtWidgets.QLineEdit(self.Login_groupBox)
        self.User_lineEdit.setGeometry(QtCore.QRect(430, 30, 61, 20))
        self.User_lineEdit.setObjectName("User_lineEdit")
        self.Pwd_lineEdit = QtWidgets.QLineEdit(self.Login_groupBox)
        self.Pwd_lineEdit.setGeometry(QtCore.QRect(600, 30, 91, 20))
        self.Pwd_lineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.Pwd_lineEdit.setObjectName("Pwd_lineEdit")
        self.IP_label = QtWidgets.QLabel(self.Login_groupBox)
        self.IP_label.setGeometry(QtCore.QRect(30, 30, 61, 21))
        self.IP_label.setObjectName("IP_label")
        self.IP_lineEdit = QtWidgets.QLineEdit(self.Login_groupBox)
        self.IP_lineEdit.setGeometry(QtCore.QRect(90, 30, 91, 20))
        self.IP_lineEdit.setObjectName("IP_lineEdit")
        self.Port_label = QtWidgets.QLabel(self.Login_groupBox)
        self.Port_label.setGeometry(QtCore.QRect(200, 30, 61, 21))
        self.Port_label.setObjectName("Port_label")
        self.Operate_groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.Operate_groupBox.setGeometry(QtCore.QRect(10, 550, 901, 181))
        self.Operate_groupBox.setObjectName("Operate_groupBox")
        self.AllDelete_pushButton = QtWidgets.QPushButton(self.Operate_groupBox)
        self.AllDelete_pushButton.setGeometry(QtCore.QRect(630, 130, 151, 31))
        self.AllDelete_pushButton.setObjectName("AllDelete_pushButton")
        self.Add_pushButton = QtWidgets.QPushButton(self.Operate_groupBox)
        self.Add_pushButton.setGeometry(QtCore.QRect(30, 130, 151, 31))
        self.Add_pushButton.setObjectName("Add_pushButton")
        self.Modify_pushButton = QtWidgets.QPushButton(self.Operate_groupBox)
        self.Modify_pushButton.setGeometry(QtCore.QRect(230, 130, 151, 31))
        self.Modify_pushButton.setObjectName("Modify_pushButton")
        self.Delete_pushButton = QtWidgets.QPushButton(self.Operate_groupBox)
        self.Delete_pushButton.setGeometry(QtCore.QRect(430, 130, 151, 31))
        self.Delete_pushButton.setObjectName("Delete_pushButton")
        self.PlateNo_label = QtWidgets.QLabel(self.Operate_groupBox)
        self.PlateNo_label.setGeometry(QtCore.QRect(30, 30, 111, 16))
        self.PlateNo_label.setObjectName("PlateNo_label")
        self.SwitchAuthorize_lineEdit = QtWidgets.QLineEdit(self.Operate_groupBox)
        self.SwitchAuthorize_lineEdit.setGeometry(QtCore.QRect(750, 30, 51, 20))
        self.SwitchAuthorize_lineEdit.setObjectName("SwitchAuthorize_lineEdit")
        self.VehicleOwner_label = QtWidgets.QLabel(self.Operate_groupBox)
        self.VehicleOwner_label.setGeometry(QtCore.QRect(290, 30, 131, 16))
        self.VehicleOwner_label.setObjectName("VehicleOwner_label")
        self.StartTime_label = QtWidgets.QLabel(self.Operate_groupBox)
        self.StartTime_label.setGeometry(QtCore.QRect(30, 80, 131, 16))
        self.StartTime_label.setObjectName("StartTime_label")
        self.SwitchAuthorize_label = QtWidgets.QLabel(self.Operate_groupBox)
        self.SwitchAuthorize_label.setGeometry(QtCore.QRect(580, 30, 171, 16))
        self.SwitchAuthorize_label.setObjectName("SwitchAuthorize_label")
        self.EndTime_label = QtWidgets.QLabel(self.Operate_groupBox)
        self.EndTime_label.setGeometry(QtCore.QRect(290, 80, 121, 16))
        self.EndTime_label.setObjectName("EndTime_label")
        self.StartTime_lineEdit = QtWidgets.QLineEdit(self.Operate_groupBox)
        self.StartTime_lineEdit.setGeometry(QtCore.QRect(160, 80, 111, 20))
        self.StartTime_lineEdit.setObjectName("StartTime_lineEdit")
        self.PlateNo_lineEdit = QtWidgets.QLineEdit(self.Operate_groupBox)
        self.PlateNo_lineEdit.setGeometry(QtCore.QRect(160, 30, 111, 20))
        self.PlateNo_lineEdit.setObjectName("PlateNo_lineEdit")
        self.EndTime_lineEdit = QtWidgets.QLineEdit(self.Operate_groupBox)
        self.EndTime_lineEdit.setGeometry(QtCore.QRect(420, 80, 111, 20))
        self.EndTime_lineEdit.setObjectName("EndTime_lineEdit")
        self.VehicleOwner_lineEdit = QtWidgets.QLineEdit(self.Operate_groupBox)
        self.VehicleOwner_lineEdit.setGeometry(QtCore.QRect(420, 30, 111, 20))
        self.VehicleOwner_lineEdit.setObjectName("VehicleOwner_lineEdit")
        self.RecordNo_label = QtWidgets.QLabel(self.Operate_groupBox)
        self.RecordNo_label.setGeometry(QtCore.QRect(580, 80, 121, 16))
        self.RecordNo_label.setObjectName("RecordNo_label")
        self.RecordNo_lineEdit = QtWidgets.QLineEdit(self.Operate_groupBox)
        self.RecordNo_lineEdit.setGeometry(QtCore.QRect(750, 80, 51, 20))
        self.RecordNo_lineEdit.setObjectName("RecordNo_lineEdit")
        self.Allowed_groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.Allowed_groupBox.setGeometry(QtCore.QRect(10, 220, 901, 311))
        self.Allowed_groupBox.setObjectName("Allowed_groupBox")
        self.Query_tableWidget = QtWidgets.QTableWidget(self.Allowed_groupBox)
        self.Query_tableWidget.setGeometry(QtCore.QRect(10, 20, 881, 281))
        self.Query_tableWidget.setMinimumSize(QtCore.QSize(881, 281))
        self.Query_tableWidget.setObjectName("Query_tableWidget")
        self.Query_tableWidget.setColumnCount(6)
        self.Query_tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.Query_tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.Query_tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.Query_tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.Query_tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.Query_tableWidget.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.Query_tableWidget.setHorizontalHeaderItem(5, item)
        self.Query_tableWidget.horizontalHeader().setCascadingSectionResizes(False)
        self.Query_tableWidget.horizontalHeader().setDefaultSectionSize(160)
        self.Query_tableWidget.horizontalHeader().setSortIndicatorShown(False)
        self.Query_tableWidget.horizontalHeader().setStretchLastSection(False)
        self.Query_Box = QtWidgets.QGroupBox(self.centralwidget)
        self.Query_Box.setGeometry(QtCore.QRect(10, 90, 901, 111))
        self.Query_Box.setObjectName("Query_Box")
        self.Query_pushButton = QtWidgets.QPushButton(self.Query_Box)
        self.Query_pushButton.setGeometry(QtCore.QRect(460, 60, 151, 31))
        self.Query_pushButton.setObjectName("Query_pushButton")
        self.plate_messageBox = QtWidgets.QGroupBox(self.Query_Box)
        self.plate_messageBox.setGeometry(QtCore.QRect(20, 30, 431, 61))
        self.plate_messageBox.setObjectName("plate_messageBox")
        self.Province_label = QtWidgets.QLabel(self.plate_messageBox)
        self.Province_label.setGeometry(QtCore.QRect(20, 30, 91, 16))
        self.Province_label.setObjectName("Province_label")
        self.Province_lineEdit = QtWidgets.QLineEdit(self.plate_messageBox)
        self.Province_lineEdit.setGeometry(QtCore.QRect(120, 30, 31, 20))
        self.Province_lineEdit.setObjectName("Province_lineEdit")
        self.PlateNum_label = QtWidgets.QLabel(self.plate_messageBox)
        self.PlateNum_label.setGeometry(QtCore.QRect(170, 30, 141, 16))
        self.PlateNum_label.setObjectName("PlateNum_label")
        self.PlateNum_lineEdit = QtWidgets.QLineEdit(self.plate_messageBox)
        self.PlateNum_lineEdit.setGeometry(QtCore.QRect(320, 30, 71, 20))
        self.PlateNum_lineEdit.setObjectName("PlateNum_lineEdit")
        self.Operate_groupBox.raise_()
        self.Login_groupBox.raise_()
        self.Allowed_groupBox.raise_()
        self.Query_Box.raise_()
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 921, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.Switch_action = QtWidgets.QAction(MainWindow)
        self.Switch_action.setObjectName("Switch_action")

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "允许名单AllowedList(离线offline)"))
        self.Login_groupBox.setTitle(_translate("MainWindow", "设备登录(Login info)"))
        self.Logout_pushButton.setText(_translate("MainWindow", "登出(Logout)"))
        self.Login_pushButton.setText(_translate("MainWindow", "登录(Login)"))
        self.Pwd_label.setText(_translate("MainWindow", "密码(Password)"))
        self.User_label.setText(_translate("MainWindow", "用户名(Username)"))
        self.IP_label.setText(_translate("MainWindow", "IP地址(IP)"))
        self.Port_label.setText(_translate("MainWindow", "端口(Port)"))
        self.Operate_groupBox.setTitle(_translate("MainWindow", "允许名单操作（Allowed List Operation）"))
        self.AllDelete_pushButton.setText(_translate("MainWindow", "全部删除（Delete All）"))
        self.Add_pushButton.setText(_translate("MainWindow", "添加（Add）"))
        self.Modify_pushButton.setText(_translate("MainWindow", "修改（Modify）"))
        self.Delete_pushButton.setText(_translate("MainWindow", "删除（Delete）"))
        self.PlateNo_label.setText(_translate("MainWindow", "车牌号（Plate No.）"))
        self.VehicleOwner_label.setText(_translate("MainWindow", "车主（Vehicle Owner）"))
        self.StartTime_label.setText(_translate("MainWindow", "开始时间（Start Time）"))
        self.SwitchAuthorize_label.setText(_translate("MainWindow", "开闸授权（Switch Authorize）"))
        self.EndTime_label.setText(_translate("MainWindow", "结束时间（End Time）"))
        self.RecordNo_label.setText(_translate("MainWindow", "记录号（Record No.）"))
        self.Allowed_groupBox.setTitle(_translate("MainWindow", "允许名单信息(Allowed List Details)"))
        item = self.Query_tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "车牌号(Plate No.)"))
        item = self.Query_tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "车主(Vehicle Owner)"))
        item = self.Query_tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "开始时间(Start Time)"))
        item = self.Query_tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "结束时间(End Time)"))
        item = self.Query_tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "开闸授权(Switch Authorize)"))
        item = self.Query_tableWidget.horizontalHeaderItem(5)
        item.setText(_translate("MainWindow", "记录号(Record No.)"))
        self.Query_Box.setTitle(_translate("MainWindow", "允许名单查询（Allowed List Query）"))
        self.Query_pushButton.setText(_translate("MainWindow", "模糊查询(Fuzzy Query)"))
        self.plate_messageBox.setTitle(_translate("MainWindow", "车牌信息（Plate Message）"))
        self.Province_label.setText(_translate("MainWindow", "省份（Province）"))
        self.PlateNum_label.setText(_translate("MainWindow", "车牌编号（Plate Number）"))
        self.Switch_action.setText(_translate("MainWindow", "中英文切换"))
