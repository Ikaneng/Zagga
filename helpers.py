import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def access_token(code, client_id, client_secret):
    """Get access token"""

    # Pass code from form 
    user_authorization_code = code


    # Contact API
    
    url = 'https://api.tink.com/api/v1/oauth/token'

    data = {
        # User Authorization Code retrieved through Tink Link
        'code' : user_authorization_code, 
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
    }

    
    response = requests.post(url, data=data)

    # Parse response
    try:
        # Retrieve and store Access Token and Refresh Token for future use 
        jsonResponse = response.json()
        return {
            "client_access_token" : jsonResponse["access_token"],
            "client_refresh_token": jsonResponse['refresh_token']
        } 

    except (KeyError, TypeError, ValueError):
        return None

def listTransactions(jsonResponse, jsonResponseCount):

    # Dictionary that will store transactions
    transactionsList = []
    for i in range(jsonResponseCount):
        transactions = {
            "name": jsonResponse["transactions"][i]["descriptions"]["display"],
            "amount": float(jsonResponse["transactions"][i]["amount"]["value"]["unscaledValue"]),
            "date": jsonResponse["transactions"][i]["dates"]["booked"]
        }
        transactionsList.append(transactions)
    
    return transactionsList


