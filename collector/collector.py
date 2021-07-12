from scraper import MemeStatsScraper
from database import DatabaseHelper
from config import USER_PARAMS
import logging
import schedule
from datetime import datetime, timedelta

# logging related info
logging.basicConfig(
    filename = "worklog.log",
    filemode = "w",
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Used for praw debugging
for logger_name in ("scraper", "praw", "prawcore"):
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
        self.update_current_ids = dict()
        for i in range(60):
            minute_string = f":0{i}" if i < 10 else f":{i}"
            self.update_current_ids[minute_string] = []

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
            self.update_current_ids[meme["time_created"][-6:-3]].append(meme["id"])
            logging.info(f"{meme['id']} has been added to database")
        
        logging.info(f"{len(new_memes)} new memes added in total")

        self.current_new_ids = [meme["id"] for meme in new_memes]
        logging.info(f"New meme ids: {', '.join(self.current_new_ids)}")

    # Retrieve current hottest "num_meme" meme ids
    def collect_current_hot_meme_ids(self, num_memes: int = 100):
        logging.info("Collecting current hot meme ids...")
        current_hot_memes = self.scraper.find_hot(num_memes)
        if current_hot_memes:
            self.current_hot_ids = [meme["id"] for meme in current_hot_memes]
            logging.info("Collected current hot meme ids")
        
        self.__log_current_rate_limit()

    def __is_hot(self, meme_id: str):
        return meme_id in self.current_hot_ids

    # Updates multiple current meme submissions
    # Will replace collect_existing_meme_data
    def collect_existing_memes_data(self, time: str, update_hours: int = 24, failsafe: bool = False):
        meme_ids = self.update_current_ids[time]
        logging.info("Updating existing meme ids...")
        if not meme_ids:
            logging.info("No memes needed to be updated.")
            return

        updated_memes = self.scraper.find_multi_specific(meme_ids)

        # Failsafe for updating existing memes:
        # If memes cannot be updated (mainly due to connection error),
        # These memes will be removed from the update list.
        if failsafe and (updated_memes == None):
            self.update_current_ids[time] = []
            logging.info(f"Memes at {time} cannot be updated. Failsafe activated, these memes will not be updated anymore.")
            return

        for meme in updated_memes:
            hours_elapsed, is_hot = self.dbhelper.search_meme_latest_status(meme["id"])
            hours_elapsed += 1
            entered_hot = self.__is_hot(meme["id"])
            self.dbhelper.insert_meme_score(meme["id"], hours_elapsed, meme["score"])
            self.dbhelper.insert_meme_comments(meme["id"], hours_elapsed, meme["num_comments"])
            self.dbhelper.insert_meme_status(meme["id"], hours_elapsed, entered_hot)
            logging.info(f"{meme['id']} is updated")

            # Update if meme has newly entered hot
            if (not is_hot) and (entered_hot):
                self.dbhelper.update_meme_info(meme["id"], entered_hot)
                logging.info(f"{meme['id']} has entered hot, updated info")

            # Remove meme from self.update_current_ids after "update_hours" elapsed
            if hours_elapsed >= update_hours:
                self.update_current_ids[time].remove(meme["id"])
        
        self.__log_current_rate_limit()

    # Removes update tasks when there is no update needed in a certain minute,
    # After the collector stops collecting new memes
    def __remove_update_tasks(self):
        logging.info("Clearing unused update tasks...")
        if schedule.get_jobs("new"):
            return
        for time in self.update_current_ids.keys():
            if not self.update_current_ids[time]:
                [job] = schedule.get_jobs(time)
                schedule.cancel_job(job)
                logging.info(f"Removed update task at {time}")

    # Schedule new/hot collection tasks
    def __collection_tasks(self, collect_new_hours: int):
        schedule.every(5).minutes.do(self.collect_new_meme_data) \
        .until(timedelta(hours = collect_new_hours)) \
        .tag("new")
        schedule.every(5).minutes.do(self.collect_current_hot_meme_ids) \
        .tag("hot")

    # Schedule update tasks
    def __update_tasks(self, update_hours: int, failsafe: bool = False):
        for time in self.update_current_ids.keys():
            schedule.every().hour.at(time).do(
                self.collect_existing_memes_data, time, update_hours, failsafe
            ) \
            .tag("update", time)
    
    # Schedule update task removal task
    def __remove_tasks(self):
        schedule.every().hour.do(
            self.__remove_update_tasks
        )

    # Used for logging after a request
    def __log_current_rate_limit(self):
        rates = self.scraper.reddit.auth.limits
        if rates['reset_timestamp'] is None:
            logging.warning("Unable to get current rate limits.")
            return
        reset_time = datetime.fromtimestamp(rates['reset_timestamp'])
        logging.info(f"Rate Limit: Used: {rates['used']} Remaining: {rates['remaining']} Next Reset: {reset_time.strftime('%Y-%m-%d, %H:%M:%S')}")

    # Configure and run
    def run(self, collect_new_hours: int, update_hours: int, failsafe: bool = False):
        self.__collection_tasks(collect_new_hours)
        schedule.run_all()
        self.__update_tasks(update_hours, failsafe)
        self.__remove_tasks()

        # Stops when there is nothing to update
        while schedule.get_jobs("update"):
            schedule.run_pending()
        logging.info("Collection finished")