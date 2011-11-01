# -*- coding: utf-8 -*-
from __future__ import absolute_import

from PyQt4.QtGui import QWidget
from ninja_ide.tools import ui_tools
from PyQt4.QtGui import QKeySequence
from PyQt4.QtGui import QSizePolicy
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QComboBox
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QSplitter
from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QSettings

from ninja_ide import resources
from ninja_ide.core import settings


__centralWidgetInstance = None


def CentralWidget(*args, **kw):
    global __centralWidgetInstance
    if __centralWidgetInstance is None:
        __centralWidgetInstance = __CentralWidget(*args, **kw)
    return __centralWidgetInstance


class __CentralWidget(QWidget):

###############################################################################
# CentralWidget SIGNALS
###############################################################################

    """
    splitterCentralRotated()
    """

###############################################################################

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        #This variables are used to save the splitter sizes before hide
        self._splitterMainSizes = None
        self._splitterAreaSizes = None
        self.lateralPanel = None

        vbox = QVBoxLayout(self)
        #Create Splitters to divide the UI in: MainPanel, Explorer, Misc
        self._splitterArea = QSplitter(Qt.Horizontal)
        self._splitterMain = QSplitter(Qt.Vertical)

        #Add to Main Layout
        vbox.addWidget(self._splitterArea)

    def insert_central_container(self, container):
        self.mainContainer = container
        self._splitterMain.insertWidget(0, container)

    def insert_lateral_container(self, container):
        self.lateralPanel = LateralPanel(container)
        self._splitterArea.insertWidget(0, self.lateralPanel)

    def insert_bottom_container(self, container):
        self.misc = container
        self._splitterMain.insertWidget(1, container)

    def showEvent(self, event):
        #Rearrange widgets on Window
        self._splitterArea.insertWidget(0, self._splitterMain)
        #Show Event
        QWidget.showEvent(self, event)
        qsettings = QSettings()
        #Lists of sizes as list of QVariant- heightList = [QVariant, QVariant]
        heightList = qsettings.value("window/central/mainSize",
            [(self.height() / 3) * 2, self.height() / 3]).toList()
        widthList = qsettings.value("window/central/areaSize",
            [(self.width() / 6) * 5, self.width() / 6]).toList()
        self._splitterMainSizes = [
            heightList[0].toInt()[0], heightList[1].toInt()[0]]
        self._splitterAreaSizes = [
            widthList[0].toInt()[0], widthList[1].toInt()[0]]
        #Set the sizes to splitters
        self._splitterMain.setSizes(self._splitterMainSizes)
        self._splitterArea.setSizes(self._splitterAreaSizes)
        if not event.spontaneous():
            self.change_misc_visibility()
        if bin(settings.UI_LAYOUT)[-1] == '1':
            self.splitter_central_rotate()
        if bin(settings.UI_LAYOUT >> 1)[-1] == '1':
            self.splitter_misc_rotate()
        if bin(settings.UI_LAYOUT >> 2)[-1] == '1':
            self.splitter_central_orientation()

    def change_misc_visibility(self):
        if self.misc.isVisible():
            self._splitterMainSizes = self._splitterMain.sizes()
            self.misc.hide()
            widget = self.mainContainer.get_actual_widget()
            if widget:
                widget.setFocus()
        else:
            self.misc.show()
            self.misc.gain_focus()

    def change_main_visibility(self):
        if self.mainContainer.isVisible():
            self.mainContainer.hide()
        else:
            self.mainContainer.show()

    def change_explorer_visibility(self):
        if self.lateralPanel.isVisible():
            self._splitterAreaSizes = self._splitterArea.sizes()
            self.lateralPanel.hide()
        else:
            self.lateralPanel.show()

    def splitter_central_rotate(self):
        w1, w2 = self._splitterArea.widget(0), self._splitterArea.widget(1)
        self._splitterArea.insertWidget(0, w2)
        self._splitterArea.insertWidget(1, w1)
        self.emit(SIGNAL("splitterCentralRotated()"))

    def splitter_central_orientation(self):
        if self._splitterArea.orientation() == Qt.Horizontal:
            self._splitterArea.setOrientation(Qt.Vertical)
        else:
            self._splitterArea.setOrientation(Qt.Horizontal)

    def splitter_misc_rotate(self):
        w1, w2 = self._splitterMain.widget(0), self._splitterMain.widget(1)
        self._splitterMain.insertWidget(0, w2)
        self._splitterMain.insertWidget(1, w1)

    def splitter_misc_orientation(self):
        if self._splitterMain.orientation() == Qt.Horizontal:
            self._splitterMain.setOrientation(Qt.Vertical)
        else:
            self._splitterMain.setOrientation(Qt.Horizontal)

    def get_area_sizes(self):
        if self.lateralPanel.isVisible():
            self._splitterAreaSizes = self._splitterArea.sizes()
        return self._splitterAreaSizes

    def get_main_sizes(self):
        if self.misc.isVisible():
            self._splitterMainSizes = self._splitterMain.sizes()
        return self._splitterMainSizes


class LateralPanel(QWidget):

    def __init__(self, explorer):
        QWidget.__init__(self)
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(explorer)
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.labelText = "Ln: %1, Col: %2"
        self.labelCursorPosition = QLabel(self.tr(self.labelText).arg(
            0).arg(0))
        hbox.addWidget(self.labelCursorPosition)
        self.combo = QComboBox()
        ui_tools.ComboBoxButton(self.combo, self.combo.clear,
            self.style().standardPixmap(self.style().SP_TrashIcon))
        self.combo.setToolTip(self.tr("Select the item from the Paste "
            "Historial list.\nYou can Copy items into this list with: "
            "%1\nor Paste them using: %2").arg(
                resources.get_shortcut("History-Copy").toString(
                    QKeySequence.NativeText)).arg(
                resources.get_shortcut("History-Paste").toString(
                    QKeySequence.NativeText)))
        self.combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hbox.addWidget(self.combo)
        vbox.addLayout(hbox)

    def update_line_col(self, line, col):
        self.labelCursorPosition.setText(self.tr(
            self.labelText).arg(line).arg(col))

    def add_new_copy(self, copy):
        self.combo.insertItem(0, copy)
        self.combo.setCurrentIndex(0)
        if self.combo.count() > settings.COPY_HISTORY_BUFFER:
            self.combo.removeItem(self.combo.count() - 1)

    def get_paste(self):
        return unicode(self.combo.currentText())