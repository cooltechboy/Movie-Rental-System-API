from flask import *
import sqlite3
from functools import wraps
import jwt
import datetime
import collections
import collections.abc
import os
import json

app = Flask(__name__)

conn = sqlite3.connect('database.db')
print("Database connected successfully!")

Thumbnail_Folder = "Thumbnails"

app.config['Thumbnail_Folder'] = Thumbnail_Folder
app.secret_key = "confidential_info"

# Handles token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        headers = request.headers
        bearer = headers.get('Authorization')
        if bearer:    # Bearer YourTokenHere
            token = bearer.split()[0]
            if not token:
                return jsonify({"message" : "Token is required to proceed!"}), 403
            else:
                try:
                    data = jwt.decode(token, app.config['SECRET_KEY'])
                except:
                    return jsonify({"message" : "Token is invalid!"}), 403
                return f(data, *args, **kwargs)
        else:
            return "You need to provide token to use the function!"
    return decorated

class create_dict(dict): 
  
    # __init__ function 
    def __init__(self): 
        self = dict() 
          
    # Function to add key:value 
    def add(self, key, value): 
        self[key] = value

# Handles signup
@app.route("/signup")
def signup():
    Name = request.form['name']
    Username = request.form['username']
    Password = request.form['password']
    Confirm_Password = request.form['confirm_password']
    conn = sqlite3.connect("database.db")
    Existing_Usernames = json.dumps(conn.execute("SELECT UserName FROM User_Details").fetchall())
    if Username != "":
        if Username in Existing_Usernames:
            return "Username already exists!"
        else:
            if Password != "":
                if Password == Confirm_Password:
                    conn.execute("INSERT INTO User_Details (Name, UserName, Password) VALUES ('{n}', '{u}', '{p}')".format(n = Name, u = Username, p = Password))
                else:
                    return "Passwords do not match!"
            else:
                return "Please enter password!"
        conn.commit()
    else:
        return "Please enter Username!"
    return "Signed Up successfully!"


# Handles login
@app.route("/login")
def login():
    auth = request.authorization
    Username = auth.username
    conn = sqlite3.connect("database.db")
    Usernames = json.dumps(conn.execute("SELECT Username FROM User_Details").fetchall())
    if Username != "":
        if Username in Usernames:
            Password = json.dumps(conn.execute("SELECT Password FROM User_Details WHERE Username = '{n}'".format(n = Username)).fetchall())
            conn.commit()
            if auth.password != "":
                if auth and auth.password in Password:
                    token = jwt.encode({'user' : auth.username, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=300)}, app.config['SECRET_KEY'])
                    return jsonify({'token' : token.decode('UTF-8')})
                else:
                    return "Incorrect password!"
            else:
                return "Please enter password!"
        else:
            return "Incorrect username or password!"
    else:
        return "Please enter username!"
    
@app.route('/', methods = ['GET'])
def showAll():
    conn = sqlite3.connect("database.db")
    Cursor = conn.execute('''SELECT ID, MovieName, Thumbnail_Filename FROM Available_Movies WHERE Status = "Active"''').fetchall()
    index_data = create_dict()
    for item in Cursor:
        index_data.add(item[0], {"id": item[0], "title": item[1], "file": os.path.abspath("Thumbnails/"+item[2])})
    conn.commit()
    return index_data