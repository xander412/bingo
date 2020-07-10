from PyQt5.QtWidgets import *
import sys
import pandas as pd
import numpy as np
from socket import *
from PyQt5.QtGui import QIcon,QFont,QColor
from PyQt5.QtCore import QSize,QRect
import multiprocessing
from threading import *

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.root = QDialog()
        self.setCentralWidget(self.root)
        self.mLayout = QVBoxLayout()
        self.turn = 'my'
        self.root.setLayout(self.mLayout)
        self.ipGui()
        self.colors = ['green', 'yellow', 'blue', 'orange', 'violet']
        self.mainTable()
        self.myScore = 0
        self.oScore = 0
        x = np.arange(1, 26)
        np.random.shuffle(x)
        self.df = pd.DataFrame(x.reshape(5, 5))
        for x in range(5):
            for j in range(5):
                self.mTable.setItem(x, j, QTableWidgetItem(str(self.df.loc[x, j])))
        self.mTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.mTable.resizeColumnsToContents()
        self.mTable.setSelectionMode(QAbstractItemView.SelectionMode(1))
        self.mTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        #self.mTable.cellChanged.connect(self.dataConnect)
        self.show()

    def ipGui(self):
        self.ipLayout = QVBoxLayout()
        self.formLayout = QHBoxLayout()
        self.ipEntry = FormEntry('IP Address:')
        self.formLayout.addLayout(self.ipEntry)
        self.portEntry = FormSpin('Port:')
        self.formLayout.addLayout(self.portEntry)
        self.setServer = QPushButton('Host Server')
        self.formLayout.addWidget(self.setServer)
        self.setServer.clicked.connect(self.serverConnection)
        self.ipLayout.addLayout(self.formLayout)
        self.mLayout.addLayout(self.ipLayout)
        self.setServer.setFixedWidth(120)

    def serverConnection(self):
        self.setServer.setEnabled(False)
        self.ip = self.ipEntry.text()
        self.port = int(self.portEntry.text())
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind((self.ip, self.port))
        self.wLayout = QHBoxLayout()
        self.thread = Thread(target = self.startServer)
        self.slabel = QLabel('Waiting for clients.........')
        self.canBut = QPushButton('Cancel')
        self.wLayout.addWidget(self.slabel)
        self.wLayout.addWidget(self.canBut)
        self.ipLayout.addLayout(self.wLayout)
        self.canBut.clicked.connect(self.stopHosting)
        self.canBut.setFixedWidth(110)
        self.thread.start()

    def stopHosting(self):
        self.server.shutdown(SHUT_RDWR)
        self.server.close()
        self.setServer.setEnabled(True)
        self.canBut.hide()
        self.slabel.hide()

    def dataConnect(self, x, y):
        self.df.loc[x, y] = self.mTable.item(x, y).text()

    def startServer(self):
        print('Waiting for clients....')
        self.server.listen(1)
        try:
            self.client, self.addr = self.server.accept()
            self.slabel.setText(str(self.addr) +  ' is connected.')
            self.canBut.setText('Start Game')
            self.canBut.clicked.disconnect()
            self.canBut.clicked.connect(self.afterConnect)
            #self.afterConnect()
        except OSError:
            print('Thread Terminated.')

    def mainTable(self):
        self.centLayout = QHBoxLayout()
        self.mTable = QTableWidget()
        self.mTable.setRowCount(5)
        self.mTable.setColumnCount(5)
        self.centLayout.addWidget(self.mTable)
        self.mLayout.addLayout(self.centLayout)
        self.mTable.horizontalHeader().setVisible(False)
        self.mTable.verticalHeader().setVisible(False)
        self.mTable.setFixedSize(287, 170)
        self.setMaximumSize(self.sizeHint())
        self.setMinimumSize(self.sizeHint())

    def afterConnect(self):
        self.mbLayout = QVBoxLayout()
        self.centLayout.addLayout(self.mbLayout)
        self.send = QPushButton('STRIKE OFF')
        self.send.setFixedWidth(110)
        self.mbLayout.addWidget(self.send)
        self.rNum = QLabel('')
        self.rNum.setFont(QFont('TlwgTypist', 50, 75))
        self.quitBut = QPushButton('Quit')
        self.mbLayout.addWidget(self.rNum)
        self.mbLayout.addWidget(self.quitBut)
        self.send.clicked.connect(self.mechThread)
        self.canBut.hide()
        self.slabel.setText('Your Move...')

    def afterConnect2(self):
        self.send.setEnabled(True)
        self.canBut.hide()
        self.client.send('Ready'.encode())
        if self.turn == 'my':
            self.slabel.setText('Your Move....')
            self.send.setEnabled(True)
        else:
            self.slabel.setText('Waiting for player two\'s move...')
            self.receive()

    def mechThread(self):
        self.mThread = Thread(target=self.sendRecv)
        self.mThread.start()

    def sendRecv(self):
        print(self.df)
        self.mTable.clearSelection()
        self.send.setEnabled(False)
        self.selection = self.mTable.currentItem()
        if self.df.loc[self.selection.row(), self.selection.column()] != 0:
            self.df.loc[self.selection.row(), self.selection.column()] = 0
            #self.df.replace(int(self.selection.text()), np.NaN, inplace=True)
            self.selection.setBackground(QColor('red'))
            self.selection.setFont(QFont('TlwgTypist', 13, 100, 50))
            count = self.checkNum()
            print(count)
            if count >= 5:
                self.client.send('0'.encode())
                self.slabel.setText('You are the Winner.')
                self.myScore += 1
                self.turn = 'other' if self.turn == 'my' else 'my'
                print('Turn Selected..')
                self.canBut.show()
                print('Can But shown')
                self.newGame()
            else:
                self.client.send(self.selection.text().encode())
                self.slabel.setText("Waiting Player two's move......")
            self.receive()
        else:
            print('Entered...')
            self.slabel.setText('Already Striked off.Please select another..')
            self.send.setEnabled(True)
    def receive(self):
        self.data = int(self.client.recv(1024).decode())
        if self.data == 0:
            self.slabel.setText('Player2 is the winner.')
            self.oScore += 1
            self.turn = 'other' if self.turn == 'my' else 'my'
            self.canBut.show()
            print('Can But shown')
            self.newGame()
        self.slabel.setText('Your Move...')
        self.rNum.setText(str(self.data))
        self.data = np.where(self.df == self.data)
        self.df.loc[self.data] = 0
        self.mTable.item(self.data[0], self.data[1]).setBackground(QColor('red'))
        self.mTable.item(self.data[0], self.data[1]).setFont(QFont('TlwgTypist', 13, 100, 50))
        count = self.checkNum()
        print(count)
        if count >= 5:
            self.client.send('0'.encode())
            self.slabel.setText('Your are the winner.')
            self.myScore += 1
            self.turn = 'other' if self.turn == 'my' else 'my'
            self.canBut.show()
            print('Can But shown')
            self.newGame()
        self.send.setEnabled(True)

    def newGame(self):
        self.scoreBoard()
        self.canBut.setText('NewGame')
        self.canBut.clicked.disconnect()
        self.canBut.clicked.connect(self.newGameFunc)
        print('Completed.....')
        raise KeyError

    def newGameFunc(self):
        x = np.arange(1, 26)
        np.random.shuffle(x)
        self.df = pd.DataFrame(x.reshape(5, 5))
        for x in range(5):
            for j in range(5):
                self.mTable.item(x, j).setText(str(self.df.loc[x, j]))
                self.mTable.item(x, j).setBackground(QColor('white'))
                self.mTable.item(x, j).setFont(QFont(''))
        self.mTable.resizeColumnsToContents()
        self.slabel.setText('Start a New Game......')
        self.canBut.setText('Start Game')
        self.canBut.clicked.disconnect()
        self.canBut.clicked.connect(self.afterConnect2)

    def scoreBoard(self):
        self.rNum.setText(f'{self.myScore}|{self.oScore}')

    def checkNum(self):
        count = 0
        cCount = 0
        for x in range(5):
            if self.df[x].sum() == 0:
                count += 1
                for i in range(0, 5):
                    self.mTable.item(i, x).setBackground(QColor(self.colors[cCount if cCount <=4 else 0]))
                cCount += 1
            if self.df.loc[x,:].sum() == 0:
                count += 1
                for i in range(0, 5):
                    self.mTable.item(x, i).setBackground(QColor(self.colors[cCount if cCount <= 4 else 0]))
                cCount += 1
        if np.trace(self.df) == 0:
            count += 1
            for i in range(0,5):
                self.mTable.item(i, i).setBackground(QColor(self.colors[cCount if cCount <= 4 else 0]))
            cCount += 1
        if np.array(self.df)[np.arange(0, 5), np.arange(4, -1, -1)].sum() == 0:
            count += 1
            for i,j in zip(range(0, 5), range(4, -1, -1)):
                self.mTable.item(i, j).setBackground(QColor(self.colors[cCount if cCount <= 4 else 0]))
            cCount += 1
        return count


    def checkByReshma(self):
        reshma = 0
        s = 0
        j = 4
        k = 0
        for x in range(0, 5):
            count = 0
            for i in range(0, 5):
                if self.df.loc[i, x] == 0:
                    count += 1
            if count == 5:
                reshma += 1
            count = 0
            for i in range(0, 5):
                if self.df.loc[x, i] == 0:
                    count += 1
            if count == 5:
                reshma += 1
            if self.df.loc[x, x] == 0:
                s += 1
            if self.df.loc[x, j] == 0:
                k += 1
                j -= 1
        if s == 5:
            reshma += 1
        if k == 5:
            reshma += 1
        return reshma

class FormEntry(QHBoxLayout):
    def __init__(self, text):
        super().__init__()
        self.addWidget(QLabel(text))
        self.lineEdit = QLineEdit()
        self.addWidget(self.lineEdit)
        self.lineEdit.setFixedWidth(85)

    def text(self):
        return self.lineEdit.text()

class FormSpin(QHBoxLayout):
    def __init__(self, text):
        super().__init__()
        self.addWidget(QLabel(text))
        self.lineEdit = QSpinBox()
        self.lineEdit.setMinimum(0)
        self.lineEdit.setMaximum(10000)
        self.addWidget(self.lineEdit)

    def text(self):
        return self.lineEdit.text()

class DestroyableMessage(QDialog):
    def __init__(self, title, text):
        super().__init__()
        self.setWindowTitle(title)
        label = QLabel(text)
       # label.setWindowIcon(QIcon('index.jpeg'))
        self.mLayout = QVBoxLayout()
        self.mLayout.addWidget(label)
        self.setLayout(self.mLayout)
        self.show()

ip = 'localhost'
port = 8000
app = QApplication(sys.argv)
obj = Main()
sys.exit(app.exec())