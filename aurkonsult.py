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
