# *-* coding: utf-8 *-*
from __future__ import absolute_import

import os
import sys

from PyQt4.QtGui import QWizard
from PyQt4.QtGui import QWizardPage
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QComboBox
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QPlainTextEdit
from PyQt4.QtGui import QGridLayout
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QFileDialog
from PyQt4.QtGui import QListWidget
from PyQt4.QtGui import QPixmap
from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL

from ninja_ide import resources
from ninja_ide.core import settings
from ninja_ide.core import plugin_interfaces
from ninja_ide.core import file_manager
from ninja_ide.tools import json_manager


class WizardNewProject(QWizard, plugin_interfaces.IProjectTypeHandler):

    def __init__(self, parent):
        QWizard.__init__(self, parent)
        self.__explorer = parent
        self.setWindowTitle(self.tr("NINJA - New Project Wizard"))
        self.setPixmap(QWizard.LogoPixmap, QPixmap(resources.IMAGES['icon']))

        self.option = 'Python'
        #settings.PROJECT_TYPES[self.option] = self
        #Add a project type handler for Python
        settings.set_project_type_handler(self.option, self)

        self.addPage(PageProjectType(self))
        self.addPage(PageProjectProperties())

    def get_pages(self):
        """
        We do not implementd the get_pages because this class is a special one
        is like a Manager and a Handler at the same time
        """
        return ()

    def add_project_pages(self, option='Python'):
        self.option = option
        #pages = settings.PROJECT_TYPES[option].getPages()
        pages = settings.get_project_type_handler(option).get_pages()
        listIds = self.pageIds()
        listIds.pop(listIds.index(0))
        for page in pages:
            self.addPage(page)
        #this page is always needed by a project!
        self.addPage(PageProjectProperties())
        for i in listIds:
            self.removePage(i)

    def get_context_menus(self):
        """
        Get  a special menu for Python projects
        """
        return ()

    def done(self, result):
        if result == 1:
            page = self.currentPage()
            if type(page) == PageProjectProperties:
                venv = unicode(page.vtxtPlace.text())
                if venv:
                    if sys.platform == 'win32':
                        venv = os.path.join(venv, 'Scripts', 'python')
                    else:
                        venv = os.path.join(venv, 'bin', 'python')
                    #check if venv folder exists
                    if  not os.path.exists(venv):
                        btnPressed = QMessageBox.information(self,
                            self.tr("Virtualenv Folder"),
                            self.tr("Folder don't exists or this is not a " \
                                "valid Folder.\n If you want to set " \
                                "or modify, go to project properties"),
                            self.tr("Back"),
                            self.tr("Continue"))
                        if btnPressed == QMessageBox.NoButton:
                            return
                        else:
                            self.currentPage().vtxtPlace.setText("")
                page.vtxtPlace.setText(venv)
            #settings.PROJECT_TYPES[self.option].onWizardFinish(self)
            settings.get_project_type_handler(self.option)\
                .on_wizard_finish(self)
        super(WizardNewProject, self).done(result)

    def on_wizard_finish(self, wizard):
        ids = wizard.pageIds()
        page = wizard.page(ids[1])
        place = unicode(page.txtPlace.text())
        if not place:
            QMessageBox.critical(self, self.tr("Incorrect Location"),
                self.tr("The project couldn\'t be create"))
            return
        folder = unicode(page.txtFolder.text()).replace(' ', '_')
        path = os.path.join(place, folder)
        try:
            file_manager.create_folder(path)
        except:
            QMessageBox.critical(self, self.tr("Incorrect Location"),
                self.tr("The folder already exists."))
            return
        project = {}
        name = unicode(page.txtName.text())
        project['name'] = name
        project['description'] = unicode(page.txtDescription.toPlainText())
        project['license'] = unicode(page.cboLicense.currentText())
        project['venv'] = unicode(page.vtxtPlace.text())
        json_manager.create_ninja_project(path, name, project)
        self._load_project(path)

    def _load_project(self, path):
        """Open Project based on path into Explorer"""
        self.__explorer.open_project_folder(path)

    def _load_project_with_extensions(self, path, extensions):
        """Open Project based on path into Explorer with extensions"""
#        self._main._properties._treeProjects.load_project(
#            self._main.open_project_with_extensions(path), path)
        pass


###############################################################################
# WIZARD FIRST PAGE
###############################################################################


