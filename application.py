import os
import logging
import time

from flask import Flask, session, render_template, request, redirect, jsonify, \
    make_response
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import apology, login_required, lookup


QUANTITY = 20
BOOKS_LIMIT = 500

app = Flask(__name__)

# Check for environment variables
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    if session.get("user_id", False):
        return render_template("index.html")
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Make sure all fields are filled out
    if request.method == 'POST':
        if not request.form.get('username'):
            return apology("Missing username")
        if not request.form.get('password'):
            return apology("Missing password")
        if not request.form.get('confirmation'):
            return apology("Missing password confirmation")

        # If the values exist in the request, store
        # them in local variables
        username = request.form.get('username')

        # Check if username exists in the db right away so
        # that we can return immediately if username exists in
        # the db.
        res = db.execute("SELECT COUNT(id) FROM users WHERE username = :username",
                         {'username': username}).fetchall()
        logging.warning("The count " + str(res))
        if res[0][0] != 0:
            return apology("Username already taken")
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')

        # compare password to password confirmation and create the hash
        # if password and passowrd confirmation do not match, infrom the user
        if password == confirmation:
            password_hash = generate_password_hash(password)
        else:
            return apology("Password and password confirmation do not match")

        # Insert the user details in the database
        db.execute("INSERT INTO users (username, hash) "
                   "VALUES (:username, :hash)",
                   {'username': username, 'hash': password_hash})
        db.commit()

        # Get user id and add to the session variables
        user_id = db.execute("SELECT id FROM users "
                             "WHERE username = :username",
                             {'username': username}).fetchall()[0][0]
        session["user_id"] = user_id
        return render_template('index.html')
    else:
        return render_template('register.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {'username': request.form.get("username")}).fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        return render_template("index.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route('/search', methods=['POST'])
def search():
    q = request.form.get('search')
    author_ids = db.execute("SELECT id FROM authors WHERE name ILIKE :q",
                           {'q': f"%{q}%"}).fetchall()
    if author_ids:
        author_ids_tup = tuple([auth[0] for auth in author_ids])
        books = db.execute("SELECT books.title, books.isbn, authors.name, "
                           "books.id "
                           "FROM books "
                           "INNER JOIN authors ON books.author_id=authors.id "
                           "WHERE title ILIKE :q "
                           "OR author_id in :author_ids",
                       {'q': f"%{q}%", 'author_ids': author_ids_tup}).fetchall()
    else:
        books = db.execute("SELECT books.title, books.isbn, authors.name, "
                           "books.id "
                           "FROM books "
                           "INNER JOIN authors ON books.author_id=authors.id "
                           "WHERE title ILIKE :q",
                       {'q': f"%{q}%"}).fetchall()
    if books:
        return render_template('search_result.html', books=books)
    else:
        return apology("No books fond")


@app.route("/post_review", methods=['POST'])
def post_review():
    user_id = session['user_id']
    book_id = session['open_book_id']
    res = db.execute("SELECT id FROM comments "
                     "WHERE user_id = :user_id AND book_id = :book_id ",
                     {'user_id': user_id,
                      'book_id': book_id}).fetchall()
    if res:
        return apology("You already reviewed this book")
    comment_text = request.form.get('comment')
    db.execute("INSERT INTO comments (user_id, book_id, text) "
               "VALUES (:user_id, :book_id, :text)",
               {'user_id': user_id,
                'book_id': book_id,
                'text': comment_text})
    db.commit()
    return redirect(f'/profile/{book_id}')


@app.route("/load_reviews")
def load_reviews():

    # Get the book_id from the request args
    if request.args:
        book_id = int(request.args.get("book_id"))

    # Get the comments from the database
    comments = db.execute("SELECT comments.text, users.username "
                       "FROM comments "
                       "INNER JOIN users "
                       "ON comments.user_id=users.id "
                       "WHERE comments.book_id = :book_id",
                       {'book_id': book_id}).fetchall()

    data = []
    for comment in comments:
        data_item = [comment[0]] + [comment[1]]
        data.append(data_item)
    res = make_response(jsonify(data), 200)
    return res


@app.route("/own_book")
def own_book():
    user_id = session['user_id']
    if request.args:
        book_id = int(request.args.get("book_id"))
    liked = db.execute("SELECT id FROM user_books "
                       "WHERE user_id = :user_id AND "
                       "book_id = :book_id",
                       {'user_id': user_id,
                        'book_id': book_id}).fetchall()
    logging.warning("data: " + str(liked))
    if liked:
        return apology("You already liked this book")
    db.execute("INSERT INTO user_books "
               "(user_id, book_id) VALUES "
               "(:user_id, :book_id)",
               {'book_id': book_id,
                'user_id': user_id})
    db.commit()
    book_name = db.execute("SELECT title FROM books "
                           "WHERE id = :book_id",
                           {'book_id': book_id}).fetchall()[0][0]

    return make_response(jsonify({'book_name': book_name}), 200)


@app.route('/my_books')
def my_books():
    user_id = session['user_id']
    books = db.execute("SELECT book_id from user_books "
                          "WHERE user_id = :user_id",
                       {'user_id': user_id}).fetchall()
    book_ids = tuple([item[0] for item in books])
    logging.warning("book_ids: " + str(book_ids))
    books = db.execute("SELECT books.title, books.isbn, authors.name, "
                       "books.id "
                       "FROM books "
                       "INNER JOIN authors "
                       "ON books.author_id=authors.id "
                       "WHERE books.id IN :book_ids",
                       {'book_ids': book_ids}).fetchall()

    logging.warning('data' + str(books))
    return render_template("my_books.html", books=books)

@app.route("/load")
def load():

    time.sleep(0.2)

    if request.args:
        counter = int(request.args.get("c"))

        if counter == 0:
            books = db.execute("SELECT books.title, books.isbn, authors.name, "
                               "books.id "
                               "FROM books "
                               "INNER JOIN authors "
                               "ON books.author_id=authors.id "
                               "LIMIT :n OFFSET 0",
                               {'n': QUANTITY}).fetchall()
            data = []
            for book in books:
                data_item = [book[0]] + [book[1]] + [book[2]] + [book[3]]
                data.append(data_item)
            logging.warning('data' + str(data))
            res = make_response(jsonify(data), 200)
        else:
            books = db.execute("SELECT books.title, books.isbn, authors.name, "
                               "books.id "
                               "FROM books "
                               "INNER JOIN authors "
                               "ON books.author_id=authors.id "
                               "LIMIT :n OFFSET :o",
                               {'n': QUANTITY,
                                'o': QUANTITY + counter}).fetchall()
            data = []
            for book in books:
                data_item = [book[0]] + [book[1]] + [book[2]] + [book[3]]
                data.append(data_item)
            res = make_response(jsonify(data), 200)

    return res


@app.route('/profile/<int:book_id>')
def profile(book_id):
    session["open_book_id"] = book_id
    books = db.execute("SELECT books.title, books.isbn, authors.name, "
                       "books.pub_date, books.id "
                       "FROM books "
                       "INNER JOIN authors ON books.author_id=authors.id "
                       "WHERE books.id = :id",
                       {'id': f"{book_id}"}).fetchall()
    isbn = books[0][1]
    goodreads_data = lookup(isbn)
    rating = goodreads_data['books'][0]['average_rating']
    rating_count = goodreads_data['books'][0]['work_ratings_count']
    for book in books:
        res = {
            'title': book[0],
            'isbn': book[1],
            'author_name': book[2],
            'pub_date': book[3],
            'rating': rating,
            'rating_count': rating_count,
            'book_id': book_id,
        }
    return render_template('profile.html', books=[res])


@app.route("/api/<int:isbn>")
def api(isbn):
    books = db.execute("SELECT books.title, books.isbn, authors.name, "
                       "books.pub_date, books.id "
                       "FROM books "
                       "INNER JOIN authors ON books.author_id=authors.id "
                       "WHERE books.isbn = :isbn",
                       {'isbn': f"{isbn}"}).fetchall()
    goodreads_data = lookup(isbn)
    rating = goodreads_data['books'][0]['average_rating']
    rating_count = goodreads_data['books'][0]['work_ratings_count']
    for book in books:
        res = {
            'title': book[0],
            'author': book[2],
            'year': book[3],
            'isbn': book[1],
            'review_count': rating_count,
            'average_score': rating,
        }
    return make_response(jsonify(res), 200)
