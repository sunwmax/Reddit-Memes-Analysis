from types import GeneratorType
from typing import Iterable
import praw
import os
from datetime import datetime, timezone

class MemeStatsScraper:

    def __init__(self, user_agent: str, client_id: str, client_secret: str):
        self.reddit = praw.Reddit(user_agent = user_agent, client_id = client_id, client_secret = client_secret)
        print(f"Reddit instance made in {os.getcwd()}")
        self.newest_id = None

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
    
    def __remove_stickied(self, memes: GeneratorType):
        return (meme for meme in memes if not meme.stickied)

    def find_hot(self, top: int):
        stickied_memes = self.reddit.subreddit("memes").hot(limit = 2)
        stickied_meme_count = sum([True for meme in stickied_memes if meme.stickied])
        memes = self.reddit.subreddit("memes").hot(limit = top + stickied_meme_count)
        memes = self.__remove_stickied(memes)
        results = self.__meme_data_compiler(memes)
        return results

    def find_new(self, before: str = None):
        if before:
            memes = self.reddit.subreddit("memes").new(params = {"before" : f"t3_{before}"})  
        else:
            memes = self.reddit.subreddit("memes").new(limit = 10)
        results = self.__meme_data_compiler(memes)
        return results

    def find_specific(self, meme_id: str):
        meme = self.reddit.submission(meme_id)
        return self.__meme_data_formatter(meme)

    def is_removed(self, meme_id: str):
        meme = self.reddit.submission(meme_id)
        if meme.removed_by_category:
            return True
        return False