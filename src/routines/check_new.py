#  Copyright 2021 Xeoth
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation version 3.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#  ---
#
#  Last modified by Xeoth on 20.1.2021
#                   ^--------^ please change when modifying to comply with the license

import praw
from praw import models
from helpers.reddit_helper import RedditHelper
from helpers.database_helper import DatabaseHelper


def check_new(reddit: praw.Reddit, db: DatabaseHelper, rh: RedditHelper, config):
    subreddit = reddit.subreddit(config["subreddit"])
    
    # log new submissions to database, apply "unsolved" flair
    submission_stream: models.ListingGenerator = subreddit.new(
        limit=10)  # if you're getting more than 10 new submissions in two seconds, you have a problem
    for submission in submission_stream:
        if submission is None or submission.author is None:
            break
        elif rh.submitter_is_mod(submission, config["mods"]):
            db.save_post(submission.id, 'overridden')
            break
        elif rh.mod_overridden(submission):
            break
        else:
            if not rh.check_flair(submission=submission, flair_text=config["flairs"]["unsolved"]["text"],
                                  flair_id=config["flairs"]["unsolved"]["id"]):
                db.save_post(submission.id, 'unsolved')
                rh.apply_flair(submission, text=config["flairs"]["unsolved"]["text"],
                               flair_id=config["flairs"]["unsolved"]["id"])