class PageProjectType(QWizardPage):

    def __init__(self, wizard):
        QWizardPage.__init__(self)
        self.setTitle(self.tr("Project Type"))
        self.setSubTitle(self.tr("Choose the Project Type"))
        self._wizard = wizard

        vbox = QVBoxLayout(self)
        self.listWidget = QListWidget()
        vbox.addWidget(self.listWidget)
        types = settings.get_all_project_types()
        types.sort()
        self.listWidget.addItems(types)
        index = types.index('Python')
        self.listWidget.setCurrentRow(index)

        self.connect(self.listWidget, SIGNAL("itemSelectionChanged()"),
            self._item_changed)

    def _item_changed(self):
        self._wizard.add_project_pages(
            unicode(self.listWidget.currentItem().text()))


###############################################################################
# WIZARD LAST PAGE
###############################################################################


class PageProjectProperties(QWizardPage):

    def __init__(self):
        QWizardPage.__init__(self)
        self.setTitle(self.tr("New Project Data"))
        self.setSubTitle(self.tr(
            "Complete the following fields to create the Project Structure"))

        gbox = QGridLayout(self)
        #Names of the fields to complete
        self.lblName = QLabel(self.tr("New Project Name (*):"))
        self.lblPlace = QLabel(self.tr("Project Location (*):"))
        self.lblFolder = QLabel(self.tr("Project Folder:"))
        self.lblDescription = QLabel(self.tr("Project Description:"))
        self.lblLicense = QLabel(self.tr("Project License:"))
        self.lblVenvFolder = QLabel(self.tr("Virtualenv Folder:"))
        gbox.addWidget(self.lblName, 0, 0, Qt.AlignRight)
        gbox.addWidget(self.lblFolder, 1, 0, Qt.AlignRight)
        gbox.addWidget(self.lblPlace, 2, 0, Qt.AlignRight)
        gbox.addWidget(self.lblDescription, 3, 0, Qt.AlignTop)
        gbox.addWidget(self.lblLicense, 4, 0, Qt.AlignRight)
        gbox.addWidget(self.lblVenvFolder, 5, 0, Qt.AlignRight)

        #Fields on de right of the grid
        #Name
        self.txtName = QLineEdit()
        self.registerField('projectName*', self.txtName)
        #Project Folder
        self.txtFolder = QLineEdit()
        #Location
        hPlace = QHBoxLayout()
        self.txtPlace = QLineEdit()
        self.txtPlace.setReadOnly(True)
        self.registerField('place*', self.txtPlace)
        self.btnExamine = QPushButton(self.tr("Examine..."))
        hPlace.addWidget(self.txtPlace)
        hPlace.addWidget(self.btnExamine)
        #Virtualenv
        vPlace = QHBoxLayout()
        self.vtxtPlace = QLineEdit()
        self.vtxtPlace.setReadOnly(True)
        self.registerField('vplace', self.vtxtPlace)
        self.vbtnExamine = QPushButton(self.tr("Examine..."))
        vPlace.addWidget(self.vtxtPlace)
        vPlace.addWidget(self.vbtnExamine)
        #Project Description
        self.txtDescription = QPlainTextEdit()
        #Project License
        self.cboLicense = QComboBox()
        self.cboLicense.setFixedWidth(250)
        self.cboLicense.addItem('Apache License 2.0')
        self.cboLicense.addItem('Artistic License/GPL')
        self.cboLicense.addItem('Eclipse Public License 1.0')
        self.cboLicense.addItem('GNU General Public License v2')
        self.cboLicense.addItem('GNU General Public License v3')
        self.cboLicense.addItem('GNU Lesser General Public License')
        self.cboLicense.addItem('MIT License')
        self.cboLicense.addItem('Mozilla Public License 1.1')
        self.cboLicense.addItem('New BSD License')
        self.cboLicense.addItem('Other Open Source')
        self.cboLicense.addItem('Other')
        self.cboLicense.setCurrentIndex(4)
        #Add to Grid
        gbox.addWidget(self.txtName, 0, 1)
        gbox.addWidget(self.txtFolder, 1, 1)
        gbox.addLayout(hPlace, 2, 1)
        gbox.addWidget(self.txtDescription, 3, 1)
        gbox.addWidget(self.cboLicense, 4, 1)
        gbox.addLayout(vPlace, 5, 1)
        #Signal
        self.connect(self.btnExamine, SIGNAL('clicked()'), self.load_folder)
        self.connect(self.vbtnExamine, SIGNAL('clicked()'),
            self.load_folder_venv)

    def load_folder(self):
        self.txtPlace.setText(unicode(QFileDialog.getExistingDirectory(
            self, self.tr("New Project Folder"))))

    def load_folder_venv(self):
        self.vtxtPlace.setText(unicode(QFileDialog.getExistingDirectory(
            self, self.tr("Select Virtualenv Folder"))))