# r/WhatsTheWord bot
# Original work Copyright 2020 Nate Harris
# Modified work Copyright 2021 Xeoth
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ---
#
# Last modified by Xeoth on 15.01.2021
#                  ^--------^ please change when modifying to comply with the license

import logging
from os import getenv

import praw
import yaml
from dotenv import load_dotenv

import helpers
import routines

load_dotenv()

with open('config.yaml') as file:
    config = yaml.safe_load(file)

REDDIT_CLIENT_ID = getenv('WTW_REDDIT_ID')
REDDIT_CLIENT_SECRET = getenv('WTW_REDDIT_SECRET')
REDDIT_USERNAME = getenv('WTW_REDDIT_USERNAME')
REDDIT_PASSWORD = getenv('WTW_REDDIT_PASSWORD')

logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] %(module)s | %(levelname)s: %(message)s")

reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET,
                     user_agent=f"{config['subreddit']}'s WhatsTheWordBot",
                     username=REDDIT_USERNAME, password=REDDIT_PASSWORD)

if not reddit.read_only:
    logging.info("Connected and running.")

if __name__ == "__main__":
    """
    New submission: automatically flaired "unsolved"
    If "solved" comment from OP -> "solved"
    If non-"solved" comment from OP -> "contested"
    If new comment from non-OP -> "unsolved"/"contested"/"unknown" -> "contested" (ignore "abandoned")
    After 24 hours, "unsolved" -> "abandoned" (check if solved first) (unsolved means no new comments; otherwise would be "contested")
    After 48 hours, "contested" -> "unknown" (check if solved first) (contested means someone has commented)
    """
    
    db = helpers.DatabaseHelper(
        username=getenv("WTW_DB_USERNAME"),
        password=getenv("WTW_DB_PASSWORD"),
        hostname=getenv("WTW_DB_IP")
    )
    
    rh = helpers.RedditHelper(
        db=db,
        config=config
    )
    
    config["mods"] = [mod.name for mod in reddit.subreddit(config["subreddit"]).subreddit.moderator()]

    while True:
        try:
            routines.check_unsolved(reddit, db, rh, config)
            routines.check_new(reddit, db, rh, config)
            routines.check_contested(reddit, db, rh, config)
            routines.check_comments(reddit, db, rh, config)
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt detected; quitting.")
            exit(0)
        except BaseException as e:
            logging.error(f'Exception occured; {e}')
