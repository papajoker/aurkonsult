import sys
import os
import time
from PyQt5 import QtCore, QtGui, QtWidgets, QtDBus
from ..core import Package
from ..config import Configuration, UserConf
from aurkonsult import api
from aurkonsult import _


class ICONS:
    """icon manager from theme"""

    # https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html
    application = ("package-x-generic", "system-software-update")  # 📦
    close = ("dialog-close77", "window-close")
    update = ("download", "download")
    new = ("appointment-new", "document-new")
    check = ("checkbox", "document-properties")
    list = ("view-list-text", "view-sort-descending")
    info = ("documentinfo", "help-about")
    install = ("run-build-install-root", "system-run")
    edit = ("document-edit", "accessories-text-editor")
    ireturn = ("go-previous-skip", "go-previous")
    warm = ("error", "emblem-unreadable")
    star = ("user-bookmarks-symbolic", "emblem-favorite")
    download = ("download", "download")

    @classmethod
    def load(cls, name: tuple[str, str]) -> QtGui.QIcon:
        """if ico not exists in theme, load classiq freedesktop icon"""
        if name[1] == "system-software-update" and Configuration.LOGO_FILE.exists():
            print("load ico app ", Configuration.LOGO_FILE)
            ico = QtGui.QIcon(str(Configuration.LOGO_FILE))
            if ico.isNull():
                print("warning, bad file", Configuration.LOGO_FILE)
            else:
                return ico
        ico = QtGui.QIcon.fromTheme(os.environ.get(f"ICO_{name[0].upper()}", name[0]))
        if ico.isNull():
            ico = QtGui.QIcon.fromTheme(name[1])
            if ico.isNull():
                print(f"Warning: 2 Icons `{name[1]}` not in user theme")
                print(
                    f"we can pass this theme icon by env var: `ICO_{name[0].upper()}=xxx`"
                )
        return ico

    @staticmethod
    def app_logo_src() -> str:
        """Svg logo source"""
        return (
            '<svg viewBox="0 0 128 128" version="1.1" xmlns="http://www.w3.org/2000/svg">'
            '<path id="A" style="fill:#5bc9f3"  d="M 25,125 55,110 70,65 80,110 110,125 70,5 Z"/>'
            '<circle cx="43" cy="25" r="6" style="fill:#fa8865" />'
            '<circle cx="22" cy="50" r="9" style="fill:#63c605" />'
            '<circle cx="18" cy="90" r="11" style="fill:#1b89f3" />'
            '</svg>'
        )



class packageTree(QtWidgets.QTreeView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.animated = False
        self.setExpandsOnDoubleClick(False)
        self.setItemsExpandable(False)
        self.setUniformRowHeights(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setDragEnabled(True)
        # self.setColumnWidth(4, 50)
        # self.setColumnHidden(4, True)


# ---------------------------------------------------- #



class WorkerSignal(QtCore.QObject):
    finished = QtCore.pyqtSignal(int)


class Worker(QtCore.QRunnable):
    """backgound download database"""

    def __init__(self, fn_callback, config: Configuration): # , *args, **kwargs):
        super(Worker, self).__init__()
        self.signal = WorkerSignal()
        self.signal.finished.connect(fn_callback)
        self.config = config
        #self.args = args
        #self.kwargs = kwargs

    def run(self):
        QtWidgets.QApplication.instance().setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor)
        )
        try:
            ret = api.download(self.config.db_file, self.config.url, self.config.db_time)
        finally:
            QtWidgets.QApplication.instance().restoreOverrideCursor()
        self.signal.finished.emit(ret)


def run_konsole(pkg_name, info: str = "i"):
    if not pkg_name or not Configuration.KONSOLE_INSTALLED:
        return
    my_dbus = QtDBus.QDBusConnection.sessionBus()

    def get_my_console() -> str:
        iface = QtDBus.QDBusInterface("org.freedesktop.DBus", "/", "", my_dbus)
        msg = iface.call("ListNames")
        for service in msg.arguments()[0]:
            if service.startswith("org.kde.konsole"):
                return service
        return ""

    service = get_my_console()
    if not service:
        process = QtCore.QProcess()
        process.startDetached("/usr/bin/konsole", [""])
        time.sleep(3)
        service = get_my_console()

    if not service:
        print("Error: not possible to load konsole!")
        return

    dep = ""
    if info != "i":
        dep = "--asdeps"  # we use a test version !
    cmd = f"yay -S{info} {pkg_name} {dep}"
    if "--pamac" in sys.argv:
        if info != "i":
            cmd = f"pamac build {pkg_name} -d"  # '-d' we use a test version !
        else:
            cmd = f"pamac info {pkg_name} --aur"

    remote_app = QtDBus.QDBusInterface(service, "/Sessions/1", "", my_dbus)
    reply = remote_app.call(f"sendText", cmd)
    if err := reply.errorMessage():
        print("Error Dbus send command: ", err)

