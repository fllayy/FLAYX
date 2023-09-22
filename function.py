from dotenv import load_dotenv
import os
import mysql.connector
import time


def convertMs(milliseconds):
    seconds = milliseconds // 1000
    minutes, remaining_seconds = divmod(seconds, 60)
    hours, remaining_minutes = divmod(minutes, 60)

    time_string = ""

    if hours > 0:
        time_string += f"{hours:02d}:"

    time_string += f"{remaining_minutes:02d}:{remaining_seconds:02d}"

    return time_string


#-------------- API Clients --------------
load_dotenv()
TOKEN = os.getenv("TOKEN")
LAVALINK_HOST = os.getenv("LAVALINK_HOST")
LAVALINK_PORT = os.getenv("LAVALINK_PORT")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_USER = os.getenv("MYSQL_USERNAME")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")


#--------------- Database ---------------
class DBClass():

    def __init__(self):
        try:
            self.db_connection = mysql.connector.connect(
                host = MYSQL_HOST,
                user = MYSQL_USER,
                password = MYSQL_PASSWORD,
                database = MYSQL_DATABASE
			)
            
            print("Successfully connected to MySQL!")

        except mysql.connector.Error as e:
            print(f"Error connecting to MySQL: {e}")


    def check(self):
        try:
            self.db_connection.ping(reconnect=True, attempts=3, delay=5)
        except mysql.connector.Error as e:
            print("Database ping failed:", e)


    def ping_mysql(self):
        self.check()
        try:
            start_time = time.time()
            conn = mysql.connector.connect(
                host = MYSQL_HOST,
                user = MYSQL_USER,
                password = MYSQL_PASSWORD,
                database = MYSQL_DATABASE
            )
            end_time = time.time()
            ping_time = (end_time - start_time) * 100
            conn.close()
            return ping_time
        except Exception as e:
            return f"Erreur : {e}"


    def create_tables(self):
        self.check()
        create_server_table_query = """
        CREATE TABLE IF NOT EXISTS settings (
                id BIGINT PRIMARY KEY,
                prefix VARCHAR(5),
                volume TINYINT,
                time INT
        )
        """

        cursor = self.db_connection.cursor()
        cursor.execute(create_server_table_query)
        cursor.close()
        self.db_connection.commit()

        print('Created tables Successfully!')


    def find_one(self, table_name, id, row):
        self.check()
        cursor = self.db_connection.cursor()
        select_query = f"SELECT {row} FROM {table_name} WHERE id = %s"
        cursor.execute(select_query, (id, ))
        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            return result[0]
        else:
            return None
        

    def set_settings(self, id):
        self.check()
        cursor = self.db_connection.cursor()
        insert_query = "INSERT INTO settings (id, prefix, volume, time) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, (id, '+', 100, 0))
        cursor.close()
        self.db_connection.commit()


    def update_one(self, table_name, row, data, id):
        self.check()
        cursor = self.db_connection.cursor()
        select_query = f"UPDATE {table_name} SET {row} = %s WHERE id = %s"
        cursor.execute(select_query, (data, id))
        cursor.close()
        self.db_connection.commit()
                  


try:
    db = DBClass()
    db.create_tables()
except Exception as e:
    raise Exception("Not able to connect MYSQL! Reason:", e)
