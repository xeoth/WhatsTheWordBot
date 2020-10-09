#!/usr/bin/python3

from os import getenv
import praw
import praw.models
import logging
import sql_library as sql
from datetime import datetime, timezone
from typing import Tuple
from dotenv import load_dotenv
load_dotenv()


REDDIT_CLIENT_ID = getenv('ID')
REDDIT_CLIENT_SECRET = getenv('SECRET')
REDDIT_USERNAME = getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = getenv('PASSWORD')
SUB_TO_MONITOR = getenv('SUBREDDIT')

SECONDS_UNTIL_ABANDONED_FROM_UNSOLVED = 86400  # 86400 = 24 hours in seconds
SECONDS_UNTIL_UNKNOWN_FROM_CONTESTED = 172800  # 172800 = 48 hours in seconds

UNSOLVED_FLAIR_TEXT = getenv('UNSOLVED_FLAIR_TEXT')
UNSOLVED_FLAIR_ID = getenv('UNSOLVED_FLAIR_ID')
UNSOLVED_DB = getenv('UNSOLVED_DB')
ABANDONDED_FLAIR_TEXT = getenv('ABANDONED_FLAIR_TEXT')
ABANDONDED_FLAIR_ID = getenv('ABANDONED_FLAIR_ID')
ABANDONDED_DB = getenv('ABANDONED_DB')
CONTESTED_FLAIR_TEXT = getenv('CONTESTED_FLAIR_TEXT')
CONTESTED_FLAIR_ID = getenv('CONTESTED_FLAIR_ID')
CONTESTED_DB = getenv('CONTESTED_DB')
SOLVED_FLAIR_TEXT = getenv('SOLVED_FLAIR_TEXT')
SOLVED_FLAIR_ID = getenv('SOLVED_FLAIR_ID')
SOLVED_DB = getenv('SOLVED_DB')
UNKNOWN_FLAIR_TEXT = getenv('UNKNOWN_FLAIR_TEXT')
UNKNOWN_FLAIR_ID = getenv('UNKNOWN_FLAIR_ID')
UNKNOWN_DB = getenv('UNKNOWN_DB')
OVERRIDEN_DB = getenv('OVERRIDEN_DB')

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

db = sql.SQL(sql_type='SQLite', sqlite_file='whats_the_word.db')

reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET,
                     user_agent='WhatsTheWordBot (by u/grtgbln)', username=REDDIT_USERNAME, password=REDDIT_PASSWORD)

if not reddit.read_only:
    logging.info("Connected and running.")


def get_posts_with_old_timestamps(status, second_limit=86400):
    old_timestamp = datetime.now().replace(
        tzinfo=timezone.utc).timestamp() - second_limit
    # print(old_timestamp)
    results = db.custom_query(
        queries=[f"SELECT id, status FROM posts WHERE last_checked <= {int(old_timestamp)} AND status == '{status}'"])
    # print(results)
    if results and len(results) > 0:
        return results
    return []


def check_status_in_db(submission_id):
    results = db.custom_query(
        queries=[f"SELECT id, status FROM posts WHERE id == '{submission_id}'"])
    if results and len(results) > 0:
        return results
    else:
        return None


def check_flair(submission, flair_text, flair_id=None):
    try:
        if submission.link_flair_text == flair_text or submission.link_flair_template_id == flair_id:
            return True
        return False
    except Exception as e:
        # logging.error(f"Could not check submission {submission.id} flair. {e}")
        return False


def apply_flair(submission, text="", flair_id=None):
    try:
        submission.mod.flair(text=text, flair_template_id=flair_id)
        logging.info(f"Marked submission {submission.id} as '{text}'")
        return True
    except Exception as e:
        logging.error(f"Could not apply {text} flair. {e}")
        return False


def solved_in_comment(comment):
    if "solved" in comment.body.lower():
        return True
    return False


def solved_in_comments(submission):
    # look for "solved" comment by OP
    submission.comments.replace_more(limit=None)
    for comment in submission.comments.list():
        if comment.author.name == submission.author.name and solved_in_comment(comment):
            return True
    return False


def already_solved(submission):
    return check_flair(submission=submission, flair_text=SOLVED_FLAIR_TEXT, flair_id=SOLVED_FLAIR_ID)


def already_contested(submission):
    return check_flair(submission=submission, flair_text=CONTESTED_FLAIR_TEXT, flair_id=CONTESTED_FLAIR_ID)


def store_entry_in_db(submission, status=UNSOLVED_DB):
    timestamp = datetime.now().replace(tzinfo=timezone.utc).timestamp()
    try:
        results = db.custom_query(
            queries=[
                f"INSERT INTO posts (id, status, last_checked) VALUES ('{str(submission.id)}', '{status}', {int(timestamp)})"],
            commit=True)
        if results and results > 0:
            logging.info(f"Added submission {submission.id} to database.")
            return True
        return False
    except Exception as e:
        # most likely issue is not unique (submission is already logged in databaase); this is fine and intended
        logging.error(f"Couldn't store submission in database. {e}")
        return False


