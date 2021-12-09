#!/usr/bin/env python

import sys
from pathlib import Path

from aurkonsult import _
from aurkonsult import Configuration
from aurkonsult.gui import run
from aurkonsult.gui import ICONS


if __name__ == "__main__":

    config = Configuration()

    def create_laucher():
        extend = ""
        if config.extended:
            extend = " --ext"
        if "--comments" in sys.argv:
            extend += " --comments"
        if "--history" in sys.argv:
            extend += " --history"
        if "--pamac" in sys.argv:
            extend += " --pamac"
        content = (
            "[Desktop Entry]\n"
            "Name=aurKonsult\n"
            "Comment=AUR Packages Qt Gui Explorer\n"
            f"Exec={__file__}{extend}\n"
            "Terminal=false\nType=Application\n"
            f"Icon={Configuration.LOGO_FILE}\n"
            "Categories=System;\nKeywords=aur;package;yay;\n"
        )
        Path(Path().home() / ".local/share/applications/aur-db.desktop").write_text(
            content
        )
        # subprocess.run("/usr/bin/update-desktop-database --quiet", shell=True) only with sudo

    if "-h" in sys.argv or "--help" in sys.argv:
        print(
            "   -h         : usage\n"
            "   -i         : install `~/.local/share/application/aur-db.desktop` in $HOME\n"
            "   -r         : remove all config files in $HOME\n"
            "   --ext      : load extended Aur Database\n"
            "   --mini     : for test, load only 100 aur packages\n"
            "   --comments : load comment dates from aur page\n"
            "   --history  : can load history dates/titles from aur repo\n"
            "   --pamac    : use pamac cli for install package\n"
            "\n"
            f"Load:  {config.url}\n"
            f"Save Database in : {config.db_file}\n"
            f"Save prev update time in : {config.db_time}\n"
            "\n"
            "create gui launcher example:\n"
            f" {Configuration.PKGNAME} -i --ext --history : create .desktop for use extended database and can load aur history \n"
        )
        exit(0)
    if "-i" in sys.argv:
        Configuration.LOGO_FILE.write_text(ICONS.app_logo_src())
        create_laucher()
    if "-r" in sys.argv:
        Path(Path().home() / ".local/share/applications/aur-db.desktop").unlink(
            missing_ok=True
        )
        config.db_file.unlink(missing_ok=True)
        config.db_time.unlink(missing_ok=True)
        config.LOGO_FILE.unlink(missing_ok=True)
        exit(0)

    run(config)

"""
TODO 
param packageName == do to page "packageName"

TODO graph best dependencies
https://github.com/PyQt5/PyQt/tree/master/QtChart

TODO:
pas d'Architecture ???

FIXED not update database in "check" page ... https://forum.manjaro.org/t/beta-gui-aur-explorer-for-plasma/92001/3
FIXED PackageBase not always exists https://forum.manjaro.org/t/beta-gui-aur-explorer-for-plasma/92001/9

TODO ? action exec copy cmd in clipboard :
org.kde.klipper /klipper org.kde.klipper.klipper.setClipboardContents 'yay -S pkg.Name'

TODO ?
not use python urllib ? but Qt modules ...
https://zetcode.com/pyqt/qnetworkaccessmanager/
https://programtalk.com/python-examples/PyQt5.QtNetwork.QNetworkRequest/

TODO ?
créer fichier test pour comparer Qt / python libs ...
read file line by line...
https://srinikom.github.io/pyside-docs/PySide/QtCore/QFile.html
https://stackoverflow.com/questions/5444959/read-a-text-file-line-by-line-in-qt/48038850#48038850
https://stackoverflow.com/questions/47336886/qt-program-to-read-text-sees-only-one-line-in-multi-line-file
http://tvaira.free.fr/dev/qt/faq-qt.html#comment-lire-des-donn%C3%A9es-dans-un-fichier-csv

TODO ... lang
https://www.programcreek.com/python/?code=Scille%2Fparsec-cloud%2Fparsec-cloud-master%2Fparsec%2Fcore%2Fgui%2Flang.py#

"""
