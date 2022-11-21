
import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import login_required, datetimenow

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///openhouse.db")



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    # if get for to login if post go to admin or main menu depending on user id
    if session["user_id"]:
        if session["user_id"] == 1:
            return adminmenu()
        else:
            return mainmenu()
    #if session id == admin go to admin menu
    # else go to main menu

    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            print("no username")
            return render_template("login.html",error="please enter a username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            print("no password")
            return render_template("login.html", error="please enter a password")


        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            print("either there is no user by that name or it was the wrong password")
            return render_template("login.html", error="username and password do not match")


        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        print(session["user_id"])

        # Redirect user to home page
        if session["user_id"] == 1:
            print("going to admin menu")
            return redirect("/adminmenu")
        else:
            print("going to main menu")
            return redirect("/mainmenu")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/adduser", methods=["GET", "POST"])
@login_required
def adduser():
    """Register user"""
    if request.method == "POST":
        user = request.form.get("username")
        pas = request.form.get("password")
        vpas = request.form.get("confirmation")
        # check if all fields filled out
        if user and pas and vpas:
            # check if passwords match
            if pas != vpas:
                return render_template("adduser.html",error="passwords must match") # return apology(user)

            # check if username already taken
            x = db.execute("select count() from users where username = %s", user)
            c = x[0]
            t = c["count()"]
            if t > 0:
                return render_template("adduser.html", error="user name already is use")
            else:

                passhash = generate_password_hash(pas)
                db.execute("INSERT INTO users (username,hash) values(%s,%s)", user, passhash)

                # Redirect user to home page
                return  usermanagement()

        else:
            return render_template("adduser.html",error="please fillout all fields")

    else:
        print(session["user_id"])
        if session["user_id"] == 1:
            return render_template("adduser.html")
        else:
            return render_template("mainmenu.html")



@app.route("/removeuser", methods=["GET", "POST"])
@login_required
def removeuser():
    if request.method == "POST":
        #verfiy that username is in users db

        # verify that username is not admin
        # remove user
        user=request.form.get("User")
        x = db.execute("select count() from users where username = %s", user) [0]["count()"]

        if x == 0 :
            error = "there is no user " + str(user)
            return render_template("removeuser.html", error=error)
        elif user == "admin":
            error = "you may not delete user admin"
            return render_template("removeuser.html", error=error)

        else:
            db.execute("DELETE FROM users WHERE username = ?", user)

            return usermanagement()

    else:
        #verify that the user is admin
        if session["user_id"] == 1:
            #create list of users (not including admin) and pass it to the html
            users = []
            Users = db.execute("SELECT username FROM users WHERE id !=1")
            for item in Users:
                users.append(item["username"])

            return render_template("removeuser.html", users=users)
        else:
            return render_template("mainmenu.html")






@app.route("/adminmenu")
@login_required
def adminmenu():
    if session["user_id"] == 1:
        return render_template("adminmenu.html")
    else:
        return render_template("mainmenu.html")


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    if request.method == "POST":
        # get form data
        oldpass = request.form.get("oldpassword")
        newpass = request.form.get("newpassword")
        confir = request.form.get("confirmation")

        # verify all feilds filled out
        if oldpass and newpass and confir:
            # verify that new passwords match
            if confir != newpass:#new passwords don't match
                return render_template("changepassword.html", error="new passwords must match")
            oldhash = db.execute("SELECT hash from users where id = 1")[0]['hash']
            print(oldhash)
            newhash = generate_password_hash(newpass)
            print(check_password_hash(oldhash, oldpass))
            if not check_password_hash(oldhash, oldpass):
                return render_template("changepassword.html", error="old password incorrect")

            if newhash == oldhash:
                return render_template("changepassword.html", error="new password must be different from old password")
            # alter usertable hash
            db.execute("UPDATE users SET hash = ? WHERE id = 1 AND username = 'admin'", newhash)
            return login()
        else:
            return render_template("changepassword.html", error="please fill-out all fields")


    else:
        if session["user_id"] == 1:
            return render_template("changepassword.html")
        else:
            return render_template("mainmenu.html")


@app.route("/usermanagement", methods=["GET", "POST"])
@login_required
def usermanagement():
    """Register user"""

    if session["user_id"] == 1:
        return render_template("usermanagement.html")
    else:
        return render_template("mainmenu.html")



@app.route("/transactionsearch")
@login_required
def transactionsearch():
    # verify user is admin
    if session["user_id"] == 1:
        locations = db.execute("SELECT location FROM locations WHERE id > 0")
        items = db.execute("SELECT itemnumber FROM items")
        users = db.execute("SELECT username FROM users WHERE username != 'admin'")
        #print(locations,users,items)

        return render_template("transactionsearch.html", locations=locations, items=items, users=users)

    #if user not admin go to main menu
    else:
        return render_template("mainmenu.html")

@app.route("/mainmenu")
@login_required
def mainmenu():

    # make variable to show name in upper left corner (this should be done on all pages except login and admin menu items)
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    return render_template("mainmenu.html", username=username)

@app.route("/error")
@login_required
def Error(text):

    return render_template("error.html", text=text)




@app.route("/lookup")
@login_required
def lookup():
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    # get list items
    data=[]
    locs = db.execute("SELECT location FROM locations")
    for item in locs:
        data.append(item["location"])
    items = db.execute("SELECT itemnumber FROM items")
    for item in items:
        data.append(item["itemnumber"])
    items = db.execute("SELECT name FROM items")
    for item in items:
        data.append(item["name"])

    return render_template("lookup.html", username=username, data=data)

@app.route("/table", methods=["POST"])
@login_required
def table():
    error=""
    data =[]
    header = ""
    title = ""
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    #check if input is valid
    it = request.form.get("thing")
    print(it)
    # get count on itemnumber
    inu = db.execute("SELECT id FROM items WHERE itemnumber = ?", it)
    ina = db.execute("SELECT id FROM items WHERE name = ?", it)
    il = db.execute("SELECT id FROM locations WHERE location = ?",it)
    print(inu, ina, il)
    total = 0
    if len(inu)> 0:
        thing = db.execute("SELECT locations.location, iqty from inventory INNER JOIN locations ON inventory.location=locations.id WHERE item = ?",inu[0]["id"])
        title =  " Locations for " + str(it)
        header = "Location"
        for item in thing:
            dict = {
                "item": item["location"],
                "qty": item["iqty"]
            }
            total += item["iqty"]
            data.append(dict)

    elif len(ina)> 0:
        thing = db.execute("SELECT locations.location, iqty from inventory INNER JOIN locations ON inventory.location=locations.id WHERE item = ?",ina[0]["id"])
        title =  " Locations for " + str(it)
        header = "Location"
        for item in thing:
            dict = {
                "item": item["location"],
                "qty": item["iqty"]
            }
            total += item["iqty"]
            data.append(dict)

    elif len(il) > 0:
        thing = db.execute("SELECT items.itemnumber, iqty from inventory INNER JOIN items ON inventory.item=items.id WHERE location = ?",il[0]["id"])
        print(thing)
        if len(thing) < 1:
            dict = {
                "location": "",
                "qty": ""
            }
            data.append(dict)
            title =  " Items in " + str(it)
            header = "item"
            error = "no items in location"
            return render_template("table.html", data=data, header=header, title=title, error=error, username=username, total=total)
        title =  " Items in " + str(it)
        header = "item"
        for item in thing:
            dict = {
                "item": item["itemnumber"],
                "qty": item["iqty"]
            }
            total="n/a"
            data.append(dict)

    else:
        error="invalid input"
        header="invalid"
        title="you idiot"
        total = "dumbass"


    return render_template("table.html", data=data, header=header, title=title, error=error, username=username, total=total)




@app.route("/locationmanagement")
@login_required
def locationmanagement():
    if session["user_id"] == 1:
        return render_template("locationmanagement.html")
    else:
        return render_template("mainmenu.html")

@app.route("/addrack",  methods=["GET", "POST"])
@login_required
def addrack():
    if request.method == "POST":
        racknum,columns,rows = request.form.get("racknumber"),request.form.get("columns"),request.form.get("rows")
        # verify all fields filled out
        if racknum and rows and columns:
            # verify positive integers 1-99 / 1-99 / 1-26
            try:
                racknum = int(racknum)
                rows = int(rows)
                columns = int(columns)
            except:
                return render_template("addrack.html",error="rack number and columns must be a whole number between 1 and 99 \n rows must be a whole number between 1 and 26")


            if racknum not in range(1,99) or columns not in range(1,99) or rows not in range(1,26):
                return render_template("addrack.html",error="rack number and columns must be a whole number between 1 and 99 \n rows must be a whole number between 1 and 26")
            # for each column, for each row create location number and add to locs list.

            locs = []
            if racknum < 10:
                racknum = "0" + str(racknum)
            else:
                racknum = str(racknum)

            for i in range(1,columns+1):
                if i < 10:
                    i = "0" + str(i)
                else:
                    i = str(i)
                for e in range(1,rows+1):
                    e = e + 64
                    e = chr(e)
                    loc = racknum + i + e
                    locs.append(loc)
            #print("I crreated a list of locations")

            for item in locs:
                # verify that location doesn't already exist
                x = db.execute("SELECT id FROM locations WHERE location =?",item)
                if x:
                    return render_template("addrack.html", error="one or more of those locations already exist")


                db.execute("INSERT INTO locations (location,type) VALUES (?,'S')",item)
            return render_template("locationmanagement.html")


        else:
            return render_template("addrack.html",error="please fill out all fields")

    else:
        if session["user_id"] == 1:
            return render_template("addrack.html")
        else:
            return render_template("mainmenu.html")


@app.route("/addlocation",  methods=["GET", "POST"])
@login_required
def addlocation():
    if request.method == "POST":
        location,type = request.form.get("location"), request.form.get("type")

        # verify all fields filled out
        if location and type and (type in ['Receiving','Storage','Shipping']):
            x = db.execute("SELECT id FROM locations WHERE location =?", location)
            if x:
                return render_template("addlocation.html", error="that location already exists")

            db.execute("INSERT INTO locations (location,type) VALUES (?,?)", location, type)
            return render_template("locationmanagement.html")


        else:
            return render_template("addlocation.html",error="please fill out all fields")

    else:
        if session["user_id"] == 1:
            return render_template("addlocation.html")
        else:
            return render_template("mainmenu.html")



@app.route("/companyinfo",  methods=["GET", "POST"])
@login_required
def companyinfo():
    if request.method == "POST":
        #if request.files["logo"]:
            # save file to static folder
            #f = request.files['logo']
            #f.save(static('logo.bmp'))

        if request.form.get("name"):
            db.execute("UPDATE info SET name=?",request.form.get("name"))

        if request.form.get("address"):
            db.execute("UPDATE info SET address=?",request.form.get("address"))

        if request.form.get("phone"):
            db.execute("UPDATE info SET phone=?",request.form.get("phone"))

        if request.form.get("email"):
            db.execute("UPDATE info SET email=?",request.form.get("email"))

        if request.form.get("motto"):
            db.execute("UPDATE info SET motto=?",request.form.get("motto"))

        if request.form.get("website"):
            db.execute("UPDATE info SET website=?",request.form.get("website"))


        else:
            return adminmenu()

        return adminmenu()


    else:
        if session["user_id"] == 1:
            # get company info from sql db and parse into list to pass to html
            info = db.execute("SELECT * FROM info")[0]
            return render_template("companyinfo.html", info=info)
        else:
            return render_template("mainmenu.html")








@app.route("/removelocation",  methods=["GET", "POST"])
@login_required
def removelocation():
    data = db.execute("SELECT location FROM locations")
    if request.method == "POST":
        location = request.form.get("location")
        # verify all fields filled out
        if location:
            x = db.execute("SELECT id FROM locations WHERE location =?", location)
            # if location is in database delete it else return error
            if x:
                db.execute("DELETE FROM locations WHERE location = ?", location)
                return render_template("locationmanagement.html")

            else:
                return render_template("removelocation.html", error="that location does not exist", data=data)

        else:
            return render_template("removelocation.html",error="please fill out all fields", data=data)

    else:
        if session["user_id"] == 1:
            return render_template("removelocation.html", data=data)
        else:
            return render_template("mainmenu.html")



@app.route("/about")
@login_required
def about():
    if session["user_id"] == 1:
        return render_template("about.html")
    else:
        return render_template("mainmenu.html")








@app.route("/pickingmenu")
@login_required
def pickingmenu():
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    ord = []
    orders = db.execute("SELECT ordernum, id, status, shipdate FROM orders WHERE status = 'unpicked' or status = 'picking' ")
    for item in orders:
        qtys = db.execute("SELECT qty FROM orderitems WHERE order_id = ?",item["id"])
        i = 0
        for it in qtys:
            i += it["qty"]

        dict = {
            "ordernum" : item["ordernum"],
            "status" : item["status"],
            "qty" : i,
            "shipdate": item["shipdate"]
        }
        ord.append(dict)
    return render_template("pickingmenu.html", ord=ord, username=username)




@app.route("/picking", methods=["GET", "POST"])
@login_required
def picking():
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    if request.method == "POST":
        ordnum = request.form.get("ordernum")
        # verify ordernumber is real and pickable
        x = db.execute("SELECT COUNT() FROM orders WHERE ordernum = ? and (status = 'unpicked' or status = 'picking')", ordnum)[0]["COUNT()"]
        if x == 0: # verify order id is in db
            return redirect("/schedulingmenu")


        # get ordenumber id
        orderid = db.execute("SELECT id FROM orders WHERE ordernum = ?",ordnum)[0]["id"]
        #print("orderid",orderid)
       #check if getting request from  picked button
        if request.form.get("location") or request.form.get("item") or request.form.get("qty") or request.form.get("shippinglocation"):
            if request.form.get("location") and request.form.get("item") and request.form.get("qty") and request.form.get("shippinglocation"):
                location, item, qty, shippinglocation = request.form.get("location"), request.form.get("item"), int(request.form.get("qty")), request.form.get("shippinglocation")
                # print(shippinglocation," gha gah gah agha gha gh")
                locid = db.execute("SELECT id from locations where location = ?",location)[0]["id"]
                # print(locid,"locid")
                itemid = db.execute("SELECT id from items where itemnumber = ?",item)[0]["id"]
                # print("itemid ",itemid)
                #ensure that all inputs will work
                thingprime = db.execute("SELECT COUNT() FROM orderitems INNER JOIN inventory ON orderitems.item_id=inventory.item WHERE order_id = ? and workingqty > 0 and location = ? and iqty >= ? and item_id = ?",orderid, locid, qty, itemid)[0]["COUNT()"]
                print(thingprime,"     thingprime")
                if thingprime == 0:
                    print("fail location item qty verification")
                    return pickingmenu()
                #verify shipping location is a shipping location
                count = db.execute("SELECT COUNT(id) FROM locations WHERE type = 'Shipping' and  location = ?",shippinglocation)
                if count == 0:
                    print("FAIL shipping location verification")
                    return pickingmenu()
                # delete qty of iten from location by subtraction or deleting

                thingprime = db.execute("SELECT iqty, workingqty FROM orderitems INNER JOIN inventory ON orderitems.item_id=inventory.item WHERE order_id = ? and workingqty > 0 and location = ? and iqty >= ? and item_id = ?",orderid, locid, qty, itemid)
                print(thingprime)
                if qty == thingprime[0]["iqty"]:
                    db.execute("DELETE from inventory WHERE location = ? and item = ?" ,locid, itemid)

                else:
                    lo = thingprime[0]["iqty"] - qty
                    db.execute("UPDATE inventory SET iqty = ? WHERE location = ? and item = ?", lo ,locid, itemid)

                # update working qty
                if qty == thingprime[0]["workingqty"]:
                    db.execute("UPDATE orderitems SET status = 'picked', workingqty = 0 WHERE workingqty = ? and item_id = ?",qty , itemid)

                else:
                    lo = thingprime[0]["workingqty"] - qty
                    db.execute("UPDATE orderitems SET status = 'picking', workingqty = ? WHERE workingqty = ? and item_id = ?",lo, thingprime[0]["workingqty"], itemid)

                # add item qty to shippin glocation
                # get length of list  (qty of iten in shippinglocation)

                shippinglocationid = db.execute("SELECT id FROM locations WHERE location = ?", shippinglocation)[0]["id"]
                x = db.execute("SELECT iqty FROM inventory WHERE item = ? and location =?",itemid, shippinglocationid)
                if len(x) ==0:
                    # add row with location item qty
                    db.execute("INSERT INTO inventory (location,item,iqty) values (?,?,?)",shippinglocationid, itemid,qty)

                else:
                    # update existing row to add qty
                    x = x[0]["iqty"]
                    db.execute("UPDATE inventory SET iqty = ? WHERE location = ? and item = ?", (qty+x), shippinglocationid, itemid)

                # create transaction log entry
                datetim = datetimenow()
                db.execute("INSERT INTO history (datetime, user, transaction_type, item, loc_to, loc_from,qty,ordernumber) VALUES (?, ?, 'Pick', ?, ?, ?,?,?)", datetim, session["user_id"], int(itemid), shippinglocationid, locid,qty, orderid)




            else:
                return pickingmenu()
        # update orderitem status after picking
        picked = db.execute("SELECT COUNT() FROM orderitems WHERE order_id = ? AND status = 'picked'",orderid)[0]["COUNT()"]
        if picked > 0:
            db.execute("UPDATE orders SET status = 'picking' WHERE id = ?", orderid)

        # update order status after picking
        picked = db.execute("SELECT COUNT() FROM orderitems WHERE order_id = ? AND (status = 'unpicked' or status = 'picking' )",orderid)[0]["COUNT()"]
        if picked == 0:
            db.execute("UPDATE orders SET status = 'picked' WHERE id = ?", orderid)
            return pickingmenu()


        try:
            thing = db.execute("SELECT * FROM orderitems INNER JOIN inventory ON orderitems.item_id=inventory.item INNER JOIN locations ON inventory.location=locations.id INNER JOIN items ON inventory.item=items.id WHERE order_id = ? and workingqty > 0 and locations.type != 'Shipping' ORDER BY location LIMIT 1",orderid)[0]
        except:
            print("items not avaliable")
            return Error("items not avaliable")
        print(thing ["location"], "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP")
        if thing["iqty"] >= thing["workingqty"]:
            quantity = thing["workingqty"]

        elif thing["iqty"] < thing["workingqty"]:
            quantity = thing["iqty"]

        shiploc = db.execute("SELECT shipping_location FROM orders WHERE id = ?",orderid)[0]["shipping_location"]
        shiploc = db.execute("SELECT location FROM locations WHERE id = ?", shiploc)[0]["location"]

        data={
            "ordernum": ordnum,
            "location": thing["location"],
            "item": thing["itemnumber"],
            "qty": quantity,
            "shippinglocation" : shiploc
        }

        return render_template("picking.html", data=data, username=username )
    else:
        return redirect("/pickingmenu")







@app.route("/receiving", methods=["GET", "POST"])
@login_required
def receiving():
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    error=""
    if request.method == "POST":
        # verify all fields filled out
        loc = request.form.get("location")
        item = request.form.get("item")
        qty = int(request.form.get("qty"))
        if loc and item and qty:
            # verify location exists and is a receiving location
            locs = db.execute("SELECT * FROM locations WHERE location = ? and type = 'R'",loc)
            if len(locs) > 0:
                # verify item number is in items db else redirect to create item
                items = db.execute("SELECT * FROM items WHERE itemnumber = ?",item)
                print(items, len(items))
                if len(items) > 0:
                    #check if identical item already in location (increment qty in db or add new row to db)
                    locid = db.execute("SELECT id FROM locations WHERE location = ?",loc)[0]["id"]
                    print(locid)
                    itemid = db.execute("SELECT id FROM items WHERE itemnumber = ?",item)[0]["id"]
                    print(itemid)
                    q = db.execute("SELECT iqty FROM inventory WHERE location = ? and item = ?",locid,itemid)#[0]["qty"]
                    print(q)
                    if len(q) > 0:
                        db.execute("UPDATE inventory SET iqty =? where location = ? and item = ?",(q[0]["iqty"])+qty, locid, itemid) # increment qty of inventoy table where loc = locid and item = itemid
                    else:
                        db.execute("INSERT INTO inventory (location,item,iqty) VALUES (?,?,?)", locid, itemid, qty) # add row with locid and itemmid qty=1
                    # update history db with transaction
                    datetim = datetimenow()

                    db.execute("INSERT INTO history (datetime,user,transaction_type,item,loc_to,loc_from,qty,ordernumber) VALUES(?,?,'Receive',?,?,0,?,0)",datetim, session["user_id"],itemid,locid,qty)
                else:
                    return redirect ("/createitem")
            else:
                error = "that is not a receivable location"

        else:
            error = "please fill out all fields"


    locs = db.execute("SELECT location FROM locations WHERE type ='R'")
    locations =[]
    for item in locs:
        locations.append(item["location"])
    return render_template("receiving.html",username=username, locations=locations, error=error )

@app.route("/createitem", methods=["GET", "POST"])
@login_required
def createitem():
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    if request.method == "POST":
        print("verify all fields filled out")
        num = request.form.get("number")
        name = request.form.get("name")
        desc = request.form.get("description")
        cost = request.form.get("cost")
        if num and name and desc and cost:
            print("verify item number does not already exist")
            x = db.execute("SELECT * FROM items where itemnumber = ?", num)
            if len(x) > 0:
                error="item already exists"
            else:
                print("add data to db")
                db.execute("INSERT INTO items (itemnumber,name,description,cost) VALUES (?,?,?,?)", num, name, desc, cost)
                # redirect to receiving?
                return redirect("/receiving")
        else:
            error="all fileds must be filled out"
        return render_template("createitem.html", username=username, error=error)

    else:
        print("if method = get")
        return render_template("createitem.html")


@app.route("/shippingmenu")
@login_required
def shippingmenu():
    error=""
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    x = db.execute("SELECT * FROM orders INNER JOIN locations ON orders.shipping_location=locations.id WHERE orders.id != 0 and (status = 'picked' or status = 'shipping')")
    orders = []
    for item in x:
        dict = {
            "shiploc": item["location"],
            "ordernum": item["ordernum"],
            "name": item["name"],
            "items": db.execute("SELECT SUM(qty) FROM orderitems WHERE order_id = ?",item["id"])[0]["SUM(qty)"],
            "shipdate": item["shipdate"],
            "status": item["status"]
        }

        orders.append(dict)
    print(orders)
    return render_template("shippingmenu.html", username=username, orders=orders, error=error)



@app.route("/shipping", methods=["POST"])
@login_required
def shipping():
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    ordernum = request.form.get("ordernum")

    # verify order number exists and is shippable
    orderid = db.execute("SELECT id FROM orders WHERE ordernum=?",ordernum)
    print(orderid)
    if len(orderid) == 0:
        return shippingmenu()
    orderid= orderid[0]["id"]
    if request.form.get("itemid"):
        db.execute("UPDATE orderitems SET status ='shipping' WHERE id = ?",int(request.form.get("itemid")))
        db.execute("UPDATE orders SET status ='shipping' WHERE id = ?",orderid)
    if request.form.get("ship"):
        # set order = shipped
        db.execute("UPDATE orders SET status = 'shipped' WHERE ordernum = ?",request.form.get("ship"))
        # delete all items from inventory
        loc = db.execute("SELECT shipping_location FROM orders WHERE id=?",orderid)[0]["shipping_location"]
        items = db.execute("SELECT item_id, qty FROM orderitems WHERE order_id=?",orderid)
        for item in items:
            iqty = db.execute("SELECT iqty FROM inventory WHERE location = ? and item = ?",loc, item["item_id"])[0]["iqty"]
            if item["qty"] < iqty:
                # update db with iqty = iqty-qty
                db.execute("UPDATE inventory SET iqty = ? WHERE location = ? and item = ?",(iqty - item["qty"]), loc, item["item_id"])
            elif item["qty"] == iqty:
                db.execute("DELETE FROM inventory WHERE iqty = ? and item = ? and location = ?",iqty,item["item_id"],loc)
            else:
                return Error("you broke it!")
            datetim = datetimenow()
            db.execute("INSERT INTO history (datetime,user,transaction_type,item,loc_to,loc_from,qty,ordernumber) VALUES(?,?,'shipping',?,0,?,?,?)",datetim, int(session["user_id"]), int(item["item_id"]),int(loc),int(item["qty"]),int(orderid))

        #items = db.execute("select ",)
        return shippingmenu()

    # get info
    info = db.execute("SELECT ordernum, name, address, shipdate, location FROM orders INNER JOIN locations ON orders.shipping_location=locations.id WHERE orders.id = ?", orderid)[0]
    dat= db.execute("SELECT orderitems.id, itemnumber,name,description, qty, status FROM items JOIN orderitems ON items.id=orderitems.item_id WHERE order_id=?",orderid)
    data=[]
    ready = True
    for item in dat:
        if item["status"] == "shipping":
            color = "gray"
            verified = "verified"
            enabled = "disabled"
        else:
            color = "#3f48cc"
            verified = "verify"
            enabled = ""
            ready = False

        dict = {
            "id": item["id"],
            "itemnumber": item["itemnumber"],
            "name": item["name"],
            "description": item["description"],
            "qty": item["qty"],
            "color": color,
            "verified": verified,
            "enabled" : enabled
        }
        data.append(dict)
    if ready == True:
        ship = {"enabled":"","color":"#3f48cc","ship": "Ship Order"}
    else:
        ship = {"enabled":"disabled","color":"gray","ship": "verify items"}
    return render_template("shipping.html", info=info, data=data, username=username, ship=ship)




@app.route("/schedulingmenu")
@login_required
def schedulingmenu():
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    orders= db.execute("select ordernum, name, status from orders where status != 'shipped' and id != 0")
    return render_template("schedulingmenu.html", orders=orders, username=username)



@app.route("/neworder")
@login_required
def neworder():
    locs = db.execute("SELECT location FROM locations WHERE type ='Shipping'")
    locations =[]
    for item in locs:
        locations.append(item["location"])
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    return render_template("neworder.html", username=username, locations=locations)



@app.route("/editorder", methods=["GET", "POST"])
@login_required
def editorder():
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]

    if request.method == "POST":
        error=""

        # check if getting post info from create order.html
        if request.form.get("name") or request.form.get("address") or request.form.get("shipdate") or request.form.get("shippinglocation"):
            if request.form.get("name") and request.form.get("address") and request.form.get("shipdate") and request.form.get("shippinglocation"):
                name, address, shipdate, shippinglocation = request.form.get("name"), request.form.get("address"), request.form.get("shipdate"), request.form.get("shippinglocation")
                ### VERIFY SHIPPING LOCATION
                 # get count of inventory locations where type= Shipping
                count = db.execute("SELECT COUNT(id) FROM locations WHERE type = 'Shipping' and  location = ?",shippinglocation)
                if count == 0:
                    return render_template("neworder.html", error="please select valid shipping location")
                old = db.execute("SELECT max(ordernum) FROM orders")[0]["max(ordernum)"]
                print(old)
                ordnum = int(old) + 1 # create new ordnum (set variable)
                # add order number, name and address to orders table
                shippinglocation = db.execute("SELECT id FROM locations WHERE location = ?", shippinglocation)[0]["id"]
                db.execute("INSERT INTO orders (name, address, ordernum, status,shipdate,shipping_location) VALUES (?,?,?,'unsubmitted',?,?)",name, address,ordnum, shipdate,shippinglocation)
                orderid = db.execute("SELECT id FROM orders WHERE ordernum = ?",ordnum)[0]["id"]

            else:
                return render_template("neworder.html", error="please fill out all fields")


        #check if getting request from scheduling menu "edit order"
        elif request.form.get("id"):
            ordnum = request.form.get("id")
            x = db.execute("SELECT COUNT(ordernum) FROM orders WHERE ordernum = ?", ordnum)[0]["COUNT(ordernum)"]
            print("an ID has been submited ",ordnum)
            if x == 0: # verify order id is in db
                return redirect("/schedulingmenu", error="invalid order number")
            orderid = db.execute("SELECT id FROM orders WHERE ordernum = ?",ordnum)[0]["id"]

            # check if getting remove item from order request
            if request.form.get("remove"):
                print("remove function was called")
                # verify item is real
                itemid= db.execute("SELECT id FROM items WHERE itemnumber = ?",request.form.get("remove"))[0]["id"]

                # verify item is in order
                if itemid:
                    # remove item from order where item id and order id are in row
                    db.execute("DELETE FROM orderitems WHERE order_id = ? and item_id = ?",orderid,itemid)

            #check if getting data from add item button
            if request.form.get("item") or request.form.get("qty"):
                if request.form.get("item")and request.form.get("qty"):
                    print("an item has been added")
                    # verify item is real
                    itemid= db.execute("SELECT id FROM items WHERE itemnumber = ?",request.form.get("item"))
                    # verify item is in inventory
                    if len(itemid) == 0:
                        error = "that item is not registered"

                    else:
                        itemid = itemid[0]["id"] # strip id from list dictionary
                        qtys = db.execute("SELECT iqty FROM inventory WHERE item =?",itemid)
                        max = 0
                        # count items in inventory
                        for item in qtys:
                            max += item["iqty"]
                        print(max , qtys)

                        # get quatity of items already scheduled
                        schdedqty = 0
                        schded = db.execute("SELECT qty FROM orderitems WHERE item_id = ?",itemid)
                        for item in schded:
                            schdedqty += item["qty"]

                        # subtract number of items in in order table from max to avoid double booking
                        maxed = max - schdedqty

                        #verify enough qty in inventory and input is a positive integer
                        if (int(request.form.get("qty")) > maxed) or (int(request.form.get("qty")) < 0):
                            # if asking for too many or less than 0. return to edit order with error message
                            error="There are not enough. There are " + str(max) + " " + str(request.form.get("item")) + "(s) in inventory and " + str(schdedqty) + " of them have already been scheduled"

                        else:
                            # add item to order
                            db.execute("INSERT INTO orderitems (order_id,item_id,qty,status,workingqty) VALUES (?,?,?,'unpicked',?)",orderid,itemid,request.form.get("qty"),request.form.get("qty"))
                else:
                    error = "you need to enter an item and a qty"

        else:
            return schedulingmenu()



        # create data to pass to editorder.html
        #select all data where ordernum == ordnum list of dictionaries containing (item number, item name, item description, item cost, order qty, total cost, item status)
        order = []
        TOTAL = 0
        items = db.execute("SELECT * FROM orderitems WHERE order_id = ?", orderid)
        print("all items in order ",items)
        for item in items:
            itemdata = db.execute("SELECT * from items WHERE id = ?",item["item_id"])
            dict = {
                "number": itemdata[0]["itemnumber"],
                "name": itemdata[0]["name"],
                "description": itemdata[0]["description"],
                "cost": itemdata[0]["cost"],
                "qty": item["qty"],
                "totalcost": int(itemdata[0]["cost"]) * int(item["qty"]),
                "status": item["status"]
            }
            TOTAL += dict["totalcost"]
            order.append(dict)
        cd = db.execute("SELECT * FROM orders WHERE id =?",orderid)[0]

        # populate items select tab
        itemnums = []
        itms = db.execute("SELECT DISTINCT item FROM inventory")
        for i in itms:
            itemnums.append(db.execute("SELECT itemnumber FROM items WHERE id = ?",i["item"])[0]["itemnumber"])



        return render_template("editorder.html", order=order, cd=cd, TOTAL=TOTAL, itemnums=itemnums,error=error, username=username)
    else: # if get request
        return schedulingmenu()




