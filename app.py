from flask import *
import sqlite3
from functools import wraps
import jwt
import datetime
import collections
import collections.abc
import os
import json
from collections import OrderedDict
from werkzeug.utils import secure_filename
import razorpay

app = Flask(__name__)

conn = sqlite3.connect('database.db')
print("Database connected successfully!")

Thumbnail_Folder = "Thumbnails"

app.config['Thumbnail_Folder'] = Thumbnail_Folder
app.secret_key = "confidential_info"

client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
client.set_app_details({"title" : "Movie Rental API", "version" : "1"})

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

# The home page that shows all the movies that are available for rental    
@app.route('/', methods = ['GET'])
def showAll():
    if request.method == 'GET':
        conn = sqlite3.connect("database.db")
        Cursor = conn.execute('''SELECT ID, MovieName, Thumbnail_Filename, RentalCharges_in_$_per_month, RentalCharges_For_Basic_Members, RentalCharges_For_Premium_Members FROM Available_Movies WHERE Status = "Active"''').fetchall()
        if not request.headers:
            membership = ""
            pass
        elif request.headers:
            @token_required
            def findMembership(data):
                username = data['user']
                membership_details = conn.execute('''SELECT UserName, MembershipType FROM Membership_Records WHERE UserName = '{n}' AND Status = "Active"'''.format(n = username)).fetchall()
                if membership_details != "":
                    for item in membership_details:
                        if item[1] == "Premium":
                            membershipType = "Premium"
                        elif item[1] == "Basic":
                            membershipType = "Basic"
                else:
                    pass
                return membershipType
            membership = findMembership()

        index_data = []
        if membership != "" and membership == "Premium":
            for item in Cursor:
                index_data.append({"id" : item[0], "title" : item[1], "thumbnail" : os.path.abspath("Thumbnails/"+item[2]), "rentForPremiumMembers" : item[5]})
        elif membership != "" and membership == "Basic":
            for item in Cursor:
                index_data.append({"id" : item[0], "title" : item[1], "thumbnail" : os.path.abspath("Thumbnails/"+item[2]), "rentForBasicMembers" : item[4], "rentForPremiumMembers" : item[5]})
        else:
            for item in Cursor:
                index_data.append({"id" : item[0], "title" : item[1], "thumbnail" : os.path.abspath("Thumbnails/"+item[2]), "rent" : item[3], "rentForPremiumMembers" : item[5]})
        conn.commit()
        return index_data

# The web page that shows all the action movies that are available for rental 
@app.route('/movies/action', methods = ['GET'])
def showActionMovies():
    conn = sqlite3.connect("database.db")
    Cursor = conn.execute('''SELECT ID, MovieName, Thumbnail_Filename, RentalCharges_in_$_per_month, RentalCharges_For_Premium_Members FROM Available_Movies WHERE Category = "Action" AND Status = "Active"''').fetchall()
    index_data_action = []
    for item in Cursor:
        index_data_action.append({"id" : item[0], "title" : item[1], "thumbnail" : os.path.abspath("Thumbnails/"+item[2]), "rent" : item[3], "rentForPremiumMembers" : item[4]})
    conn.commit()
    return index_data_action

# The web page that shows all the horror movies that are available for rental 
@app.route('/movies/horror', methods = ['GET'])
def showHorrorMovies():
    conn = sqlite3.connect("database.db")
    Cursor = conn.execute('''SELECT ID, MovieName, Thumbnail_Filename, RentalCharges_in_$_per_month, RentalCharges_For_Premium_Members FROM Available_Movies WHERE Category = "Horror" AND Status = "Active"''').fetchall()
    index_data_horror = []
    for item in Cursor:
        index_data_horror.append({"id" : item[0], "title" : item[1], "thumbnail" : os.path.abspath("Thumbnails/"+item[2]), "rent" : item[3], "rentForPremiumMembers" : item[4]})
    conn.commit()
    return index_data_horror

# The web page that shows all the sci-fi movies that are available for rental 
@app.route('/movies/sci-fi', methods = ['GET'])
def showSciFiMovies():
    conn = sqlite3.connect("database.db")
    Cursor = conn.execute('''SELECT ID, MovieName, Thumbnail_Filename, RentalCharges_in_$_per_month, RentalCharges_For_Premium_Members FROM Available_Movies WHERE Category = "Sci-Fi" AND Status = "Active"''').fetchall()
    index_data_sci_fi = []
    for item in Cursor:
        index_data_sci_fi.append({"id" : item[0], "title" : item[1], "thumbnail" : os.path.abspath("Thumbnails/"+item[2]), "rent" : item[3], "rentForPremiumMembers" : item[4]})
    conn.commit()
    return index_data_sci_fi

