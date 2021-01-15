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
#  Last modified by Xeoth on 15.1.2021
#                   ^--------^ please change when modifying to comply with the license

import praw
from praw import models
import helpers
import logging


def check_unsolved(reddit: praw.Reddit, db: helpers.DatabaseHelper, rh: helpers.RedditHelper, config):
    old_unsolved_submissions = db.get_old_posts(status='unsolved',
                                                second_limit=config["unsolved_to_abandoned"])
    
    for entry in old_unsolved_submissions:
        try:
            # get submission object from id
            submission = reddit.submission(id=entry)
            # check comments one last time for potential solve
            
            if rh.mod_overridden(submission):
                continue
            
            # only update flair if successfully updated in database, to avoid out-of-sync issues
            if rh.solved_in_comments(submission=submission) or rh.check_flair(submission=submission,
                                                                              flair_text=config["flairs"]["solved"][
                                                                                  "text"],
                                                                              flair_id=config["flairs"]["solved"][
                                                                                  "id"]):
                if db.save_post(post_id=entry, status='solved'):
                    rh.apply_flair(
                        submission=submission, text=config["flairs"]["solved"]["text"],
                        flair_id=config["flairs"]["solved"]["id"])
            else:
                if db.save_post(post_id=entry, status='abandoned'):
                    rh.apply_flair(
                        submission=submission, text=config["flairs"]["abandoned"]["text"],
                        flair_id=config["flairs"]["abandoned"]["id"])
        except Exception as e:
            logging.error(f"Couldn't check old submission {entry}. {e}")
