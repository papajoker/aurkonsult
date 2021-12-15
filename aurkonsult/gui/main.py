#!/usr/bin/env python

import sys
import os
import time
from urllib import request
import json
import subprocess
from pathlib import Path
import shutil


try:
    from PyQt5 import QtCore, QtGui, QtWidgets
except ImportError:
    print("pacman -S python-pyqt5 --asdeps")
    exit(13)


import aurkonsult

from aurkonsult import _, set_lang
from aurkonsult import UserConf, Configuration
from aurkonsult import vercmp
from aurkonsult import Package
from aurkonsult import api
from aurkonsult.gui import models
from aurkonsult.gui import widgets, ICONS


class WinMain(QtWidgets.QMainWindow):
    def __init__(self, config: Configuration):
        super(WinMain, self).__init__()
        self.threadpool = QtCore.QThreadPool()

        exitAction = QtWidgets.QAction(
            ICONS.load(ICONS.close), _("Exit") + " (Ctrl+X)", self
        )
        exitAction.triggered.connect(self.close)
        exitAction.setShortcut(QtGui.QKeySequence("Ctrl+x"))
        updateAction = QtWidgets.QAction(
            ICONS.load(ICONS.update), _("Update") + " (Ctrl+U)", self
        )
        updateAction.triggered.connect(self.onUpdate)
        updateAction.setShortcut(QtGui.QKeySequence("Ctrl+u"))
        newAction = QtWidgets.QAction(
            ICONS.load(ICONS.new), _("New packages") + " (Ctrl+N)", self
        )
        newAction.triggered.connect(self.onNew)
        newAction.setShortcut(QtGui.QKeySequence("Ctrl+n"))
        checkAction = QtWidgets.QAction(
            ICONS.load(ICONS.check), _("Check my aur packages") + " (Ctrl+C)", self
        )
        checkAction.triggered.connect(self.onCheck)
        checkAction.setShortcut(QtGui.QKeySequence("Ctrl+c"))
        listAction = QtWidgets.QAction(
            ICONS.load(ICONS.list), _("Packages") + " (Ctrl+L)", self
        )
        listAction.triggered.connect(self.onList)
        listAction.setShortcut(QtGui.QKeySequence("Ctrl+l"))
        infoAction = QtWidgets.QAction(
            ICONS.load(ICONS.info), _("Info") + " (Ctrl+I)", self
        )
        infoAction.triggered.connect(self.onInfo)
        infoAction.setShortcut(QtGui.QKeySequence("Ctrl+i"))
        configAction = QtWidgets.QAction(
            ICONS.load(ICONS.application), _("Configuration") + " (Ctrl+C)", self
        )
        configAction.triggered.connect(self.onConfig)
        configAction.setShortcut(QtGui.QKeySequence("Ctrl+c"))

        QtWidgets.QShortcut("Ctrl++", self).activated.connect(lambda: self.onZoom(1))
        QtWidgets.QShortcut("Ctrl+-", self).activated.connect(lambda: self.onZoom(0))

        toolbar = QtWidgets.QToolBar("Update", self)
        self.addToolBar(QtCore.Qt.RightToolBarArea, toolbar)
        toolbar.addAction(updateAction)
        toolbar.addSeparator()
        toolbar.addAction(listAction)
        toolbar.addAction(checkAction)
        toolbar.addAction(newAction)
        toolbar.addSeparator()

        btn = widgets.dropButton(toolbar)
        btn.setDefaultAction(infoAction)
        toolbar.addWidget(btn)
        if Configuration.KONSOLE_INSTALLED:
            installAction = QtWidgets.QAction(
                ICONS.load(ICONS.install), "Install", self
            )
            installAction.triggered.connect(self.onInstall)
            btn = widgets.dropButton(toolbar)
            btn.setDefaultAction(installAction)
            toolbar.addWidget(btn)

        sep = QtWidgets.QWidget()
        sep.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        toolbar.addWidget(sep)
        toolbar.addAction(configAction)
        toolbar.addAction(exitAction)

        self.win = Window(self, config)

        self.setCentralWidget(self.win)
        self.resize(990, 650)
        self.setWindowTitle(_("AUR list"))

        if not config.db_file.exists():
            # after install or first run of the day, we download DB
            QtCore.QTimer.singleShot(400, self.onUpdate)

    def onUpdate(self):
        worker = widgets.Worker(self.isUpdated, self.win.config)
        self.threadpool.start(worker)
        self.win.tabs.setCurrentIndex(0)

    @QtCore.pyqtSlot(int)
    def isUpdated(self, return_code: int):
        print("database is updated", return_code)
        txt = "?"
        if return_code == 304:
            txt = _("No new database available")
        elif return_code == 200:
            txt = _("OK new version")
        # update treeview
        QtCore.QTimer.singleShot(200, self.win.loadPackages)
        QtWidgets.QMessageBox.information(
            None,
            _("Database update"),
            _("End Update")
            + "...\n\n"
            + f"{return_code if return_code != 200 else ''} {txt}\n",
        )

    def onZoom(self, direction):
        delegate = self.win.sourceView.itemDelegate()
        size = delegate.hfont
        nsize = size
        if direction == 0:
            if size > 5:
                nsize = size - 1
        else:
            nsize = size + 1
        if size != nsize:
            delegate.hfont = nsize
            delegate.sizeHintChanged.emit(QtCore.QModelIndex())  # refresh

    def onCheck(self):
        if isinstance(self.win.currentModel, models.packageModel):
            self.win.sourceView.setItemDelegate(
                models.checkDelegate(self.win.sourceView)
            )
            self.win.findGroupBox.hide()
            self.win.loadPackagesCheck()
        # else:
        #    self.onList()
        self.win.sourceGroupBox.setTitle(_("Check local packages"))
        self.win.tabs.setCurrentIndex(0)

    def onList(self):
        QtWidgets.QApplication.instance().setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor)
        )
        try:
            self.win.sourceView.setItemDelegate(
                models.listDelegate(
                    self.win.sourceView, self.win.config.time_since_update
                )
            )
            self.win.loadPackages(False)
            self.win.sourceView.setModel(self.win.proxyModel)
            self.win.filterPatternLineEdit.setText("")
            self.setWindowTitle(
                f"{_('AUR list')} - {len(self.win.currentModel._origin)} - {self.win.currentModel.rowCount()}"
            )
            self.win.findGroupBox.show()
            self.win.sourceGroupBox.setTitle(_("Packages"))
            self.win.tabs.setCurrentIndex(0)
        finally:
            QtWidgets.QApplication.instance().restoreOverrideCursor()

    def onNew(self):
        # if isinstance(self.win.currentModel, checkModel):
        #    return
        self.win.sourceView.setItemDelegate(
            models.listDelegate(self.win.sourceView, self.win.config.time_since_update)
        )
        self.win.loadPackages(False)
        self.win.filterPatternLineEdit.setText("")
        self.win.currentModel.filterNews(self.win.config.time_since_update)
        self.setWindowTitle(
            f"{_('AUR list')} - {len(self.win.currentModel._origin)} - {self.win.currentModel.rowCount()}"
        )
        self.win.findGroupBox.hide()
        self.win.sourceGroupBox.setTitle(_("New packages"))
        self.win.tabs.setCurrentIndex(0)

    def onInfo(self):
        self.win.index = self.win.sourceView.currentIndex()
        if not self.win.index.isValid():
            return
        self.win.findGroupBox.show()
        if pkg := self.win.index.internalPointer():
            self.win.populate_Info(pkg)
            self.win.tabs.setCurrentIndex(1)

    def onInstall(self):
        self.win.index = self.win.sourceView.currentIndex()
        if not self.win.index.isValid():
            return
        if pkg := self.win.index.internalPointer():
            widgets.run_konsole(pkg.name, self.win.config.attributes["pamac"])

    def onConfig(self):
        """dialog app preferences"""
        dialog_box = widgets.ConfigDialog(self)
        if dialog_box.exec():
            pass