# The web page that shows all the comedy movies that are available for rental 
@app.route('/movies/comedy', methods = ['GET'])
def showComedyMovies():
    conn = sqlite3.connect("database.db")
    Cursor = conn.execute('''SELECT ID, MovieName, Thumbnail_Filename, RentalCharges_in_$_per_month, RentalCharges_For_Premium_Members FROM Available_Movies WHERE Category = "Comedy" AND Status = "Active"''').fetchall()
    index_data_comedy = []
    for item in Cursor:
        index_data_comedy.append({"id" : item[0], "title" : item[1], "thumbnail" : os.path.abspath("Thumbnails/"+item[2]), "rent" : item[3], "rentForPremiumMembers" : item[4]})
    conn.commit()
    return index_data_comedy

# The web page that shows all the romantic movies that are available for rental 
@app.route('/movies/romance', methods = ['GET'])
def showRomanticMovies():
    conn = sqlite3.connect("database.db")
    Cursor = conn.execute('''SELECT ID, MovieName, Thumbnail_Filename, RentalCharges_in_$_per_month, RentalCharges_For_Premium_Members FROM Available_Movies WHERE Category = "Romance" AND Status = "Active"''').fetchall()
    index_data_romance = []
    for item in Cursor:
        index_data_romance.append({"id" : item[0], "title" : item[1], "thumbnail" : os.path.abspath("Thumbnails/"+item[2]), "rent" : item[3], "rentForPremiumMembers" : item[4]})
    conn.commit()
    return index_data_romance

# Searches movies with the given keyword                            
@app.route('/search', methods = ['GET'])
def showSearchResults():
    name = request.args.get("name")
    conn = sqlite3.connect("database.db")
    Cursor = conn.execute('''SELECT ID, MovieName, Thumbnail_Filename, RentalCharges_in_$_per_month, RentalCharges_For_Premium_Members FROM Available_Movies WHERE SearchingName LIKE "%{n}%" AND Status = "Active"'''.format(n = name)).fetchall()
    search_results = []
    for item in Cursor:
        search_results.append({"id" : item[0], "title" : item[1], "thumbnail" : os.path.abspath("Thumbnails/"+item[2]), "rent" : item[3], "rentForPremiumMembers" : item[4]})
    conn.commit()
    return search_results

# Shows the preview of a particular movie along with all relevant details, rental charges, and other movies from the same category
@app.route('/movies/preview/<name>', methods = ['GET'])
def showPreview(name):
    # name = request.form["name"]
    id = request.args.get("id")
    conn = sqlite3.connect("database.db")
    Cursor = conn.execute('''SELECT ID, MovieName, Category, Thumbnail_Filename, TrailerLink, RentalCharges_in_$_per_month, RentalCharges_For_Premium_Members FROM Available_Movies 
    WHERE ID = "{i}" AND SearchingName = "{n}" AND Status = "Active"'''.format(i = id, n = name)).fetchall()
    if request.headers:
        @token_required
        def findRentals(data):
            username =  data['user']
            SearchResults = conn.execute("SELECT UserName, Movie FROM Rental_Records WHERE UserName = '{n}' AND Status = 'Active'".format(n = username)).fetchall()
            RentedMovies = []
            for item in SearchResults:
                RentedMovies.append(item[1])
            return RentedMovies
        ActiveRentals = findRentals()
    elif not request.headers:
        pass

    preview_info = []
    for item in Cursor:
        if item[1] in ActiveRentals:
            preview_info.append({"id" : item[0], "title" : item[1], "category" : item[2], "thumbnail" : os.path.abspath("Thumbnails/"+item[3]), "trailer" : item[4]})
        else:
            preview_info.append({"id" : item[0], "title" : item[1], "category" : item[2], "thumbnail" : os.path.abspath("Thumbnails/"+item[3]), "trailer" : item[4], "rent" : item[5], "rentForPremiumMembers" : item[6]})
        # The following query finds all other movies in the same category
        similar_movies_query = conn.execute('''SELECT ID, MovieName, Thumbnail_Filename, RentalCharges_in_$_per_month, RentalCharges_For_Premium_Members FROM Available_Movies 
        WHERE Category = "{c}" AND Status = "Active" AND NOT SearchingName = "{n}"'''.format(c = item[2], n = name)).fetchall()
        similar_movies = []
        for similar in similar_movies_query:
            similar_movies.append({"id" : similar[0], "title" : similar[1], "thumbnail" : os.path.abspath("Thumbnails/"+similar[2]), "rent" : similar[3], "rentForPremiumMembers" : similar[4]})
        preview_info.append(similar_movies)
    conn.commit()
    return preview_info

