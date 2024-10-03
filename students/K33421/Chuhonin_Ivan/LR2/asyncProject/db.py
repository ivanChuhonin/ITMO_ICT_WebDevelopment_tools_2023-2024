import sqlite3


def create_db(dbname:str):
    conn = sqlite3.connect(dbname, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS site_data (title TEXT)")
    cursor.execute("DELETE FROM site_data")
    conn.commit()


def create_rec(data, dbname):
    conn = sqlite3.connect(dbname, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO site_data VALUES (?)", (data,))
    conn.commit()
