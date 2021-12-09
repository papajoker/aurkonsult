'''
Packages class
'''
import json
import time
from typing import Any, Generator
from urllib import request, error, parse
from ctypes import cdll, CDLL


FIELDS = (
    "ID",
    "Name",
    "Version",
    "PackageBase",
    "Description",
    "URL",
    "Maintainer",
    "OutOfDate",
    "FirstSubmitted",
    #'URLPath',
    "LastModified",
    "Popularity",
    "NumVotes",
    "License",
    "Provides",
    "Keywords",
    "Depends",
    "MakeDepends",
    "OptDepends",
    "Conflicts",
    "localversion",
    "vercmp",
)


class Package:
    """json representation"""

    __slots__ = FIELDS
    # _arrays = ('License', 'Keywords', 'Depends', 'MakeDepends', 'OptDepends', 'Conflicts', 'Provides')

    def __init__(self, jsondict: dict = None) -> None:
        self.ID = ""
        self.Name = ""
        self.PackageBase = ""
        self.Version = ""
        self.Description = ""
        self.URL = ""
        # self.URLPath = ""
        self.Maintainer = ""
        self.OutOfDate = None
        self.FirstSubmitted: int = 0
        self.LastModified: int = 0
        self.Popularity: float = 0.0
        self.NumVotes: int = 0
        # extend :
        self.License: list[str] = []
        self.Keywords: list[str] = []
        self.Depends: list[str] = []
        self.MakeDepends: list[str] = []
        self.OptDepends: list[str] = []
        self.Conflicts: list[str] = []
        self.Provides: list[str] = []
        self.vercmp: int = 0

        self.localversion: str = ""
        if jsondict:
            self.populate(jsondict)

    def populate(self, data: dict):
        """inject datas from json field"""
        for attr in FIELDS:
            try:
                if data[attr]:
                    # not inject other type as NoneType (bad for sort)
                    setattr(self, attr, data[attr])
            except:
                pass  # this model not use
                # raise
        self.set_localversion(self.localversion)
        if self.PackageBase == self.Name:
            self.PackageBase = ""

    def is_installed(self):
        return bool(self.localversion)

    def set_localversion(self, version):
        self.localversion = version
        self.vercmp = 0
        if self.localversion and self.Version:
            self.vercmp = vercmp(self.localversion, self.Version)

    def __neg__(self) -> bool:
        """ if not pkg then is_out_of_date """
        return bool(self.OutOfDate)

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
        """ >> asign fields in Package """
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
        for k, v in self.fields():
            if isinstance(v, str):
                v = v.replace('"','\"')
                v = f'"{v}"'
            ret += f"'{k}':{v}, "
        return f"{{{ret}}}"

    def __format__(self, format_spec: str) -> str:
        """format output for f-string
        usage: f"pkg:LastModified"
        """
        if not format_spec or format_spec == "s":
            return str(self)
        if format_spec == "LastModified":
            return self.epoch_to_str(self.LastModified)
        if format_spec == "FirstSubmitted":
            return self.epoch_to_str(self.FirstSubmitted)
        if format_spec == "Popularity":
            return f"{float(self.Popularity):.5f}"
        if format_spec == "URL":
            if not self.URL:
                return ""
            else:
                return f'<a href="{self.URL}">{self.URL}</a>'
        if format_spec == "hostname":
            if url := self.URL:
                if url := parse.urlparse(url).hostname:
                    url = url.split(".", 3)
                    return ".".join(url[-2:])
            return " -"
        if format_spec == "PKGBUILD":
            url = "https://aur.archlinux.org/cgit/aur.git/tree/PKGBUILD?h="
            return f'<a href="{url}{self.Name}">{url}{self.Name}</a>'
        if format_spec == "Aur":
            url = "https://aur.archlinux.org/packages/"
            return f'<a href="{url}{self.Name}/">{url}{self.Name}</a>'
        if format_spec == "OutOfDate":
            return (
                '<b style="color:red">Flagged out-of-date</b>' if self.OutOfDate else ""
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
    def epoch_to_str(epoch: int) -> str:
        """epoch time to user time date"""
        if not epoch:
            return ""
        strdate = time.strftime("%Y-%m-%d %X %Z", time.localtime(epoch))[0:]
        return f"{strdate[0:16]}"  # truncate date time

    '''
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
    '''

'''
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
'''

cdll.LoadLibrary("libalpm.so")
libalpm = CDLL("libalpm.so")


def vercmp(ver1: str, ver2: str) -> int:
    """ ==0 : same, <0: if ver1<ver2 , >0: if ver1>ver2 """
    cchar1, cchar2 = bytes(ver1.encode()), bytes(ver2.encode())
    return libalpm.alpm_pkg_vercmp(cchar1, cchar2)
