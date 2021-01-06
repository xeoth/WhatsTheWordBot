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
#  Last modified by Xeoth on 06.01.2021
#                   ^--------^ please change when modifying to comply with the license

import logging
import praw
from praw import exceptions
import helpers


def check_contested(reddit: praw.Reddit, db: helpers.DatabaseHelper, rh: helpers.RedditHelper, config):
    old_contested_submissions = db.get_old_posts(status='contested', second_limit=config["contested_to_unknown"])

    for submission_id in old_contested_submissions:
        try:
            # get submission object from id
            submission = reddit.submission(submission_id)
            
            # check comments one last time for potential solve
            if rh.mod_overridden(submission_id):
                break
            elif rh.solved_in_comments(submission=submission) or \
                    rh.check_flair(submission=submission,
                                   flair_text=config["flairs"]["solved"]["text"],
                                   flair_id=config["flairs"]["solved"]["id"]):
                db.save_post(submission_id, 'solved')
                rh.apply_flair(
                    submission=submission, text=config["flairs"]["solved"]["text"],
                    flair_id=config["flairs"]["solved"]["id"])
            else:
                db.save_post(submission_id, 'unknown')
                rh.apply_flair(
                    submission=submission, text=config["flairs"]["solved"]["text"],
                    flair_id=config["flairs"]["solved"]["id"])
        except exceptions.PRAWException as e:
            logging.error(f"Couldn't check old submission {submission_id}. {e}")
