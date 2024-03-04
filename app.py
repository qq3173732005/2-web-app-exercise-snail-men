from flask import Flask, render_template, redirect, request, url_for
from flask_pymongo import PyMongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv
import flask_login
import os

load_dotenv()  # take environment variables from .env.

# create app
app = Flask(__name__)
app.secret_key = 'Gauss'

#Setup login
login_manager = flask_login.LoginManager()

login_manager.init_app(app)

# connect to the database
cxn = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = cxn[os.getenv("MONGO_DB")]  # store a reference to the database
print(db)
#print(os.getenv("MONGO_DB"))
#print(os.getenv("MONGO_URI"))
#print(db.Users.find_one())
#print(db.Users.insert_one({"username": "Gez G"}))

try:
    # verify the connection works by pinging the database
    cxn.admin.command("ping")  # The ping command is cheap and does not require auth.
    print(" *", "Connected to MongoDB!")  # if we get here, the connection worked!
except Exception as e:
    # the ping command failed, so the connection is not available.
    print(" * MongoDB connection error:", e)  # debug

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    if db.Users.find_one({"username": username}) == None:
        return

    user = User()
    user.id = "username"
    return user


@login_manager.request_loader
def request_loader(request):
    username = request.form.get("username")
    if db.Users.find_one({"username": username}) == None:
        return

    user = User()
    user.id = "username"
    return user

# home page redirects to login page
@app.route('/')
def index():
    return redirect('/login', code=301)

# login page
@app.route('/login')
# login page
@app.route('/login', methods=['GET', 'POST'])  # Add methods=['GET', 'POST']
def login():
    if request.method == 'POST':
        # Process login form data
        username = request.form.get('username')
        password = request.form.get('password')
        # Add your authentication logic here

        # For demonstration, redirect to profile page after login
        return redirect('/profile')

    return render_template('login.html')

# profile page
@app.route('/profile')
def profile():
    return render_template('profile.html')
    # users = mongo.db.users
    # user_data = users.find_one({'username': username}) Example query, replace with dynamic username
    # return render_template('profile.html', user=user_data)

# picture history page
@app.route('/history')
def history():
    #username = flask_login.current_user.id 
    #user_history = list(db.History.find({"username": username}).sort("timestamp", -1))
    #return render_template('history.html', history=user_history)
    return render_template('history.html')

# account creation page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        if db.Users.find_one({"username": username}) != None:
            return render_template('signup.html') #Username taken, should display error
        else:
            db.Users.insert_one({"username": username})
            return redirect('/login') #add user and send them to sign in
    return render_template('signup.html')

# picture change page
@app.route('/change-pfp', methods=['GET', 'POST'])
def change_pfp():
    if request.method == 'POST':
        # username = flask_login.current_user.id ?
        link = request.form.get('link')
        db.Images.insert_one({"link": link}) # -> change this to db.Images.insert_one({"username": username, "link": link})

        # Record history
        """db.History.insert_one({
            "username": username,
            "action": "Profile Picture Change",
            "timestamp": datetime.utcnow(),
            "details": {"newPictureLink": link}
        })
        """
        return redirect('/profile')
    else:
        return render_template('change-pfp.html')

# account deletion page
@app.route('/delete-account')
def delete_account():
    return render_template('delete-account.html')

# Error pages
@app.errorhandler(404)
@app.errorhandler(500)
def error_page(error):
    error_code = error.code
    if error_code == 404:
        error_description = "Page not found"
    else:
        error_description = "Internal server error"
    return render_template('error.html', error_code=error_code, error_description=error_description), error_code

# run app
if __name__ == '__main__':
    app.run()