"""
Packages class
"""
import json
import time
from typing import Any, Generator
from urllib import parse
from ctypes import cdll, CDLL


FIELDS = (
    "id",
    "name",
    "version",
    "package_base",
    "description",
    "url",
    "maintainer",
    "out_of_date",
    "first_submitted",
    # 'URLPath',
    "last_modified",
    "popularity",
    "num_votes",
    "license",
    "provides",
    "keywords",
    "depends",
    "make_depends",
    "opt_depends",
    "conflicts",
    "version_local",
    "vercmp",
)


class Package:
    """json representation"""

    __slots__ = FIELDS
    # _arrays = ('License', 'Keywords', 'Depends', 'MakeDepends', 'OptDepends', 'Conflicts', 'Provides')

    def __init__(self, jsondict: dict = None) -> None:
        self.id = ""
        self.name = ""
        self.package_base = ""
        self.version = ""
        self.description = ""
        self.url = ""
        # self.url_path = ""
        self.maintainer = ""
        self.out_of_date = None
        self.first_submitted: int = 0
        self.last_modified: int = 0
        self.popularity: float = 0.0
        self.num_votes: int = 0
        # extend :
        self.license: list[str] = []
        self.keywords: list[str] = []
        self.depends: list[str] = []
        self.make_depends: list[str] = []
        self.opt_depends: list[str] = []
        self.conflicts: list[str] = []
        self.provides: list[str] = []
        self.vercmp: int = 0

        self.version_local: str = ""
        if jsondict:
            self.populate(jsondict)

    def populate(self, data: dict):
        """inject datas from json field"""
        for attr in FIELDS:
            attr_aur = self.denormalize_name_attr(attr)
            try:
                if value := data[attr_aur]:
                    # not inject other type as NoneType (bad for sort)
                    setattr(self, attr, value)
            except:
                pass  # this model not use
                # raise
        self.set_version_local(self.version_local)
        if self.package_base == self.name:
            self.package_base = ""

    def is_installed(self):
        return bool(self.version_local)

    def set_version_local(self, version):
        self.version_local = version
        self.vercmp = 0
        if self.version_local and self.version:
            self.vercmp = vercmp(self.version_local, self.version)

    def __neg__(self) -> bool:
        """if not pkg then is_out_of_date"""
        return bool(self.out_of_date)

    def __gt__(self, compare: str):
        if compare == "aur":
            return self.vercmp < 0
        else:
            raise TypeError("Compare only local version vs aur version")

    def __lt__(self, compare: str):
        if compare == "aur":
            return self.vercmp > 0
        else:
            raise TypeError("Compare only local version vs aur version")

    def __rrshift__(self, other):
        """>> asign fields in Package"""
        if isinstance(other, dict):
            self.populate(other)
        elif isinstance(other, str):
            self.populate(json.loads(other))
        else:
            raise TypeError("entry is not compatible with package")
        return self

    def fields(self) -> Generator[tuple[str, Any], None, None]:
        """iterate from attributes, return tuple key, value"""
        for k in self.__slots__:
            yield k, getattr(self, k, "")

    def __repr__(self):
        ret = ""
        for k, value in self.fields():
            if isinstance(value, str):
                value = value.replace('"', '"')
                value = f'"{value}"'
            ret += f"'{k}':{value}, "
        return f"{{{ret}}}"

    def __format__(self, format_spec: str) -> str:
        """format output for f-string
        usage: f"pkg:LastModified"
        """
        if not format_spec or format_spec == "s":
            return str(self)
        if format_spec == "LastModified":
            return self.epoch_to_str(self.last_modified)
        if format_spec == "FirstSubmitted":
            return self.epoch_to_str(self.first_submitted)
        if format_spec == "Popularity":
            return f"{float(self.popularity):.5f}"
        if format_spec == "URL":
            if not self.url:
                return ""
            else:
                return f'<a href="{self.url}">{self.url}</a>'
        if format_spec == "hostname":
            if url := self.url:
                if url := parse.urlparse(url).hostname:
                    url = url.split(".", 3)
                    return ".".join(url[-2:])
            return " -"
        if format_spec == "PKGBUILD":
            url = "https://aur.archlinux.org/cgit/aur.git/tree/PKGBUILD?h="
            return f'<a href="{url}{self.name}">{url}{self.name}</a>'
        if format_spec == "Aur":
            url = "https://aur.archlinux.org/packages/"
            return f'<a href="{url}{self.name}/">{url}{self.name}</a>'
        if format_spec == "OutOfDate":
            return (
                '<b style="color:red">Flagged out-of-date</b>'
                if self.out_of_date
                else ""
            )
        raise ValueError(f"Unknown format '{format_spec}' for object `Package`")

    def __getattr__(self, name: str):
        """
        if exists some optional fields, return as empty
        # TODO usefull this Pacage.method ?
        """
        raise Exception(f"package Field not found: {name}")

    def __getitem__(self, index):
        try:
            return getattr(self, index)
        except TypeError:
            print("Bad index:", index)
            raise

    @staticmethod
    def normalize_name_attr(name: str) -> str:
        """aur field name to python class name attribute"""
        if name == "URL":
            return "url"
        ret = ""
        for i, char_name in enumerate(name):
            if ord(char_name) in range(ord("A"), ord("Z") + 1):
                char_name = char_name.lower()
                ret = f"{ret}_{char_name}" if i > 0 else char_name
            else:
                ret = f"{ret}{char_name}"
        return ret

    @staticmethod
    def denormalize_name_attr(name: str) -> str:
        """python class name attribute to aur field name"""
        if name == "url":
            return "URL"
        ret = ""
        names = list(name)
        names[0] = names[0].upper()
        for i, char_name in enumerate(names):
            if char_name == "_":
                try:
                    names[i + 1] = names[i + 1].upper()
                except IndexError:
                    pass
                continue
            ret = f"{ret}{char_name}"
        return ret

    @staticmethod
    def epoch_to_str(epoch: int) -> str:
        """epoch time to user time date"""
        if not epoch:
            return ""
        strdate = time.strftime("%Y-%m-%d %X %Z", time.localtime(epoch))[0:]
        return f"{strdate[0:16]}"  # truncate date time

    """
    @staticmethod
    def epoch_to_QDateTime(epoch):
        if epoch == 0:
            return ""
        try:
            dpkg = time.localtime(epoch)
        except:
            print("Erreur epoch=", epoch)
            raise
        return QtCore.QDateTime(
            QtCore.QDate(dpkg.tm_year, dpkg.tm_mon, dpkg.tm_mday),
            QtCore.QTime(dpkg.tm_hour, dpkg.tm_min),
        )
    """


