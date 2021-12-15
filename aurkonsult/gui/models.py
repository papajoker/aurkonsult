import sys
import time
from typing import Any
from PyQt5 import QtCore, QtGui, QtWidgets
from aurkonsult import Package


class ModelBase(QtCore.QAbstractItemModel):
    """Absract class aur packages container"""

    _HEADERS = []

    def __init__(self, parent, *args):
        super().__init__(parent, *args)
        self._data = []
        self._origin = []

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

    def inject(self, datas):
        self._data = []
        self._origin = list(datas)

    def headerData(self, section, orientation, role) -> str:
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self._HEADERS[section].capitalize()
        return ""

    def rowCount(self, index=None) -> int:
        return len(self._data)

    def columnCount(self, index=None) -> int:
        return len(self._HEADERS)

    def parent(self, index=None):
        return QtCore.QModelIndex()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return (
            QtCore.Qt.ItemIsEnabled
            | QtCore.Qt.ItemIsSelectable
            | QtCore.Qt.ItemIsDragEnabled
        )

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        return self.createIndex(row, column, self._data[row])

    def sort(self, column, order):
        key = self._HEADERS[column]
        csort = lambda t: t[key]
        self.layoutAboutToBeChanged.emit()
        try:
            self._data = sorted(self._data, key=csort, reverse=(order == 0))
        except:
            print(f"Error sort: {key}")
            raise
        self.layoutChanged.emit()

    def filterPkg(self, regex: str, dep_wants: set[str], dep_nones: set[str], target=1):
        self.layoutAboutToBeChanged.emit()
        lists = self._origin

        if dep_nones:
            lists = (pkg for pkg in lists if set(pkg.depends).isdisjoint(dep_nones))
        if dep_wants:
            lists = (pkg for pkg in lists if dep_wants.issubset(pkg.depends))

        if regex == "":
            self._data = list(lists)
        else:
            regex = regex.casefold()
            if target == 0:
                self._data = [pkg for pkg in lists if regex in pkg.name.lower()]
            else:
                self._data = []
                for pkg in lists:
                    if regex in f"{pkg.name} {pkg.description}".casefold():
                        self._data.append(pkg)
        self.layoutChanged.emit()

    def mimeTypes(self):
        return ["text/plain", "text/uri-list"]

    def supportedDragActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.LinkAction  # | QtCore.Qt.MoveAction

    def mimeData(self, indexes) -> QtCore.QMimeData:
        """Set text dadas for drag&drop"""
        mimedata = QtCore.QMimeData()
        index = indexes[0]
        pkg: Package = index.internalPointer()
        if not pkg:
            pkg = self._data[index.row()]

        modifiers = QtWidgets.QApplication.keyboardModifiers()
        # ControlModifier, ShiftModifier, AltModifier , (Qt.ControlModifier | Qt.ShiftModifier) ...
        # cmd = pkg.name
        # if modifiers == QtCore.Qt.ShiftModifier:
        cmd = f"yay -Si {pkg.name}"
        if "--pamac" in sys.argv:
            cmd = f"pamac info {pkg.name} --aur"
        if modifiers == QtCore.Qt.AltModifier:  # ControlModifier:
            cmd = f"yay -S {pkg.name} --asdeps"
            if "--pamac" in sys.argv:
                cmd = f"pamac build {pkg.name} -d"  # '-d' we use a test version !
        mimedata.setData("text/plain", QtCore.QByteArray(bytes(cmd, encoding="utf8")))
        if modifiers == QtCore.Qt.ShiftModifier:
            mimedata.setData(
                "text/uri-list", QtCore.QByteArray(bytes(pkg.url, encoding="utf8"))
            )
        return mimedata

    @classmethod
    def pkgVal(cls, pkg, index) -> Any:
        """Get cell value from column index"""
        try:
            return pkg[cls._HEADERS[index]]
        except:
            return ""


