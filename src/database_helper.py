"""
SQL Helper Library


Copyright 2020 Xeoth

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

Last modified by Xeoth on 14.12.2020
                 ^--------^ please change when modifying to comply with the license
"""

import mysql.connector


class DatabaseHelper:
    """Class made for easier interactions with MySQL, without the need for writing bare SQL inside the bot's code."""

    def __init__(self, username, password, hostname):
        self.cnx = mysql.connector.connect(
            user=username,
            password=password,
            host=hostname,
            database="WTWbot"
        )

        self.cur = self.cnx.cursor(prepared=True)

    def __del__(self):
        self.cur.close()
        self.cnx.close()

    def save_post(self, post_id: str, status: str) -> None:
        """Adds or updates a post in the database and returns None"""
        if status not in ('unsolved', 'abandoned', 'contested', 'unknown', 'overridden'):
            raise ValueError(
                "Invalid status provided. Must be one of: unsolved, abandoned, contested, unknown, overridden")

        self.cur.execute(
            'REPLACE INTO posts VALUES (?, ?, NOW());', (post_id, status))
        self.cnx.commit()

    def check_post(self, post_id: str) -> str or None:
        """Fetches a post's status from the database and returns it or None if no results are found."""
        self.cur.execute('SELECT status FROM posts WHERE id=?;', (post_id,))
        results = self.cur.fetchone()

        # fetchone() returns a tuple with a string, or None if no results are found.
        return None if not results else results[0]
