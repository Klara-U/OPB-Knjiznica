import csv
import os

# Get the current script's directory
script_dir = os.path.dirname(__file__)

# Construct the full path to the CSV file
csv_file = os.path.join(script_dir, '..', 'books_data.csv')  # Assumes the CSV file is in the root directory

import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki
conn = psycopg2.connect(database='opb2023_klarau', host='baza.fmf.uni-lj.si', user='', password='')
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogocimo transakcije
cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        name TEXT,
        surname TEXT,
        is_admin INTEGER DEFAULT 0,
        gender TEXT,
        age INTEGER
    );
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id_book SERIAL PRIMARY KEY,
        title TEXT,
        author_first_name TEXT,
        author_last_name TEXT,
        genre TEXT,
        status TEXT,
        rating FLOAT DEFAULT 0.0,
        num_ratings INTEGER DEFAULT 0,
        user_id INTEGER REFERENCES users(id)
    );
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_ratings (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        book_id INTEGER REFERENCES books(id_book),
        rating INTEGER
    );
''')
conn.commit()
conn.close()
1/0
# Read the CSV file and insert data into the database
with open(csv_file, 'r', newline='', encoding='ISO-8859-1') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        cursor.execute('''
            INSERT INTO books (id_book,title, author_first_name, author_last_name, genre, status, rating, num_ratings, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (row['id'], row['title'], row['author_first_name'], row['author_last_name'], row['genre'], 'free', 0.0, 0,None))

# Commit changes and close the database connection
conn.commit()
conn.close()
