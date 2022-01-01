import os
from typing import Counter
import requests
import json
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

from babel.numbers import format_currency


# Load environment vaariables
load_dotenv

from helpers import apology, login_required, access_token, listTransactions

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Converts to my local currency SEK
@app.template_filter()
def sek(value):
   return format_currency(value, 'SEK', locale='sv_SE')

# Custom filter - http://babel.pocoo.org/en/latest/api/numbers.html
app.jinja_env.filters['sek'] = sek

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("CLIENT_ID"):
    raise RuntimeError("CLIENT_ID not set")
if not os.environ.get("CLIENT_SECRET"):
    raise RuntimeError("CLIENT_SECRET not set")

# Set client_id and client_secret
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")


@app.route("/authentication", methods=["GET", "POST"])
@login_required
def authentication():
    """Authentication Link"""

    # Get user id from session variable
    user_id = session["user_id"]

    # User reached route by submitting a form via POST
    if request.method == "POST":

        user_authorization_code = request.form.get("code")
        print(user_authorization_code)

        # Check if user entered the value into the form field
        if not user_authorization_code:
            return apology("missing authorization code")

        # Get dictionary from access token API call from helpers
        try:
            client_access_token = access_token(user_authorization_code, client_id, client_secret)["client_access_token"]
        except:
            return apology("invalid authorization code")

        # List transactions 

        # API call
        url = 'https://api.tink.com/data/v2/transactions'

        headers = {
            'Authorization': f'Bearer {client_access_token}',
        }

        response = requests.get(url, headers=headers)

        print(response.url)

        # Get json body if page loads successfully
        if response.status_code == 200:
            jsonResponse = response.json()

            # Retrieve and store Next Page Token if there is one
            if jsonResponse['nextPageToken']: 
                transaction_next_page_token = jsonResponse['nextPageToken']

            # Get the number of transactions over the last 3 months
            transactionCount = len(jsonResponse["transactions"])

            # Print a list of transactions 
            print(listTransactions(jsonResponse, transactionCount))

            transactions = listTransactions(jsonResponse, transactionCount)

            for transaction in transactions:
                # Add username to databse if it is unique, otherwise issue apology
                name = transaction["name"]
                amount = transaction["amount"]
                date = transaction["date"]
                try:
                    # Insert registrant to users table
                    db.execute("INSERT INTO transactions (name, amount, date, user_id) VALUES(?, ?, ?, ?)", name, amount, date, user_id)

                except:
                    # Issue apology if username is not unique
                    return apology("did not insert data into database")

        else:
            print(response.status_code)

        # Redirect user to home page
        return redirect("/")

    # User reached route by clicking a link or by redirect
    else:

        return render_template("authentication.html", client_id = client_id)


@app.route("/")
@login_required
def index():
    """Display last 3 months transactions """

     # Get user id from session variable
    user_id = session["user_id"]

    # Create index table from column data from transactions table
    
    # Get transactions from database

    transactions = db.execute("SELECT id, name, amount, category, date FROM transactions WHERE user_id = ?", user_id)

    sumTransactions = db.execute("SELECT sum(amount) FROM transactions WHERE user_id = ?", user_id)[0]["sum(amount)"]

    try:
        # Pass usd function to render template to be accessible in index
        return render_template("index.html", transactions = transactions, sek = sek, sumTransactions = sumTransactions)

    except:
        return redirect("/authentication")


@app.route("/insights")
@login_required
def insights():
    """Display last 3 months transactions """

    # Get user id from session variable
    user_id = session["user_id"]
    
    # Get transactions from transactions table
    transactions = db.execute("SELECT category, sum(amount) FROM transactions WHERE user_id = ? GROUP BY category ORDER BY sum(amount)", user_id)

    date = db.execute("SELECT date FROM transactions WHERE user_id = ?", user_id)

    sumTransactions = db.execute("SELECT sum(amount) FROM transactions WHERE user_id = ?", user_id)[0]["sum(amount)"]

    end = date[0]["date"]
    start = date[len(date) - 1]["date"]

    try:
        # Pass usd function to render template to be accessible in index
        return render_template("insights.html", sek = sek, transactions = transactions, sumTransactions = sumTransactions, start = start, end = end)
    except:
        # return apology("You need get access code by completing the authentication step")
        return redirect("/authenticate")



