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
from hashlib import sha256

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

@app.context_processor
def inject_username():
    if hasattr(flask_login.current_user, "id"):
        return dict(username=flask_login.current_user.id)
    return dict(username=None)



@login_manager.user_loader
def user_loader(username):
    if db.Users.find_one({"username": username}) == None:
        return

    user = User()
    user.id = username
    return user


@login_manager.request_loader
def request_loader(request):
    username = request.form.get("username")
    if db.Users.find_one({"username": username}) == None:
        return

    user = User()
    user.id = username
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
        account = db.Users.find_one({"username": username})
        if account != None:
            if account["passHash"] == sha256(password.encode('utf-8')).hexdigest():
                user = User()
                user.id = username
                flask_login.login_user(user)
                return redirect(url_for('profile', profileName = username))
            else:
                return render_template('login.html', username_dne = False, wrong_pw = True)
        # For demonstration, redirect to profile page after login
        return render_template('login.html', username_dne = True, wrong_pw = False)
    return render_template('login.html', username_dne = False, wrong_pw = False)

# profile page
@app.route('/profile/<profileName>')
def profile(profileName):
    user = db.Users.find_one({'username': profileName})
    pic = user['currentPFP']
    return render_template('profile.html', pic = pic, profileName = profileName)
    # users = mongo.db.users
    # user_data = users.find_one({'username': username}) Example query, replace with dynamic username
    # return render_template('profile.html', user=user_data)

# picture history page
@app.route('/history/<profileName>', methods=['GET', 'POST'])
def history(profileName):
    currentUser = flask_login.current_user.id
    if request.method == 'POST':
        db.Users.update_one({"username": currentUser},
                  { "$set": {
                             "currentPFP": request.form.get('setable')
                             }
                 })
        return redirect(url_for('profile', profileName = currentUser))
    pics = db.Images.find({'username': profileName})
    picList = [pic['link'] for pic in pics]
    return render_template('history.html', pics = picList, profileName = profileName)
    #username = flask_login.current_user.id 
    #user_history = list(db.History.find({"username": username}).sort("timestamp", -1))
    #return render_template('history.html', history=user_history)
    

# account creation page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if db.Users.find_one({"username": username}) != None:
            return redirect('/signup') #Username taken, should display error
        else:
            db.Users.insert_one({"username": username, "passHash": sha256(password.encode('utf-8')).hexdigest(), "currentPFP": "https://www.shutterstock.com/image-vector/blank-avatar-photo-place-holder-600nw-1095249842.jpg"})
            return redirect('/login') #add user and send them to sign in
    return render_template('signup.html', username_taken = True)

# picture change page
@app.route('/change-pfp', methods=['GET', 'POST'])
@flask_login.login_required
def change_pfp():
    if request.method == 'POST':
        username = flask_login.current_user.id
        link = request.form.get('link')
        db.Images.insert_one({"link": link, "username": username}) # -> change this to db.Images.insert_one({"username": username, "link": link})
        db.Users.update_one({"username": username},
                  { "$set": {
                             "currentPFP": link
                             }
                 })
        # db.Images.insert_one({"link": link, "username": username})
        # Record history
        """db.History.insert_one({
            "username": username,
            "action": "Profile Picture Change",
            "timestamp": datetime.utcnow(),
            "details": {"newPictureLink": link}
        })
        """
        return redirect(url_for('profile', profileName = username))
    else:
        return render_template('change-pfp.html')

# account deletion page
@app.route('/delete', methods=['GET', 'POST'])
@flask_login.login_required
def delete():
    if request.method == 'POST':
        db.Images.find_one_and_delete({'username': flask_login.current_user.id, "link": request.form.get('deletable')})
    
        return redirect('/delete')
    pics = db.Images.find({'username': flask_login.current_user.id})
    picList = [pic['link'] for pic in pics]
    return render_template('delete.html', pics = picList)

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect("/login")

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