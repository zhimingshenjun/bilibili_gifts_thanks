# -*- coding: utf-8 -*-
import os
import sys
import shutil
import asyncio
import zlib
import json
import codecs
from aiowebsocket.converses import AioWebSocket
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtMultimedia import QMediaPlayer


class remoteThread(QThread):
    giftInfo = Signal(list)
    guard = Signal(str)

    def __init__(self, url):
        super(remoteThread, self).__init__()
        self.filterToken = True
        self.roomID = url.split('/')[-1]
        if '?' in self.roomID:
            self.roomID = self.roomID.split('?')[0]

    def setFilter(self, token):
        self.filterToken = token

    async def startup(self, url):
        data_raw = '000000{headerLen}0010000100000007000000017b22726f6f6d6964223a{roomid}7d'
        data_raw = data_raw.format(headerLen=hex(27 + len(self.roomID))[2:],
                                   roomid=''.join(map(lambda x: hex(ord(x))[2:], list(self.roomID))))
        async with AioWebSocket(url) as aws:
            converse = aws.manipulator
            await converse.send(bytes.fromhex(data_raw))
            tasks = [self.receDM(converse), self.sendHeartBeat(converse)]
            await asyncio.wait(tasks)

    async def sendHeartBeat(self, websocket):
        hb = '00000010001000010000000200000001'
        while True:
            await asyncio.sleep(30)
            await websocket.send(bytes.fromhex(hb))

    async def receDM(self, websocket):
        while True:
            recv_text = await websocket.receive()
            self.printDM(recv_text)

    def printDM(self, data):
        packetLen = int(data[:4].hex(), 16)
        ver = int(data[6:8].hex(), 16)
        op = int(data[8:12].hex(), 16)

        if len(data) > packetLen:
            self.printDM(data[packetLen:])
            data = data[:packetLen]

        if ver == 2:
            data = zlib.decompress(data[16:])
            self.printDM(data)
            return

        if ver == 1:
            if op == 3:
                # print('[RENQI]  {}'.format(int(data[16:].hex(),16)))
                pass
            return

        if op == 5:
            try:
                jd = json.loads(data[16:].decode('utf-8', errors='ignore'))
                # if jd['cmd'] == 'SEND_GIFT':
                #     print(jd['data']['uname'], ' 投喂 ', jd['data']['num'], 'x', jd['data']['giftName'])
                if jd['cmd'] == 'COMBO_SEND':
                    d = jd['data']
                    if self.filterToken:
                        giftName = d['gift_name']
                        if giftName not in ['小心心', '辣条']:
                            self.giftInfo.emit([d['uname'], d['batch_combo_num'], giftName])
                    else:
                        self.giftInfo.emit([d['uname'], d['batch_combo_num'], d['gift_name']])
                elif jd['cmd'] == 'GUARD_BUY':
                    self.guard.emit(jd['data']['username'])
            except Exception as e:
                print(e)

    def run(self):
        remote = r'wss://broadcastlv.chat.bilibili.com:2245/sub'
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            asyncio.get_event_loop().run_until_complete(self.startup(remote))
        except KeyboardInterrupt as e:
            print('exit')