@app.route("/transactionlog", methods=["GET", "POST"])
@login_required
def transactionlog():
    if request.method == "POST":
        username=""
        print("it hasn't broken yet")
        id = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("user"))
        item = db.execute("SELECT id FROM items WHERE itemnumber = ?",request.form.get("item"))
        location = db.execute("SELECT id FROM locations WHERE location = ?", request.form.get("location"))

        print(id, item, location)


        # test =  db.execute("SELECT datetime,transaction_type, qty, itemnumber, location, loc_from, ordernum FROM history INNER JOIN items ON history.item = items.id INNER JOIN orders ON history.ordernumber=orders.id INNER JOIN locations ON history.loc_to = locations.id WHERE user=? and item=? and (loc_to = ? or loc_from = ?) ORDER BY datetime DESC",id[0]["id"], item[0]["id"], location[0]["id"], location[0]["id"])
        # print(test)


        if id and item and location:
            dat = db.execute("SELECT username, datetime,transaction_type, qty, itemnumber, location, loc_from, ordernum FROM history INNER JOIN items ON history.item = items.id INNER JOIN orders ON history.ordernumber=orders.id INNER JOIN locations ON history.loc_to = locations.id INNER JOIN users ON history.user = users.id WHERE user=? and item=? and (loc_to = ? or loc_from = ?) ORDER BY datetime DESC",id[0]["id"], item[0]["id"], location[0]["id"], location[0]["id"])
        elif id and item:
            dat = db.execute("SELECT username, datetime,transaction_type, qty, itemnumber, location, loc_from, ordernum FROM history INNER JOIN items ON history.item = items.id INNER JOIN orders ON history.ordernumber=orders.id INNER JOIN locations ON history.loc_to = locations.id INNER JOIN users ON history.user = users.id WHERE user=? and item=? ORDER BY datetime DESC",id[0]["id"], item[0]["id"])
        elif id and location:
            dat= db.execute("SELECT username, datetime,transaction_type, qty, itemnumber, location, loc_from, ordernum FROM history INNER JOIN items ON history.item = items.id INNER JOIN orders ON history.ordernumber=orders.id INNER JOIN locations ON history.loc_to = locations.id INNER JOIN users ON history.user = users.id WHERE user=? and (loc_to = ? or loc_from = ?) ORDER BY datetime DESC",id[0]["id"], location[0]["id"], location[0]["id"])
        elif item and location:
            dat= db.execute("SELECT username, datetime,transaction_type, qty, itemnumber, location, loc_from, ordernum FROM history INNER JOIN items ON history.item = items.id INNER JOIN orders ON history.ordernumber=orders.id INNER JOIN locations ON history.loc_to = locations.id INNER JOIN users ON history.user = users.id WHERE item=? and (loc_to = ? or loc_from = ?) ORDER BY datetime DESC", item[0]["id"], location[0]["id"], location[0]["id"])
        elif id:
            dat= db.execute("SELECT username, datetime,transaction_type, qty, itemnumber, location, loc_from, ordernum FROM history INNER JOIN items ON history.item = items.id INNER JOIN orders ON history.ordernumber=orders.id INNER JOIN locations ON history.loc_to = locations.id INNER JOIN users ON history.user = users.id WHERE user=? ORDER BY datetime DESC",id[0]["id"])
        elif item:
            dat= db.execute("SELECT username, datetime,transaction_type, qty, itemnumber, location, loc_from, ordernum FROM history INNER JOIN items ON history.item = items.id INNER JOIN orders ON history.ordernumber=orders.id INNER JOIN locations ON history.loc_to = locations.id INNER JOIN users ON history.user = users.id WHERE item=? ORDER BY datetime DESC",item[0]["id"])
        elif location:
            dat= db.execute("SELECT username, datetime,transaction_type, qty, itemnumber, location, loc_from, ordernum FROM history INNER JOIN items ON history.item = items.id INNER JOIN orders ON history.ordernumber=orders.id INNER JOIN locations ON history.loc_to = locations.id INNER JOIN users ON history.user = users.id WHERE (loc_to = ? or loc_from = ?) ORDER BY datetime DESC", location[0]["id"], location[0]["id"])
        else:
            return Error("you fool! you destroyed it!!")



    else:
        username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
        id = session["user_id"]
        dat = db.execute("SELECT username, datetime,transaction_type, qty, itemnumber, location, loc_from, ordernum FROM history INNER JOIN items ON history.item = items.id INNER JOIN orders ON history.ordernumber=orders.id INNER JOIN locations ON history.loc_to = locations.id INNER JOIN users ON history.user = users.id WHERE user=? ORDER BY datetime DESC",id)


    data=[]
    for item in dat:
        #print(item["item"])
        dict = {
            "username" : item["username"],
            "datetime": item["datetime"],
            "transaction_type": item["transaction_type"],
            "item": item["itemnumber"],
            "loc_to": item["location"],
            "loc_from": (db.execute("SELECT location FROM locations WHERE id = ?",item["loc_from"])[0]["location"]),
            "qty": item["qty"],
            "ordernumber": item["ordernum"],
        }
        #print(dict['item'],dict['loc_to'])
        data.append(dict)
    return render_template("transactionlog.html", data=data, username=username)











