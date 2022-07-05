# from collector import DataCollector
from config import REDDIT_PARAMS
from scraper import MemeStatsScraper

# Disabled for now
# if __name__ == "__main__":
#     collector = DataCollector()
#     collector.prepare_database("memes0709")
#     collector.run(collect_new_hours=24, update_hours=24, failsafe=True)


if __name__ == "__main__":
    mss = MemeStatsScraper(
        REDDIT_PARAMS["USER_AGENT"],
        REDDIT_PARAMS["CLIENT_ID"],
        REDDIT_PARAMS["CLIENT_SECRET"],
    )

    posts = mss.find_hot(10)
    print(posts)