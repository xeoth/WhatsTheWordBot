"""
Helpers for interacting with Reddit's API

Original work Copyright 2020 Xeoth

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

Last modified by Xeoth on 24.12.2020
                 ^--------^ please change when modifying to comply with the license
"""

class RedditHelper:
    def get_posts_with_old_timestamps(status, second_limit=86400):
        old_timestamp = datetime.now().replace(
            tzinfo=timezone.utc).timestamp() - second_limit
        
        return db.get_old_posts(old_timestamp, status)
    
    def check_flair(submission, flair_text, flair_id=None):
        try:
            if submission.link_flair_text == flair_text or submission.link_flair_template_id == flair_id:
                return True
            return False
        except Exception as e:
            logging.error(f"Could not check {submission.id}'s' flair. {e}")
            return False
    
    def apply_flair(submission, text="", flair_id=None):
        try:
            submission.mod.flair(text=text, flair_template_id=flair_id)
            logging.info(f"Marked submission {submission.id} as '{text}'")
            return True
        except Exception as e:
            logging.error(f"Could not apply {text} flair. {e}")
            return False
    
    def solved_in_comment(comment) -> bool:
        return "solved" in comment.body.lower()
    
    def solved_in_comments(submission) -> bool:
        """Looks for comments containing 'solved' made by OP"""
        submission.comments.replace_more(limit=None)
        for comment in submission.comments.list():
            if comment.author.name == submission.author.name and solved_in_comment(comment):
                return True
        return False
    
    def already_solved(submission):
        return check_flair(submission=submission, flair_text=config["flairs"]["solved"]["text"],
                           flair_id=config["flairs"]["solved"]["id"])
    
    def already_contested(submission):
        return check_flair(submission=submission, flair_text=config["flairs"]["contested"]["text"],
                           flair_id=config["flairs"]["contested"]["id"])
    
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
        except Exception:
            # most likely issue is not unique (submission is already logged in databaase); this is fine and intended
            # logging.error(f"Couldn't store submission in database. {e}")
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
        database_status = db.check_post(submission.id)
        
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
