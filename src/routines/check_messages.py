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
#  Last modified by Xeoth on 22.02.2021
#                   ^--------^ please change when modifying to comply with the license

import praw
from prawcore import exceptions
from helpers.reddit_helper import RedditHelper
from helpers.database_helper import DatabaseHelper
import logging
import re

logger = logging.getLogger(__name__)
id_regex = re.compile(r"^[a-z0-9]{6}$")


def check_messages(reddit: praw.Reddit, db: DatabaseHelper, rh: RedditHelper, config):
    # processing each message and adding subscriptions
    for message in reddit.inbox.messages(limit=25):
        # we only have one DM action
        if message.subject != "subscribe":
            continue
        # checking whether the ID makes sense
        elif not id_regex.match(message.body.strip()):
            continue
        elif db.check_subscription(message.body, message.author.name):
            # user already subscribed
            continue
        
        author = message.author.name
        
        # catching 404 errors in case the post doesn't exist
        submission = reddit.submission(id=message.body)
        try:
            if submission.subreddit.display_name != config["subreddit"]:
                # wrong subreddit, continue
                continue
            elif rh.already_solved(submission):
                continue
        except exceptions.NotFound:
            # post doesn't exist, continue
            continue
        
        db.add_subscriber(submission.id, author)
        logger.info(f"{author} subscribed to {submission.id}.")