class GIFWidget(QWidget):
    finish = Signal()

    def __init__(self, gifPath='', parent=None):
        super().__init__(parent)
        self.mousePressToken = False
        self.executeToken = False
        self.resize(300, 300)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.show()
        layout = QGridLayout()
        self.setLayout(layout)

        self.showText = QLabel('感谢 甲鱼 投喂的\n100个小心心')
        self.showText.setStyleSheet("QLabel{color:#00CED1;font-size:22px;font-weight:bold;font-family:Yahei;}")
        self.showText.setAlignment(Qt.AlignCenter)
        self.showText.setAttribute(Qt.WA_TranslucentBackground)
        layout.addWidget(self.showText, 1, 0, 1, 1)

        self.showGIF = QLabel()
        self.showGIF.setAttribute(Qt.WA_TranslucentBackground)
        self.showGIF.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.showGIF, 0, 0, 1, 1)
        if gifPath:
            movie = QMovie(gifPath)
            self.showGIF.setMovie(movie)
            movie.start()

        self.frame = 180
        self.animationTimer = QTimer()
        self.animationTimer.setInterval(16)
        self.animationTimer.timeout.connect(self.playAnimate)

    def setGIFPath(self, gifPath):
        movie = QMovie(gifPath)
        self.showGIF.setMovie(movie)
        movie.start()

    def setFont(self, font):
        self.showText.setFont(font)

    def setColor(self, color):
        self.showText.setStyleSheet('color:' + color)

    def setGiftInfo(self, giftInfo):
        self.showText.setText('感谢 %s 投喂的\n%s个%s' % tuple(giftInfo))

    def setGuard(self, guardInfo):
        self.showText.setText('%s %s %s' % tuple(guardInfo))

    def mousePressEvent(self, QEvent):
        self.mousePressToken = True
        self.startPos = QEvent.pos()

    def mouseReleaseEvent(self, QEvent):
        self.mousePressToken = False

    def mouseMoveEvent(self, QEvent):
        if self.mousePressToken:
            self.move(self.pos() + (QEvent.pos() - self.startPos))

    def playAnimate(self):
        if self.frame > 160:
            self.setWindowOpacity((180 - self.frame) / 20)
            self.frame -= 1
        elif self.frame > 60:
            self.frame -= 1
        elif self.frame > 0:
            self.setWindowOpacity(self.frame / 60)
            self.frame -= 1
        else:
            self.frame = 180
            self.animationTimer.stop()
            if not self.executeToken:
                self.setWindowOpacity(1)
                self.showText.setText('感谢 甲鱼 投喂的\n100个小心心')
            else:
                self.setWindowOpacity(0)
                self.showText.setText('')
            self.finish.emit()


