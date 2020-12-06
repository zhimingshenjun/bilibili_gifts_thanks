# -*- coding: utf-8 -*-
import os
import sys
import shutil
import json
import codecs
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtMultimedia import QMediaPlayer
from remote import remoteThread
from GIFWidget import GIFWidget
from option import OptionWidget


class Slider(QSlider):
    pointClicked = Signal(QPoint)

    def __init__(self):
        super(Slider, self).__init__()
        self.setOrientation(Qt.Horizontal)

    def mousePressEvent(self, event):
        self.pointClicked.emit(event.pos())

    def mouseMoveEvent(self, event):
        self.pointClicked.emit(event.pos())


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
        self.setFixedWidth(540)
        self.sound = QMediaPlayer()
        self.executeToken = False
        self.setAcceptDrops(True)
        self.installEventFilter(self)
        self.presetIndex = '0'
        if os.path.exists('utils/config.json'):
            with codecs.open('utils/config.json', 'r', 'utf_8_sig') as config:
                config = config.read()
            self.config = json.loads(config)
        else:
            self.config = {str(x): {'gift': '请输入礼物名字 多个礼物间用空格隔开', 'words': '感谢 {用户} 投喂的{数量}个{礼物}~',
                                    'bgm_path': '', 'volume': 100, 'gif_path': '', 'gif_scale': 50,
                                    'second': 4, 'font_color': '#3c9dca', 'out_color': '#1c54a7', 'out_size': 15,
                                    'font_name': '微软雅黑', 'font_size': 36, 'font_bold': False, 'font_italic': False
                                    } for x in range(10)}
            self.config['0']['gift'] = ('辣条 小心心 “棋”开得胜 盛典门票 盛典之杯 吃瓜 冰阔落 给大佬递茶 打榜 盛典小电视 '
                                        'B坷垃 天空之翼 摩天大楼 礼花 凉了 比心 喵娘 节奏风暴 疯狂打call 泡泡机 爱之魔力 '
                                        '摩天轮 转运锦鲤 冲浪 亿圆')
            self.config['9']['words'] = '恭迎 {用户} 上舰~~~'
            self.config['room_url'] = '123456'
            self.config['background_color'] = '#00d600'
            self.config['opacity'] = False
            self.config['top'] = False
        self.gift = self.config['0']['gift']
        self.second = self.config['0']['second']
        self.color = self.config['0']['font_color']
        self.outColor = self.config['0']['out_color']
        self.outSize = self.config['0']['out_size']
        self.gifScale = self.config['0']['gif_scale']
        self.gifSize = None
        self.volume = self.config['0']['volume']
        self.oldBGM = self.config['0']['bgm_path']
        self.movieList = []
        self.gifSizeList = []
        for index in [str(i) for i in range(10)]:
            movie = QMovie(self.config[index]['gif_path'])
            gifSize = QPixmap(self.config[index]['gif_path']).size()
            if gifSize:
                movie.setScaledSize(gifSize * self.config[index]['gif_scale'] / 50)
            self.movieList.append(movie)
            self.gifSizeList.append(gifSize)
        self.option = OptionWidget(self.config['background_color'], self.config['opacity'], self.config['top'])
        self.option.color.connect(self.selectBackgroundColor)
        self.option.opacity.connect(self.setopacity)
        self.option.top.connect(self.setTop)

        self.GIFWidget = GIFWidget(self.movieList[0], self.config['opacity'],
                                   self.config['top'], self.second * 60, self.color, self.outColor)
        self.GIFWidget.showText.w = self.outSize / 250
        self.GIFWidget.setBackgroundColor(self.config['background_color'])
        self.GIFWidget.finish.connect(self.animateFinish)
        self.GIFWidget.moveDelta.connect(self.changeCenter)
        self.GIFWidget.setText(self.config['0']['words'], 'gift')
        w, h = self.GIFWidget.width(), self.GIFWidget.height()
        x, y = self.GIFWidget.pos().x(), self.GIFWidget.pos().y()
        self.GIFWidgetCenterPos = QPoint(x + w / 2, y + h / 2)

        self.setWindowTitle('DD答谢机 V1.0  (by 执明神君)')
        self.main_widget = QWidget()
        self.main_widget.setAcceptDrops(True)
        self.setCentralWidget(self.main_widget)
        layout = QGridLayout()
        self.main_widget.setLayout(layout)
        self.roomIDLabel = QLabel('B站直播房间')
        self.roomIDLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.roomIDLabel, 0, 0, 1, 1)
        self.biliLiveLabel = QLabel('https://live.bilibili.com/')
        layout.addWidget(self.biliLiveLabel, 0, 2, 1, 2)
        self.roomURLEdit = QLineEdit(self.config['room_url'])
        self.roomURLEdit.setValidator(QIntValidator(0, 2000000000))
        self.roomURLEdit.textChanged.connect(self.setURL)
        layout.addWidget(self.roomURLEdit, 0, 4, 1, 3)

        self.presetCombobox = QComboBox()
        self.presetCombobox.addItems(['    礼物预设%d' % x for x in range(1, 10)] + ['    舰长上船'])
        self.presetCombobox.currentIndexChanged.connect(self.changePreset)
        layout.addWidget(self.presetCombobox, 1, 0, 1, 1)
        self.giftEdit = QLineEdit(self.gift)
        self.giftEdit.textChanged.connect(self.changeGift)
        layout.addWidget(self.giftEdit, 1, 2, 1, 5)

        self.defaultWordsButton = QPushButton('重置台词')
        self.defaultWordsButton.clicked.connect(self.setDefaultWords)
        layout.addWidget(self.defaultWordsButton, 2, 0, 1, 1)
        self.wordsEdit = QLineEdit(self.config['0']['words'])
        self.wordsEdit.textChanged.connect(self.setWords)
        layout.addWidget(self.wordsEdit, 2, 2, 1, 5)

        self.fontButton = QPushButton('字体设置')
        self.fontButton.clicked.connect(self.getFont)
        layout.addWidget(self.fontButton, 3, 0, 1, 1)
        self.fontLabel = QLabel()
        fontInfo = '%s  %s  %s  ' % (self.config['0']['font_name'], self.config['0']['font_size'], self.config['0']['font_color'])
        self.font = QFont(self.config['0']['font_name'], self.config['0']['font_size'])
        if self.config['0']['font_bold']:
            self.font.setBold(self.config['0']['font_bold'])
            fontInfo += '加粗  '
        if self.config['0']['font_italic']:
            self.font.setItalic(self.config['0']['font_italic'])
            fontInfo += '斜体'
        self.fontLabel.setText(fontInfo)
        self.fontLabel.setStyleSheet('color:' + self.color)
        self.GIFWidget.setFont(self.font)
        self.GIFWidget.setColor(self.color)
        layout.addWidget(self.fontLabel, 3, 2, 1, 5)

        self.outLineButton = QPushButton('描边颜色')
        self.outLineButton.clicked.connect(self.setOutLine)
        layout.addWidget(self.outLineButton, 4, 0, 1, 1)
        self.outLineLabel = QLabel(self.outColor)
        self.outLineLabel.setStyleSheet('color:' + self.outColor)
        layout.addWidget(self.outLineLabel, 4, 2, 1, 1)
        self.outLineSizeLabel = QLabel('粗细')
        self.outLineSizeLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.outLineSizeLabel, 4, 4, 1, 1)
        self.outLineSizeBar = Slider()
        self.outLineSizeBar.setMaximum(100)
        self.outLineSizeBar.setValue(self.outSize)
        self.outLineSizeBar.pointClicked.connect(self.sizeChange)
        layout.addWidget(self.outLineSizeBar, 4, 5, 1, 2)

        self.bgmButton = QPushButton('音效设置')
        self.bgmButton.clicked.connect(self.selectBGM)
        layout.addWidget(self.bgmButton, 5, 0, 1, 1)
        self.bgmEdit = QLabel(os.path.split(self.config['0']['bgm_path'])[1])
        self.sound.setMedia(QUrl.fromLocalFile(self.config['0']['bgm_path']))
        layout.addWidget(self.bgmEdit, 5, 2, 1, 2)
        self.volumeLabel = QLabel('音量')
        self.volumeLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.volumeLabel, 5, 4, 1, 1)
        self.volumeBar = Slider()
        self.volumeBar.setMaximum(100)
        self.volumeBar.setValue(self.volume)
        self.volumeBar.pointClicked.connect(self.changevolume)
        layout.addWidget(self.volumeBar, 5, 5, 1, 2)

        self.animeSecond = QLabel('持续时间')
        self.animeSecond.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.animeSecond, 6, 0, 1, 1)
        self.animeSecondComboBox = QComboBox()
        self.animeSecondComboBox.addItems([str(i) + '秒' for i in range(1, 31)])
        self.animeSecondComboBox.setCurrentIndex(self.second - 1)
        self.animeSecondComboBox.currentIndexChanged.connect(self.setSecond)
        layout.addWidget(self.animeSecondComboBox, 6, 2, 1, 2)

        self.scaledValue = QLabel('大小')
        self.scaledValue.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.scaledValue, 6, 4, 1, 1)
        self.scaledBar = Slider()
        self.scaledBar.setValue(self.gifScale)
        self.scaledBar.pointClicked.connect(self.scaleChange)
        layout.addWidget(self.scaledBar, 6, 5, 1, 2)

        self.advancedButton = QPushButton('高级设置')
        self.advancedButton.clicked.connect(self.popOption)
        layout.addWidget(self.advancedButton, 7, 0, 1, 1)

        self.preview = previewLabel('点击或拖入要播放的答谢gif动图')
        self.preview.setFrameShape(QFrame.Box)
        self.preview.setStyleSheet('border:2px dotted #cfcfd0')
        self.preview.setMaximumSize(522, 400)
        self.preview.click.connect(self.click)
        if self.config['0']['gif_path']:
            self.gifSize = self.gifSizeList[0]
            self.movie = self.movieList[0]
            self.movie.setScaledSize(self.gifSize * self.gifScale / 50)
            self.preview.setMovie(self.movie)
            # self.GIFWidget.movie.setScaledSize(self.gifSize * self.gifScale / 50)
            self.movie.start()
        layout.addWidget(self.preview, 8, 0, 4, 7)

        self.testButton = QPushButton('预览效果')
        self.testButton.clicked.connect(self.testAnimate)
        self.testButton.setFixedSize(205, 65)
        layout.addWidget(self.testButton, 12, 0, 2, 3)

        self.startButton = QPushButton('开始捕获')
        self.startButton.clicked.connect(self.startMonitor)
        self.startButton.setFixedSize(205, 65)
        layout.addWidget(self.startButton, 12, 4, 2, 3)

        self.resizeTimer = QTimer()
        self.resizeTimer.setInterval(16)
        self.resizeTimer.timeout.connect(self.resizeGIFWidget)
        self.resizeTimer.start()

        self.widgetsList = [self.roomURLEdit, self.presetCombobox, self.giftEdit, self.defaultWordsButton,
                            self.wordsEdit, self.fontButton, self.outLineButton, self.outLineSizeBar,
                            self.bgmButton, self.volumeBar, self.animeSecondComboBox, self.scaledBar,
                            self.advancedButton, self.preview, self.testButton, self.outLineSizeLabel,
                            self.volumeLabel, self.scaledValue, self.animeSecond, self.bgmEdit,
                            self.roomIDLabel, self.biliLiveLabel, self.fontLabel, self.outLineLabel]

    def resizeGIFWidget(self):
        self.GIFWidget.resize(300, 200)
        self.resize(540, 600)
        w, h = self.GIFWidget.width(), self.GIFWidget.height()
        x, y = self.GIFWidget.pos().x(), self.GIFWidget.pos().y()
        currentCenterPos = QPoint(x + w / 2, y + h / 2)
        self.GIFWidget.move(self.GIFWidget.pos() - currentCenterPos + self.GIFWidgetCenterPos)

    def changePreset(self, index):
        if index == 9:
            self.giftEdit.setEnabled(False)
        else:
            self.giftEdit.setEnabled(True)
        self.presetIndex = str(index)
        self.gift = self.config[self.presetIndex]['gift']
        self.giftEdit.setText(self.gift)
        self.wordsEdit.setText(self.config[self.presetIndex]['words'])

        self.second = self.config[self.presetIndex]['second']
        self.animeSecondComboBox.setCurrentIndex(self.second - 1)
        self.GIFWidget.setSecond(self.second)
        self.color = self.config[self.presetIndex]['font_color']

        fontInfo = '%s  %s  %s  ' % (self.config[self.presetIndex]['font_name'],
                                     self.config[self.presetIndex]['font_size'],
                                     self.config[self.presetIndex]['font_color'])
        self.font = QFont(self.config[self.presetIndex]['font_name'],
                          self.config[self.presetIndex]['font_size'])
        if self.config[self.presetIndex]['font_bold']:
            self.font.setBold(self.config[self.presetIndex]['font_bold'])
            fontInfo += '加粗  '
        if self.config[self.presetIndex]['font_italic']:
            self.font.setItalic(self.config[self.presetIndex]['font_italic'])
            fontInfo += '斜体'
        self.fontLabel.setText(fontInfo)
        self.fontLabel.setStyleSheet('color:' + self.color)
        self.GIFWidget.setFont(self.font)
        self.GIFWidget.showText.setBrush(QColor(self.color))

        self.outColor = self.config[self.presetIndex]['out_color']

        self.config[self.presetIndex]['out_color'] = self.outColor
        self.GIFWidget.showText.setPen(self.outColor)
        self.GIFWidget.showText.repaint()
        self.outLineLabel.setText(self.outColor)
        self.outLineLabel.setStyleSheet('color:' + self.outColor)

        self.outSize = self.config[self.presetIndex]['out_size']

        self.outLineSizeBar.setValue(self.outSize)
        self.config[self.presetIndex]['out_size'] = self.outSize
        self.GIFWidget.showText.w = self.outSize / 250
        self.GIFWidget.showText.repaint()

        self.preview.clear()
        self.GIFWidget.showGIF.clear()
        self.preview.setText('点击或拖入要播放的答谢gif动图')
        if self.config[self.presetIndex]['gif_path']:
            self.movie = self.movieList[index]
            self.gifSize = self.gifSizeList[index]
            pos = self.config[self.presetIndex]['gif_scale']
            self.scaledBar.setValue(pos)
            if self.gifSize:
                self.movie.setScaledSize(self.gifSize * pos / 50)
            self.preview.setMovie(self.movie)
            self.GIFWidget.showGIF.setMovie(self.movie)
            self.movie.start()

        self.bgmEdit.setText(os.path.split(self.config[self.presetIndex]['bgm_path'])[1])
        self.sound.setMedia(QUrl.fromLocalFile(self.config[self.presetIndex]['bgm_path']))

        self.volume = self.config[self.presetIndex]['volume']
        self.volumeBar.setValue(self.volume)
        self.sound.setVolume(self.volume)

    def setURL(self, text):
        self.config['room_url'] = text

    def setWords(self, text):
        if self.presetIndex == '9':
            self.GIFWidget.setText(text, 'captain')
        else:
            self.GIFWidget.setText(text, 'gift')
        self.config[self.presetIndex]['words'] = text

    def setDefaultWords(self):
        if self.presetIndex == '9':
            text = '恭迎 {用户} 上舰~~~'
            self.GIFWidget.setText(text, 'captain')
        else:
            text = '感谢 {用户} 投喂的{数量}个{礼物}~'
            self.GIFWidget.setText(text, 'gift')
        self.wordsEdit.setText(text)
        self.config[self.presetIndex]['words'] = text

    def changeGift(self):
        self.config[self.presetIndex]['gift'] = self.giftEdit.text()

    def selectBGM(self):
        if not os.path.exists('bgm'):
            os.mkdir('bgm')
        filePath = QFileDialog.getOpenFileName(self, "请选择bgm文件", 'bgm', "*.mp3 *.wav")[0]
        if filePath:
            fileName = os.path.split(filePath)[1]
            if not os.path.exists(r'bgm/%s' % fileName):
                shutil.copy(filePath, 'bgm')
            self.bgmEdit.setText(os.path.split(filePath)[1])
            self.sound.setMedia(QUrl.fromLocalFile(filePath))
            self.config[self.presetIndex]['bgm_path'] = filePath

    def changevolume(self, p):
        pos = p.x() / self.volumeBar.width() * 100
        if pos > 100:
            pos = 100
        elif pos < 0:
            pos = 0
        self.volumeBar.setValue(pos)
        self.volume = pos
        self.sound.setVolume(pos)
        self.config[self.presetIndex]['volume'] = pos

    def selectBackgroundColor(self, color):
        self.config['background_color'] = color
        self.GIFWidget.setBackgroundColor(color)

    def setTop(self, topToken):
        self.config['top'] = topToken

    def setopacity(self, opacityToken):
        self.config['opacity'] = opacityToken

    def setSecond(self, index):
        self.second = index + 1
        self.GIFWidget.setSecond(self.second)
        self.config[self.presetIndex]['second'] = self.second

    def scaleChange(self, p):
        pos = p.x() / self.scaledBar.width() * 100
        if pos > 100:
            pos = 100
        elif pos < 1:
            pos = 1
        self.scaledBar.setValue(pos)
        self.config[self.presetIndex]['gif_scale'] = pos
        scale = pos / 50
        if self.gifSize:
            self.movie.setScaledSize(self.gifSize * scale)
            # self.GIFWidget.movie.setScaledSize(self.gifSize * scale)

    def sizeChange(self, p):
        self.outSize = p.x() / self.outLineSizeBar.width() * 100
        if self.outSize > 100:
            self.outSize = 100
        elif self.outSize < 1:
            self.outSize = 1
        self.outLineSizeBar.setValue(self.outSize)
        self.config[self.presetIndex]['out_size'] = self.outSize
        self.GIFWidget.showText.w = self.outSize / 400
        self.GIFWidget.showText.repaint()

    def click(self):
        filePath = QFileDialog.getOpenFileName(self, "请选择gif文件", 'gif', "*.gif;;所有文件 *.*")[0]
        if filePath:
            self.openFile(filePath)
        else:
            self.preview.clear()
            self.GIFWidget.showGIF.clear()
            self.preview.setText('点击或拖入要播放的答谢gif动图')
            self.config[self.presetIndex]['gif_path'] = ''

    def openFile(self, filePath):
        fileName = os.path.split(filePath)[1]
        if not os.path.exists('gif'):
            os.mkdir('gif')
        if not os.path.exists(r'gif/%s' % fileName):
            shutil.copy(filePath, 'gif')
        self.gifSize = QPixmap(filePath).size()
        index = self.presetCombobox.currentIndex()
        self.movieList[index] = QMovie(filePath)
        self.movie = self.movieList[index]
        self.preview.setMovie(self.movie)
        self.GIFWidget.showGIF.setMovie(self.movie)
        self.movie.start()
        # self.GIFWidget.setGIFPath(filePath)
        self.config[self.presetIndex]['gif_path'] = r'%s/gif/%s' % (os.getcwd(), fileName)
        self.scaledBar.setValue(50)

    def dragEnterEvent(self, QDragEnterEvent):
        QDragEnterEvent.accept()

    def dropEvent(self, QEvent):
        if QEvent.mimeData().hasUrls:
            self.openFile(QEvent.mimeData().urls()['0'].toLocalFile())

    def closeEvent(self, QCloseEvent):
        self.GIFWidget.close()
        self.option.close()
        with codecs.open('utils/config.json', 'w', 'utf_8_sig') as config:
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
            self.config[self.presetIndex]['font_name'] = fontName
            self.config[self.presetIndex]['font_size'] = fontSize
            self.config[self.presetIndex]['font_bold'] = fontBold
            self.config[self.presetIndex]['font_italic'] = fontItalic
            self.GIFWidget.setFont(self.font)
            fontInfo = '%s  %s  %s  ' % (self.config[self.presetIndex]['font_name'],
                                         self.config[self.presetIndex]['font_size'],
                                         self.config[self.presetIndex]['font_color'])
            if fontBold:
                fontInfo += '加粗  '
            if fontItalic:
                fontInfo += '斜体'
            self.fontLabel.setText(fontInfo)
            self.fontLabel.setStyleSheet('color:' + self.color)
        color = QColorDialog.getColor(self.color)
        if color.isValid():
            self.color = color.name()
            self.config[self.presetIndex]['font_color'] = self.color
            self.GIFWidget.showText.setBrush(QColor(self.color))
            self.GIFWidget.showText.repaint()

    def setOutLine(self):
        color = QColorDialog().getColor(self.outColor)
        if color.isValid():
            self.outColor = color.name()
            self.config[self.presetIndex]['out_color'] = self.outColor
            self.GIFWidget.showText.setPen(self.outColor)
            self.GIFWidget.showText.repaint()
            self.outLineLabel.setText(self.outColor)
            self.outLineLabel.setStyleSheet('color:' + self.outColor)

    def setConfig(self, config, mode, index):
        self.GIFWidget.setText(config['words'], mode)

        # self.movie = self.movieList[index]
        # self.gifSize = self.gifSizeList[index]
        # if self.gifSize:
        #     self.movie.setScaledSize(self.gifSize * config['gif_scale'] / 50)
        # self.GIFWidget.showGIF.setMovie(self.movie)
        # self.movie.start()

        self.GIFWidget.showGIF.clear()
        movie = self.movieList[index]
        gifSize = self.gifSizeList[index]
        if gifSize:
            movie.setScaledSize(gifSize * config['gif_scale'] / 50)
        self.GIFWidget.showGIF.setMovie(movie)
        # self.GIFWidget.movie = QMovie(config['gif_path'])
        # self.gifSize = QPixmap(config['gif_path']).size()
        # if self.gifSize:
        #     self.GIFWidget.movie.setScaledSize(self.gifSize * config['gif_scale'] / 50)
        # self.GIFWidget.showGIF.setMovie(self.GIFWidget.movie)
        # self.GIFWidget.movie.start()
        self.GIFWidget.setSecond(config['second'])
        self.GIFWidget.showText.setBrush(QColor(config['font_color']))
        self.GIFWidget.showText.setPen(config['out_color'])
        self.GIFWidget.showText.w = config['out_size'] / 400
        self.GIFWidget.showText.repaint()
        font = QFont(config['font_name'], config['font_size'])
        if config['font_bold']:
            font.setBold(True)
        if config['font_italic']:
            font.setItalic(True)
        self.GIFWidget.setFont(font)

    def testAnimate(self):
        if self.bgmEdit.text():
            self.sound.stop()
            self.sound.play()
        self.GIFWidget.frame = self.second * 60
        self.GIFWidget.animationTimer.start()

    def playAnimate(self, giftInfo):
        uid, num, gift = giftInfo
        self.GIFWidget.ID = uid
        self.GIFWidget.number = str(num)
        self.GIFWidget.gift = gift
        self.GIFWidget.gifOpacity.setOpacity(0)
        self.GIFWidget.textOpacity.setOpacity(0)
        if gift == 'captain':
            self.setConfig(self.config['9'], 'captain', 9)
            self.GIFWidget.animationTimer.start()
            presetIndex = '9'
        else:
            for presetIndex in ['8', '7', '6', '5', '4', '3', '2', '1', '0']:
                if gift in self.config[presetIndex]['gift']:
                    self.setConfig(self.config[presetIndex], 'gift', int(presetIndex))
                    self.GIFWidget.animationTimer.start()
                    break
        bgm = self.config[presetIndex]['bgm_path']
        if bgm:
            # if bgm != self.oldBGM:
            #     self.oldBGM = bgm
            self.sound.setMedia(QUrl.fromLocalFile(bgm))
            self.sound.setVolume(self.config[presetIndex]['volume'])
            self.sound.play()

    def popOption(self):
        self.option.hide()
        self.option.show()

    def animateFinish(self):
        self.sound.stop()

    def changeCenter(self, qpoint):
        self.GIFWidgetCenterPos += qpoint

    def startMonitor(self):
        if not self.executeToken:
            self.remoteThread = remoteThread(self.config['room_url'])
            self.remoteThread.giftInfo.connect(self.playAnimate)
            self.remoteThread.start()
            for widget in self.widgetsList:
                widget.setEnabled(False)
            self.executeToken = True
            self.GIFWidget.executeToken = True
            self.GIFWidget.gifOpacity.setOpacity(0)
            self.GIFWidget.textOpacity.setOpacity(0)
            self.startButton.setStyleSheet('background-color:#3daee9')
            self.startButton.setText('停止捕获')
        else:
            self.sound.stop()
            self.GIFWidget.animationTimer.stop()

            self.GIFWidget.showGIF.clear()
            self.GIFWidget.showGIF.setMovie(self.movie)

            self.remoteThread.terminate()
            self.remoteThread.quit()
            self.remoteThread.wait()
            for widget in self.widgetsList:
                widget.setEnabled(True)
            self.executeToken = False
            self.GIFWidget.executeToken = False
            self.GIFWidget.gifOpacity.setOpacity(1)
            self.GIFWidget.textOpacity.setOpacity(1)
            self.startButton.setStyleSheet('background-color:#31363b')
            self.startButton.setText('开始捕获')
            text = self.wordsEdit.text()
            if self.presetIndex == '9':
                self.GIFWidget.setText(text, 'captain', True)
            else:
                self.GIFWidget.setText(text, 'gift', True)


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
    w, h = 540, 600
    mainWindow.resize(w, h)
    mainWindow.move((screen.width() - w) / 2 - 300, (screen.height() - h) / 2)
    mainWindow.show()
    mainWindow.GIFWidget.hide()
    mainWindow.GIFWidget.show()
    sys.exit(app.exec_())