class checkModel(ModelBase):
    """treeview Compare packages, local to aur"""
    ID_NAME, ID_LOCAL_VERSION, ID_VERSION, ID_DATE, ID_DESC = range(5)
    _HEADERS = ("name", "version_local", "version", "last_modified", "description")

    def inject(self, datas, user_aurs):
        super().inject(datas)
        self.pkg_installeds = user_aurs
        if not self.pkg_installeds:
            return

        short = [p for p in self.pkg_installeds.keys()]
        self._data = [p for p in self._origin if p.name in short]
        for pkg in self._data:
            if pkg.name in short:
                pkg.set_version_local(self.pkg_installeds[pkg.name][1])
        pkg_last = {p.name: p.version for p in self._data if p.name in short}

        for _, pkg in self.pkg_installeds.items():
            try:
                _ = pkg_last[pkg[0]]
            except KeyError:
                # pkg is not in aur, add new to list
                package = Package()
                {
                    "Name": pkg[0],
                    "VersionLocal": pkg[1],
                    "Description": pkg[2],
                    "URL": pkg[3],
                } >> package
                self._data.append(package)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        super().data(index, role)
        pkg: Package = index.internalPointer()
        if not pkg:
            pkg = self._data[index.row()]

        match role:
            case QtCore.Qt.DisplayRole:
                match index.column():
                    case self.ID_DATE:
                        return f"{pkg:LastModified}"
                    case self.ID_VERSION if not pkg.version:
                        return " ❌"  # 🔴 ❌
                return pkg[self._HEADERS[index.column()]]

            case QtCore.Qt.ToolTipRole:
                if pkg.version:
                    desc = ""
                    if pkg.vercmp < 0:
                        desc = "- New version in Aur"
                    elif pkg.vercmp > 0:
                        desc = "- Forward local version"
                    if desc:
                        return f"{pkg.name} {desc}"
                else:
                    return f"{pkg.name} not exists in Aur!"

        """if role == QtCore.Qt.DecorationRole:
            # TODO ? if installed user-bookmarks-symbolic
            if index.column() == self.ID_VERSION and not pkg.version:
                return ICONS.load(ICONS.warm)"""

        return None

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            _HEADERS = ("Name", "Locale", "Aur", "Last Aur Update", "Description")
            ret = _HEADERS[section].capitalize()
            return ret
        return None


class packageModel(ModelBase):
    """treeview list aur packages"""
    """
    https://doc.qt.io/qt-5/qabstractitemmodel.html
    """

    nameRole = QtCore.Qt.UserRole + 1  # 257
    versionRole = QtCore.Qt.UserRole + 2
    urlRole = QtCore.Qt.UserRole + 3
    matchRole = QtCore.Qt.UserRole + 100
    ID_NAME, ID_VERSION, ID_DATE, ID_URL, ID_DESC = range(5)
    _HEADERS = ("name", "version", "last_modified", "url", "description")

    def inject(self, datas):
        # self.layoutAboutToBeChanged.emit()
        super().inject(datas)
        self._data = self._origin
        # self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            ret = self._HEADERS[section].capitalize()
            if section == self.ID_DATE:
                ret = "Aur Update"
            return ret
        return None

    def data(self, index, role=QtCore.Qt.DisplayRole) -> str | None:
        if not index.isValid():
            return None
        super().data(index, role)
        if not index.isValid():
            print("data(): not index.isValid")
            return None

        pkg: Package
        if index.internalPointer():
            pkg = index.internalPointer()
        else:
            pkg = self._data[index.row()]

        match role:
            case QtCore.Qt.DisplayRole:
                if index.column() == self.ID_URL:
                    return f"{pkg:hostname}"
                if index.column() == self.ID_DATE:
                    return f"{pkg:LastModified}"

                return self.pkgVal(
                    pkg, index.column()
                )

            case QtCore.Qt.ToolTipRole:
                return f"{pkg.name} {pkg.version}"
            case self.urlRole:
                return pkg.url
            case self.nameRole:
                return pkg.name

        return None

    def filterNews(self, time_since_update: int):
        self.layoutAboutToBeChanged.emit()
        self._data = [p for p in self._origin if p.first_submitted > time_since_update]
        self.layoutChanged.emit()


