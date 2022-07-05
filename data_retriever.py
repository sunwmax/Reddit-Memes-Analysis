import mysql.connector
from mysql.connector import Error
import csv

def create_connection(hostname: str, username: str, 
                      password: str, database_name: str = None):
    connection = None
    try:
        connection = mysql.connector.connect(
            host = hostname,
            user = username,
            passwd = password,
            database = database_name
        )
        print("Connection successful")
        return connection
    except Error as e:
        print(f"Error: {e}")

def fetch_results(query: str):
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        return f"Error: {e}"

def fetch_tables():
    tables = [result[0] for result in fetch_results("SHOW TABLES;")]
    return tables

def fetch_column_names(table_name: str):
    columns = [result[0] for result in fetch_results(f"DESCRIBE {table_name};")]
    return columns

def fetch_table_data(table_name: str):
    data = fetch_results(f"SELECT * FROM {table_name};")
    return data

def table_to_csv(table_name: str):
    with open(f'{table_name}.csv', 'w', newline = '', encoding = 'utf-8') as csvfile:
        column_names = fetch_column_names(table_name)
        table_data = fetch_table_data(table_name)      
        writer = csv.writer(csvfile)
        writer.writerow(column_names)
        writer.writerows(table_data)

def export_data_from_db():
    tables = fetch_tables()
    for table in tables:
        table_to_csv(table)

if __name__ == "__main__":
    conn = create_connection(
        hostname="localhost",
        username="Max",
        password="ilovearia24",
        database_name="memes0709"
    )
    export_data_from_db()