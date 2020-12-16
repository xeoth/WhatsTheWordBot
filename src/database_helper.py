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

Last modified by Xeoth on 16.12.2020
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

    def add_subscriber(self, post_id: str, username: str) -> None:
        """Adds a subscriber to a post and returns None"""
        self.cur.execute(
            'INSERT INTO subscribers (name, id) VALUES (?, ?);', (username, post_id))
        self.cnx.commit()

    def remove_all_subs(self, post_id: str) -> None:
        """Removes all subscribers from a post and returns None"""
        self.cur.execute("DELETE FROM subscribers WHERE id=?;", (post_id))
        self.cnx.commit()

    def check_points(self, username: str) -> int:
        """Queries the database for amount of points a specified user has and returns it"""
        self.cur.execute('SELECT points FROM users WHERE name=?;', (username,))
        results = self.cur.fetchone()

        return 0 if not results else results[0]

    def modify_points(self, username: str, difference: int):
        """
        Adds or removes specified amount of points from the user and returns None.
        Points can be both positive or negative, but score stored in DB cannot be negative.
        Creates the user in DB if does not exist yet.

        Arguments:
            username {string} -- The username of a user we want to modify points for

            difference {integer} -- The amount of points we can add to the user (or subtract from the user, if negative.)

        CAUTION! This does NOT set the points to the specified amount. Only either adds or subtracts from
        existing ones. To set points to a desired amount directly, use `set_points()`.
        """

        # I probably could've done it with pure SQL, but it'd be overly complicated. Python it is!

        # first, we need to get the current amount of points (or 0)
        self.cur.execute(
            'SELECT points FROM users WHERE name=?;', (username,))

        # this returns either a tuple with the score or None
        current_points = self.cur.fetchone()[0] or 0

        # now that we have our points, we can add or subtract the desired amount
        modified_points = current_points+difference

        # we're using unsigned ints, so the number cannot be smaller than 0
        if modified_points < 0:
            modified_points = 0

        self.cur.execute(
            'REPLACE INTO users VALUES (?, ?);', (username, modified_points))
        self.cnx.commit()
