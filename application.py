import os

from flask import Flask, session,render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def login():
    return render_template("login.html")

@app.route("/signout")
def signout():
    session["logged_in"] = False
    session["username"] = None
    session["isbn"] = None
    return redirect("/")
@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/users")
def users():
    users = db.execute("SELECT * FROM users").fetchall()
    return render_template("users.html", users = users)

@app.route("/books")
def books():
    books = db.execute("SELECT * FROM books").fetchall()
    return render_template("books.html", books = books)

@app.route("/reviews")
def reviews():
    reviews = db.execute("SELECT * FROM reviews").fetchall()
    return render_template("reviews.html", reviews = reviews)

@app.route("/signing_up", methods = ["POST"])
def signing_up():
    name = request.form.get('name')
    password = request.form.get('password')
    if name == "" or password == "":
        return render_template("signup.html", message = "Username and password can not be empty")
    elif " " in name:
        return render_template("signup.html", message = "Username can not contain space bar")
    elif db.execute("SELECT * FROM users WHERE username = :name",{"name": name}).rowcount == 1:
        return render_template("signup.html", message ="This username is not available")
    db.execute("INSERT INTO users (username, password) VALUES (:name, :password)", {"name":name, "password":password})
    db.commit()
    return render_template("success.html")

@app.route("/loging_in", methods = ["POST"])
def loging_in():
    name = request.form.get('name')
    password  = request.form.get('password')
    if db.execute("SELECT * FROM users WHERE username = :name AND password = :password",{"name": name, "password":password}).rowcount == 1:
        session["logged_in"] = True
        session["username"] = name
        return redirect("/search")
    else:
        return render_template("login.html", message = "Your username or password is incorrect!")

@app.route("/submit_comment", methods = ["POST"])
def submit_comment():
    username = session.get("username")
    comment = request.form.get("comment")
    rate = int(request.form.get("star"))
    isbn = session.get("current_book")
    if db.execute("SELECT * FROM reviews WHERE username = :username AND isbn = :isbn",{"username":username, "isbn":isbn}).rowcount != 0:
        db.execute("UPDATE reviews SET review = :review, rate = :rate WHERE username = :username AND isbn = :isbn",{"review":comment,"rate":rate, "username":username, "isbn":isbn})
    else:
        db.execute("INSERT INTO reviews (isbn, username, review, rate) VALUES (:isbn, :username, :comment, :rate)", {"isbn":isbn, "username":username, "comment":comment, "rate":rate})
    db.commit()
    return redirect("/books/" + isbn)

@app.route("/search")
def search():
    if not session.get("logged_in"):
        return redirect("/")
    else:
        return render_template("search.html")

@app.route("/searching", methods = ["POST"])
def searching():
    isbn =  "%"+ request.form.get("isbn") + "%"
    title = "%"+ request.form.get("title") + "%"
    author = "%"+ request.form.get("author") + "%"

    try:
        year = int(request.form.get("year"))
        books = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn AND title LIKE :title AND author LIKE :author AND year = :year" ,{"isbn": isbn, "title": title, "author":author,"year":year}).fetchall()
    except ValueError:
        books = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn AND title LIKE :title AND author LIKE :author",{"isbn": isbn, "title": title, "author":author}).fetchall()
    if len(books) == 0:
        return render_template("search.html", message = "There is no book with that infomation")
    else:
        return render_template("search_result.html", books = books)

@app.route("/books/<string:isbn>")
def book_info(isbn):
    if not session.get("logged_in"):
        return redirect("/")
    books = db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchall()
    reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn",{"isbn":isbn}).fetchall()
    session["current_book"] = isbn
    return render_template("book.html", books = books, reviews = reviews)
