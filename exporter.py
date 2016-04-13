from BeautifulSoup import BeautifulSoup
import logging
import requests


class PHPMyAdmin(object):
    def __init__(self, baseurl, username, password):
        self._logger = logging.getLogger("PHPMyAdmin")
        self._session = requests.Session()
        self._baseurl = baseurl
        self._username = username
        self._password = password
        self._logged_in = False

    def __del__(self):
        if self._logged_in:
            self._logger.debug("logging out...")
            self.logout()

    def login(self):
        if self._logged_in:
            raise RuntimeError("already logged in")

        self._logger.debug("getting index.php...")
        resp = self._session.get(self._baseurl + "/index.php")
        resp.raise_for_status()
        self._logger.debug("extracting token...")
        soup = BeautifulSoup(resp.content)
        token = soup.find('input', dict(name='token'))['value']
        self._token = token
        self._logger.info("token: %s" % token)
        self._logger.debug("logging in...")
        data = {
            'pma_username': self._username,
            'pma_password': self._password,
            'server': 1,
            'token': token,
        }
        resp = self._session.post(self._baseurl + "/index.php", data=data)
        resp.raise_for_status()
        self._logged_in = True
        self._logger.info("logged in")

    def logout(self):
        if not self._logged_in:
            raise RuntimeError("not logged in")
            
        self._logger.debug("logging out...")
        data = {
            'old_usr': self._username,
        }
        resp = self._session.get(self._baseurl + "/index.php", data=data)
        resp.raise_for_status()
        self._logged_in = False
        self._logger.info("logged out")

    def export_database(self, database, filename=None):
        if not self._logged_in:
            self.login()

        if not filename:
            filename = "%s.sql" % database

        self._logger.debug("exporting database...")
        data = {
            "token": self._token,
            "export_type": "server",
            "export_method": "quick",
            "quick_or_custom": "quick",
            "db_select[]": database,
            "output_format": "sendit",
            "filename_template": "__SERVER__",
            "remember_template": "on",
            "charset_of_file": "utf-8",
            "compression": "none",
            "what": "sql",
            "sql_include_comments": "something",
            "sql_header_comment": "",
            "sql_compatibility": "NONE",
            "sql_structure_or_data": "structure_and_data",
            "sql_procedure_function": "something",
            "sql_create_table_statements": "something",
            "sql_if_not_exists": "something",
            "sql_auto_increment": "something",
            "sql_backquotes": "something",
            "sql_type": "INSERT",
            "sql_insert_syntax": "both",
            "sql_max_query_size": "50000",
            "sql_hex_for_blob": "something",
            "sql_utc_time": "something",
        }
        resp = self._session.post(
            self._baseurl + "/export.php", data=data)
        resp.raise_for_status()

        with open(filename, "w+") as f:
            f.write(resp.content)
        self._logger.info("database exported")


if __name__ == "__main__":
    from optparse import OptionParser

    usage = "usage: %prog [options] <baseurl> <username> <password> <database>"
    parser = OptionParser(usage)
    parser.add_option("-o", "--output", dest="filename",
                      help="write output to FILENAME")
    (options, args) = parser.parse_args()
    if len(args) != 4:
        parser.error("incorrect number of arguments")

    admin = PHPMyAdmin(*args[:3])
    admin.export_database(args[3], filename=options.filename)