class listDelegate(QtWidgets.QStyledItemDelegate):
    """Howto display treeview aur packages"""
    # https://doc.qt.io/qtforpython-5/PySide2/QtGui/QColor.html
    OUTOFDATE = QtGui.QColor(160, 0, 0, 220)  # QtGui.QColor("salmon")
    # GREEN = QtGui.QColor(0, 60, 0, 220)    # QtGui.QColor("green")
    NOW = time.time() - (3600 * 72)

    def __init__(self, parent, time_since_update: int):
        super().__init__(parent)
        self.time_since_update = time_since_update
        self.hfont = -1
        # parent.setMouseTracking(True)
        # parent.viewport().installEventFilter(self)
        self.view = parent.viewport()

    def initStyleOption(self, option, index):
        """Set cell style"""
        if not index.isValid():
            return None
        super(listDelegate, self).initStyleOption(option, index)
        pkg: Package
        if index.internalPointer():
            pkg = index.internalPointer()
        else:
            pkg = self._data[index.row()]
        if not pkg:
            return
        if index.data(QtCore.Qt.DisplayRole):
            if self.hfont < 0:
                self.hfont = option.font.pointSize()
            option.font.setPointSize(self.hfont)
            if index.column() == packageModel.ID_NAME and pkg.is_installed():
                # can change color to red if pkg.vercmp > 1 == new version available ?
                option.palette.setBrush(
                    QtGui.QPalette.Text, QtGui.QPalette().highlight()
                )
            """if index.column() == packageModel.ID_URL and pkg.url.startswith("http"):
                # TODO change cursor, text deco.. ?
                pass"""
            if index.column() == packageModel.ID_VERSION:
                if -pkg:  # is outofdate
                    option.palette.setBrush(QtGui.QPalette.Text, self.OUTOFDATE)
                    option.font.setBold(True)
                return
            if index.column() == packageModel.ID_DATE:
                if pkg.first_submitted > self.time_since_update:
                    option.palette.setBrush(
                        QtGui.QPalette.Text, QtGui.QPalette().highlight()
                    )
                return
            return

    def eventFilter(self, source, event):
        # ??? for change cursor ???
        if event.type() == QtCore.QEvent.MouseMove:
            gp = QtGui.QCursor.pos()
            print(gp)
            print(event.type(), source)
            print(event.pos())
            lp = self.view.mapFromGlobal(gp)
            print(lp)
            data = self.view.mapToGlobal(event.pos())
            print("data ? ", data)
            self.view.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        return super().eventFilter(source, event)
        pass


class checkDelegate(QtWidgets.QStyledItemDelegate):
    """Howto display treeview : check differences local/aur"""

    OUTOFDATE = QtGui.QColor(160, 0, 0, 220)  # QtGui.QColor("salmon")

    def __init__(self, parent):
        super().__init__(parent)
        self.hfont = -1

    def initStyleOption(self, option, index):
        """Set cell style"""
        if not index.isValid():
            return None
        super(checkDelegate, self).initStyleOption(option, index)
        pkg = None
        if index.internalPointer():
            pkg = index.internalPointer()
        else:
            pkg = self._data[index.row()]
        if not pkg:
            return
        if index.data(QtCore.Qt.DisplayRole):
            if self.hfont < 0:
                self.hfont = option.font.pointSize()
            option.font.setPointSize(self.hfont)
            if index.column() == checkModel.ID_VERSION:
                if -pkg or pkg.version == "":
                    option.palette.setBrush(QtGui.QPalette.Text, self.OUTOFDATE)
                    # option.font.setBold(True)
                elif pkg > "aur":
                    option.palette.setBrush(
                        QtGui.QPalette.Text, QtGui.QPalette().highlight()
                    )
                return
            if index.column() == checkModel.ID_LOCAL_VERSION:
                if pkg < "aur":
                    option.palette.setBrush(
                        QtGui.QPalette.Text, QtGui.QPalette().highlight()
                    )
                return
            return