class previewLabel(QLabel):
    click = Signal()

    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setAlignment(Qt.AlignCenter)

    def mousePressEvent(self, QEvent):
        self.click.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sound = QMediaPlayer()
        self.executeToken = False
        self.setAcceptDrops(True)
        self.installEventFilter(self)
        if os.path.exists('config.json'):
            with codecs.open('config.json', 'r', 'utf_8_sig') as config:
                config = config.read()
            self.config = json.loads(config)
        else:
            self.config = {'room_url': '', 'bgm_path': '', 'gif_path': '', 'font_color': '#000000',
                           'font_name': 'yahei', 'font_size': '10', 'font_bold': '0', 'font_italic': '0',
                           'guard_text_before': '恭迎', 'guard_text_after': '舰长登船~~', 'filter': '1'}
        self.GIFWidget = GIFWidget(self.config['gif_path'])
        self.GIFWidget.finish.connect(self.animateFinish)

        self.setWindowTitle('B站直播打赏感谢机 测试版   (by up 执鸣神君)')
        self.main_widget = QWidget()
        self.main_widget.setAcceptDrops(True)
        self.setCentralWidget(self.main_widget)
        layout = QGridLayout()
        self.main_widget.setLayout(layout)
        roomIDLabel = QLabel('主播房间地址')
        roomIDLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(roomIDLabel, 0, 0, 1, 1)
        self.roomURLEdit = QLineEdit(self.config['room_url'])
        layout.addWidget(self.roomURLEdit, 0, 2, 1, 5)

        bgmButton = QPushButton('选择答谢音效')
        bgmButton.clicked.connect(self.selectBGM)
        layout.addWidget(bgmButton, 1, 0, 1, 1)
        self.bgmEdit = QLineEdit(self.config['bgm_path'])
        self.sound.setMedia(QUrl.fromLocalFile(self.config['bgm_path']))
        layout.addWidget(self.bgmEdit, 1, 2, 1, 5)

        fontButton = QPushButton('设置字体样式')
        fontButton.clicked.connect(self.getFont)
        layout.addWidget(fontButton, 2, 0, 1, 1)
        self.font = QFont(self.config['font_name'], int(self.config['font_size']))
        if self.config['font_bold'] == '1':
            self.font.setBold(True)
        if self.config['font_italic'] == '1':
            self.font.setItalic(True)
        self.color = self.config['font_color']
        self.fontLabel = QLabel('感谢甲鱼投喂的100个小心心')
        self.fontLabel.setFont(self.font)
        self.fontLabel.setStyleSheet('color:' + self.color)
        self.GIFWidget.setFont(self.font)
        self.GIFWidget.setColor(self.color)
        layout.addWidget(self.fontLabel, 2, 2, 1, 5)

        guardLabel = QLabel('舰长专属贺词')
        guardLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(guardLabel, 3, 0, 1, 1)
        self.guardEditBefore = QLineEdit(self.config['guard_text_before'])
        layout.addWidget(self.guardEditBefore, 3, 2, 1, 2)
        guardNameLabel = QLabel('舰长名')
        guardNameLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(guardNameLabel, 3, 4, 1, 1)
        self.guardEditAfter = QLineEdit(self.config['guard_text_after'])
        layout.addWidget(self.guardEditAfter, 3, 5, 1, 2)

        self.filterToken = True if int(self.config['filter']) == 1 else False
        if self.filterToken:
            self.filterButton = QPushButton('过滤银币礼物')
            self.filterButton.setStyleSheet('background-color:#3daee9')
        else:
            self.filterButton = QPushButton('显示所有礼物')
            self.filterButton.setStyleSheet('background-color:#31363b')
        self.filterButton.clicked.connect(self.changeFilter)
        layout.addWidget(self.filterButton, 4, 0, 1, 1)

        self.preview = previewLabel('点击或拖入要播放的答谢gif动图')
        self.preview.click.connect(self.click)
        if self.config['gif_path']:
            movie = QMovie(self.config['gif_path'])
            self.preview.setMovie(movie)
            movie.start()
        layout.addWidget(self.preview, 5, 0, 5, 7)

        self.testButton = QPushButton('测试一下')
        self.testButton.clicked.connect(self.testAnimate)
        self.testButton.setFixedSize(200, 65)
        layout.addWidget(self.testButton, 10, 0, 2, 3)
        self.startButton = QPushButton('开始捕获')
        self.startButton.clicked.connect(self.startMonitor)
        self.startButton.setFixedSize(200, 65)
        layout.addWidget(self.startButton, 10, 4, 2, 3)

    def changeFilter(self):
        if self.filterToken:
            self.filterButton.setText('显示所有礼物')
            self.filterButton.setStyleSheet('background-color:#31363b')
        else:
            self.filterButton.setText('过滤银币礼物')
            self.filterButton.setStyleSheet('background-color:#3daee9')
        self.filterToken = not self.filterToken
        try:
            self.remoteThread.setFilter(self.filterToken)
        except:
            pass

    def selectBGM(self):
        if not os.path.exists('bgm'):
            os.mkdir('bgm')
        filePath = QFileDialog.getOpenFileName(self, "请选择bgm文件", 'bgm', "*.mp3 *.wav")[0]
        if filePath:
            fileName = os.path.split(filePath)[1]
            if not os.path.exists(r'bgm/%s' % fileName):
                shutil.copy(filePath, 'bgm')
            self.bgmEdit.setText(filePath)
            self.sound.setMedia(QUrl.fromLocalFile(filePath))

    def click(self):
        filePath = QFileDialog.getOpenFileName(self, "请选择gif文件", 'gif', "*.gif")[0]
        if filePath:
            self.openFile(filePath)

    def openFile(self, filePath):
        if filePath.endswith('.gif'):
            fileName = os.path.split(filePath)[1]
            if not os.path.exists('gif'):
                os.mkdir('gif')
            if not os.path.exists(r'gif/%s' % fileName):
                shutil.copy(filePath, 'gif')
            movie = QMovie(filePath)
            self.preview.setMovie(movie)
            movie.start()
            self.GIFWidget.setGIFPath(filePath)
            self.config['gif_path'] = r'%s/gif/%s' % (os.getcwd(), fileName)

    def dragEnterEvent(self, QDragEnterEvent):
        QDragEnterEvent.accept()

    def dropEvent(self, QEvent):
        if QEvent.mimeData().hasUrls:
            self.openFile(QEvent.mimeData().urls()[0].toLocalFile())

    def closeEvent(self, QCloseEvent):
        self.GIFWidget.close()
        self.config['room_url'] = self.roomURLEdit.text()
        self.config['bgm_path'] = self.bgmEdit.text()
        self.config['guard_text_before'] = self.guardEditBefore.text()
        self.config['guard_text_after'] = self.guardEditAfter.text()
        self.config['filter'] = '1' if self.filterToken else '0'
        with codecs.open('config.json', 'w', 'utf_8_sig') as config:
            config.write(json.dumps(self.config, ensure_ascii=False))

    def getFont(self):
        status, font = QFontDialog.getFont(self.font)
        if status:
            font = QFontInfo(font)
            fontName = font.family()
            fontSize = font.pointSize()
            fontBold = font.bold()
            fontItalic = font.italic()
            self.font = QFont(fontName, fontSize)
            if fontBold:
                self.font.setBold(True)
            if fontItalic:
                self.font.setItalic(True)
            self.config['font_name'] = fontName
            self.config['font_size'] = fontSize
            self.config['font_bold'] = '1' if fontBold else '0'
            self.config['font_italic'] = '1' if fontItalic else '0'
            self.fontLabel.setFont(self.font)
            self.GIFWidget.setFont(self.font)
        color = QColorDialog.getColor(self.color)
        if color.isValid():
            self.color = color.name()
            self.config['font_color'] = self.color
            self.fontLabel.setStyleSheet('color:' + self.color)
            self.GIFWidget.setColor(self.color)

    def testAnimate(self):
        if self.bgmEdit.text():
            self.sound.play()
        self.GIFWidget.animationTimer.start()

    def playAnimate(self, giftInfo):
        if self.bgmEdit.text():
            self.sound.play()
        self.GIFWidget.setGiftInfo(giftInfo)
        self.GIFWidget.frame = 180
        self.GIFWidget.animationTimer.start()

    def playGuardAnimate(self, guardName):
        if self.bgmEdit.text():
            self.sound.play()
        guardTextBefore = self.guardEditBefore.text()
        guardTextAfter = self.guardEditAfter.text()
        if not guardTextBefore and not guardTextAfter:
            guardTextBefore = '恭迎'
            guardTextAfter = '舰长登船~~'
            self.guardEditBefore.setText(guardTextBefore)
            self.guardEditAfter.setText(guardTextAfter)
        self.GIFWidget.setGuard([guardTextBefore, guardName, guardTextAfter])
        self.GIFWidget.frame = 180
        self.GIFWidget.animationTimer.start()

    def animateFinish(self):
        self.sound.stop()

    def startMonitor(self):
        if not self.executeToken:
            self.remoteThread = remoteThread(self.roomURLEdit.text())
            self.remoteThread.giftInfo.connect(self.playAnimate)
            self.remoteThread.guard.connect(self.playGuardAnimate)
            self.remoteThread.setFilter(self.filterToken)
            self.remoteThread.start()
            self.executeToken = True
            self.GIFWidget.executeToken = True
            self.GIFWidget.setWindowOpacity(0)
            self.testButton.setEnabled(False)
            self.startButton.setStyleSheet('background-color:#3daee9')
            self.startButton.setText('停止捕获')
        else:
            self.remoteThread.terminate()
            self.remoteThread.quit()
            self.remoteThread.wait()
            self.executeToken = False
            self.GIFWidget.executeToken = False
            self.GIFWidget.setWindowOpacity(1)
            self.testButton.setEnabled(True)
            self.startButton.setStyleSheet('background-color:#31363b')
            self.startButton.setText('开始捕获')
            self.GIFWidget.showText.setText('感谢 甲鱼 投喂的\n100个小心心')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    qss = ''
    try:
        with open('utils/qdark.qss', 'r') as f:
            qss = f.read()
    except:
        print('警告！找不到QSS文件！')
    app.setStyleSheet(qss)
    app.setFont(QFont('微软雅黑', 9))
    mainWindow = MainWindow()
    screen = app.primaryScreen().geometry()
    w, h = 500, 500
    mainWindow.resize(w, h)
    mainWindow.move((screen.width() - w) / 2 - 300, (screen.height() - h) / 2)
    mainWindow.show()
    sys.exit(app.exec_())
