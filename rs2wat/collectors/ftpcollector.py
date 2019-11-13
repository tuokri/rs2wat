import datetime
import fnmatch
import ftplib
import io
import logging
import os
import re
import sys
from typing import AnyStr
from typing import Sequence

import progressbar
from dateutil import relativedelta
from logbook import Logger, StreamHandler

from rs2wat import db

DIR_LISTING_PAT = r"([0-9]{2}-[0-9]{2}-[0-9]{2}\s{2}[0-9]{2}:[0-9]{2}\w{2})\s*(\d*) (.*)"
DIR_LISTING_TIME_FMT = "%m-%d-%y  %I:%M%p"
RS2_LOG_DATE_FMT = "%d/%m/%y %H:%M:%S"

StreamHandler(sys.stdout, level=logging.INFO).push_application()
logger = Logger(__name__)


class ProgressFile(object):
    """
    TODO: fix progress bar only updating once download is finished.
    """

    def __init__(self, file_path, mode, max_value=progressbar.UnknownLength):
        self.file_obj = open(file_path, mode)
        fct = progressbar.FormatCustomText("%(f)s", dict(f=""))
        self.progressbar = progressbar.ProgressBar(max_value=max_value, widgets=[
            progressbar.Counter(format='[%(value)02d/%(max_value)d]'),
            progressbar.Bar(marker=u'\u2588', fill='.', left='|', right='|'),
            fct,
        ])
        fct.update_mapping(f=file_path)

    def __enter__(self):
        return self.file_obj

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def write(self, data):
        length = self.file_obj.write(data)
        self.progressbar.update(length)
        return length

    def close(self):
        file_obj = self.file_obj
        if file_obj is None:
            return
        self.file_obj = None
        file_obj.close()


class FTPCollector(object):

    def __init__(self, host="", port=21, username="", password="", config=None):
        """
        If config is passed, all other arguments are ignored.

        :param host: FTP server address.
        :param port: FTP server port.
        :param username: FTP server username.
        :param password: FTP server password.
        :param config: FTP configuration dictionary.
        """
        if config is not None:
            host = config["host"]
            port = config["port"]
            username = config["username"]
            password = config["password"]

        self._username = username
        self._password = password

        host = str(host)
        port = int(port)

        self._ftp = ftplib.FTP_TLS()
        # self._ftp.set_debuglevel(2)
        self._ftp.connect(host, port)
        self._login(username, password)

        self._load_cached_modifications()

    def __del__(self):
        try:
            self._ftp.quit()
        except Exception as e:
            logger.error(e)

        try:
            self._ftp.close()
        except Exception as e:
            logger.error(e)

    def _send_username(self, username=""):
        if not username:
            username = self._username
        return self._ftp.sendcmd(f"USER {username}")

    def _send_password(self, password=""):
        if not password:
            password = self._password
        return self._ftp.sendcmd(f"PASS {password}")

    def _cwd(self, path=""):
        return self._ftp.cwd(path)

    def _pwd(self):
        return self._ftp.pwd()

    def _nlst(self, path=""):
        return self._ftp.nlst(path)

    def _retrbinary(self, cmd, callback, blocksize=8192, rest=None):
        return self._ftp.retrbinary(cmd, callback, blocksize, rest)

    def _size(self, path):
        return self._ftp.size(path)

    def _login(self, userame, password):
        self._send_username(userame)
        self._send_password(password)

    def _load_cached_modifications(self):
        mod_dict = db.get_log_cache()
        logger.info("loaded {m} cached modifications", m=len(mod_dict))
        self._modifications = mod_dict

    def _update_log_cache(self, path: str, open_time: datetime.datetime, bookmark: int):
        db.update_log_cache(path, open_time, bookmark)
        self._modifications[(path, open_time)] = bookmark

    def _insert_log_cache(self, path: str, open_time: datetime.datetime, bookmark: int):
        db.insert_log_cache(path, open_time, bookmark)
        self._modifications[(path, open_time)] = bookmark

    def collect_logs(self, path="", out_dir="", filename_pattern="*"):
        self._cwd(path)
        logs = self._nlst()
        length = len(logs)
        logs = reversed(logs)

        if logs:
            logger.info("found {length} files", length=length)
            os.makedirs(out_dir, exist_ok=True)

        for log in logs:
            if fnmatch.fnmatch(log, filename_pattern):
                out_path = os.path.join(out_dir, log)
                size = self._size(log)
                with ProgressFile(out_path, "wb", max_value=size) as pf:
                    self._retrbinary(f"RETR {log}", callback=pf.write)

    def prune_logs(self, path="", older_than: datetime.datetime = None,
                   filename_pattern="*.log"):
        """
        TODO:
        :param path:
        :param older_than:
        :param filename_pattern:
        :return:
        """
        if older_than is None:
            older_than = datetime.datetime.now() - relativedelta.relativedelta(days=15)

        self._cwd(path)
        listings = []
        self._ftp.dir("", listings.append)
        print(f"found {len(listings)} listings")
        listings = "\n".join(listings)

        matches = re.finditer(DIR_LISTING_PAT, listings)
        for m in matches:
            try:
                g = m.groups()
                try:
                    timestamp = datetime.datetime.strptime(
                        g[0].strip(), DIR_LISTING_TIME_FMT)
                except Exception as e:
                    logger.error("error, modifying timestamp: {e}", e=e.__class__.__name__)
                    timestamp = datetime.datetime.strptime(
                        g[0].strip().replace("00:", "12:"), DIR_LISTING_TIME_FMT)
                # size = g[1]
                fname = g[2]

                if (timestamp < older_than) and (fnmatch.fnmatch(fname, filename_pattern)):
                    print(f"removing {fname}, with modified time: {timestamp}")
                    self._ftp.delete(fname)

            except Exception as e:
                print(f"error: {e}, skipping: {m}")

    def get_new_modifications(self, path) -> Sequence[AnyStr]:
        """
        TODO:
        :param path:
        :return:
        """
        logger.info("getting new modifications from {p}", p=path)
        log = io.BytesIO()
        self._retrbinary(f"RETR {path}", callback=log.write)
        log = log.getvalue().decode("latin-1").split("\r\n")
        length = len(log)
        logger.info("got log with {lines} lines", lines=length)

        first = log[0].strip()
        log_open_time = datetime.datetime.strptime(first.split(", ")[1], RS2_LOG_DATE_FMT)
        logger.info("log open time: {t}", t=log_open_time.isoformat())

        bookmark_row_idx = 0
        if (path, log_open_time) not in self._modifications:
            logger.info("new, non-cached logfile: {path}", path=path)
            try:
                self._insert_log_cache(path, log_open_time, bookmark_row_idx)
            except Exception as e:
                # logger.error
                print("error saving new logfile to db: {path}: {e},"
                      "current modifications: {m}".format(path=path, e=e, m=self._modifications))
                raise
        else:
            logger.info("logfile: {path} is cached, bookmark: {bmi}", path=path, bmi=bookmark_row_idx)
            bookmark_row_idx = self._modifications[(path, log_open_time)]

        # Last row is discarded because it might be incomplete.
        new_bookmark = length - 1
        new_modifications = log[bookmark_row_idx:new_bookmark]

        self._update_log_cache(path, log_open_time, new_bookmark)

        return new_modifications
