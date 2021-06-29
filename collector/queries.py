MEME_INFO_CREATION_QUERY = """
    CREATE TABLE meme_info 
    (
        meme_id VARCHAR(6) NOT NULL,
        title VARCHAR(300) NOT NULL,
        creation_time DATETIME NOT NULL,
        entered_hot BOOLEAN NOT NULL,
        meme_url VARCHAR(300) NOT NULL,
        post_url VARCHAR(300) NOT NULL,
        PRIMARY KEY (meme_id)
    );
    """

MEME_SCORE_CREATION_QUERY = """
    CREATE TABLE meme_score
    (
        meme_id       VARCHAR(6) NOT NULL,
        hours_elapsed INT NOT NULL,
        score         INT NOT NULL,
        PRIMARY KEY (meme_id, hours_elapsed),
        FOREIGN KEY (meme_id) REFERENCES meme_info(meme_id)
    ); 
    """

MEME_COMMENTS_CREATION_QUERY = """
    CREATE TABLE meme_comments 
    (
        meme_id VARCHAR(6) NOT NULL,
        hours_elapsed INT NOT NULL,
        num_comments int NOT NULL,
        PRIMARY KEY (meme_id, hours_elapsed),
        FOREIGN KEY (meme_id) REFERENCES meme_info(meme_id)       
    );
    """

MEME_STATUS_CREATION_QUERY = """
    CREATE TABLE meme_status 
    (
        meme_id VARCHAR(6) NOT NULL,
        hours_elapsed INT NOT NULL,
        is_hot BOOLEAN NOT NULL,
        PRIMARY KEY (meme_id, hours_elapsed),
        FOREIGN KEY (meme_id) REFERENCES meme_info(meme_id)      
    );
    """

SHOW_ALL_DATABASES_QUERY = "SHOW DATABASES;"

SHOW_ALL_TABLES_QUERY = "SHOW TABLES;"

# Helper function for values of types bool, string and int to ideal formats needed in a SQL query
def __process_value_to_sql_format(value):
    if type(value) == str:
        value = value.replace("'", "''")
        return f"'{value}'"
    if type(value) == int:
        return str(value)
    if value:
        return "true"
    if not value:
        return "false"
    return

def database_creation_query(database_name: str):
    return f"CREATE DATABASE {database_name}"

def insert_query(table_name: str, *values):
    values = (__process_value_to_sql_format(value) for value in values) 
    return f"""
    INSERT INTO {table_name}
    VALUES ({", ".join(values)});
    """
# Updating happens only when a meme has entered hot, 
# and only the "entered_hot" value of "meme_info" table has to be changed
def update_meme_info_query(meme_id: str, entered_hot: bool):
    return f"""
    UPDATE meme_info
    SET entered_hot = {entered_hot}
    WHERE meme_id = '{meme_id}';
    """

def search_specific_meme_query(meme_id: str):
    return f"""
    SELECT *
    FROM meme_status
    WHERE meme_id = '{meme_id}' 
    AND hours_elapsed = (SELECT MAX(hours_elapsed) 
						 FROM meme_status
                         WHERE meme_id = '{meme_id}');
    """