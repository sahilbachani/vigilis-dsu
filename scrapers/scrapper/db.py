# scrapper/db.py
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="vigilis_db",
        user="postgres",
        password="5757",
        port=5432
    )
