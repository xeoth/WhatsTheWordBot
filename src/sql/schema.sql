/*
r/WTW Bot's Database Schema
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

Last modified by Xeoth on 12.12.2020
                 ^--------^ please change when modifying to comply with the license
*/

CREATE TABLE posts (
  id VARCHAR(7),
  status ENUM (
    'unsolved',
    'abandoned',
    'contested',
    'unknown',
    'overridden'
  ) NOT NULL,
  timestamp DATETIME NOT NULL, -- so that we can wipe old records
  PRIMARY KEY (id)
);

CREATE TABLE users (
  name VARCHAR(20),
  points INT UNSIGNED NOT NULL,
  PRIMARY KEY (name)
);

-- this one will be used for storing members who subsribe to a thread
CREATE TABLE subscribers (
  name VARCHAR(20) NOT NULL, -- subscriber username
  id VARCHAR(7) NOT NULL, -- post ID
  internal_id INT UNSIGNED AUTO_INCREMENT, -- internal ID uniquely identifying every record and used for DB maintenance purposes. this should not be accessed from code too often, if at all.
  PRIMARY KEY (internal_id)
);