def update_db_entry(submission_id, status):
    try:
        time_now = datetime.now().replace(tzinfo=timezone.utc).timestamp()
        results = db.custom_query(
            queries=[
                f"UPDATE posts SET status = '{status}', last_checked = {int(time_now)} WHERE id = '{submission_id}'"],
            commit=True)
        if results and results > 0:
            logging.info(
                f"Updated submission {submission_id} to '{status}' in database.")
            return True
        return False
    except Exception as e:
        logging.error(
            f"Couldn't update submission {submission_id} in database. {e}")
        return False


def mod_overriden(submission: praw.models.Submission) -> bool:
    """Checks whether the submission's flair has been overriden by a mod"""
    database_status = check_status_in_db(submission.id)

    if database_status is None:
        return False

    if submission.link_flair_text is None:
        return False

    if database_status[0][1] == 'o':
        return True
    elif ':overriden:' in submission.link_flair_text:
        store_entry_in_db(submission, 'o')
        return True
    else:
        return False


def submitter_is_mod(submission: praw.models.Submission, mods: Tuple[praw.models.Redditor]) -> bool:
    """Checks whether the author of submission is a sub moderator"""
    if submission is None:
        return False

    if submission.author in mods:
        return True
    else:
        return False


def delete_old_entry(submission_id):
    try:
        results = db.custom_query(
            queries=[
                f"DELETE FROM posts WHERE id = '{submission_id}'"],
            commit=True)
        if results and results > 0:
            logging.info(f"Deleted submission {submission_id} from database.")
            return True
        return False
    except Exception as e:
        logging.error(
            f"Couldn't delete submission {submission_id} in database. {e}")
        return False


def clean_db():
    results = db.custom_query(queries=['DELETE FROM posts'], commit=True)
    if results >= 0:
        logging.info('Database cleared.')
        return True
    logging.error('Database could not be cleared.')
    return False


