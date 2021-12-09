'''
interface with AUR
'''
import os
import time
import datetime
from pathlib import Path
from urllib import request, error
import gzip
import platform
from .config import Configuration

def _get_user_agent():
    """http signature"""
    uname = platform.uname()
    return (
        f"{Configuration.PKGNAME}/{Configuration.VERSION} ({uname.system} {uname.release}; "
        f"{uname.machine}; {os.environ['DESKTOP_SESSION']})"
    )


def convert_header_date(header: str) -> datetime.datetime:
    """http header `Wed, 24 Nov 2021 21:36:46 GMT` to datetime"""
    months = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12",
    }
    headers = header.split(" ")[1:]
    try:
        headers[1] = months[headers[1]]
        header = " ".join(headers)
    except KeyError:
        header = "24 11 2020 21:00:00 GMT"
        # return datetime.datetime.now()
    return datetime.datetime.strptime(header, "%d %m %Y %H:%M:%S %Z")


def download(file_name: Path, url: str, time_file: Path) -> int:
    """download aur database in /tmp/"""
    print(file_name)
    modified_since = ""
    check_time = True
    dt_last_update = datetime.datetime.utcnow()
    if file_name.exists():
        check_time = False
        last_update = file_name.stat().st_mtime
        dt_last_update = datetime.datetime(*time.gmtime(last_update)[:6])
        print("dt_last_update (json age): ", dt_last_update)
        modified_since = time.strftime(
            "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(file_name.stat().st_mtime)
        )[0:]
        print("download if after:", modified_since)

    print(f"\n:: Download Database... in {file_name}")
    req = request.Request(url, method="HEAD")
    req.add_header("User-Agent", f"'User-Agent': '{_get_user_agent()}'")
    req.add_header(
        "Accept-Encoding", "gzip"
    )  # ? https://gitlab.archlinux.org/archlinux/aurweb/-/issues/175

    if file_name.exists():
        req.add_header("If-Modified-Since", modified_since)

        with request.urlopen(req) as response:
            expire = convert_header_date(response.headers["Expires"])
            ismodified = convert_header_date(response.headers["Last-Modified"])
            print("expire:", expire)
            utc_time = datetime.datetime.utcnow()
            print("cache expire in:", expire - utc_time)
            if file_name.exists():
                if dt_last_update > ismodified or expire < dt_last_update:
                    print("http 304: use cache")
                    return 304

    req.method = "GET"
    try:
        with request.urlopen(req) as response:
            if response.status == 200:
                file_name.unlink(missing_ok=True)
            if response.status == 304:
                return 304
            with gzip.GzipFile(fileobj=response) as uncompressed, open(
                file_name, "wb"
            ) as out_file:
                out_file.write(uncompressed.read())
    except error.HTTPError as err:  # can also have gz error
        print(err)
        print(f"\nBad connexion ?: {url}")
        return 404
        # exit(7)
    if file_name.exists():
        # if check_time:
        #    TIME_SINCE_UPDATE = get_update_since()
        last_update = int(file_name.stat().st_mtime)
        time_file.write_text(f"{last_update}")
        return 200
    return 500
