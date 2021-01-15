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

with open('../config.yaml') as file:
    config = yaml.safe_load(file)

REDDIT_CLIENT_ID = getenv('ID')
REDDIT_CLIENT_SECRET = getenv('SECRET')
REDDIT_USERNAME = getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = getenv('PASSWORD')

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

    # # check old "unsolved" submissions and change to "abandoned"
    # old_unsolved_submissions = get_posts_with_old_timestamps(status='u',
    #                                                          second_limit=config["unsolved_to_abandoned"])
#
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
