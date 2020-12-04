# -*- coding: utf-8 -*-
from PySide2.QtWidgets import *
from PySide2.QtCore import *


def _translate(context, text, disambig):
    return QApplication.translate(context, text, disambig)


class OptionWidget(QWidget):
    color = Signal(str)
    opacity = Signal(bool)
    top = Signal(bool)

    def __init__(self, color, opacityToken, topToken):
        super().__init__()
        self.resize(540, 130)
        self.setWindowTitle('高级设置')
        layout = QGridLayout()
        self.setLayout(layout)
        backgroundColorButton = QPushButton('背景颜色')
        backgroundColorButton.clicked.connect(self.selectBackgroundColor)
        layout.addWidget(backgroundColorButton, 0, 0, 1, 1)
        self.backgroundColorLabel = QLabel(color)
        self.backgroundColorLabel.setStyleSheet('color:%s' % color)
        layout.addWidget(self.backgroundColorLabel, 0, 1, 1, 1)

        self.opacityButton = QPushButton('透明背景 (需重启)')
        self.opacityButton.clicked.connect(self.setOpacity)
        self.opacityToken = opacityToken
        if self.opacityToken:
            self.opacityButton.setStyleSheet('background-color:#3daee9')
        else:
            self.opacityButton.setStyleSheet('background-color:#31363b')
        layout.addWidget(self.opacityButton, 0, 2, 1, 2)

        self.stayTopButton = QPushButton('特效置顶 (需重启)')
        self.stayTopButton.clicked.connect(self.setTop)
        self.topToken = topToken
        if self.topToken:
            self.stayTopButton.setStyleSheet('background-color:#3daee9')
        else:
            self.stayTopButton.setStyleSheet('background-color:#31363b')
        layout.addWidget(self.stayTopButton, 0, 4, 1, 2)

        layout.addWidget(QLabel('更多使用教程 请访问'), 1, 0, 1, 2)

        bilibili_url = QLabel()
        bilibili_url.setOpenExternalLinks(True)
        bilibili_url.setText(_translate("MainWindow", "<html><head/><body><p><a href=\"https://space.bilibili.com/637783\">\
<span style=\" text-decoration: underline; color:#cccccc;\">执明神君B站主页:  https://space.bilibili.com/637783</span></a></p></body></html>",
                                        None))
        layout.addWidget(bilibili_url, 1, 2, 1, 4)

    def selectBackgroundColor(self):
        color = QColorDialog.getColor(self.backgroundColorLabel.text())
        if color.isValid():
            color = color.name()
            self.color.emit(color)
            self.backgroundColorLabel.setText(color)
            self.backgroundColorLabel.setStyleSheet('color:%s' % color)

    def setOpacity(self):
        self.opacityToken = not self.opacityToken
        if self.opacityToken:
            self.opacityButton.setStyleSheet('background-color:#3daee9')
        else:
            self.opacityButton.setStyleSheet('background-color:#31363b')
        self.opacity.emit(self.opacityToken)

    def setTop(self):
        self.topToken = not self.topToken
        if self.topToken:
            self.stayTopButton.setStyleSheet('background-color:#3daee9')
        else:
            self.stayTopButton.setStyleSheet('background-color:#31363b')
        self.top.emit(self.topToken)
