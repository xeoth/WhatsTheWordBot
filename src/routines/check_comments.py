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


def check_comments(reddit: praw.Reddit, db: helpers.DatabaseHelper, rh: helpers.RedditHelper, config):
    subreddit = reddit.subreddit(config["subreddit"])

    # check if any new comments, update submissions accordingly
    comment_stream = subreddit.comments(limit=50)
    for comment in comment_stream:
        # checking whether we have all necessary values, as the post could've been deleted + some prerequisites
        try:
            assert comment and comment.author and comment.submission and comment.submission.author
        except AssertionError:
            break
        # much better than a big if!
        
        # we don't want to get in the way of mods
        if comment.author.name == 'AutoModerator':
            break
        elif rh.mod_overridden(comment.submission):
            break

        # on new comments made by OP
        if comment.author.name == comment.submission.author.name:
            # if OP's comment is "solved", flair submission as "solved"
            if not rh.already_solved(comment.submission) and rh.solved_in_comment(comment):
                try:
                    db.save_post(comment.submission.id, 'solved')
                    rh.apply_flair(
                        submission=comment.submission, text=config["flairs"]["solved"]["text"],
                        flair_id=config["flairs"]["solved"]["id"])
                except exceptions.PRAWException:
                    logging.error(
                        f"Couldn't flair submission {comment.submission.id} as 'solved' following OP's new comment.")
            # if OP's comment is not "solved", flair submission as "contested"
            elif not rh.already_contested(comment.submission) and not rh.already_solved(comment.submission):
                db.save_post(comment.submission.id, 'contested')
                rh.apply_flair(submission=comment.submission, text=config["flairs"]["contested"]["text"],
                               flair_id=config["flairs"]["contested"]["id"])

        # otherwise, if new non-OP comment on an "unknown", "contested" or "unsolved" submission,
        # flair submission as "contested"
        else:
            submission_entry_in_db = db.check_post(
                comment.submission.id)
            if (
                    submission_entry_in_db in ['unknown', 'contested', 'unsolved'] and
                    comment.submission.link_flair_template_id not in (
                    config["flairs"]["solved"]["id"],
                    config["flairs"]["unsolved"]["id"],
                    config["flairs"]["contested"]["id"])
            ):
                db.save_post(comment.submission.id, 'contested')
                rh.apply_flair(
                    comment.submission,
                    config["flairs"]["contested"]["text"],
                    config["flairs"]["contested"]["id"],
                )
