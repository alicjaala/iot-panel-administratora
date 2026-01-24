import sqlite3
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import raspberries.constants as const


def create_database():
    if os.path.exists(const.DB_NAME):
        os.remove(const.DB_NAME)
        print("An old database removed.")

    try:
        connection = sqlite3.connect(const.DB_NAME)
        cursor = connection.cursor()

        cursor.execute("""
        CREATE TABLE lockers (
            nr INTEGER PRIMARY KEY,
            uid TEXT DEFAULT NULL
        );
        """)

        for i in range(1, const.NUM_OF_LOCKERS + 1):
            cursor.execute("INSERT INTO lockers (nr) VALUES(?)", (i,))

        cursor.execute("""
        CREATE TABLE entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT NOT NULL,
            locker_nr INTEGER DEFAULT NULL,
            entry_tmsp TEXT DEFAULT NULL,
            exit_tmsp TEXT DEFAULT NULL
        );
        """)

        connection.commit()
        connection.close()
        print("The new database created.")

    except sqlite3.Error as e:
        print("Failed to create a database.")


if __name__ == "__main__":
    create_database()
