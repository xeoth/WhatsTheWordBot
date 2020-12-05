/*
r/WTW Bot's Database Schema
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

Last modified by Xeoth on 04.12.2020
                 ^--------^ please change when modifying to comply with the license
*/

CREATE TABLE posts (
  id VARCHAR(7) PRIMARY KEY,
  status ENUM (
    'u', -- unsolved
    'a', -- abandoned
    'c', -- contested
    'k', -- unknown
  ),
  timestamp DATETIME
);

CREATE TABLE users (
  name VARCHAR(20) PRIMARY KEY,
  solved INT UNSIGNED,
);