class Window(QtWidgets.QWidget):
    def __init__(self, parent, config: Configuration):
        super(Window, self).__init__()
        self.parent = parent
        self.config = config
        self.index = QtCore.QModelIndex()

        layout = QtWidgets.QGridLayout()

        self.tabs = QtWidgets.QStackedWidget()  # can use QStackedWidget or QTabWidget ?
        list_tab = QtWidgets.QWidget()
        info_tab = QtWidgets.QWidget()

        if self.tabs is QtWidgets.QTabWidget:  # TODO remove for final, we not use Tabs
            self.tabs.addTab(list_tab, "Packages")
            self.tabs.addTab(info_tab, "Info")
        else:
            self.tabs.addWidget(list_tab)
            self.tabs.addWidget(info_tab)

        self.proxyModel = models.packageModel(self)
        self.checkModel = models.checkModel(self)
        self.currentModel = self.proxyModel

        self.sourceView = widgets.packageTree()
        self.sourceView.doubleClicked.connect(self.on_doubleClicked)
        self.sourceView.clicked.connect(self.on_clicked)
        self.sourceView.customContextMenuRequested.connect(self.onContextTree)
        self.sourceView.setItemDelegate(
            models.listDelegate(self.sourceView, self.config.time_since_update)
        )

        sourceLayout = QtWidgets.QHBoxLayout()
        sourceLayout.addWidget(self.sourceView)
        self.sourceGroupBox = QtWidgets.QGroupBox(_("Packages"))
        self.sourceGroupBox.setLayout(sourceLayout)

        self.filterPatternLineEdit = QtWidgets.QLineEdit()
        self.filterPatternLineEdit.setText("")
        self.completer_model = QtCore.QStringListModel()
        self.completer = QtWidgets.QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(False)
        self.completer.setModelSorting(True)
        # self.completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)    # start by is best
        self.filterPatternLineEdit.setCompleter(self.completer)
        filterPatternLabel = QtWidgets.QLabel(_("Search") + ":")
        filterPatternLabel.setBuddy(self.filterPatternLineEdit)
        self.filterSyntaxComboBox = QtWidgets.QComboBox()
        self.filterSyntaxComboBox.addItem(_("Package name"), 0)
        self.filterSyntaxComboBox.addItem(_("Package name and Description"), 1)

        self.filterPatternLineEdit.textChanged.connect(self.textFilterChanged)
        self.filterSyntaxComboBox.currentIndexChanged.connect(self.textFilterChanged)

        findLayout = QtWidgets.QGridLayout()
        findLayout.addWidget(filterPatternLabel, 1, 0)
        findLayout.addWidget(self.filterPatternLineEdit, 1, 1)
        findLayout.addWidget(self.filterSyntaxComboBox, 1, 2)

        if self.config.extended:
            self.filterDepLineEdit = QtWidgets.QLineEdit()
            self.filterDepLineEdit.setText("")
            self.filterDepLineEdit.setPlaceholderText("+qt5-base -Gtk3")
            filterDepLabel = QtWidgets.QLabel(_("Dependencies") + ":")
            filterDepLabel.setBuddy(self.filterDepLineEdit)
            self.filterDepLineEdit.textChanged.connect(self.textFilterChanged)

            findLayout.addWidget(filterDepLabel, 2, 0)
            findLayout.addWidget(self.filterDepLineEdit, 2, 1)

        self.findGroupBox = QtWidgets.QGroupBox(_("Filter"))
        self.findGroupBox.setLayout(findLayout)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.sourceGroupBox)
        mainLayout.addWidget(self.findGroupBox)
        list_tab.setLayout(mainLayout)

        infoLayout = QtWidgets.QVBoxLayout()
        forms = self.createPackageInfo()
        infoLayout.addWidget(forms)

        info_tab.setLayout(infoLayout)

        layout.addWidget(self.tabs)
        self.setLayout(layout)

        QtCore.QTimer.singleShot(600, self.loadPackages)

    def createPackageInfo(self):
        """create Form in page Package infos"""
        self.form = {
            "Name": QtWidgets.QLineEdit(),
            "Version": QtWidgets.QLineEdit(),
            "PackageBase": QtWidgets.QLabel(""),
            "Description": QtWidgets.QLabel(""),
            "URL": QtWidgets.QLabel(""),
            "Aur": QtWidgets.QLabel(""),
            "FirstSubmitted": QtWidgets.QLabel(""),
            "LastModified": QtWidgets.QLabel(""),
            "NumVotes": QtWidgets.QLabel(""),
            "Popularity": QtWidgets.QLabel(""),
            "Maintainer": QtWidgets.QLabel(""),
            "MaintainerList": QtWidgets.QComboBox(),
            "Dependencies": QtWidgets.QComboBox(),
            "MakeDepends": QtWidgets.QComboBox(),
            "OptDepends": QtWidgets.QComboBox(),
            "Licences": QtWidgets.QComboBox(),
            "Provides": QtWidgets.QComboBox(),
            "Comments": QtWidgets.QComboBox(),
            "histories": QtWidgets.QComboBox(),
            "PKGBUILD": QtWidgets.QLabel(""),
        }
        self.form["URL"].setOpenExternalLinks(True)
        self.form["Aur"].setOpenExternalLinks(True)
        self.form["PKGBUILD"].setOpenExternalLinks(True)
        self.form["Maintainer"].setOpenExternalLinks(True)
        self.form["Description"].setWordWrap(True)
        self.form["Description"].setMinimumWidth(400)
        self.form["Description"].setMinimumHeight(40)
        self.form["Name"].setReadOnly(True)
        self.form["Version"].setReadOnly(True)

        btn = QtWidgets.QPushButton("", self)  # ↩
        btn.setFlat(True)
        btn.setToolTip(_("Return") + " (Ctrl+R)")
        btn.setShortcut(QtGui.QKeySequence("Ctrl+R"))
        btn.setIcon(ICONS.load(ICONS.ireturn))
        btn.clicked.connect(self.onCloseInfo)

        btnLoad = QtWidgets.QPushButton("", self)
        btnLoad.setFlat(True)
        btnLoad.setIcon(ICONS.load(ICONS.edit))
        btnLoad.setToolTip(_("Load") + " PKGBUILD (Ctrl+P)")
        btnLoad.setShortcut(QtGui.QKeySequence("Ctrl+P"))
        btnLoad.clicked.connect(self.onLoadPkgBuild)

        grid = QtWidgets.QGridLayout()

        def setLabel(row, col, caption: str) -> int:
            if col == 0:
                row += 1
            caption = f"<i>{caption}</i>&nbsp;:&nbsp;" if caption else ""
            grid.addWidget(QtWidgets.QLabel(caption), row, col, QtCore.Qt.AlignRight)
            return row

        row = 0
        grid.addWidget(btn, 0, 4, 1, 1, QtCore.Qt.AlignRight)
        row = setLabel(row, 0, _("Name"))
        grid.addWidget(self.form["Name"], row, 1, 1, 3, QtCore.Qt.Alignment())
        row = setLabel(row, 0, "Version")
        grid.addWidget(self.form["Version"], row, 1, 1, 3, QtCore.Qt.Alignment())
        row = setLabel(row, 0, "Description")
        grid.addWidget(self.form["Description"], row, 1, 1, 3, QtCore.Qt.AlignVCenter)

        row = setLabel(row, 0, _("Last Modified"))
        grid.addWidget(self.form["LastModified"], row, 1, 1, 3, QtCore.Qt.Alignment())
        row = setLabel(row, 0, _("First Submitted"))
        grid.addWidget(self.form["FirstSubmitted"], row, 1, 1, 3, QtCore.Qt.Alignment())
        # TODO useful ?
        # row = setLabel(row, 0, "Package Base")
        # grid.addWidget(self.form['PackageBase'], row, 1, 1, 3, QtCore.Qt.Alignment())
        row = setLabel(row, 0, "")
        row = setLabel(row, 0, _("Url project"))
        grid.addWidget(self.form["URL"], row, 1, 1, 3, QtCore.Qt.Alignment())
        row = setLabel(row, 0, _("Aur Url"))
        grid.addWidget(self.form["Aur"], row, 1, 1, 3, QtCore.Qt.Alignment())
        row = setLabel(row, 0, "PKGBUILD")
        grid.addWidget(self.form["PKGBUILD"], row, 1, 1, 3, QtCore.Qt.Alignment())
        grid.addWidget(btnLoad, row, 4, 1, 1, QtCore.Qt.AlignRight)
        if self.config.extended:
            row = setLabel(row, 0, _("Dependencies"))
            grid.addWidget(self.form["Dependencies"], row, 1)
            setLabel(row, 2, _("Optional"))
            grid.addWidget(self.form["OptDepends"], row, 3)
        row = setLabel(row, 0, "")
        row = setLabel(row, 0, _("Maintainer"))
        grid.addWidget(self.form["Maintainer"], row, 1)
        setLabel(row, 2, _("Packages"))
        grid.addWidget(self.form["MaintainerList"], row, 3)
        row = setLabel(row, 0, "")
        grid.setRowStretch(row, 1)
        row = setLabel(row, 0, _("Votes"))
        grid.addWidget(self.form["NumVotes"], row, 1)
        setLabel(row, 2, _("Popularity"))
        grid.addWidget(self.form["Popularity"], row, 3)

        if self.config.extended:
            row = setLabel(row, 0, "")
            row = setLabel(row, 0, _("Make Dependencies"))
            grid.addWidget(self.form["MakeDepends"], row, 1)
            row = setLabel(row, 0, _("Provide"))
            grid.addWidget(self.form["Provides"], row, 1)
            row = setLabel(row, 0, _("Licence"))
            grid.addWidget(self.form["Licences"], row, 1)

        if self.config.attributes["comment"]:
            row = setLabel(row, 0, _("Comments"))
            grid.addWidget(self.form["Comments"], row, 1)
            """ or add btn "load", an only after loading, populate combo
            """

        if self.config.attributes["history"]:
            btnHistory = QtWidgets.QPushButton("", self)
            btnHistory.setFlat(True)
            btnHistory.setIcon(ICONS.load(ICONS.download))
            btnHistory.setToolTip(_("Get History") + " (Ctrl+H)")
            btnHistory.setShortcut(QtGui.QKeySequence("Ctrl+H"))
            btnHistory.clicked.connect(self.onLoadPkgHistory)
            row = setLabel(row, 0, _("History") + ":")
            grid.addWidget(self.form["histories"], row, 1, 1, 2)
            grid.addWidget(btnHistory, row, 3, QtCore.Qt.AlignLeft)

        formGroupBox = QtWidgets.QGroupBox(_("package Informations"))

        # TODO ? add image...
        # background process ?
        # if github: get first "big?" image in readme.md ???

        formGroupBox.setLayout(grid)
        formGroupBox.keyPressEvent = self.eventFilterKeyPress

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(formGroupBox)

        return scrollArea

    def eventFilterKeyPress(self, event):
        """move in page package info"""
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Left):
                self.index = self.currentModel.index(
                    self.index.row() - 1, 0, QtCore.QModelIndex()
                )
                if pkg := self.index.internalPointer():
                    self.populate_Info(pkg)
            if event.key() in (QtCore.Qt.Key_Down, QtCore.Qt.Key_Right):
                self.index = self.currentModel.index(
                    self.index.row() + 1, 0, QtCore.QModelIndex()
                )
                if pkg := self.index.internalPointer():
                    self.populate_Info(pkg)
        return super().keyPressEvent(event)

    def onLoadPkgHistory(self):
        """download aur pkg and read git history"""
        if not self.index.isValid():
            return
        pkg = self.index.internalPointer()
        if not pkg.name:
            return
        QtWidgets.QApplication.instance().setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor)
        )
        try:
            dir_clone = "/tmp/aurkonsult/gitclone"
            shutil.rmtree(dir_clone, ignore_errors=True)
            cmd = (
                f"git clone -qn https://aur.archlinux.org/{pkg.name}.git {dir_clone} && cd {dir_clone};"
                "git log --pretty=format:'%ad | %s' --date=short;"
            )
            # print(cmd)
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if proc.returncode == 0:
                # print(proc.stdout)
                self.form["histories"].clear()
                self.form["histories"].addItems((i for i in proc.stdout.split("\n")))
        finally:
            QtWidgets.QApplication.instance().restoreOverrideCursor()

    def onLoadPkgBuild(self, pkg_name):
        """download PKGBUILD and load local editor by dbus"""
        if not self.index.isValid():
            return
        pkg = self.index.internalPointer()
        tmp_file = "/tmp/PKGBUILD"
        # print(pkg)
        print(
            f"wget: https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={pkg.name}"
        )
        if pkg.name:
            req = request.Request(
                f"https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={pkg.name}"
            )
            # req.add_header("User-Agent", f"'User-Agent': '{_get_user_agent()}'")
            try:
                with request.urlopen(req, timeout=2) as response:
                    content = response.read()
                    Path(tmp_file).write_bytes(content)
                    process = QtCore.QProcess()
                    process.startDetached("xdg-open", [tmp_file])
            except:
                pass

    def populate_Info(self, pkg: Package):
        """set values in page Package Infos"""
        is_present = " ✅ (Installed)" if pkg.is_installed() else ""
        self.form["Name"].setText(f"{pkg.name}    {is_present}")
        self.form["Version"].setText(pkg.version)
        self.form["PackageBase"].setText(pkg.package_base)
        self.form["Description"].setText(pkg.description)
        self.form["Maintainer"].setText(pkg.maintainer)
        self.form["URL"].setText(f"{pkg:URL}")
        self.form["PKGBUILD"].setText(f"{pkg:PKGBUILD}")
        self.form["Aur"].setText(f"{pkg:Aur}")
        self.form["NumVotes"].setText(str(pkg.num_votes))
        self.form["Popularity"].setText(f"{pkg:Popularity}")
        self.form["LastModified"].setText(
            f"{pkg:LastModified} <i>&nbsp;</i> {pkg:OutOfDate}"
        )
        self.form["FirstSubmitted"].setText(f"{pkg:FirstSubmitted}")

        self.form["MaintainerList"].clear()
        self.form["MaintainerList"].addItems(
            sorted(
                p.name
                for p in self.currentModel._origin
                if p.maintainer == pkg.maintainer
            )
        )
        self.form["Dependencies"].clear()
        self.form["Dependencies"].addItems(sorted(pkg.depends))
        self.form["OptDepends"].clear()
        self.form["OptDepends"].addItems(sorted(pkg.opt_depends))
        self.form["MakeDepends"].clear()
        self.form["MakeDepends"].addItems(sorted(pkg.make_depends))
        self.form["Licences"].clear()
        self.form["Licences"].addItems(pkg.license)
        self.form["Provides"].clear()
        self.form["Provides"].addItems(sorted(pkg.provides))
        self.form["histories"].clear()

        # get last comments: ?
        if self.config.attributes["comment"]:
            self.form["Comments"].clear()
            url = "https://aur.archlinux.org/packages/"
            req = request.Request(f"{url}{pkg.name}/")
            # req.add_header("User-Agent", f"'User-Agent': '{_get_user_agent()}'")
            try:
                with request.urlopen(req, timeout=2) as response:
                    for line in response:
                        if "#comment-" in line.decode("utf-8"):
                            line = str(line).replace(">", "<").split("<")
                            self.form["Comments"].addItem(line[-3])
            except:
                raise

    def on_clicked(self, index):
        if not isinstance(self.currentModel, models.packageModel):
            return
        if not index.isValid():
            return

        if index.column() == models.packageModel.ID_URL:
            url = index.internalPointer()["url"]
            if url and url.startswith("http"):
                print("Go to:", url)
                if QtWidgets.QMessageBox.Yes == QtWidgets.QMessageBox.question(
                    self,
                    _("Open browser") + " ?",
                    f"\n{_('Do you want go to this url')} ?\n\n{url}\n",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No,
                ):
                    QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def on_doubleClicked(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return
        pkg = index.internalPointer()
        if pkg.version == "":
            # local package in check page, is not in aur database
            return
        self.index = self.sourceView.currentIndex()
        self.populate_Info(pkg)
        self.tabs.setCurrentIndex(1)

    def onCloseInfo(self):
        self.index = -1
        self.tabs.setCurrentIndex(0)

    def onContextTree(self, point):
        index = self.sourceView.currentIndex()
        if not index.isValid():
            return
        pkg: Package = index.internalPointer()

        menu = QtWidgets.QMenu()
        notUsed = menu.addAction(pkg.name)
        notUsed.setEnabled(False)
        menu.addSeparator()

        aInfo = menu.addAction(_("Information"))
        aInstall = None
        # print(pkg)
        if len(pkg.version) > 1 and Configuration.KONSOLE_INSTALLED:
            aInstall = menu.addAction(_("Install in Konsole"))

        action = menu.exec_(self.sourceView.mapToGlobal(point))
        if not action:
            return

        if action == aInfo:
            self.index = self.sourceView.currentIndex()
            self.populate_Info(pkg)
            self.tabs.setCurrentIndex(1)

        if action == aInstall:
            widgets.run_konsole(pkg.name, self.config.attributes["pamac"])

    def textFilterChanged(self):
        if not isinstance(self.currentModel, models.packageModel):
            return

        search = self.filterPatternLineEdit.text()
        if search and len(search) < 3:
            return
        try:
            deps = self.filterDepLineEdit.text().split()
        except AttributeError:
            deps = []
        deps_wants = {
            d[1:].lower() if d[0:1] == "+" else d.lower() for d in deps if d[0:1] != "-"
        }
        deps_nones = {d[1:].lower() for d in deps if d[0:1] == "-"}
        print("Deps filter: want:", deps_wants, "not:", deps_nones)
        QtWidgets.QApplication.instance().setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor)
        )
        try:
            self.currentModel.filterPkg(
                search, deps_wants, deps_nones, self.filterSyntaxComboBox.currentIndex()
            )
            if self.filterSyntaxComboBox.currentIndex() == 0:
                self.completer_model.setStringList(
                    (p.name for p in self.currentModel._data)
                )
            else:
                self.completer_model.setStringList([""])
            print("search end:", self.filterPatternLineEdit.text())
        finally:
            QtWidgets.QApplication.instance().restoreOverrideCursor()
        self.parent.setWindowTitle(
            f"{_('AUR list')} - {len(self.currentModel._origin)} - {self.currentModel.rowCount()}"
        )

    def loadPackages(self, update=True):
        QtWidgets.QApplication.instance().setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor)
        )
        if update:
            self.setSourceModel(self.config.db_file)
        else:
            self.proxyModel._data = self.proxyModel._origin
        QtWidgets.QApplication.instance().restoreOverrideCursor()
        self.proxyModel.layoutChanged.emit()
        self.sourceView.setModel(self.proxyModel)
        self.currentModel = self.proxyModel

    def loadPackagesCheck(self):
        QtWidgets.QApplication.instance().setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor)
        )
        self.checkModel.inject(self.proxyModel._origin, self.config.user_aurs)
        QtWidgets.QApplication.instance().restoreOverrideCursor()
        self.checkModel.layoutChanged.emit()
        self.sourceView.setModel(self.checkModel)
        self.currentModel = self.checkModel
        self.parent.setWindowTitle(
            f"{_('AUR list')} - {len(self.currentModel._origin)} - {self.currentModel.rowCount()}"
        )

    def setSourceModel(self, file_name):
        def load_json():
            max = -1
            installeds = self.config.user_aurs.keys()
            if "--mini" in sys.argv:
                max = int(os.environ.get("MINI", 100))
            with open(file_name, mode="r") as json_file:
                i = -1
                for line in json_file:
                    """load line by line and convert to package : time is x2 !"""
                    if len(line) > 10:
                        i += 1
                        line = line.rstrip("\n")
                        if line.endswith(","):
                            line = line[:-1]
                        try:
                            data = json.loads(line)
                            try:
                                if data["Name"] in installeds:
                                    data["VersionLocal"] = self.config.user_aurs[
                                        data["Name"]
                                    ][1]
                                yield data >> Package()
                            except:
                                print(f"Error: Package no imported ! {data}")
                                raise
                        except:
                            print(f"Error: read json! {line}")
                            raise
                    if max > -1 and i > max:
                        break

        if file_name.exists():
            print("\n:: Load Database...")
            start_time = time.time()
            self.proxyModel.inject(load_json())
            if not self.proxyModel.rowCount():
                exit(3)
            print(f"json to data duration: -- {(time.time() - start_time)} seconds --")
            self.parent.setWindowTitle(
                f"{_('AUR list')} - {self.proxyModel.rowCount()}"
            )
            self.sourceView.sortByColumn(2, QtCore.Qt.AscendingOrder)


def run(config):
    app = QtWidgets.QApplication(sys.argv)
    set_lang(QtCore.QLocale().name().split("_")[1])
    app.setWindowIcon(ICONS.load(ICONS.application))

    win = WinMain(config)
    win.show()
    sys.exit(app.exec_())
