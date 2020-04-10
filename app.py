from flask import Flask,render_template,request,redirect,url_for,session
from pymongo import MongoClient
import pandas
import bcrypt
import random
import datetime


demo = MongoClient()
myclient = MongoClient('localhost', 27017)


db = myclient["Canteen"]  # db name
Canteen = db["Canteen"]# collection name
reg = db["Registration"] # collection name
foods = db["food"]
clg = db['clg']


app = Flask(__name__)

app.secret_key = "Darshan"


@app.route("/",methods=['POST','GET'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        collage = request.form['clg_name']
        session['clg_name'] = collage
        session ['username'] = username
        print (collage)
        if 'username' in session:
            user = session['username']
            print(user)
        # login_user = db.reg.find_one({"Username":username})           
        # if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['Password'].encode('utf-8')) == login_user['Password'].encode('utf-8'):
            return redirect(url_for('users'))
        return "Errorr"     
    return render_template("index.html")


@app.route("/canteen_selection", methods=['GET','POST'])
def canteen_selection():
    if request.method == 'POST':
        clg_name = request.form['clg_name']
        session['collage_name_session'] = clg_name
        collage_exist = db.clg.find_one({"Collage_name":clg_name})
        if collage_exist is not None:
            return redirect(url_for('canteen'))
        return "such collage is not exist"
    all_clg_name = db.clg.distinct("Collage_name")
    return render_template("canteen_selection.html",all_clg_name = all_clg_name)


@app.route("/canteen",methods=['GET','POST'])
def canteen():
    if 'collage_name_session' in session:
        s = session['collage_name_session']
        print (s)
        if request.method == 'POST':
            collage_name = session['collage_name_session'] 
            Food_name = request.form['food_name']
            Food_price = request.form['food_price']
            item_pic = request.form['item_pic']
            test_food = db.canteen.find_one({"Food_Name":Food_name,"Collage_Name":collage_name})
            if test_food is None:
                db.canteen.insert_one({"Collage_Name":collage_name,"Food_Name":Food_name,"Food_Price":Food_price,"Item_Pic":item_pic})
                return redirect(url_for("canteen"))
            return "food name is already exist"
        items = db.canteen.find({"Collage_Name":s})
        return render_template("canteen.html",clg_name = s,items=items)
    return '''
<h3> session timeout </h3>
'''

@app.route("/menue")
def login():
    return render_template("menue.html")


@app.route("/registration", methods=['POST','GET'])
def registration():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        username = request.form['username']
        email = request.form['email']
        mblno = request.form['mblno']
        exist_user = db.reg.find_one({'Username':username})    
        if exist_user is None:
            hash_password = bcrypt.hashpw(request.form['password'].encode('utf-8'),bcrypt.gensalt())
            print(hash_password)
            db.reg.insert_one({"First_Name":fname,"Last_Name":lname,"Username":username,"Password":hash_password,"Email":email,"Mobile_Number":mblno})
            return redirect(url_for("login"))
        return "Username already exist"
    return render_template("registration.html")
             
    
@app.route("/admin", methods=['POST','GET'])
def admin():
    if request.method == 'POST':
        Collage_name = request.form['clg_name']
        Collage_number = request.form['clg_no']
        collage_exist = db.clg.find_one({"Collage_name":Collage_name})
        if collage_exist is None:
            db.clg.insert_one({"Collage_name":Collage_name,"Collage_number":Collage_number})
            return redirect(url_for("admin"))
        return "Colage Name or Collage Number is already exist"
    return render_template("Admin.html")



@app.route("/delete_item",methods=['POST'])
def delete_items():
    delete_id = request.form['deletable_item']
    print(delete_id)
    db.canteen.remove({"Food_Name":delete_id})
    return redirect(url_for('canteen',alert = delete_id))

    
@app.route("/users",methods=['GET','POST'])
def users():
    if request.method == 'POST':
        if 'username' in session:
            username = session['username']    
            purchased_item = request.form['purchased_item']
            item_count = request.form['item_count']
            item_url = request.form['Item_Url']
            item_price = request.form['item_price']
            total_price = int(item_price) * int(item_count)
            print (total_price,item_count,purchased_item)
            username = session['username']
            table_number = request.form['table_number']
            payment_method = request.form['payment_menthod']
            collage_name = session['clg_name']
            count = db.order_details.find().count()
            total_count = int(count) + 1
            print(total_count)
            order_status = "Waiting"
            if payment_method == 'COD':
                payment_status = "Pending"
                db.order_details.insert_one({"Username":username,"Table_Number":table_number,"Item_Url":item_url,"Order_Number":total_count,"Payment_Method":payment_method,"Purchased_Item":purchased_item,"Date":datetime.datetime.now(),"item_count":item_count,"Name_Of_Purchaser":username,"Collage_Name":collage_name,"Total_Price":total_price,"Payment_Status":payment_status,"Order_Status":order_status})
                if db.order_status.find({"status":"Waiting"}):
                    return redirect(url_for('ordered_status'))
            return redirect(url_for('payment'))
    if 'username' in session:
        all_items = db.canteen.find()
        return render_template("users.html",all_items=all_items)
    return "session timeout"




@app.route("/ordered_status")
def ordered_status():
    if 'username' in session:
        username = session['username']
        order_details = db.order_details.find({"Username":username})
        return render_template("order_status.html",order_status=order_details)
    return redirect(url_for("session_timeout"))

    
@app.route("/food_orders", methods = ['GET','POST'])
def food_orders():
    if request.method == 'POST':
        order_status = request.form['order_status']
        order_number = request.form['order_number']
        o_number = int(order_number)
        db.order_details.update({"Order_Number":o_number},{"$set":{"Order_Status":order_status}})
        return redirect(url_for("food_orders"))
    food_order = db.order_details.find()
    return render_template("food_orders.html",food_order=food_order)


        
    



@app.route("/payment")
def payment():
    return "This is UPI Payment"


if __name__ == "__main__":
    app.debug = True
    app.run(port=3000)