# Zagga app
Zagga is a simple personal finance management app.

### Video Demo 
<https://youtu.be/9bgHjjYoPaU>

### Description
Zagga utilises [Tink's Open Banking API (OAuth 2.0)](https://docs.tink.com/) to securely [fetch your real bank transactions](https://docs.tink.com/resources/transactions) from your bank of choice. The app allows you the ability to recategorise your transactions into a taxonomy suitable to your needs, as well as determine your financial state based on your specified budget constraints. 

### Disclaimer
To use Zagga to access your real bank transactions, you must have a bank account in the EU or UK and your bank must be covered by Tink's API. Alternatively you can utilise another Open banking API (Plaid, True Layer, etc.) covering your geography or bank of choice, while applying Zagga's code base to handle all necessary logic. For testing purposes you have the ability to utilise Tink's demo bank to obtain test financial data.

### Technologies

* flask 
* python 3
* sqlite3 
* pipenv 
* bootstrap4
* jinja
* OAuth 2.0
* HTML5
* CSS
* JavaScript

### Installation
Install [pipenv](https://pipenv.pypa.io/en/stable/) for package management 

```zsh
pip install pipenv 
```

Activate your virtual environment
```zsh
pipenv shell 
```

In the projects root directory install the necessary packages located in the Pipfile

```zsh
pipenv install 
```

### Usage
Run [flask](https://flask.palletsprojects.com/en/2.0.x/) in your projects root directory

```zsh
flask run 
```

### Tink API
Allows you to access a users financial data securely

1. Create a developer account on [Tink console ](https://console.tink.com/signup)
2. Create an app and get your client credentials from `app settings` 
3. Copy your `client_id` and `client_secret` into the `.env`file in your root directory

### application.py

#### User account creation
* `register` allows a user to create an account and hashes their password using `werkzeug.security` WSGI web application library.
* Upon registration a user is immediately redirected to complete the Tink Link via `authentication`.

> ⚠️`authentication` is a prerequisite to fetch data from `Tink's API`, otherwise the app will not have any data to render.
* Once a user has completed the Tink Link they are required to copy the `authorization_code` back to the app. The authorization code is a one time use code, and is valid for 30 minutes.

>ℹ️ To provide a better user experience you can avoid having the user do the manual step of copying the `authorization_code`. This can be accomplished by setting up a server with an event listener and have the callback url sent back to your app. You would also additionally need to either integrate the [embed Tink link in iframe ](https://docs.tink.com/resources/tink-link-web/tink-link-web-embed-in-iframe) or use [early redirect ](https://docs.tink.com/resources/tink-link-web/tink-link-web-early-redirect)in your app. 


#### User recategorisation
* `recategorisation` allows a user to alter their individual transactions based on a `transaction_id` or to do a bulk recategorisation by entering the `transaction_name`.

> ⚠️ To offer bulk and and indvidual recategorization form validation was ommited for the fields. Therefore, is is imporatant that the user completes either the bulk or individual recategorization, otherwise and error will be thrown off. This is not a major issue as the user can just return to the page and try recomplete the form.

> ℹ️ Spending categories can be modified by altering the `CATEGORIES` global dictionary depending on the user(s) needs. The categories drop-down list could be made more user-friendly by grouping similar categories using `optgroup` html tag. 

#### Budget and Insights

* `insights` allows a user to view their spending by category.  
* `budget` allows a user to determine whether they are under or over their required budget category set.

#### Convert to float to SEK 

To convert the transaction amount to the local currency the following code can be altered. Below is an example using Swedish SEK.

```python
# source: http://babel.pocoo.org/en/latest/api/numbers.html

from babel.numbers import format_currency

# Converts numbers to desired currency SEK
@app.template_filter()
def sek(value):
   return format_currency(value, 'SEK', locale='sv_SE')

# Custom filter
app.jinja_env.filters['sek'] = sek

# returns
>> print(sek(36500.00))
>> 36,500.00 kr
```
### helpers.py

* `acccess_token` performs and api call to retrieve the `access_token` required to securely fetch transaction data from Tink API.
* `listTransactions` is helper function that retrieves data from the jsonResponse returned from the API call.