"""
# TODO graph dependencies
def getAllDependencies(package_list) ->dict:
    print("getAllDependencies()...")
    rets = {}
    pkg: Package
    for pkg in package_list:
        for dep in pkg.Depends:
            if '>' in dep:
                dep = dep.split('>')[0]
            if '<' in dep:
                dep = dep.split('<')[0]
            if '=' in dep:
                dep = dep.split('=')[0]
            #if dep in rets:
            value = rets.get(dep, 0)
            rets[dep] = value + 1
            #else:
            #    rets[dep] = 1

    print("deps count:", len(rets))
    #sort_orders = sorted(rets.items(), key=rets.get, reverse=True) # lambda x: x[1], reverse=True)
    sort_orders = {k: v for k, v in sorted(rets.items(), key=lambda x: x[1], reverse=True) if v > 500}
    for i, item in enumerate(sort_orders.items()):
        print(item)
        if i > 50:
            break
    return sort_orders
"""

cdll.LoadLibrary("libalpm.so")
libalpm = CDLL("libalpm.so")


def vercmp(ver1: str, ver2: str) -> int:
    """==0 : same, <0: if ver1<ver2 , >0: if ver1>ver2"""
    cchar1, cchar2 = bytes(ver1.encode()), bytes(ver2.encode())
    return libalpm.alpm_pkg_vercmp(cchar1, cchar2)
