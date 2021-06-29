from types import GeneratorType
from typing import Iterable, Union
import praw
import os
from datetime import datetime, timezone
from prawcore.exceptions import NotFound

class MemeStatsScraper:

    def __init__(self, user_agent: str, client_id: str, client_secret: str):
        self.reddit = praw.Reddit(user_agent = user_agent, client_id = client_id, client_secret = client_secret)
        print(f"Reddit instance made in {os.getcwd()}")

    # See if there's a fix for time offset, praw returns local time
    def __unix_to_utc_string(self, unix_time: float):
        utc_time = datetime.fromtimestamp(unix_time, tz = timezone.utc)
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
        return stickied_id

    def find_hot(self, top: int):
        params = {}
        stickied_id = self.__find_stickied_id()
        if stickied_id:
            params["after"] = f"t3_{stickied_id}"
        memes = self.reddit.subreddit("memes").hot(limit = top, params = params)
        results = self.__meme_data_compiler(memes)
        return results

    def find_new(self, before: str = None):
        if before:
            memes = self.reddit.subreddit("memes").new(params = {"before" : f"t3_{before}"})  
        else:
            memes = self.reddit.subreddit("memes").new(limit = 10)
        results = self.__meme_data_compiler(memes)
        return results

    # This will be deprecated
    def find_specific(self, meme_id: str):
        meme = self.reddit.submission(meme_id)
        return self.__meme_data_formatter(meme)

    def find_multi_specific(self, meme_ids: Union[str, Iterable[str]]):
        memes = self.reddit.info([f"t3_{meme_id}" for meme_id in meme_ids])
        results = self.__meme_data_compiler(memes)
        return results

    def is_removed(self, meme_id: str):
        meme = self.reddit.submission(meme_id)
        if meme.removed_by_category:
            return True
        return False