# ---------------------------------------------------- #


class dropButton(QtWidgets.QToolButton):  # QtWidgets.QPushButton):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCheckable(False)

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat("text/plain"):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        # self.setText(e.mimeData().text())
        self.defaultAction().setData(e.mimeData().text())
        """if self.defaultAction().text() == "Info":
            run_konsole(e.mimeData().text(), "i")
        if self.defaultAction().text() == "Install":
            run_konsole(e.mimeData().text(), "")
            return"""
        self.defaultAction().activate(QtWidgets.QAction.ActionEvent())

'''
class DepsDialog(QtWidgets.QDialog):
    def __init__(self, parent, store):
        super().__init__(parent)
        self.packages = store
        self.setWindowTitle(_("Dependencies"))
        self.setMinimumSize(600, 600)
        chart = self._init_ui()

        view = QtChart.QChartView(chart)
        view.setRenderHint(QtGui.QPainter.Antialiasing)  # 抗锯齿
        view.resize(600, 600)
        view.show()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(view)
        self.setLayout(self.layout)

    def _init_ui(self):
        chart = QtChart.QChart()
        chart.setTitle("Deps")
        for pkg, counter in getAllDependencies(self.packages).items():


            series = QtChart.QLineSeries(chart)
            series.append(pkg, counter)
            series.append(pkg, counter)
            chart.addSeries(series)
        chart.createDefaultAxes()
        return chart
'''

class ConfigDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Configuration"))
        self.setMinimumSize(370, 140)
        self._init_ui()

    def _init_ui(self):

        QBtn = QtWidgets.QDialogButtonBox.Yes | QtWidgets.QDialogButtonBox.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.form = {
            "extended": QtWidgets.QCheckBox(_("with dependencies")),
            "comment": QtWidgets.QCheckBox(_("Comments")),
            "history": QtWidgets.QCheckBox(_("History")),
            "pamac": QtWidgets.QCheckBox("pamac"),
            "homecache": QtWidgets.QCheckBox("user home cache"),
        }
        if not Configuration.USER_CONF_FILE.exists():
            Configuration.USER_CONF_FILE.touch()
        conf = UserConf(Configuration.USER_CONF_FILE)
        datas = conf.read()
        for key, item in self.form.items():
            item.setChecked(datas.get(key, False))

        grid = QtWidgets.QGridLayout()

        grid.addWidget(QtWidgets.QLabel(_("Extend Database") + ":"), 0, 0, QtCore.Qt.AlignRight)
        grid.addWidget(self.form["extended"], 0, 1)

        grid.addWidget(QtWidgets.QLabel(_("Load") + ":"), 1, 0, QtCore.Qt.AlignRight)
        grid.addWidget(self.form["comment"], 1, 1)

        grid.addWidget(QtWidgets.QLabel(_("Can load") + ":"), 2, 0, QtCore.Qt.AlignRight)
        grid.addWidget(self.form["history"], 2, 1)

        grid.addWidget(QtWidgets.QLabel(_("Propose app for install") + ":"), 3, 0, QtCore.Qt.AlignRight)
        grid.addWidget(self.form["pamac"], 3, 1)

        grid.addWidget(QtWidgets.QLabel(_("Save Database in") + ":"), 4, 0, QtCore.Qt.AlignRight)
        grid.addWidget(self.form["homecache"], 4, 1)

        formGroupBox = QtWidgets.QGroupBox(_("Preferences"))
        formGroupBox.setLayout(grid)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(formGroupBox)
        self.layout.addWidget(QtWidgets.QLabel(_("Save this config")))
        self.layout.addWidget(QtWidgets.QLabel(_("Changes will be effective after reloading")))
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def accept(self):
        print("save prefs")
        conf = UserConf(Configuration.USER_CONF_FILE)
        conf.save({k:v.isChecked() for k,v in self.form.items()})
        super().accept()
