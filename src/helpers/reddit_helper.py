"""
Helpers for interacting with Reddit's API

Original work Copyright 2020 Nate Harris
Modified work Copyright 2021 Xeoth

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

Last modified by Xeoth on 23.02.2021
                 ^--------^ please change when modifying to comply with the license
"""

from datetime import datetime, timezone
import logging
from .database_helper import DatabaseHelper
from typing import Tuple, Optional
from praw import models, exceptions, Reddit

logger = logging.getLogger(__name__)


class RedditHelper:
    """Utility class made for working with posts"""

    def __init__(self, db: DatabaseHelper, config, reddit: Reddit):
        self._db = db
        self._config = config
        self._reddit = reddit
    
    def get_posts_with_old_timestamps(self, status=None, second_limit=86400) -> Optional[Tuple[str, ...]]:
        """
        Fetches posts before made before a set amount of seconds and returns them
        
        :param status: If provided, will return posts only with this status
        :param second_limit: How old the posts have to be to get listed
        :return: Tuple with post IDs
        """
        old_timestamp = datetime.now().replace(
            tzinfo=timezone.utc).timestamp() - second_limit
        
        return self._db.get_old_posts(old_timestamp, status)
    
    @staticmethod
    def check_flair(submission: models.Submission, flair_text: str, flair_id=None) -> bool:
        """Checks whether the submission has a specified flair"""
        # if it does not have these attributes, then it does not have a flair
        if not hasattr(submission, 'link_flair_template_id') or not hasattr(submission, 'link_flair_text'):
            return False
    
        try:
            if submission.link_flair_text == flair_text or submission.link_flair_template_id == flair_id:
                return True
            return False
        except exceptions.PRAWException as e:
            logger.error(f"Could not check {submission.id}'s' flair. {e}")
            return False
    
    @staticmethod
    def apply_flair(submission, text="", flair_id=None) -> bool:
        """Applies a specified flair to a submission and returns whether the flair assignment was successful"""
        try:
            submission.mod.flair(text=text, flair_template_id=flair_id)
            return True
        except exceptions.InvalidFlairTemplateID as e:
            logger.error(f"Could not apply {text} flair. {e}")
            return False
    
    @staticmethod
    def solved_in_comment(comment: models.Comment) -> bool:
        """Checks whether 'solved' is in the comment"""
        return "solved" in comment.body.lower()
    
    def solved_in_comments(self, submission: models.Submission) -> bool:
        """Looks for comments containing 'solved' made by OP"""
        # noinspection PyTypeChecker
        submission.comments.replace_more(limit=None)
        # noinspection PyTypeChecker
        for comment in submission.comments.list():
            if not comment or not comment.author or not submission or not submission.author:
                continue
            if comment.author.name == submission.author.name and self.solved_in_comment(comment):
                return True
        return False
    
    def already_solved(self, submission: models.Submission):
        """Checks whether the post is already solved and returns a boolean"""
        return self.check_flair(submission=submission, flair_text=self._config["flairs"]["solved"]["text"],
                                flair_id=self._config["flairs"]["solved"]["id"])

    def already_contested(self, submission: models.Submission):
        """Checks whether the post is already contested and returns a boolean"""
        return self.check_flair(submission=submission, flair_text=self._config["flairs"]["contested"]["text"],
                                flair_id=self._config["flairs"]["contested"]["id"])
    
    def mod_overridden(self, submission: models.Submission) -> bool:
        """Checks whether the submission's flair has been overriden by a mod and returns a boolean"""
        database_status = self._db.check_post(submission.id)
        
        if database_status is None:
            return False
        elif database_status == 'overridden':
            return True

        if submission.link_flair_text is None:
            return False

        # made a typo earlier, leaving the 'overriden' for backwards compatibility
        elif any(i in submission.link_flair_text for i in (':overriden:', ':overridden')):
            self._db.save_post(submission.id, 'overridden')
            return True
        else:
            return False

    def notify_subscribers(self, post_id: str, sub_name: str, title: str, permalink: str):
        """Notifes post's subscribers that the post was solved."""
        message = self._config["constants"]["solved_message"].format(
            f"r/{sub_name}",
            title,
            permalink
        ) + self._config["constants"]["footer"].format(self._reddit.user.me().name)
    
        for subscriber in self._db.get_subscribers(post_id):
            if not subscriber:
                # if no subs, finish
                break
        
            self._reddit.redditor(subscriber).message(
                subject="The post you subscribed to was solved!",
                message=message
            )
    
        self._db.remove_all_subs(post_id)
