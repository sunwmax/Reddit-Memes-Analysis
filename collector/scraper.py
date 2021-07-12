from types import GeneratorType
from typing import Iterable, Union
import praw
import os
import logging
from datetime import datetime
from prawcore.exceptions import PrawcoreException, NotFound

class MemeStatsScraper:

    def __init__(self, user_agent: str, client_id: str, client_secret: str):
        self.reddit = praw.Reddit(user_agent = user_agent,
                                  client_id = client_id,
                                  client_secret = client_secret)
        print(f"Reddit instance made in {os.getcwd()}")

    # Fix for time offset pending. PRAW returns local time
    def __unix_to_utc_string(self, unix_time: float):
        utc_time = datetime.fromtimestamp(unix_time)
        return utc_time.strftime("%Y-%m-%d %H:%M:%S")

    def __meme_data_formatter(self, meme: GeneratorType):
        return {"id": meme.id,
                "title": meme.title,
                "score": meme.score,
                "num_comments": meme.num_comments,
                "time_created": self.__unix_to_utc_string(meme.created),
                "meme_url": meme.url,
                "post_url": f"reddit.com{meme.permalink}"
        }

    def __meme_data_compiler(self, memes: GeneratorType):
        return [self.__meme_data_formatter(meme) for meme in memes]
    
    def __find_stickied_id(self):
        stickied_id = ""
        try:
            stickied_id = self.reddit.subreddit("memes").sticky(1).id
            stickied_id = self.reddit.subreddit("memes").sticky(2).id
        except NotFound:
            pass
        except PrawcoreException as e:
            logging.warning(f"Error: {e}")
            logging.warning("Request from PRAW failed. Please check your connection.")
            return
        return stickied_id

    def find_hot(self, top: int):
        params = {}
        stickied_id = self.__find_stickied_id()
        if stickied_id:
            params["after"] = f"t3_{stickied_id}"
        try:
            memes = self.reddit.subreddit("memes").hot(limit = top, params = params)
            results = self.__meme_data_compiler(memes)
            return results
        except PrawcoreException as e:
            logging.warning(f"Error: {e}")
            logging.warning("Request from PRAW failed. Please check your connection.")
            return

    def find_new(self, before: str = None):
        if before:
            memes = self.reddit.subreddit("memes").new(params = {"before" : f"t3_{before}"})  
        else:
            memes = self.reddit.subreddit("memes").new(limit = 10)
        try:
            results = self.__meme_data_compiler(memes)
            return results
        except PrawcoreException as e:
            logging.warning(f"Error: {e}")
            logging.warning("Request from PRAW failed. Please check your connection.")
            return

    def find_multi_specific(self, meme_ids: Union[str, Iterable[str]]):
        memes = self.reddit.info([f"t3_{meme_id}" for meme_id in meme_ids])
        try:
            results = self.__meme_data_compiler(memes)
            return results
        except PrawcoreException as e:
            logging.warning(f"Error: {e}")
            logging.warning("Request from PRAW failed. Please check your connection.")
            return

    def is_removed(self, meme_id: str):
        meme = self.reddit.submission(meme_id)
        try:
            return meme.removed_by_category
        except PrawcoreException as e:
            logging.warning(f"Error: {e}")
            logging.warning("Request from PRAW failed. Please check your connection.")
            return