@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    username = db.execute("SELECT username from users where id = ?", session["user_id"])[0]["username"]
    error = ""
    data = db.execute("SELECT location FROM locations")
    items = db.execute("SELECT itemnumber FROM items")
    if request.method == "POST":
        # verify all fields filled out
        if request.form.get("origin") and request.form.get("item") and request.form.get("qty") and request.form.get("destination"):
            origin , item, qty, destination = request.form.get("origin"), request.form.get("item"), int(request.form.get("qty")), request.form.get("destination")
            # verify all feilds are valid (one by one)
            x = db.execute("SELECT id FROM locations WHERE location = ?", origin)
            if len(x) == 0:
                error = "origin location does not exist"
                return render_template("transfer.html", data=data, items=items, error=error, username=username)
            x = db.execute("SELECT id FROM locations WHERE location = ?", destination)
            if len(x) == 0:
                error = "destination does not exist"
                return render_template("transfer.html", data=data, items=items, error=error, username=username)
            x = db.execute("SELECT id FROM items WHERE itemnumber = ?", item)
            if len(x) == 0:
                error = "item does not exist"
                return render_template("transfer.html", data=data, items=items, error=error, username=username)
            itemid = db.execute("SELECT id FROM items WHERE itemnumber = ?",item)[0]["id"]
            locid = db.execute("SELECT id FROM locations WHERE location = ?",origin)[0]["id"]
            dest =db.execute("SELECT id FROM locations WHERE location = ?",destination)[0]["id"]



            x = db.execute("SELECT iqty FROM inventory WHERE location = ? and item = ?",locid, itemid)
            print(x)
            if len(x) == 0:
                error = "there are not enough in that location"
                return render_template("transfer.html", data=data, items=items, error=error, username=username)
            if x[0]["iqty"] < qty:
                error = "there are not enough in that location"
                return render_template("transfer.html", data=data, items=items, error=error, username=username)
            x = x[0]["iqty"]
        else:
            error="fillout all fields"


        if error == "":
                # remove items from origin
                if x == qty:
                    db.execute("DELETE FROM inventory WHERE location = ? and item = ? and iqty = ?",locid, itemid, qty)
                else:
                    db.execute("UPDATE inventory SET iqty = ? WHERE location =? and item = ?",(x - qty) ,locid,itemid)
                # add items to destination
                destid = db.execute("SELECT id FROM locations WHERE location = ?",destination)[0]["id"]
                i = db.execute("SELECT iqty FROM inventory WHERE location = ? and item = ?",destid, itemid)
                print(i)
                if len(i) > 0:
                    i = i[0]["iqty"]
                    db.execute("UPDATE inventory SET iqty = ? WHERE location = ? and item = ?", (i + qty), destid, itemid)

                else:
                    db.execute("INSERT INTO inventory (location, item, iqty) VALUES (?,?,?)", destid, itemid ,qty)
                 # update history db with transactiono
                datetim = datetimenow()

                db.execute("INSERT INTO history (datetime,user,transaction_type,item,loc_to,loc_from,qty,ordernumber) VALUES(?,?,'Transfer',?,?,?,?,0)",datetim, session["user_id"],int(itemid),dest,locid,qty)


        return render_template("transfer.html", data=data, items=items, error=error, username=username)
    else:
        return render_template("transfer.html", data=data, items=items, error=error, username=username)


