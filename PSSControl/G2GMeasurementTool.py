#-*-coding:utf8 -*-
#https://segmentfault.com/a/1190000005165656
#http://www.cnblogs.com/hhh5460/p/5189843.html
import serial
import time
import serial.tools.list_ports
from PyQt4 import QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar
from matplotlib import gridspec

QTextCodec.setCodecForTr(QTextCodec.codecForName("utf8"))

global groupNum
groupNum = 10

global testData, delayCulDist, jitterData, jitterCulDist,valueCom
testData = []  #G2G time delay
delayCulDist = []  #delay cumulative distribution
jitterData = []  #G2G jitter
jitterCulDist = []  #jitter cumulative distribution
valueCom = []  #combobox values

global getDataFlag
getDataFlag = False

RFileName = 'C:\\Users\\5G\\Desktop\\20180703162419R.txt'
G2GFileName = 'C:\\Users\\5G\\Desktop\\20180703162625G2G.txt'
# RFileName = ''
# G2GFileName = ''
localTime = ''

#----------------------------------------------

class mainWindow(QDialog):
    def __init__(self, parent=None):
        super(mainWindow, self).__init__(parent)
        self.initSerialFlag = 0
        self.ser = serial.Serial()
        self.initUI()
        self.getData_t = getDataThread()
        self.getData_t.signal_time.connect(self.updateProgressBar)

    def initUI(self):
        self.setWindowTitle(self.tr("时延测量"))
        self.setWindowIcon(QIcon("picture\\p3.png"))

        #==========================================================================================================
        # ================================create ParamSet and Function modules=======================================
        #==========================================================================================================
        self.fp = 'C:\\Users\\5G\\Desktop'
        print(self.fp)

        # ===================== ParamSet modules=============================
        layoutLabel1 = QLabel(self.tr("参数设置"))
        layoutLabel1.setAlignment(Qt.AlignCenter)
        layoutLabel1.setFont(QFont("Roman times", 14, QFont.Bold))
        label1 = QLabel(self.tr("输入采集次数："))
        self.testTimesLineEdit = QLineEdit(self.tr('请输入200-1000之间的数'))
        label2 = QLabel(self.tr("COM口选择："))
        self.portComboBox = QComboBox()
        self.portSearchButton = QPushButton(self.tr("端口搜索"))
        self.portSearchButton.setToolTip('Click to search COM ports')
        self.portSearchButton.clicked.connect(self.portSearchButtonClicked)
        label3 = QLabel(self.tr("文件保存位置："))
        self.filePathLineEdit = QLineEdit()
        self.filePathChooseButton = QPushButton(self.tr("路径选择"))
        self.filePathChooseButton.setToolTip('Click to choose file path')
        self.filePathChooseButton.clicked.connect(self.fpButtonClicked)

        labelCol = 0
        contentCol = 1
        buttonCol = 2
        leftLayout = QGridLayout()
        leftLayout.setSpacing(20)
        leftLayout.addWidget(layoutLabel1, 0, contentCol)
        leftLayout.addWidget(label1, 1, labelCol)
        leftLayout.addWidget(self.testTimesLineEdit, 1, contentCol)
        leftLayout.addWidget(label2, 2, labelCol)
        leftLayout.addWidget(self.portComboBox, 2, contentCol)
        leftLayout.addWidget(self.portSearchButton, 2, buttonCol)
        leftLayout.addWidget(label3, 3, labelCol)
        leftLayout.addWidget(self.filePathLineEdit, 3, contentCol)
        leftLayout.addWidget(self.filePathChooseButton, 3, buttonCol)

        # ==================function modules=============
        layoutLabel2 = QLabel(self.tr("操作实现"))
        layoutLabel2.setAlignment(Qt.AlignCenter)
        layoutLabel2.setFont(QFont("Roman times", 14, QFont.Bold))
        self.errorCalibrationButton = QPushButton(self.tr("误差校准"))
        self.errorCalibrationButton.setToolTip('Click to start error calibration')
        self.errorCalibrationButton.clicked.connect(self.ecButtonClicked)
        self.delayTestButton = QPushButton(self.tr("G2G时延测量"))
        self.delayTestButton.setToolTip('Click to start G2G time delay test')
        self.delayTestButton.clicked.connect(self.dtButtonClicked)
        self.calculateResultButton = QPushButton(self.tr("结果统计"))
        self.calculateResultButton.setToolTip('Click to count results')
        self.calculateResultButton.clicked.connect(self.crButtonClicked)
        label4 = QLabel(self.tr("时延中位数："))
        self.middleDataLineEdit = QLineEdit()
        self.progressBar = QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)

        rightLayout = QGridLayout()
        rightLayout.setContentsMargins(50, 0, 0, 0)
        rightLayout.setSpacing(22)
        rightLayout.addWidget(layoutLabel2, 0, contentCol)
        rightLayout.addWidget(self.errorCalibrationButton, 1, 0)
        rightLayout.addWidget(self.delayTestButton, 1, 1)
        rightLayout.addWidget(self.calculateResultButton, 1, 2)
        rightLayout.addWidget(label4, 2, 0)
        rightLayout.addWidget(self.middleDataLineEdit, 2, 1, 1, 2)
        rightLayout.addWidget(self.progressBar, 3, 0, 1, 3)

        # =================create mainLayout of ParamSet and function modules================
        layout1 = QGridLayout(self)
        layout1.setMargin(25)
        layout1.setSpacing(20)
        layout1.addLayout(leftLayout, 0, 0)
        layout1.addLayout(rightLayout, 0, 3)
        layout1.setSizeConstraint(QLayout.SetFixedSize)

        # ================create widget for stack==============
        widget = QWidget()
        widget.setLayout(layout1)

        # ==================================================================================
        # =================create stack and add widget====================
        stack = QStackedWidget()
        stack.setFrameStyle(QFrame.Panel | QFrame.Raised)
        stack.addWidget(widget)

        self.picLayout = QVBoxLayout()
        self.picLayout.setSpacing(10)

        #self.figure = plt.figure()
        self.figure = plt.figure(figsize=(2, 8))
        self.gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1])
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.hide()

        self.picLayout.addWidget(self.toolbar)
        self.picLayout.addWidget(self.canvas)

        layout2 = QVBoxLayout()
        layout2.setMargin(10)
        layout2.setSpacing(6)
        layout2.addWidget(stack)
        layout2.addLayout(self.picLayout)

        mainLayout = QHBoxLayout(self)
        mainLayout.addLayout(layout2)
        self.setLayout(mainLayout)
        self.resize(400,800)

    def portComboxClicked(self):  # 处理事件，*args表示可变参数
        p = self.portComboBox.currentText()
        self.ser = serial.Serial(str(p), 115200, timeout=1, xonxoff=False, rtscts=False, dsrdtr=False, writeTimeout=2)
        print('please wait 5 seconds......')
        time.sleep(5)

    def updateProgressBar(self, num):
        self.progressBar.setValue(num)
        if self.getData_t.working == False:
            QMessageBox.information(self, self.tr("提示！"), self.tr("已完成G2G测量....."), QMessageBox.Ok)

    def portSearchButtonClicked(self):
        self.portComboBox.clear()  # 清空组合框
        valueCom = []
        for port in serial.tools.list_ports.comports():
            if port[2] != 'n/a':
                valueCom.append(port[0])
        self.portComboBox.addItems(valueCom) # 为combox添加item

    def fpButtonClicked(self):   # 路径选择
        # self.portComboxClicked();
        path_ = QFileDialog.getExistingDirectory()
        self.filePathLineEdit.setText(path_)
        self.fp = path_

    def getMedianData(self,TDData):
        n = len(TDData)
        m = n / 2
        md = 0
        if n == 0:
            md = 0
        elif n % 2 == 0:
            md = (TDData[m] + TDData[m + 1]) / 2
        else:
            md = TDData[m]
        self.middleDataLineEdit.setText(str(md))
        print ('中位数：'+str(md))

    def ecButtonClicked(self):
        if self.testTimesLineEdit.text() == '':
            QMessageBox.warning(self, self.tr("告警！"), self.tr("请输入G2G时延测量次数。。。。。"), QMessageBox.Ok)
        elif self.fp == '':
            QMessageBox.warning(self,self.tr("告警！"), self.tr("请选择文件保存路径。。。。。"), QMessageBox.Ok)
        else:
            # 生成文件
            if self.initSerialFlag == 0:
                self.portComboxClicked()
                self.initSerialFlag = 1
            # check if serial is opened
            try:
                if not self.ser.isOpen():
                    self.ser.open()
            except serial.SerialException:
                QMessageBox.warning(self, self.tr("告警！"), self.tr("serial.SerialException ERROR....."), QMessageBox.Ok)
                exit()
            RNum = 100
            self.getData_t.start_timer(RNum,self.fp,self.ser)

    def dtButtonClicked(self):
        if self.testTimesLineEdit.text() == '':
            QMessageBox.warning(self, self.tr("告警！"), self.tr("请输入G2G时延测量次数。。。。。"), QMessageBox.Ok)
        elif self.fp == '':
            QMessageBox.warning(self,self.tr("告警！"), self.tr("请选择文件保存路径。。。。。"), QMessageBox.Ok)
        else:
            if self.initSerialFlag == 0:
                self.portComboxClicked()
                self.initSerialFlag = 1

            try:
                if not self.ser.isOpen():
                    self.ser.open()
            except serial.SerialException:
                QMessageBox.warning(self, self.tr("告警！"), self.tr("serial.SerialException ERROR....."), QMessageBox.Ok)
                exit()

            TNum = int(self.testTimesLineEdit.text())
            self.getData_t.start_timer(TNum, self.fp, self.ser)

    def crButtonClicked(self):
        if self.fp == '':
            QMessageBox(self, self.tr("告警！"), self.str("请选择文件保存路径。。。。。"), QMessageBox.Ok)
        else:
            self.figure.clf()
            # self.canvas._tkcanvas.grid_forget()
            # now ,start caculate the G2G time delay and draw pic
            print(RFileName)
            fRD = open(RFileName, 'r')
            fTD = open(G2GFileName, 'r')
            RTmp = 0
            TTmp = 0
            rawSum = 0

            # 读取第一行数据
            forDataS = 0
            forDataMS = 0
            for dataString in fRD:  # get raw data means
                RTmp = RTmp + 1
                if RTmp == 1:
                    data1 = dataString.split('.')
                    data11 = data1[0].split(':')
                    forDataS = int(data11[2])  # 获取s
                    data12 = data1[1].split('Z')
                    forDataMS = int(data12[0])  # 获取ms
                else:
                    data1 = dataString.split('.')
                    data11 = data1[0].split(':')
                    data12 = data1[1].split('Z')
                    if ((int(data11[2]) - forDataS) == 2) or ((int(data11[2]) - forDataS) == -58):
                        dataMS = int(data12[0]) + 1000
                    elif (int(data11[2]) - forDataS) == 0:
                        dataMS = int(data12[0]) - forDataMS
                    else:
                        dataMS = int(data12[0])
                    rawSum = rawSum + dataMS
                    forDataS = int(data11[2])  # 获取s
                    forDataMS = int(data12[0])  # 获取ms

            meanRaw = rawSum / (RTmp - 1)
            for dataString in fTD:  # put test data in array
                # print data2
                TTmp = TTmp + 1
                if TTmp == 1:
                    data2 = dataString.split('.')
                    data21 = data2[0].split(':')
                    forDataS = int(data21[2]);  # 获取s
                    data22 = data2[1].split('Z')
                    forDataMS = int(data22[0]);  # 获取ms
                else:
                    data2 = dataString.split('.')
                    data21 = data2[0].split(':')
                    data22 = data2[1].split('Z')
                    if ((int(data21[2]) - forDataS) == 2) or ((int(data21[2]) - forDataS) == -58):
                        dataMS = int(data22[0]) + 1000
                        print('+1000')
                    elif (int(data21[2]) - forDataS) == 0:
                        dataMS = int(data22[0]) - forDataMS
                    else:
                        dataMS = int(data22[0])
                    d = float(dataMS - meanRaw)
                    if d <= 0:
                        d = d + 1000
                    testData.append(d)
                    forDataS = int(data21[2])  # 获取s
                    forDataMS = int(data22[0])  # 获取ms
            # ================================
            sortedTD = sorted(testData)
            TDData = sorted(testData)
            print ("time delay.............")
            print (testData)
            print (sortedTD)
            TDY = []
            l1 = len(sortedTD)
            TDY.append(float(1) / l1)
            for i in range(2, l1 + 1):
                TDY.append(float(1) / l1 + TDY[i - 2])
            TD_CDF_X = []
            TD_CDF_Y = []
            # print l1
            max1 = max(sortedTD)
            min1 = min(sortedTD)
            ii = min1
            stepLength = (max1 - min1) / groupNum
            while ii < max1:
                TD_CDF_X.append(ii);
                # caculate cumulative
                dataTmp = 0
                while dataTmp < l1:
                    dataTmp = dataTmp + 1
                    if sortedTD[dataTmp] > ii:
                        TD_CDF_Y.append(TDY[dataTmp - 1])
                        break;
                ii = ii + stepLength;
            if ii >= max1:
                TD_CDF_X.append(sortedTD[l1 - 1])
                TD_CDF_Y.append(TDY[l1 - 1])
            self.getMedianData(TDData)
            time.sleep(10)
            axes1 = self.figure.add_subplot(self.gs[0])
            axes1.set_title(u'time delay CDF curve', {'fontname': 'STSong'})
            axes1.plot(TD_CDF_X, TD_CDF_Y, 'bo-', label='delay (ms)', markersize=5)
            axes1.grid(True)
            axes1.set_yticks([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
            axes1.set_yticklabels(['0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%'])
            axes1.legend(loc="lower right")
            tmp = 0
            while tmp < (l1 - 1):  # caculate jitter
                jitterData.append(abs(testData[tmp + 1] - testData[tmp]))
                tmp = tmp + 1
            sortedJD = sorted(jitterData)
            print ("jitter...............")
            print (jitterData)
            print (sortedJD)
            JDY = []
            l2 = len(sortedJD)
            JDY.append(float(1) / l2)
            for j in range(2, l2 + 1):
                JDY.append(float(1) / l2 + JDY[j - 2])
            JD_CDF_X = []
            JD_CDF_Y = []
            max2 = max(sortedJD)
            min2 = min(sortedJD)
            jj = min2
            stepLength = (max2 - min2) / groupNum
            while jj < max2:
                JD_CDF_X.append(jj);
                # caculate cumulative
                dataTmp = 0
                while dataTmp < l2:
                    dataTmp = dataTmp + 1
                    if sortedJD[dataTmp] > jj:
                        JD_CDF_Y.append(JDY[dataTmp - 1])
                        break;
                jj = jj + stepLength;
            if jj >= l2:
                JD_CDF_X.append(sortedJD[l2 - 1])
                JD_CDF_Y.append(JDY[l2 - 1])
            axes2 = self.figure.add_subplot(self.gs[1])
            axes2.set_title(u'jitter CDF curve', {'fontname': 'STSong'})
            axes2.plot(JD_CDF_X, JD_CDF_Y, 'go-', label='jitter (ms)', markersize=5)
            axes2.grid(True)
            axes2.legend(loc="lower right")
            axes2.set_yticks([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
            axes2.set_yticklabels(['0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%'])
            self.figure.tight_layout()
            localTime = time.strftime("%Y%m%d%H%M%S", time.localtime())
            PicFileName = self.fp + '\\' + localTime + "Pic" + ".png"
            self.canvas.show()
            self.figure.savefig(str(PicFileName), dpi=1000, bbox_inches='tight')
            fRD.close()
            fTD.close()

class drawPicThread(QtCore.QThread):
    signal_canvas = QtCore.pyqtSignal()   #信号

class getDataThread(QtCore.QThread):
    signal_time = QtCore.pyqtSignal(int)  # 信号

    def __init__(self, parent=None):
        super(getDataThread, self).__init__(parent)
        self.working = True
        self.fp = ''
        self.testTimes = 0   #测量次数
        self.ser = serial.Serial()
        self.cmd = ''
        self.tmp = 0
    def start_timer(self, testTimes, fp, ser):
        self.tmp = 0
        self.working = True
        self.cmd = ''
        self.fp = fp
        self.testTimes = testTimes  # 测量次数
        self.ser = ser
        self.start()

    def run(self):
        # get local time
        localTime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        if self.testTimes == 100:
            # create file
            global RFileName
            RFileName = self.fp + '\\' + localTime + 'R' + ".txt"
            print (RFileName)
            time.sleep(1)
            # open file
            fopen = open(RFileName, 'w')
            fopen.truncate()
            # send command to measurement tool
            cmd = 'R'
        else:
            # create file
            global G2GFileName
            G2GFileName = self.fp + '\\' + localTime + 'G2G' + ".txt"
            print (G2GFileName)
            time.sleep(1)
            # open file
            fopen = open(G2GFileName, 'w')  # open file ,if not exit ,create new one
            fopen.truncate()  # clear file
            # send command to measurement tool
            cmd = 'F'
        # send command to measurement tool
        self.ser.write(cmd)

        self.ser.flushInput()  # 清空缓存区
        time.sleep(1)  # 延迟1s

        while self.working:
            print "Working", self.thread()
            try:
                data = self.ser.readline()
                if len(data) > 0:
                    if self.tmp < 20:
                        self.tmp = self.tmp + 1
                    elif self.tmp < (self.testTimes + 21):
                        self.tmp = self.tmp + 1
                        fopen.write(data)
                        fopen.flush()
                    elif self.tmp == (self.testTimes + 21):
                        self.working = False
                        fopen.close()
                        #self.ser.close()
                    num = self.tmp * 100 / (self.testTimes + 20)
                    self.signal_time.emit(num)  # 发送信号
            except serial.SerialException:
                print('timeout')
                time(1)


def main():
    app = QApplication(sys.argv)
    dialog = mainWindow()
    dialog.show()
    app.exec_()

if __name__ == '__main__':
     main()