# Show active rentals for an user
@app.route("/myprofile/rentals", methods = ['GET'])
@token_required
def showRentals(data):
    name = data['user']
    conn = sqlite3.connect('database.db')
    rental_update = conn.execute("SELECT ID, UserName, Movie, RentedUpto FROM Rental_Records WHERE UserName = '{n}'".format(n = name)).fetchall()
    for item in rental_update:
        if datetime.date.today().strftime('%m-%d-%Y') == datetime.datetime.strptime(item[3], '%m-%d-%Y'):
            conn.execute("UPDATE Rental_Records SET Status = 'Inactive' WHERE UserName = '{n}' AND RentedUpto = '{d}'".format(n = name, d = datetime.date.today().strftime('%m-%d-%Y')))
    Active_rentals = conn.execute("SELECT ID, UserName, Movie, RentedUpto FROM Rental_Records WHERE UserName = '{n}' Status = 'Active'".format(n = name)).fetchall()
    user_active_rentals = []
    preview_data = []
    if Active_rentals != []:
        for item in Active_rentals:
            if item[1] == name:
                user_active_rentals.append(item[2])
                for movie in user_active_rentals:
                    movie_details = conn.execute("SELECT ID, MovieName, Category, Thumbnail_Filename FROM Available_Movies WHERE MovieName = '{m}'".format(m = movie)).fetchall()
                    for each_movie in movie_details:
                        preview_data.append({"id" : each_movie[0], "title" : each_movie[1], "category" : each_movie[2], "thumbnail" : os.path.abspath("Thumbnails/"+each_movie[3]), "rental_validity" : item[3]})
            else:
                return "You don't have any active rental!"
    else:
        return "There is no active rental for any user!"
    return preview_data

'''HTML template with a form to create movie rental order. In real case the necessary details will be passed as a JSON object to the request.'''
@app.route("/movies/rent")
def rentMovie():
    return render_template('app.html')

# Add movie function to add movie. Form needs to be used to pass data.
@app.route("/admin/movies/add", methods = ['POST'])
@token_required
def adminAddMovie(data):
    if request.method == 'POST':
        name = data['user']
        moviename = request.form['moviename']
        searchingname = request.form['searchingname']
        category = request.form['category']
        file = request.files['file']
        trailer = request.form['trailer']
        rent = float(request.form['rent'])
        rentForBasicMembers = rent*0.8
        rentForPremiumMembers = rent*0.5
        conn = sqlite3.connect("database.db")
        Admins = conn.execute("SELECT AdminUsername From Admin_Details WHERE Status = 'Active'").fetchall()
        if name in (item[0] for item in Admins):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['Thumbnail_Folder'],filename))
            conn.execute('''INSERT INTO Available_Movies (MovieName, SearchingName, Category, Thumbnail_Filename, TrailerLink, RentalCharges_in_$_per_month, RentalCharges_For_Basic_Members, RentalCharges_For_Premium_Members, Status) 
                        VALUES ('{m}', '{s}', '{c}', '{f}', '{t}', '{r}', '{b}', '{p}', 'Active')'''.format(m = moviename, s = searchingname, c = category, f = filename, t = trailer, r = rent, b = rentForBasicMembers, p = rentForPremiumMembers))
            conn.commit()
    return "File and details saved successfully!"

# Creates Razorpay order for renting a movie. Collects form data from app.html
@app.route("/movies/rent/payment", methods = ['POST'])
def createRentOrder():
    if request.method == 'POST':
        id = request.form["id"]
        price = float(request.form["price"])
        name = request.form['user']
        movie = request.form["movie"]
        orderReceipt = f"{name}-{datetime.datetime.utcnow().strftime('%B-%d-%Y-%H-%M-%S')}"
        orderDate =  datetime.date.today().strftime('%m-%d-%Y')
        orderdata = {
            "amount" : price*100,
            "currency" : "USD",
            "receipt" : orderReceipt,
            "notes" : {
                "movie" : movie,
                "user" : name,
                "orderDate" : orderDate
            }
        }
        client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        payment = client.order.create(data=orderdata)
            
        return render_template('payment.html', payment=payment)
    
