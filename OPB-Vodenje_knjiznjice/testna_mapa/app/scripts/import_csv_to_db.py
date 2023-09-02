import sqlite3
import csv
import os

# Get the current script's directory
script_dir = os.path.dirname(__file__)

# Construct the full path to the CSV file
csv_file = os.path.join(script_dir, '..', 'books_data.csv')  # Assumes the CSV file is in the root directory

# Connect to your SQLite database
conn = sqlite3.connect('app/database.db')
cursor = conn.cursor()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        name TEXT,
        surname TEXT,
        is_admin INTEGER DEFAULT 0,
        gender TEXT DEFAULT NULL,
        age INTEGER DEFAULT NULL
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id_book INTEGER PRIMARY KEY,
        title TEXT,
        author_first_name TEXT,
        author_last_name TEXT,
        genre TEXT,
        status TEXT,
        rating FLOAT DEFAULT 0.0,  -- Initial rating is 0.0
        num_ratings INTEGER DEFAULT 0,  -- Initial number of ratings is 0
        id INTEGER DEFAULT 0 
    );
''')


# Read the CSV file and insert data into the database
with open(csv_file, 'r', newline='', encoding='ISO-8859-1') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        cursor.execute('''
            INSERT INTO books (id,title, author_first_name, author_last_name, genre, status, rating, num_ratings, id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row['id'], row['title'], row['author_first_name'], row['author_last_name'], row['genre'], 'free', 0.0, 0,0))

# Commit changes and close the database connection
conn.commit()
conn.close()