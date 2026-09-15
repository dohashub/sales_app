import mysql.connector
from mysql.connector import Error

# Create a new database connection
def get_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="password",
            database="sales_db"
        )

        if connection.is_connected():
            return connection

    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        raise