##############################################################################################################delete me#########################
"""
@app.route("/deleteme", methods=["GET", "POST"])
@login_required
def deleteme():

    if request.method == "POST":
        return render_template("deleteme.html")
    else:
        return render_template("deleteme.html")


"""

################################################################################################################################################










@app.route("/invoice", methods=["GET", "POST"])
@login_required
def invoice():
    if request.method == "POST":
        # verify order number
       if request.form.get("ordernum"):
            ordnum = request.form.get("ordernum")
            # verify ordernumber exists
            x = db.execute("SELECT COUNT(ordernum) FROM orders WHERE ordernum = ?", ordnum)[0]["COUNT(ordernum)"]
            if x == 0: # verify order id is in db
                return redirect("/schedulingmenu", error="invalid order number")

            orderid = db.execute("SELECT id FROM orders WHERE ordernum = ?",ordnum)[0]["id"]
            order = []
            TOTAL = 0
            items = db.execute("SELECT * FROM orderitems WHERE order_id = ?", orderid)
            print("all items in order ",items)
            for item in items:
                itemdata = db.execute("SELECT * from items WHERE id = ?",item["item_id"])
                dict = {
                    "number": itemdata[0]["itemnumber"],
                    "name": itemdata[0]["name"],
                    "description": itemdata[0]["description"],
                    "cost": itemdata[0]["cost"],
                    "qty": item["qty"],
                    "totalcost": int(itemdata[0]["cost"]) * int(item["qty"]),
                    "status": item["status"]
                }
                TOTAL += dict["totalcost"]
                order.append(dict)

            cd = db.execute("SELECT * FROM orders WHERE id =?",orderid)[0]
            info = db.execute("SELECT * FROM info")[0]
            db.execute("UPDATE orders SET status = 'unpicked' where id = ?", orderid)

            return render_template("invoice.html", info=info, order=order, cd=cd, TOTAL=TOTAL)

    else:
        return schedulingmenu()
