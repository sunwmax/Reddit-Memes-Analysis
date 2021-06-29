from scraper import MemeStatsScraper
from database import DatabaseHelper
from config import USER_PARAMS
import threading
import logging
import schedule
import time
import datetime

# logging related info
logging.basicConfig(
    filename = "worklog.log",
    filemode = "w",
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(message)s'
)

# Used for praw debugging
for logger_name in ("praw", "prawcore"):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

class DataCollector:
    
    def __init__(self):
        # Find a way to encrypt/hide info later
        USER_AGENT = USER_PARAMS["reddit"]["USER-AGENT"]
        CLIENT_ID = USER_PARAMS["reddit"]["CLIENT-ID"]
        CLIENT_SECRET = USER_PARAMS["reddit"]["CLIENT-SECRET"]
        HOST_NAME = USER_PARAMS["mysql-db"]["HOST-NAME"]
        USER_NAME = USER_PARAMS["mysql-db"]["USER-NAME"]
        USER_PASSWORD = USER_PARAMS["mysql-db"]["USER-PASSWORD"]
        
        # Scraper and Database Helper configurations
        self.scraper = MemeStatsScraper(USER_AGENT, CLIENT_ID, CLIENT_SECRET)
        self.dbhelper = DatabaseHelper(HOST_NAME, USER_NAME, USER_PASSWORD)
        self.dbhelper.connect_server()
        self.current_hot_ids = []
        self.current_new_ids = []

    # Prepares the database and contained tables for data insertion
    # Note: this function does not cover the case where database exists but the tables doesn't
    def prepare_database(self, database_name: str):
        if not self.dbhelper.database_exists(database_name):
            print("Database with the given name doesn't exist. Creating...")
            self.dbhelper.create_database(database_name, connect = True)
            self.dbhelper.create_tables()
        else:
            print("Found existing database. Connecting...")
            self.dbhelper.connect_database(database_name)
        logging.info(f"Connection to {database_name} has been establised. Data will be stored there.")

    def __add_new_collection_task(self, meme_id: str, time: str):
        schedule.every().hour.at(time).do(self.collect_existing_meme_data, meme_id)

    def __retrieve_valid_newest_id(self):
        for meme_id in self.current_new_ids:
            if not self.scraper.is_removed(meme_id):
                return meme_id
            logging.info(f"{meme_id} is removed. Finding next new meme")
        return

    # Finds new memes from scraper, and updates to database
    def collect_new_meme_data(self):
        logging.info("Collecting new memes...")
        newest_id = self.__retrieve_valid_newest_id()
        new_memes = self.scraper.find_new(before = newest_id)
        self.__log_current_rate_limit()
        if not new_memes:
            logging.info(f"No new memes after {newest_id}")
            return
        
        for meme in new_memes:
            self.dbhelper.insert_meme_info(meme["id"], meme["title"], meme["time_created"],
             False, meme["meme_url"], meme["post_url"])
            self.dbhelper.insert_meme_score(meme["id"], 0, 0)
            self.dbhelper.insert_meme_comments(meme["id"], 0, 0)
            self.dbhelper.insert_meme_status(meme["id"], 0, False)
            self.__add_new_collection_task(meme["id"], meme["time_created"][-5:])
            logging.info(f"{meme['id']} has been added to database")
        
        logging.info(f"{len(new_memes)} new memes added in total")

        self.current_new_ids = [meme["id"] for meme in new_memes]
        logging.info(f"New meme ids: {', '.join(self.current_new_ids)}")

    # Retrieve current hottest "num_meme" meme ids
    def collect_current_hot_meme_ids(self, num_memes: int = 100):
        logging.info("Collecting current hot meme ids...")
        self.current_hot_ids = [meme["id"] for meme in self.scraper.find_hot(num_memes)]
        logging.info("Collected current hot meme ids")
        self.__log_current_rate_limit()

    # Updates a current meme submission
    # Updates score, comments
    # Check if post has entered hot
    def collect_existing_meme_data(self, meme_id: str):
        # Get the most recent entry from meme_status, and retrieve hours and is_hot
        try:
            hours_elapsed, is_hot = self.dbhelper.search_meme_latest_status(meme_id)
        except ValueError:
            logging.error(f"{meme_id} not found in meme_status")
            return
        
        hours_elapsed += 1
        # Returns newest status
        meme = self.scraper.find_specific(meme_id)
        entered_hot = self.__is_hot(meme_id)
        self.dbhelper.insert_meme_score(meme_id, hours_elapsed, meme["score"])
        self.dbhelper.insert_meme_comments(meme_id, hours_elapsed, meme["num_comments"])
        self.dbhelper.insert_meme_status(meme_id, hours_elapsed, entered_hot)
        logging.info(f"{meme_id} is updated")
        self.__log_current_rate_limit()

        # Update if meme has newly entered hot
        if (not is_hot) and (entered_hot):
            self.dbhelper.update_meme_info(meme_id, entered_hot)
            logging.info(f"{meme_id} has entered hot, updated info")
    
    def __is_hot(self, meme_id: str):
        if meme_id in self.current_hot_ids:
            return True
        return False

    def __scheduler(self):
        schedule.every(5).minutes.do(self.collect_new_meme_data)
        schedule.every(5).minutes.do(self.collect_current_hot_meme_ids)

    def __log_current_rate_limit(self):
        rates = self.scraper.reddit.auth.limits
        reset_time = datetime.datetime.fromtimestamp(rates["reset_timestamp"])
        logging.info(f"""Rate Limit: Used: {rates["used"]} Remaining: {rates["remaining"]} Next Reset: {reset_time.strftime("%Y-%m-%d, %H:%M:%S")}""")

    def run(self):
        self.__scheduler()
        schedule.run_all()
        while True:
            schedule.run_pending()
            time.sleep(1)