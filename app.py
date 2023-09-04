from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2, psycopg2.extensions, psycopg2.extras

app = Flask(__name__)
app.secret_key = 'secret_key'

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki
conn = psycopg2.connect(database='opb2023_klarau', host='baza.fmf.uni-lj.si', user='klarau', password='4hoayx6s')
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogocimo transakcije

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Initialize the database
def initialize_database():
    cursor = conn.cursor()
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

initialize_database()


@app.route('/')
def index():
    cursor = conn.cursor()
    cursor.execute('SELECT b.title, b.num_ratings, b.rating  FROM books b ORDER BY rating DESC LIMIT 5')
    top_rated = cursor.fetchall()
    cursor.execute('SELECT b.title, b.num_ratings, b.rating FROM books b ORDER BY num_ratings DESC LIMIT 5')
    most_reviewed = cursor.fetchall()
    return render_template('index.html', top_rated=top_rated, most_reviewed=most_reviewed)

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if 'user' in session:
        flash('Already logged in. Redirecting...')
        return redirect(url_for('profile')) #if this part is blocked you always have to sign in even if you do not logout
    if request.method == 'POST':
        if request.form['admin_password'] == 'posebensem':
            username = request.form['username']
            password = request.form['password']
            repeat_password = request.form['repeat_password']
            name = request.form['name']
            surname = request.form['surname']
            is_admin = 1
            # Check if passwords match
            if password == repeat_password:
                hashed_password = generate_password_hash(password, method='sha256')

                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password, name, surname, is_admin) VALUES (%s, %s, %s, %s, %s)',
                            (username, hashed_password, name, surname, is_admin))
                conn.commit()
                ()
                return redirect(url_for('login'))
            else:
                return "Passwords do not match."
        else:
            return "Admin registration code is incorrect."

    return render_template('admin_register.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if 'user' in session:
        flash('Already logged in. Redirecting...')
        return redirect(url_for('profile')) #if this part is blocked you always have to sign in even if you do not logout

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']


        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password) and user[5] == 1:
            session['user'] = user
            return redirect(url_for('profile'))
        else:
            return "Invalid admin credentials."

    return render_template('admin_login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    
    if 'user' in session:
        flash('Already logged in. Redirecting...')
        return redirect(url_for('profile')) #if this part is blocked you always have to sign in even if you do not logout
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session['user'] = user
            return redirect(url_for('profile'))
        else:
            error_message = "Username or password is incorrect."

    return render_template('login.html', error_message=error_message)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        flash('Already logged in. Redirecting...')
        return redirect(url_for('profile')) #if this part is blocked you always have to sign in even if you do not logout

    if request.method == 'POST':
        # Extract user input
        username = request.form['username']
        password = request.form['password']
        repeat_password = request.form['repeat_password']
        name = request.form['name']
        surname = request.form['surname']

        # Check if passwords match
        if password == repeat_password:
            hashed_password = generate_password_hash(password, method='sha256')

            # Insert user data into the database
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password, name, surname) VALUES (%s, %s, %s, %s)',
                           (username, hashed_password, name, surname))
            conn.commit()

            return redirect(url_for('login'))
        else:
            return "Passwords do not match."

    return render_template('register.html')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user' in session and session['user'][5] == 1:  # Check if user is admin
        if request.method == 'POST':
            # Extract user input
            title = request.form['title']
            firstName = request.form['firstName']
            lastName = request.form['lastName']
            genre = request.form['genre']
            cursor = conn.cursor()
            cursor.execute('INSERT INTO books (title, author_first_name, author_last_name, genre, status) VALUES (%s, %s, %s, %s, %s)',
                           (title, firstName, lastName, genre, 'free'))
            conn.commit()
            flash('Book added!')

    return render_template('add_book.html')


@app.route('/profile')
def profile():
    if 'user' in session:
        user = session['user']
        return render_template('profile.html', user=user)
    else:
        return redirect(url_for('login'))

# Define the User model
class User(UserMixin):
    def __init__(self, id):
        self.id = id

    
# Define the user loader function
@login_manager.user_loader
def load_user(user_id):
    # Retrieve the user object based on the user_id
    return User(user_id)

@app.route('/view_users')
def view_users():
    if 'user' in session and session['user'][5] == 1:  # Check if user is admin

        cursor = conn.cursor()
        cursor.execute('SELECT id, username, name, surname, is_admin, gender, age FROM users')
        users = cursor.fetchall()

        return render_template('user_list.html', users=users)
    else:
        return redirect(url_for('login'))

@app.route('/view_books')
def view_books():
    if 'user' in session:

        cursor = conn.cursor()
        cursor.execute('SELECT books.*, users.username FROM books LEFT JOIN users ON books.user_id = users.id ORDER BY books.rating DESC;')
        books = cursor.fetchall()
        return render_template('book_list.html', books=books)
    else:
        return redirect(url_for('login'))

