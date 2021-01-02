"""
r/WhatsTheWord Bot
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

Last modified by Xeoth on 2.1.2021
                 ^--------^ please change when modifying to comply with the license
"""

import logging
from os import getenv
import praw
from praw import models
import yaml
from dotenv import load_dotenv

import helpers

import routines

load_dotenv()

with open('../config.yaml') as file:
    config = yaml.safe_load(file)

REDDIT_CLIENT_ID = getenv('ID')
REDDIT_CLIENT_SECRET = getenv('SECRET')
REDDIT_USERNAME = getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = getenv('PASSWORD')

UNSOLVED_DB = 'unsolved'
ABANDONDED_DB = 'abandoned'
CONTESTED_DB = 'contested'
SOLVED_DB = 'solved'
UNKNOWN_DB = 'unknown'
OVERRIDEN_DB = 'overridden'

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

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
    
    # execute all routines
    while True:
        routines.check_new()
        routines.check_unsolved()
        routines.check_contested()
        routines.check_comments()


# def run():
#
#     subreddit = reddit.subreddit(config["subreddit"])
#
#     # store current subreddit mods not to look them up every time we want to check
#     sub_mods = tuple(moderator.name for moderator in subreddit.moderator())
#
#     while True:
#         # log new submissions to database, apply "unsolved" flair
#         submission_stream: models.ListingGenerator = subreddit.new(
#             limit=10)  # if you're getting more than 10 new submissions in two seconds, you have a problem
#         for submission in submission_stream:
#             if submission is None or submission.author is None:
#                 break
#             elif rh.submitter_is_mod(submission, sub_mods):
#                 db.save_post(submission, 'overridden')
#                 break
#             elif rh.mod_overriden(submission):
#                 break
#             else:
#                 # only update flair if successfully added to database, to avoid out-of-sync issues
#                 if not rh.check_flair(submission=submission, flair_text=config["flairs"]["unsolved"]["text"],
#                                       flair_id=config["flairs"]["unsolved"]["id"]):
#                     db.save_post(submission.id, 'unsolved')
#                     rh.apply_flair(submission, text=config["flairs"]["unsolved"]["text"],
#                                    flair_id=config["flairs"]["unsolved"]["id"])
#
#         # check if any new comments, update submissions accordingly
#         comment_stream = subreddit.comments(limit=50)
#         for comment in comment_stream:
#             if comment is None or comment.author is None or comment.submission.author is None or (
#                     comment.author.name == 'AutoModerator'):
#                 break
#
#             if rh.mod_overriden(comment.submission):
#                 break
#
#             # on new comment by OP
#             if (
#                     comment.author and
#                     comment.submission and
#                     comment.submission.author and
#                     comment.author.name == comment.submission.author.name):
#                 # if OP's comment is "solved", flair submission as "solved"
#                 if not rh.already_solved(comment.submission) and rh.solved_in_comment(comment):
#                     try:
#                         db.save_post(comment.submission.id, SOLVED_DB)
#                         rh.apply_flair(
#                             submission=comment.submission, text=config["flairs"]["solved"]["text"],
#                             flair_id=config["flairs"]["solved"]["id"])
#                     except:
#                         logging.error(
#                             f"Couldn't flair submission {comment.submission.id} as 'solved' following OP's new comment.")
#                 # if OP's comment is not "solved", flair submission as "contested"
#                 elif not rh.already_contested(comment.submission) and not rh.already_solved(comment.submission):
#                     try:
#                         # if update_db_entry(submission_id=comment.submission.id, status=CONTESTED_DB):
#                         db.save_post(comment.submission.id, CONTESTED_DB)
#                         rh.apply_flair(submission=comment.submission, text=config["flairs"]["contested"]["text"],
#                                        flair_id=config["flairs"]["contested"]["id"])
#                     except:
#                         logging.error(
#                             f"Couldn't flair submission {comment.submission.id} as 'contested' following OP's new comment.")
#
#             # otherwise, if new non-OP comment on an "unknown", "contested" or "unsolved" submission,
#             # flair submission as "contested"
#             else:
#                 try:
#                     submission_entry_in_db = db.check_post(
#                         comment.submission.id)
#                     if (
#                             submission_entry_in_db in [UNKNOWN_DB, CONTESTED_DB, UNSOLVED_DB] and
#                             comment.submission.link_flair_template_id not in (
#                             config["flairs"]["solved"]["id"],
#                             config["flairs"]["unsolved"]["id"],
#                             config["flairs"]["contested"]["id"])
#                     ):
#                         try:
#                             db.save_post(comment.submission.id, CONTESTED_DB)
#                             rh.apply_flair(
#                                 comment.submission,
#                                 config["flairs"]["contested"]["text"],
#                                 config["flairs"]["contested"]["id"],
#                             )
#                         except Exception as e:
#                             logging.error(
#                                 f"Couldn't flair submission {comment.submission.id} as 'contested' following a new "
#                                 f"non-OP comment."
#                             )
#                 except Exception as e:
#                     logging.error(
#                         f"Couldn't grab submmision {comment.submission.id} status from database.")
#         # check old "unsolved" submissions and change to "abandoned"
#         old_unsolved_submissions = get_posts_with_old_timestamps(status='u',
#                                                                  second_limit=config["unsolved_to_abandoned"])
#         for entry in old_unsolved_submissions:
#             try:
#                 # get submission object from id
#                 submission = reddit.submission(id=entry[0])
#                 # check comments one last time for potential solve
#
#                 if mod_overriden(submission):
#                     continue
#
#                 # only update flair if successfully updated in database, to avoid out-of-sync issues
#                 if solved_in_comments(submission=submission) or check_flair(submission=submission,
#                                                                             flair_text=config["flairs"]["solved"][
#                                                                                 "text"],
#                                                                             flair_id=config["flairs"]["solved"]["id"]):
#                     if update_db_entry(submission_id=entry[0], status=SOLVED_DB):
#                         apply_flair(
#                             submission=submission, text=config["flairs"]["solved"]["text"],
#                             flair_id=config["flairs"]["solved"]["id"])
#                 else:
#                     if update_db_entry(submission_id=entry[0], status=ABANDONDED_DB):
#                         apply_flair(
#                             submission=submission, text=config["flairs"]["abandoned"]["text"],
#                             flair_id=config["flairs"]["abandoned"]["id"])
#             except Exception as e:
#                 logging.error(f"Couldn't check old submission {entry[0]}. {e}")
#                 # if '404' in e:
#                 #    delete_old_entry(submission_id=entry[0])
#         # check old "contested" submissions and change to "unknown"
#         old_contested_submissions = get_posts_with_old_timestamps(status='c',
#                                                                   second_limit=config["contested_to_unknown"])
#         for entry in old_contested_submissions:
#             try:
#                 # get submission object from id
#                 submission = reddit.submission(id=entry[0])
#                 # check comments one last time for potential solve
#                 if mod_overriden(submission):
#                     break
#
#                 # only update flair if successfully updated in database, to avoid out-of-sync issues
#                 if solved_in_comments(submission=submission) or check_flair(submission=submission,
#                                                                             flair_text=config["flairs"]["solved"][
#                                                                                 "text"],
#                                                                             flair_id=config["flairs"]["solved"]["id"]):
#                     if update_db_entry(submission_id=entry[0], status=SOLVED_DB):
#                         apply_flair(
#                             submission=submission, text=config["flairs"]["solved"]["text"],
#                             flair_id=config["flairs"]["solved"]["id"])
#                 else:
#                     if update_db_entry(submission_id=entry[0], status=UNKNOWN_DB):
#                         apply_flair(
#                             submission=submission, text=config["flairs"]["solved"]["text"],
#                             flair_id=config["flairs"]["solved"]["id"])
#             except Exception as e:
#                 logging.error(f"Couldn't check old submission {entry[0]}. {e}")
#                 # if '404' in e:
#                 #    delete_old_entry(submission_id=entry[0])
#
#
# run()
