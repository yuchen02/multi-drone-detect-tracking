# -*- coding: utf-8 -*-
import sys
from PyQt5 import  QtWidgets
from PyQt5.QtGui import QIcon

from core.ui_process import MyWindow

if __name__=="__main__":
    app = QtWidgets.QApplication(sys.argv)
    icon=QIcon("source/icon.ico")
    app.setWindowIcon(icon)
    ui = MyWindow()
    ui.show()
    sys.exit(app.exec_())

