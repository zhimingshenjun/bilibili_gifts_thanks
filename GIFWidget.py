# -*- coding: utf-8 -*-
import math
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *


class OutlinedLabel(QLabel):
    def __init__(self, text='', fontColor='#FFFFFF', outColor='#FFFFFF'):
        super().__init__()
        self.setText(text)
        self.w = 1 / 10
        self.mode = True
        self.setBrush(QColor(fontColor))
        self.setPen(outColor)

    def scaledOutlineMode(self):
        return self.mode

    def setScaledOutlineMode(self, state):
        self.mode = state

    def outlineThickness(self):
        return self.w * self.font().pointSize() if self.mode else self.w

    def setOutlineThickness(self, value):
        self.w = value

    def setBrush(self, brush):
        if not isinstance(brush, QBrush):
            brush = QBrush(brush)
        self.brush = brush

    def setPen(self, pen):
        if not isinstance(pen, QPen):
            pen = QPen(pen)
        pen.setJoinStyle(Qt.RoundJoin)
        self.pen = pen

    def sizeHint(self):
        w = math.ceil(self.outlineThickness() * 2)
        return super().sizeHint() + QSize(w, w)

    def minimumSizeHint(self):
        w = math.ceil(self.outlineThickness() * 2)
        return super().minimumSizeHint() + QSize(w, w)

    def paintEvent(self, event):
        w = self.outlineThickness()
        rect = self.rect()
        metrics = QFontMetrics(self.font())
        tr = metrics.boundingRect(self.text()).adjusted(0, 0, w, w)
        if self.indent() == -1:
            if self.frameWidth():
                indent = (metrics.boundingRect('x').width() + w * 2) / 2
            else:
                indent = w
        else:
            indent = self.indent()

        if self.alignment() & Qt.AlignLeft:
            x = rect.left() + indent - min(metrics.leftBearing(self.text()['0']), 0)
        elif self.alignment() & Qt.AlignRight:
            x = rect.x() + rect.width() - indent - tr.width()
        else:
            x = (rect.width() - tr.width()) / 2

        if self.alignment() & Qt.AlignTop:
            y = rect.top() + indent + metrics.ascent()
        elif self.alignment() & Qt.AlignBottom:
            y = rect.y() + rect.height() - indent - metrics.descent()
        else:
            y = (rect.height() + metrics.ascent() - metrics.descent()) / 2

        path = QPainterPath()
        path.addText(x, y, self.font(), self.text())
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        self.pen.setWidthF(w * 2)
        qp.strokePath(path, self.pen)
        if 1 < self.brush.style() < 15:
            qp.fillPath(path, self.palette().window())
        qp.fillPath(path, self.brush)


class GIFWidget(QWidget):
    finish = Signal()

    def __init__(self, gifPath='', opacity=False, top=True, frame=180,
                 fontColor='#000000', outColor='#FFFFFF', parent=None):
        super().__init__(parent)
        self.mousePressToken = False
        self.executeToken = False
        self.ID = 'DD'
        self.number = '100'
        self.gift = '小心心'
        self.setWindowTitle('答谢特效')
        if opacity:
            self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlag(Qt.FramelessWindowHint)
        if top:
            self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.show()
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.text = ' 感谢 DD 投喂的100个小心心 '
        self.showText = OutlinedLabel(self.text, fontColor, outColor)
        self.showText.setAlignment(Qt.AlignCenter)
        self.showText.setAttribute(Qt.WA_TranslucentBackground)
        self.layout.addWidget(self.showText, 1, 0, 1, 1)
        self.textOpacity = QGraphicsOpacityEffect()
        self.showText.setGraphicsEffect(self.textOpacity)
        self.textOpacity.setOpacity(1)

        self.showGIF = QLabel()
        self.showGIF.setAttribute(Qt.WA_TranslucentBackground)
        self.showGIF.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.showGIF, 0, 0, 1, 1)
        if gifPath:
            self.movie = QMovie(gifPath)
            self.showGIF.setMovie(self.movie)
            self.movie.start()
        self.gifOpacity = QGraphicsOpacityEffect()
        self.showGIF.setGraphicsEffect(self.gifOpacity)
        self.gifOpacity.setOpacity(1)

        self.totalFrame = frame
        self.frame = self.totalFrame
        self.animationTimer = QTimer()
        self.animationTimer.setInterval(16)
        self.animationTimer.timeout.connect(self.playAnimate)

    def setGIFPath(self, gifPath):
        self.movie = QMovie(gifPath)
        self.showGIF.setMovie(self.movie)
        self.movie.start()

    def setText(self, text, mode, default=False):
        if default:
            self.ID = 'DD'
            self.number = '100'
            self.gift = '小心心'
        if mode == 'gift':
            text = ' %s ' % text.replace('{用户}', self.ID).replace('{数量}', self.number).replace('{礼物}', self.gift)
            self.showText.setText(text)
        elif mode == 'captain':
            text = ' %s ' % text.replace('{用户}', self.ID)
            self.showText.setText(text)

    def setFont(self, font):
        metrics = QFontMetrics(font)
        path = QPainterPath()
        pen = QPen(Qt.red)
        penwidth = 2
        pen.setWidth(penwidth)
        l = metrics.width(self.text)
        w = self.showText.width()
        px = (l - w) / 2
        if px < 0:
            px = -px
        py =  (self.showText.height() - metrics.height()) / 2 + metrics.ascent()
        if py < 0:
            py = -py
        path.addText(px, py, font, self.text)
        painter = QPainter()
        painter.strokePath(path, pen)
        painter.drawPath(path)
        painter.fillPath(path, QBrush(Qt.red))
        self.showText.setFont(font)

    def setColor(self, color):
        self.showText.setStyleSheet('color:' + color)

    def setBackgroundColor(self, color):
        self.setStyleSheet('background-color:%s' % color)

    def setGiftInfo(self, giftInfo):
        self.text = ' 感谢 %s 投喂的%s个%s ' % tuple(giftInfo)
        self.showText.setText(self.text)

    def setGuard(self, guardInfo):
        self.text = '%s %s %s' % tuple(guardInfo)
        self.showText.setText(self.text)

    def setSecond(self, seconds):
        self.frame = seconds * 60
        self.totalFrame = seconds * 60

    def mousePressEvent(self, QEvent):
        self.mousePressToken = True
        self.startPos = QEvent.pos()

    def mouseReleaseEvent(self, QEvent):
        self.mousePressToken = False

    def mouseMoveEvent(self, QEvent):
        if self.mousePressToken:
            self.move(self.pos() + (QEvent.pos() - self.startPos))

    def playAnimate(self):
        if self.frame >= self.totalFrame - 10:
            self.gifOpacity.setOpacity((self.totalFrame - self.frame) / 10)
            self.textOpacity.setOpacity((self.totalFrame - self.frame) / 10)
            self.frame -= 1
        elif self.frame > 40:
            self.frame -= 1
        elif self.frame > 0:
            self.gifOpacity.setOpacity(self.frame / 40)
            self.textOpacity.setOpacity(self.frame / 40)
            self.frame -= 1
        else:
            self.frame = self.totalFrame
            self.animationTimer.stop()
            if not self.executeToken:
                self.gifOpacity.setOpacity(1)
                self.textOpacity.setOpacity(1)
            else:
                self.gifOpacity.setOpacity(0)
                self.textOpacity.setOpacity(0)
            self.finish.emit()