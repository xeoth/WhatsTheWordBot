"""
SQL Helper Library


Copyright 2021 Xeoth

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

Last modified by Xeoth on 2.1.2021
                 ^--------^ please change when modifying to comply with the license
"""


import mysql.connector
from typing import Tuple, Optional


class DatabaseHelper:
    """Class made for easier interactions with MySQL, without the need for writing bare SQL inside the bot's code."""

    def __init__(self, username, password, hostname):
        self._cnx = mysql.connector.connect(
            user=username,
            password=password,
            host=hostname,
            database="WTWbot"
        )

        self._cur = self._cnx.cursor(prepared=True)

    def __del__(self):
        self._cur.close()
        self._cnx.close()

    def save_post(self, post_id: str, status: str) -> None:
        """Adds or updates a post in the database and returns None"""
        if status not in ('unsolved', 'abandoned', 'contested', 'unknown', 'overridden'):
            raise ValueError(
                "Invalid status provided. Must be one of: unsolved, abandoned, contested, unknown, overridden")

        self._cur.execute(
            'REPLACE INTO posts VALUES (?, ?, UNIX_TIMESTAMP());', (post_id, status))
        self._cnx.commit()

    def check_post(self, post_id: str) -> Optional[str]:
        """Fetches a post's status from the database and returns it or None if no results are found."""
        self._cur.execute('SELECT status FROM posts WHERE id=?;', (post_id,))
        results = self._cur.fetchone()

        # fetchone() returns a tuple with a string, or None if no results are found.
        return None if not results else results[0]

    def add_subscriber(self, post_id: str, username: str) -> None:
        """Adds a subscriber to a post and returns None"""
        self._cur.execute(
            'INSERT INTO subscribers (name, id) VALUES (?, ?);', (username, post_id))
        self._cnx.commit()

    def remove_all_subs(self, post_id: str) -> None:
        """Removes all subscribers from a post and returns None"""
        self._cur.execute("DELETE FROM subscribers WHERE id=?;", (post_id,))
        self._cnx.commit()

    def check_points(self, username: str) -> int:
        """Queries the database for amount of points a specified user has and returns it"""
        self._cur.execute(
            'SELECT points FROM users WHERE name=?;', (username,))
        results = self._cur.fetchone()

        return 0 if not results else results[0]

    def modify_points(self, username: str, difference: int) -> None:
        """
        Adds or removes specified amount of points from the user and returns None.
        Points can be both positive or negative, but score stored in DB cannot be negative.
        Creates the user in DB if does not exist yet.
        
        **Caution!** This does **not** set the points to the specified amount. Only either adds or subtracts from
        existing ones. To set points to a desired amount directly, use ``set_points()``.

        :param username: Username of the user we want to modify points for
        :param difference: The amount of points we can add to the user (or subtract from the user, if negative.)
        """

        # I probably could've done it with pure SQL, but it'd be overly complicated. Python it is!

        # first, we need to get the current amount of points (or 0)
        self._cur.execute(
            'SELECT points FROM users WHERE name=?;', (username,))

        # this returns either a tuple with the score or None
        current_points = self._cur.fetchone()[0] or 0

        # now that we have our points, we can add or subtract the desired amount
        modified_points = current_points+difference

        # we're using unsigned ints, so the number cannot be smaller than 0
        if modified_points < 0:
            modified_points = 0

        self._cur.execute(
            'REPLACE INTO users VALUES (?, ?);', (username, modified_points))
        self._cnx.commit()

    def set_points(self, username: str, amount: int) -> None:
        """Sets user's points in the DB to a specified amount"""

        # since we're dealing with unsigned ints, we cannot have negatives
        if amount < 0:
            raise ValueError("Amount of points cannot be negative.")

        self._cur.execute("REPLACE INTO users VALUES (?, ?);",
                          (username, amount))
        self._cnx.commit()

    def get_old_posts(self, second_limit: float, status: str) -> Optional[Tuple[str, ...]]:
        """Returns posts saved in the DB that are older than a specified amount of time and have the specified status.
        
        :param second_limit: Limit (in seconds) which the posts must surpass to be returned
        :param status: Status of the post in the database (unsolved, overridden, solved, etc.)
        :returns: If any posts with provided criteria exist, will return a tuple with their IDs
        """
        if status:
            self._cur.execute(
                'SELECT id FROM posts WHERE timestamp <= ? AND status = ?;', (second_limit, status))
        else:
            self._cur.execute(
                'SELECT id FROM posts WHERE timestamp <= ?;', (second_limit,))

        results = self._cur.fetchall()

        if not results:
            # means there are no old posts
            return None
        else:
            # this query will return a list of tuples in which the only element will be post IDs, like [('ks72b',),
            # ('jbdno3',)]
            # this turns this hellspawned list-tuple-thing into a regular tuple with normal post IDs
            return tuple([post[0] for post in results])
