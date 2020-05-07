from flask import Flask, render_template, session, url_for, redirect, flash, request
import re
import pymysql
import mysql.connector

mydb = mysql.connector.connect(host='localhost', user='root', passwd='Hundo978!', auth_plugin='mysql_native_password', database="cs4400spring2020")
mycursor = mydb.cursor(buffered=True)

app = Flask(__name__)
app.secret_key = "key"

@app.route('/') # main starting page
def home():
    return render_template('base.html')

@app.route('/login', methods=['POST', 'GET']) # login page
def login():
    return render_template("login.html")

@app.route('/register', methods=['POST', 'GET'])
def register():
    return render_template("register.html")

if __name__ == "__main__":
    if mydb:
        print("I REFUSE TO TAKE THE FINAL!: connection successful")
    else:
        print("GET THIS TO WORK!: connection failed")

    #app.run(debug=True, host='0.0.0.0', port=3000)

# export FLASK_APP=foodtruck.py
# set FLASK_APP=foodtruck.py