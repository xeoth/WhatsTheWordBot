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
#  Last modified by Xeoth on 20.02.2021
#                   ^--------^ please change when modifying to comply with the license

import logging
import praw
from praw import exceptions
from helpers.reddit_helper import RedditHelper
from helpers.database_helper import DatabaseHelper


def check_comments(reddit: praw.Reddit, db: DatabaseHelper, rh: RedditHelper, config):
    logger = logging.getLogger(__name__)
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
                    # marking post as solved and changing the status in the DB
                    db.save_post(comment.submission.id, 'solved')
                    rh.apply_flair(
                        submission=comment.submission, text=config["flairs"]["solved"]["text"],
                        flair_id=config["flairs"]["solved"]["id"])
                    logger.info(f"Marked submission {comment.submission.id} as solved")

                except exceptions.PRAWException:
                    logger.error(
                        f"Couldn't flair submission {comment.submission.id} as 'solved' following OP's new comment.")

                # we don't want to assign points when OP replied to themselves (or their submission)
                if not comment.parent_id.startswith('t3') and \
                        (parent := reddit.comment(comment.parent_id[3:])).author.name != comment.submission.author.name:
                    # adding a point to solver's balance
                    points = db.modify_points(parent.author.name, 1)
    
                    # modifying the flair of the person who solved the query
                    flair_index = 0  # index of the flair template ID on the template array
    
                    # if the user has more points than the highest bound, just apply the highest flair
                    if points >= (flair_bounds := config["user_flairs"]["bounds"])[-1]:
                        flair_index = len(flair_bounds)
    
                    for index, bound in enumerate(flair_bounds):
                        # if user's points are smaller than the bound, then user qualifies for the flair
                        if points < bound:
                            flair_index = index
                            break
    
                    reddit.subreddit(config["subreddit"]).flair.set(
                        redditor=parent.author.name,
                        text=config["user_flairs"]["text"].format(points),
                        flair_template_id=config["user_flairs"][flair_index]
                    )

            # if OP's comment is not "solved", flair submission as "contested"
            elif not rh.already_contested(comment.submission) and not rh.already_solved(comment.submission):
                db.save_post(comment.submission.id, 'contested')
                rh.apply_flair(submission=comment.submission, text=config["flairs"]["contested"]["text"],
                               flair_id=config["flairs"]["contested"]["id"])
                logger.info(f"Marked submission {comment.submission.id} as contested")

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
                logger.info(f"Marked submission {comment.submission.id} as contested.")
