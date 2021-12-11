import os
import sys
import time
from pathlib import Path
from typing import Generator


class Configuration:
    VERSION = "0.1.30"
    PKGNAME = "aurkonsult"
    USER_CONF_FILE = Path.home() / f".config/{PKGNAME}.conf"
    LOGO_FILE = Path.home() / f".local/share/icons/{PKGNAME}.svg"
    KONSOLE_INSTALLED = Path("/usr/bin/konsole").exists()

    def __init__(self) -> None:
        self.attributes = {
            "extended": False,
            "comment": False,
            "history": False,
            "pamac": False,
            "homecache": False,
        }
        self.load_user_conf()
        self.load_user_params()
        self.time_since_update = int(time.time() - (3600 * 48))
        start_time = time.time()
        # NOTE : never reload (bab if pkg installed since ; bof: version is the last)
        self.user_aurs = self.load_aur_user()
        print(
            "get aur pkgs installed, duration: "
            f"-- {(time.time() - start_time)} seconds --"
        )
        self.time_since_update = self.get_update_since()

    @property
    def extended(self) -> bool:
        return self.attributes["extended"]

    @property
    def db_name(self) -> str:
        if self.attributes["extended"]:
            return "packages-meta-ext-v1"
        return "packages-meta-v1"

    @property
    def url(self) -> str:
        return f"https://aur.archlinux.org/{self.db_name}.json.gz"

    @property
    def db_file(self) -> Path:
        if self.attributes["homecache"]:
            return Path.home() / f".cache/{self.db_name}.json"
        return Path(f"/tmp/{self.db_name}.json")  # in ~/;cache ?

    @property
    def db_save(self) -> Path:
        return Path.home() / f".cache/{self.db_name}.json"

    @property
    def db_time(self) -> Path:
        return Path.home() / f".cache/{self.db_name}.time"

    def load_user_conf(self):
        """load user configuration"""
        conf = UserConf(self.USER_CONF_FILE)
        datas = conf.read()
        for key in self.attributes:
            self.attributes[key] = datas.get(key, False)

    def load_user_params(self):
        """override .conf file"""
        if "--comments" in sys.argv:
            self.attributes["comment"] = True
        if "--ext" in sys.argv:
            self.attributes["extended"] = True
        if "--pamac" in sys.argv:
            self.attributes["pamac"] = True
        if "--history" in sys.argv:
            self.attributes["history"] = True
        if "--pamac" in sys.argv:
            self.attributes["pamac"] = True
        if "--homecache" in sys.argv:
            self.attributes["homecache"] = True

    def get_update_since(self) -> int:
        def setlong(stime):
            return stime if len(stime) > 1 else f"0{stime}"

        try:
            last_update = self.db_file.stat().st_mtime
        except FileNotFoundError:
            last_update = int(time.time())
        try:
            old_update = float(self.db_time.read_text())
        except FileNotFoundError:
            print(f"warning: file '{self.db_time}' not found!")
            return 0
        diff = last_update - old_update
        days, remainder = divmod(diff, 3600 * 24)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        hours, minutes = int(hours), int(minutes)
        ret = (
            f"{'' if int(days)<1 else str(int(days))+' days '}"
            f"{'' if int(hours)<1 else setlong(str(hours))+' hours '}"
            f"{'' if int(minutes)<1 else setlong(str(minutes))+' minutes '}"
        )
        print("New package since:", ret, "in 'highlight' color\n")
        return int(old_update)

    @staticmethod
    def load_aur_user() -> dict[str, tuple[str, str, str, str, str]]:
        ret = {}
        for pkg in Configuration._get_aur_pkgs():
            ret[pkg[0]] = pkg
        return ret

    @staticmethod
    def _get_aur_pkgs() -> Generator[tuple, None, None]:
        """pkg installed with no packager
        not have all pkg not in repot !
        diff : old packages in repot (as yaourt,...)
        ----
        best speed here vs use pacman pacman -Qm :
            get_aur_pkgs(): duration: -- 0.10 seconds --
            pacman -Qm:     duration: -- 0.48 seconds --
        """
        pkg = ()
        for desc_file in Path("/var/lib/pacman/local/").glob("*/desc"):
            with desc_file.open("r") as file:
                for line in file:
                    if line == "%NAME%\n":
                        pkg = (str(next(file)).rstrip(),)
                    elif line == "%VERSION%\n":
                        pkg += (str(next(file)).rstrip(),)
                    elif line == "%DESC%\n":
                        pkg += (str(next(file)).rstrip(),)
                    elif line == "%URL%\n":
                        pkg += (str(next(file)).rstrip(),)
                    elif line == "%VALIDATION%\n":
                        line = str(next(file)).rstrip()
                        if line == "none":
                            yield pkg
                            break


class UserConf:
    """read/save configuration in home file"""

    def __init__(self, filename: Path) -> None:
        self.file = filename
        if not self.file.exists():
            self.file.touch()

    def read(self) -> dict:
        ret = {}
        with self.file.open("r") as fin:
            for line in fin:
                lines = line.strip().split("=", 1)
                value = lines[1].lstrip().capitalize()
                value = True if value in ("1", "True") else value
                value = False if value in ("0", "False") else value
                ret[lines[0].rstrip()] = value
        return ret

    def save(self, datas: dict):
        with self.file.open("w") as fin:
            for key, value in datas.items():
                fin.write(f"{key} = {value}\n")
