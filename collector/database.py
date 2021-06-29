# Retrieve data from scraper.py
# Then use this to store the data into a database (mySQL)

# Existing meme updates happen every hour
# Finding new memes happens every ~5 mins
# Finding hot memes happens every hour 
# (Thinking about memes that entered and left hot between two successive finds)
# Subject to change later according to performance
# Thinking if this can be configured

import mysql.connector
from mysql.connector import Error
import queries

class DatabaseHelper:

    def __init__(self, host_name: str, user_name: str, user_password: str):
        self.hostname = host_name
        self.username = user_name
        self.password = user_password
        self.connection = None
        self.current_database = None
    
    def __create_connection(self, database_name: str = None):
        connection = None
        try:
            connection = mysql.connector.connect(
                host = self.hostname,
                user = self.username,
                passwd = self.password,
                database = database_name
            )
            print("Connection successful")
            self.connection = connection
            self.current_database = database_name
        except Error as e:
            print(f"Error: {e}")

    def connect_server(self):
        self.__create_connection()

    def connect_database(self, database_name: str):
        self.__create_connection(database_name)

    def execute_query(self, query: str, mode: str = "update"):
        assert self.connection, "No connection is established, connect to server/database first"
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
        except Error as e:
            print(f"Error: {e}")
        if mode == "update":
            self.connection.commit()
            return
        if mode == "search":
            return cursor.fetchall()
        if mode == "create":
            return
        
    # Given a database_name, check if a database exists
    def database_exists(self, database_name: str):
        result = self.execute_query(queries.SHOW_ALL_DATABASES_QUERY, mode = "search")
        current_databases = [item[0] for item in result]
        return database_name in current_databases

    def create_database(self, database_name: str, connect: bool = False):
        self.execute_query(queries.database_creation_query(database_name), mode = "create")
        # If user wants to connect immediately
        if connect:
            self.connect_database(database_name)

    def create_tables(self):
        assert self.current_database, "Current database is not specified"
        self.execute_query(queries.MEME_INFO_CREATION_QUERY, mode = "create")
        self.execute_query(queries.MEME_SCORE_CREATION_QUERY, mode = "create")
        self.execute_query(queries.MEME_COMMENTS_CREATION_QUERY, mode = "create")
        self.execute_query(queries.MEME_STATUS_CREATION_QUERY, mode = "create")

    def insert_data(self, table_name: str, *values):
        self.execute_query(queries.insert_query(table_name, *values))

    # Insert in meme_info
    def insert_meme_info(self, meme_id: str, meme_title: str, creation_time: str,
                         entered_hot: bool, meme_url: str, post_url: str):
        self.insert_data("meme_info", meme_id, meme_title, creation_time,
                         entered_hot, meme_url, post_url)

    # Insert in meme_score
    def insert_meme_score(self, meme_id: str, hours_elapsed: int, score: int):
        self.insert_data("meme_score", meme_id, hours_elapsed, score)

    def insert_meme_comments(self, meme_id: str, hours_elapsed: int, num_comments: int):
        self.insert_data("meme_comments", meme_id, hours_elapsed, num_comments)

    def insert_meme_status(self, meme_id: str, hours_elapsed: int, is_hot: int):
        self.insert_data("meme_status", meme_id, hours_elapsed, is_hot)
    
    def update_meme_info(self, meme_id: str, entered_hot: bool):
        self.execute_query(queries.update_meme_info_query(meme_id, entered_hot))

    def search_meme_latest_status(self, meme_id: str):
        try:
            results = self.execute_query(queries.search_specific_meme_query(meme_id), mode = "search")[0]
            return results[1], bool(results[2])
        except IndexError:
            return []