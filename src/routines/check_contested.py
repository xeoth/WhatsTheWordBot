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
#  Last modified by Xeoth on 21.01.2021
#                   ^--------^ please change when modifying to comply with the license

import logging
import praw
from praw import exceptions
from helpers.reddit_helper import RedditHelper
from helpers.database_helper import DatabaseHelper


def check_contested(reddit: praw.Reddit, db: DatabaseHelper, rh: RedditHelper, config):
    logger = logging.getLogger(__name__)
    old_contested_submissions = db.get_old_posts(status='contested', second_limit=config["contested_to_unknown"])

    if old_contested_submissions is None:
        return

    for submission_id in old_contested_submissions:
        try:
            # get submission object from id
            submission = reddit.submission(submission_id)
        
            # check comments one last time for potential solve
            if rh.mod_overridden(submission):
                break
            elif rh.solved_in_comments(submission=submission) or \
                    rh.check_flair(submission=submission,
                                   flair_text=config["flairs"]["solved"]["text"],
                                   flair_id=config["flairs"]["solved"]["id"]):
                db.save_post(submission_id, 'solved')
                rh.apply_flair(
                    submission=submission, text=config["flairs"]["solved"]["text"],
                    flair_id=config["flairs"]["solved"]["id"])
                logger.info(f"Marked submission {submission.id} as solved")

            else:
                db.save_post(submission_id, 'unknown')
                rh.apply_flair(
                    submission=submission, text=config["flairs"]["solved"]["text"],
                    flair_id=config["flairs"]["solved"]["id"])
                logger.info(f"Marked submission {submission.id} as solved")

        except exceptions.PRAWException as e:
            logger.error(f"Couldn't check old submission {submission_id}. {e}")