@app.route('/reserve_book/<int:book_id>', methods=['POST'])
def reserve_book(book_id):
    if 'user' in session:

        cursor = conn.cursor()
        cursor.execute('SELECT status, user_id FROM books WHERE id_book = %s', (book_id,))
        status = cursor.fetchone()
        reserved_by = status[1]
        status = status[0]
        user_id = session['user'][0]

        if status == 'free' and reserved_by is None:
            cursor.execute('UPDATE books SET status = %s WHERE id_book = %s', ('reserved', book_id))
            cursor.execute('UPDATE books SET user_id = %s WHERE id_book = %s', (user_id, book_id))
            conn.commit()
            flash('Reservation successful!')
        elif status == 'reserved' and reserved_by == user_id:
            cursor.execute('UPDATE books SET status = %s WHERE id_book = %s', ('free', book_id))
            cursor.execute('UPDATE books SET user_id = %s WHERE id_book = %s', (None, book_id))
            conn.commit()
            flash('Return successful!')
        else:
            flash('Sorry! You did not reserve this book.')

        return redirect(url_for('view_books'))
    else:
        return redirect(url_for('login'))


@app.route('/my_profile')
def my_profile():
    if 'user' in session:
        return render_template('my_profile.html', user=session['user'])
    else:
        return redirect(url_for('login'))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user' in session:
        if request.method == 'POST':
            gender = request.form['gender']
            age = request.form['age']


            cursor = conn.cursor()
            cursor.execute('UPDATE users SET gender = %s, age = %s WHERE id = %s', (gender, age, session['user'][0]))
            conn.commit()

            # Update the session data immediately
            session['user'] = (session['user'][0], session['user'][1], session['user'][2], session['user'][3], session['user'][4], session['user'][5], gender, age)

            return redirect(url_for('my_profile'))

        return render_template('edit_profile.html', user=session['user'])
    else:
        return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user' in session:
        if request.method == 'POST':
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            repeat_new_password = request.form['repeat_new_password']

            if check_password_hash(session['user'][2], current_password):
                if new_password == repeat_new_password:
                    hashed_password = generate_password_hash(new_password, method='sha256')


                    cursor = conn.cursor()
                    cursor.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password, session['user'][0]))
                    conn.commit()
                    return redirect(url_for('my_profile'))
                else:
                    error_message = "New passwords do not match."
            else:
                error_message = "Current password is incorrect."

            return render_template('change_password.html', error_message=error_message)

        return render_template('change_password.html')
    else:
        return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/rate_book/<int:book_id>', methods=['GET', 'POST'])
def rate_book(book_id):
    if 'user' in session:
        if request.method == 'POST':
            user_id = session['user'][0]
            new_rating = float(request.form['rating'])

            # Check if the user has already rated this book

            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_ratings WHERE user_id = %s AND book_id = %s', (user_id, book_id))
            existing_rating = cursor.fetchone()

            if existing_rating:
                # Update the existing rating
                cursor.execute('UPDATE user_ratings SET rating = %s WHERE id = %s', (new_rating, existing_rating[0]))
                flash('You have already rated this book. Your rating has been updated!')

            else:
                # Insert a new rating
                cursor.execute('INSERT INTO user_ratings (user_id, book_id, rating) VALUES (%s, %s, %s)', (user_id, book_id, new_rating))
                flash('Rating accepted!')

            conn.commit()

            # Calculate the new book rating based on all user ratings
            update_book_rating(book_id)

        # Retrieve the book details and rating
        book = get_book_details(book_id)
        return render_template('rate_book.html', book=book)
    else:
        return redirect(url_for('login'))

def update_book_rating(book_id):
    # Calculate the new book rating based on user ratings

    cursor = conn.cursor()
    cursor.execute('SELECT AVG(rating) FROM user_ratings WHERE book_id = %s', (book_id,))
    average_rating = cursor.fetchone()[0]

    # Update the book's rating and number of ratings
    cursor.execute('UPDATE books SET rating = %s, num_ratings = (SELECT COUNT(*) FROM user_ratings WHERE book_id = %s) WHERE id_book = %s', (average_rating, book_id, book_id))
    conn.commit()

def get_book_details(book_id):
    # Retrieve book details, including the rating

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM books WHERE id_book = %s', (book_id,))
    book = cursor.fetchone()
    return book

@app.route('/my_ratings')
def my_ratings():
    if 'user' in session:
        user_id = session['user'][0]
        
        # Retrieve the user's ratings from the database
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.id_book, b.title, b.author_first_name, b.author_last_name, b.genre, r.rating, b.rating, b.num_ratings
            FROM user_ratings AS r
            INNER JOIN books AS b ON r.book_id = b.id_book
            WHERE r.user_id = %s
        ''', (user_id,))
        user_ratings = cursor.fetchall()

        return render_template('my_ratings.html', my_ratings=user_ratings)
    else:
        return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)