# Verifies payment signature and provides rental access to the movie. Runs JS from payment.html
@app.route("/payment/success", methods = ['POST'])
def successPayment():
    if request.method == 'POST':
        razorpay_payment_id = request.form['razorpay_payment_id']
        razorpay_order_id = request.form['razorpay_order_id']
        razorpay_signature = request.form['razorpay_signature']
        responseData = {
            "razorpay_payment_id" : razorpay_payment_id,
            "razorpay_order_id" : razorpay_order_id,
            "razorpay_signature" : razorpay_signature
        }
        client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        verify = client.utility.verify_payment_signature({
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
        })
        delta = datetime.timedelta(days=30)
        if verify:
            orderDetails = client.order.fetch(razorpay_order_id)
            paymentDetails = client.order.payments(razorpay_order_id)
            Movie = orderDetails["notes"]["movie"]
            username = orderDetails["notes"]["user"]
            rentedOn = datetime.datetime.strptime(orderDetails["notes"]["orderDate"], '%m-%d-%Y')
            rentedUpto = rentedOn + delta
            conn = sqlite3.connect('database.db')
            entry = conn.execute('''INSERT INTO Rental_Records (UserName, Movie, RentedOn, RentedUpto, Status, OrderID, PaymentID) 
                         VALUES ('{n}', '{m}', '{o}', '{u}', 'Active', '{OI}', '{PI}')'''.format(n = username, m = Movie, o = rentedOn, u = rentedUpto, OI = razorpay_order_id, PI = razorpay_payment_id))
            newRental = conn.execute('''SELECT ID, MovieName, Category, Thumbnail_Filename, TrailerLink FROM Available_Movies 
                        WHERE MovieName = "{m}" AND Status = "Active"'''.format(m = Movie)).fetchall()
            newRentalPreview = []
            for item in newRental:
                newRentalPreview.append({"id" : item[0], "title" : item[1], "category" : item[2], "thumbnail" : os.path.abspath("Thumbnails/"+item[3]), "trailer" : item[4]})
            conn.commit()
            return newRentalPreview
        
# HTML template with a form to create movie membership order. In real case the necessary details will be passed as a JSON object to the request.
@app.route("/membership/order")
def membership():
    return render_template('membershipOrder.html')

# Creates Razorpay order for purchasing a membership. Collects form data from membershipOrder.html
@app.route("/membership/order/payment", methods = ['POST'])
def createMembershipOrder():
    if request.method == 'POST':
        username = request.form.get("username")
        userEmail = request.form.get("userEmail")
        if request.form.get("gridRadios") == "basicMembership":
            membership = 'Basic'
            price = 5
        elif request.form.get("gridRadios") != "basicMembership":
            if request.form.get("gridRadios") == "premiumMembership":
                membership = 'Premium'
                price = 8
        orderReceipt = f"{username}-{datetime.datetime.utcnow().strftime('%B-%d-%Y-%H-%M-%S')}"
        orderDate =  datetime.date.today().strftime('%m-%d-%Y')
        orderdata = {
            "amount" : price*100,
            "currency" : "USD",
            "receipt" : orderReceipt,
            "notes" : {
                "membership" : membership,
                "username" : username,
                "userEmail" : userEmail,
                "orderDate" : orderDate
            }
        }
        client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        payment = client.order.create(data=orderdata)
            
        return render_template('membershipPayment.html', payment=payment)
    
# Verifies payment signature and provides membership to the user. Runs JS from membershipPayment.html
@app.route("/mermbership/payment/success", methods = ['POST'])
def membershipPaymentSuccess():
    if request.method == 'POST':
        razorpay_payment_id = request.form['razorpay_payment_id']
        razorpay_order_id = request.form['razorpay_order_id']
        razorpay_signature = request.form['razorpay_signature']
        responseData = {
            "razorpay_payment_id" : razorpay_payment_id,
            "razorpay_order_id" : razorpay_order_id,
            "razorpay_signature" : razorpay_signature
        }
        client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        verify = client.utility.verify_payment_signature({
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
        })
        delta = datetime.timedelta(days=30)
        if verify:
            orderDetails = client.order.fetch(razorpay_order_id)
            paymentDetails = client.order.payments(razorpay_order_id)
            Membership = orderDetails["notes"]["membership"]
            username = orderDetails["notes"]["username"]
            userEmail = orderDetails["notes"]["userEmail"]
            startedOn = datetime.datetime.strptime(orderDetails["notes"]["orderDate"], '%m-%d-%Y')
            expiresOn = startedOn + delta
            conn = sqlite3.connect('database.db')
            entry = conn.execute('''INSERT INTO Membership_Records (UserName, UserEmail, MembershipType, StartedOn, ExpiresOn, Status, OrderID, PaymentID) 
                         VALUES ('{n}', '{e}', '{m}', '{s}', '{x}', 'Active', '{OI}', '{PI}')'''.format(n = username, e = userEmail, m = Membership, s = startedOn, x = expiresOn, OI = razorpay_order_id, PI = razorpay_payment_id))
            newRental = conn.execute('''SELECT UserName, UserEmail, MembershipType, StartedOn, ExpiresOn FROM Membership_Records 
                        WHERE UserName = "{n}" AND Status = "Active"'''.format(n = username)).fetchall()
            activeMembershipPreview = []
            for item in newRental:
                activeMembershipPreview.append({"username" : item[0], "userEmail" : item[1], "membership" : item[2], "startedOn" : item[3], "expiresOn" : item[4]})
            conn.commit()
            return activeMembershipPreview