CATEGORIES = [
    "Rent",
    "Salary",
    "Insurance",
    "Medical & Healthcare",
    "Saving",
    "Investing",
    "Phones",
    "Transportation",
    "Car",
    "Petrol",
    "Groceries",
    "Restaurant",
    "Phone",
    "Wellness & Gym",
    "Shopping",
    "Cleaning supplies",
    "Gifts & Donation",
    "Large unplanned purchases (e.g furniture, etc.)",
    "Student Loans",
    "Toiletries",
    "Grooming",
    "Heating",
    "Electricity",
    "Internet",
    "Mortgage",
    "Property",
    "HOA Fees",
    "Parking",
    "Movies",
    "Alcohol & Bars",
    "General Entertainment",
    "Vacation",
    "Subscriptions"
]


@app.route("/recategorise", methods=["GET", "POST"])
@login_required
def recategorise():
    """Change the category of a transaction"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # Get form data
        category = request.form.get("category")
        transactionId = request.form.get("transactionId")
        name = request.form.get("name")

        # Check whether form data was entered
        if not category:
            return apology("missing category")

        # Updates the category of on category (e.g shops that sell or offer different servies) 
        db.execute("UPDATE transactions SET category = ? WHERE id = ?", category, transactionId)

        # Allows a user to do a bulk recategorisation based on transaction name
        db.execute("UPDATE transactions SET category = ? WHERE name LIKE ?", category, name.title())

        # Redirect user to home page
        return redirect("/")
        

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("recategorise.html", categories = CATEGORIES)


@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    """Change the category of a transaction"""

    # Get user id from session variable
    user_id = session["user_id"]

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
       
        # Get form data
        querryCategory = request.form.get("category")
        budget = request.form.get("budget")

        # Check whether form data was entered

        if not querryCategory:
            return apology("missing category")
        
        if not budget:
            return apology("missing budget")

                # Check if shares are integer
        try:
            budget = float(budget)
        except:
            return apology("missing fields")

        # Get data from transactions table
        transactions = db.execute("SELECT category, sum(amount) AS totalCategory FROM transactions WHERE user_id = ? GROUP BY category ORDER BY sum(amount)", user_id)

        for transaction in transactions:
            
            # Get current spending from transactions table
            category = transaction["category"]
            expenditure = float(transaction["totalCategory"])

            print(category)
            print(expenditure)

            # Ensure the correct catogories are compared
            if category == querryCategory:

                # Check whether category is above budget
                if expenditure > budget:
                    direction   = "above"
                    percentage = budget - expenditure


                    # Redirect user to home page
                    return render_template("budget_check.html", category = category, percentage = sek(percentage), direction = direction)

                else:
                    direction = "below"
                    percentage = budget + expenditure


                    # Redirect user to home page
                    return render_template("budget_check.html", category = category, percentage = sek(percentage), direction = direction)
        

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Get unique categories from transaction table
        categories = db.execute("SELECT DISTINCT(category) FROM transactions WHERE user_id = ?", user_id)

        return render_template("budget.html", categories = categories)


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/authentication")

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting form via POST)
    if (request.method == "POST"):

        # Get required form fields
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check user inputs into form fields
        if not username:
            return apology("must provide username", 401)

        elif not password:
            return apology("must provide password", 401)

        elif not confirmation:
            return apology("must provide password", 401)
        
        # Check whether passwords match
        elif password != confirmation:
            return apology("passwords do not match", 401)

        # Hash passwords 
        hash = generate_password_hash(password)

        # Add username to databse if it is unique, otherwise issue apology
        try:

            # Insert user into database
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)

            # Redirect user to home page 
            return redirect("/")

        except:
            return apology("username already exsists", 400)

    # User reached route via GET (as by clicking link via redirect)
    else:
        return render_template("register.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change account settings"""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Get user_id from session variable
        user_id = session["user_id"]

        # Get form field data
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        password_confirmation = request.form.get("password_confirmation")
                
        # Check if user enters data to form
        if not current_password:
            return apology("missing current password password")

        if not new_password:
            return apology("missing new password")

        if not password_confirmation:
            return apology("missing password confirmation")

            
        # Get user data from users table
        rows = db.execute("SELECT * FROM users WHERE id = ?", user_id)
        
        # Check current password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], current_password):
            return apology("invalid current password")
            
        # Check if new passwords match
        if new_password != password_confirmation:
            return apology("passwords do not match")
            
        # Change password stored in users table
        hash = generate_password_hash(new_password)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", hash, user_id)
        
        return redirect("/login")
        
    # else if user reached route via GET (as by clicking a link or via redirect)  
    else:
        return render_template("change_password.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