def run():
    """
    New submission: automatically flaired "unsolved"
    If "solved" comment from OP -> "solved"
    If non-"solved" comment from OP -> "contested"
    If new comment from non-OP -> "unsolved"/"contested"/"unknown" -> "contested" (ignore "abandoned")
    After 24 hours, "unsolved" -> "abandoned" (check if solved first) (unsolved means no new comments; otherwise would be "contested")
    After 48 hours, "contested" -> "unknown" (check if solved first) (contested means someone has commented)
    """
    # clean_db()
    subreddit = reddit.subreddit(SUB_TO_MONITOR)

    # cache current subreddit mods not to look them up every time we want to check
    sub_mods = tuple(moderator.name for moderator in subreddit.moderator())

    while True:
        # log new submissions to database, apply "unsolved" flair
        submission_stream = subreddit.new(
            limit=10)  # if you're getting more than 10 new submissions in two seconds, you have a problem
        for submission in submission_stream:
            if submission is None or submission.author is None:
                break
            # elif submitter_is_mod(submission, sub_mods):
                # store_entry_in_db(submission, 'o')
                # break
            elif mod_overriden(submission):
                break
            else:
                # only update flair if successfully added to database, to avoid out-of-sync issues
                if not check_flair(submission=submission, flair_text=UNSOLVED_FLAIR_TEXT, flair_id=UNSOLVED_FLAIR_ID) and store_entry_in_db(submission=submission):
                    apply_flair(submission, text=UNSOLVED_FLAIR_TEXT,
                                flair_id=UNSOLVED_FLAIR_ID)
                    print(submission.title)

        # check if any new comments, update submissions accordingly
        comment_stream = subreddit.comments(limit=50)
        for comment in comment_stream:
            if comment is None or comment.author is None or comment.submission.author is None or (comment.author.name == 'AutoModerator'):
                print('comment is none')
                break

            if mod_overriden(comment.submission):
                print('mo passed')
                break

            # if new comment by OP
            if comment.author and comment.submission and comment.submission.author and comment.author.name == comment.submission.author.name:
                print('ca exists')
                # if OP's comment is "solved", flair submission as "solved"
                if not already_solved(comment.submission) and solved_in_comment(comment):
                    print(comment.body)

                    try:
                        # only update flair if successfully updated in database, to avoid out-of-sync issues
                        if update_db_entry(submission_id=comment.submission.id, status=SOLVED_DB):
                            apply_flair(
                                submission=comment.submission, text=SOLVED_FLAIR_TEXT, flair_id=SOLVED_FLAIR_ID)
                    except Exception as e:
                        logging.error(
                            f"Couldn't flair submission {comment.submission.id} as 'solved' following OP's new comment.")
                # if OP's comment is not "solved", flair submission as "contested"
                elif not already_contested(comment.submission) and not already_solved(comment.submission):
                    try:
                        # only update flair if successfully updated in database, to avoid out-of-sync issues
                        if update_db_entry(submission_id=comment.submission.id, status=CONTESTED_DB):
                            apply_flair(submission=comment.submission, text=CONTESTED_FLAIR_TEXT,
                                        flair_id=CONTESTED_FLAIR_ID)
                    except Exception as e:
                        logging.error(
                            f"Couldn't flair submission {comment.submission.id} as 'contested' following OP's new comment.")

            # otherwise, if new non-OP comment on an "unknown", "contested" or "unsolved" submission, flair submission as "contested"
            else:
                try:
                    submission_entry_in_db = check_status_in_db(
                        submission_id=comment.submission.id)
                    if submission_entry_in_db and submission_entry_in_db[0][1] in [UNKNOWN_DB, CONTESTED_DB, UNSOLVED_DB]\
                            and not (
                                check_flair(submission=comment.submission, flair_text=UNKNOWN_FLAIR_TEXT, flair_id=UNKNOWN_FLAIR_ID) or
                                check_flair(submission=comment.submission, flair_text=UNSOLVED_FLAIR_TEXT, flair_id=UNSOLVED_FLAIR_ID) or
                                check_flair(
                                    submission=comment.submission, flair_text=CONTESTED_FLAIR_TEXT, flair_id=CONTESTED_FLAIR_ID)
                    ):
                        try:
                            # only update flair if successfully updated in database, to avoid out-of-sync issues
                            if update_db_entry(submission_id=comment.submission.id, status=CONTESTED_DB):
                                apply_flair(submission=comment.submission, text=CONTESTED_FLAIR_TEXT,
                                            flair_id=CONTESTED_FLAIR_ID)
                        except Exception as e:
                            logging.error(
                                f"Couldn't flair submission {comment.submission.id} as 'contested' following a new non-OP comment.")
                except Exception as e:
                    logging.error(
                        f"Couldn't grab submmision {comment.submission.id} status from database.")
        # check old "unsolved" submissions and change to "abandoned"
        old_unsolved_submissions = get_posts_with_old_timestamps(status='u',
                                                                 second_limit=SECONDS_UNTIL_ABANDONED_FROM_UNSOLVED)
        for entry in old_unsolved_submissions:
            try:
                # get submission object from id
                submission = reddit.submission(id=entry[0])
                # check comments one last time for potential solve

                if mod_overriden(submission):
                    continue

                # only update flair if successfully updated in database, to avoid out-of-sync issues
                if solved_in_comments(submission=submission) or check_flair(submission=submission,
                                                                            flair_text=SOLVED_FLAIR_TEXT,
                                                                            flair_id=SOLVED_FLAIR_ID):
                    if update_db_entry(submission_id=entry[0], status=SOLVED_DB):
                        apply_flair(
                            submission=submission, text=SOLVED_FLAIR_TEXT, flair_id=SOLVED_FLAIR_ID)
                else:
                    if update_db_entry(submission_id=entry[0], status=ABANDONDED_DB):
                        apply_flair(
                            submission=submission, text=ABANDONDED_FLAIR_TEXT, flair_id=ABANDONDED_FLAIR_ID)
            except Exception as e:
                logging.error(f"Couldn't check old submission {entry[0]}. {e}")
                # if '404' in e:
                #    delete_old_entry(submission_id=entry[0])
        # check old "contested" submissions and change to "unknown"
        old_contested_submissions = get_posts_with_old_timestamps(status='c',
                                                                  second_limit=SECONDS_UNTIL_UNKNOWN_FROM_CONTESTED)
        for entry in old_contested_submissions:
            try:
                # get submission object from id
                submission = reddit.submission(id=entry[0])
                # check comments one last time for potential solve
                if mod_overriden(submission):
                    break

                # only update flair if successfully updated in database, to avoid out-of-sync issues
                if solved_in_comments(submission=submission) or check_flair(submission=submission,
                                                                            flair_text=SOLVED_FLAIR_TEXT,
                                                                            flair_id=SOLVED_FLAIR_ID):
                    if update_db_entry(submission_id=entry[0], status=SOLVED_DB):
                        apply_flair(
                            submission=submission, text=SOLVED_FLAIR_TEXT, flair_id=SOLVED_FLAIR_ID)
                else:
                    if update_db_entry(submission_id=entry[0], status=UNKNOWN_DB):
                        apply_flair(
                            submission=submission, text=UNKNOWN_FLAIR_TEXT, flair_id=UNKNOWN_FLAIR_ID)
            except Exception as e:
                logging.error(f"Couldn't check old submission {entry[0]}. {e}")
                # if '404' in e:
                #    delete_old_entry(submission_id=entry[0])


run()
