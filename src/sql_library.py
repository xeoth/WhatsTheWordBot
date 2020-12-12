"""
SQL Helper Library


Original work Copyright 2020 Nate Harris
Modified work Copyright 2020 Xeoth

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

---

Last modified by Xeoth on 12.12.2020
                 ^--------^ please change when modifying to comply with the license
"""


# import sqlite3
# from pysqlcipher3 import dbapi2 as sqlcipher
import mysql.connector
# import pyodbc


class SQL:
    def __init__(self, sql_type: str, server_ip: str = None, database_name: str = None, username: str = None,
                 password: str = None, use_Active_Directory: bool = False, sqlite_file: str = None,
                 encryption_key: str = None):
        self.SQL_TYPE = sql_type
        self.SERVER_IP = server_ip
        self.DATABASE_NAME = database_name
        self.USERNAME = username
        self.PASSWORD = password
        self.USE_ACTIVE_DIRECTORY = use_Active_Directory
        self.SQLITE_FILE = sqlite_file
        self.KEY = encryption_key
        self._requirements_check()

    def _requirements_check(self):
        if self.SQL_TYPE not in ['MySQL', 'SQLite', 'SQLCipher', 'MSSQL']:
            raise Exception("Not a valid sql_type.")
        if self.SQL_TYPE in ['SQLite', 'SQLCipher']:
            if not self.SQLITE_FILE:
                raise Exception("Please provide an SQLite or SQLCipher file.")
        if self.SQL_TYPE == 'SQLCipher':
            if not self.KEY and self.PASSWORD:
                self.KEY = self.PASSWORD
            if not self.KEY:
                raise Exception("Missing key to unlock encrypted database.")
        if self.SQL_TYPE in ['MySQL', 'MSSQL']:
            if not (self.SERVER_IP and self.DATABASE_NAME):
                raise Exception(
                    "Please provide a server IP address and a database name.")
        if self.SQL_TYPE == 'MySQL':
            if not (self.USERNAME and self.PASSWORD):
                raise Exception("Please provide a username and password.")
        if self.SQL_TYPE == 'MSSQL':
            if not ((self.USERNAME and self.PASSWORD) or self.USE_ACTIVE_DIRECTORY):
                raise Exception(
                    "Please use either username/password or Active Directory.")

    def _get_connection(self):
        db = mysql.connector.connect(user=self.USERNAME, password=self.PASSWORD, host=self.SERVER_IP,
                                     database=self.DATABASE_NAME)
        # db = sqlite3.connect(self.SQLITE_FILE)

        return db

    def use_sql_locally(self):
        """
        Pass SQL instance over.
        :return:
        """
        return self._get_connection()

    def custom_query(self, queries: [], commit: bool = False, print_queries: bool = False):
        conn = self._get_connection()
        if conn:
            cur = conn.cursor()
            for query in queries:
                if print_queries:
                    print(query)
                cur.execute(query)
            results = cur.fetchall()
            if commit:
                results = cur.rowcount
                conn.commit()
            cur.close()
            conn.close()
            return results
        else:
            raise Exception("Couldn't connect to the database.")
