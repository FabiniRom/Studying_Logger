import sqlite3
import pytz
from datetime import datetime


def setup_database():
    conn = sqlite3.connect('window_log.db')
    cursor = conn.cursor()

    # Create table if it doesn't exist
    # Adjusting the timestamp column to store it as TEXT
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS window_changes (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        time_length TEXT,
        window_title TEXT
    )
    ''')

    conn.commit()
    conn.close()

