from flask import Flask, render_template, session, url_for, redirect, flash, request
from app import app
import re
import pymysql
import mysql.connector
import ctypes


mydb = mysql.connector.connect(host='localhost', user='root', passwd='Hundo978!', auth_plugin='mysql_native_password', database="cs4400spring2020")
mycursor = mydb.cursor(buffered=True)

'''
-------------------------------------------------------------------------------------
pages
-------------------------------------------------------------------------------------
'''

@app.route('/')
@app.route('/home.html')
def home():
    return render_template('home.html', title='Home')

@app.route('/login.html', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate_login(username, password):
            session['username'] = username
            
            # get the uer type
            sql_Q =(f'SELECT username, userType FROM login_classifier WHERE username = "{username}"')
            mycursor.execute(sql_Q)
            result = mycursor.fetchone()
            print("user type: " , result[1])
            session['user_type'] = result[1]

            flash("Logged in")
            return redirect('/about.html')
        else:
            flash("Log in denied")
    return render_template('login.html', title='Login')

@app.route('/about.html')
def about():
    return render_template('about.html', title='About')

@app.route('/register.html', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        password = request.form['password']
        balance = request.form['balance']
        balance = emptyStringToNone(balance)
        user_type = request.form['user_type']
        if register_user(username, email, firstName, lastName, password, balance, user_type):
            flash("Registered")
            return redirect('/login.html')
        else:
            flash("Registration Invalid")
    return render_template('register.html', title='Register')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/home.html')
    # NOTE: cookies remian between sessions unless logged out, 
    # you can also change the key varibale in __init__.py to clear session cookies

@app.route('/screen4.html', methods=['POST', 'GET'])
def screen4():
    if request.method == 'POST':
        if request.form['submit_button'] == 'Filter':
            buildingName = request.form['buildingName']
            buildingName = emptyStringToNone(buildingName)
            buildingTagContain = request.form['buildingTagContain']
            buildingTagContain = emptyStringToNone(buildingTagContain)
            stationName = request.form['stationName']
            stationName = emptyStringToNone(stationName)
            minCapacity = request.form['capacityMin']
            minCapacity = emptyStringToNone(minCapacity)
            maxCapacity = request.form['capacityMax']
            maxCapacity = emptyStringToNone(maxCapacity)
            resultTable = filter_building_station(buildingName, buildingTagContain, stationName, minCapacity, maxCapacity)
            return render_template('screen4.html', title='Screen4', data = resultTable)
        
        elif request.form['submit_button'] == 'Create Building':
            return redirect('/screen5.html')

        elif request.form['submit_button'] == 'Update Building':
            rowBuildingName = request.form.get('rowBuildingName')
            return redirect(url_for('screen6', building=rowBuildingName)) 

        elif request.form['submit_button'] == 'Delete Building':
            rowBuildingName = request.form.get('rowBuildingName')
            if rowBuildingName != "" and rowBuildingName != "None" and delete_building(rowBuildingName):
                print("DELETED BUILDING") 
            return render_template('screen4.html', title='Screen4')

        elif request.form['submit_button'] == 'Create Station':
            return redirect('/screen7.html')

        elif request.form['submit_button'] == 'Update Station':
            rowBuildingName = request.form.get('rowBuildingName')
            # rowBuildingTags = request.form.get('rowBuildingTags')
            rowStation = request.form.get('rowStation')
            rowCapacity = request.form.get('rowCapacity')
            # rowFoodTrucks = request.form.get('rowFoodTrucks')
            if rowStation != "None" and rowStation != "": # prevents a row with None station or no row being selected form going to STATION UPDATE page
                return redirect(url_for('screen8', building=rowBuildingName, station = rowStation, capacity = rowCapacity, ))
            else:
                print("station is null!!!!")
                pass
        elif request.form['submit_button'] == 'Delete Station':
            rowStation = request.form.get('rowStation')
            if rowStation != "" and rowStation != "None" and delete_station(rowStation):
                print("DELETED STATION")  
            return render_template('screen4.html', title='Screen4')

    return render_template('screen4.html', title='Screen4')

@app.route('/screen5.html', methods=['POST', 'GET'])
def screen5():
    if request.method == 'POST':
        #create building request
        buildingName = request.form['buildingName']    
        description = request.form['description']
        tag = request.form['tag']
        tags = tag.split(',')
        if buildingName != "" and description != "" and tag != "" and create_building(buildingName, description):
            print("BUILDING CREATED")
            for tag in tags:
                add_building_tag(buildingName, tag)
            print("TAG(S) ADDED")
        else:
            return render_template('screen5.html', title='Screen5', buildingName = buildingName, description = description)
    return render_template('screen5.html', title='Screen5')

@app.route('/screen6.html', methods=['POST', 'GET'])
def screen6():
    if request.method == 'GET':
        gotBuildingName = request.args.get('building')
        result = get_building_info(gotBuildingName)
        if not result:
            result = ""
        else:
            result = result[0][0]
        resultTable = get_tags(gotBuildingName)
        return render_template('screen6.html', title='Screen6', buildingName = gotBuildingName, data = resultTable, description = result)
    if request.method == 'POST':
        if request.form['submit_button'] == 'Add Tag':
            buildingName = request.form['buildingName']
            newBuildingName = request.form['newBuildingName']
            description = request.form['description']
            tag = request.form['tag']
            if buildingName != "" and tag != "" and add_building_tag(buildingName, tag):
                print("TAG ADDED")
                result = get_building_info(buildingName)
                if not result:
                    result = ""
                else:
                    result = result[0][0]
                resultTable = get_tags(buildingName) #BUG: possibly fix the way description is got cause it will undo changes if ADD TAG is called
                return render_template('screen6.html', title='Screen6', data = resultTable, buildingName = buildingName, newBuildingName = newBuildingName, description = description)
            else:
                resultTable = get_tags(buildingName)
                return render_template('screen6.html', title='Screen6', data = resultTable, buildingName = buildingName, newBuildingName = newBuildingName, description = description)


        elif request.form['submit_button'] == 'Delete Tag':
            buildingName = request.form['buildingName']
            newBuildingName = request.form['newBuildingName']
            description = request.form['description']
            tag = request.form['tag']
            if buildingName != "" and tag != "" and delete_building_tag(buildingName, tag): 
                print("TAG DELETED")
                result = get_building_info(buildingName)
                if not result:
                    result = ""
                else:
                    result = result[0][0]
                resultTable = get_tags(buildingName)
                return render_template('screen6.html', title='Screen6', data = resultTable, buildingName = buildingName, newBuildingName = newBuildingName, description = result)
            else:
                resultTable = get_tags(buildingName)
                return render_template('screen6.html', title='Screen6', data = resultTable, buildingName = buildingName, newBuildingName = newBuildingName, description = description)
        
        elif request.form['submit_button'] == 'Get Tags And Description':
            buildingName = request.form['buildingName']
            newBuildingName = request.form['newBuildingName']
            description = request.form['description']
            tag = request.form['tag']
            result = get_building_info(buildingName)
            if not result:
                result = ""
            else:
                result = result[0][0]
            resultTable = get_tags(buildingName)
            return render_template('screen6.html', title='Screen6', data = resultTable, buildingName = buildingName, newBuildingName = newBuildingName, description = result)

        else: #update building request
            buildingName = request.form['buildingName']
            newBuildingName = request.form['newBuildingName']     
            description = request.form['description']
            if buildingName != "" and description != "" and update_building(buildingName, newBuildingName, description):
                print("BUILDING UPDATED")
            else:
                return render_template('screen6.html', title='Screen6', buildingName = buildingName, newBuildingName = newBuildingName, description = description)
    return render_template('screen6.html', title='Screen6')

@app.route('/screen7.html', methods=['POST', 'GET'])
def screen7():
    if request.method == 'POST':
        if request.form['submit_button'] == 'Create Station':
            stationName = request.form['stationName']  
            capacity = request.form['capacity']
            sponsBuilding = request.form.get('sponsBuilding')
            if stationName != "" and capacity != "" and sponsBuilding != "" and create_station(stationName, sponsBuilding, capacity):
                print("STATION CREATED")
            else:
                print("uhhhh")
                buildings = get_available_buildings()
                return render_template('screen7.html', title='Screen7', stationName = stationName,  data = buildings)
        else:
            stationName = request.form['stationName']    
            capacity = request.form['capacity']
            sponsBuilding = request.form.get('sponsBuilding')
            buildings = get_available_buildings()
            return render_template('screen7.html', title='Screen7', stationName = stationName,  data = buildings)
    return render_template('screen7.html', title='Screen7')

@app.route('/screen8.html', methods=['POST', 'GET'])
def screen8():
    if request.method == 'GET':
        gotBuildingName = request.args.get('building')
        gotStation = request.args.get('station')
        gotCapacity = request.args.get('capacity')

        buildings = get_available_buildings()
        return render_template('screen8.html', title='Screen8', stationName = gotStation, currSponsBuilding = gotBuildingName, capacity = gotCapacity, data = buildings)
   
    if request.method == 'POST':
        print("text1")  
        if request.form['submit_button'] == 'Update Station':
            stationName = request.form.get('stationNameAccess') # NOTE: you get station from here becuase the regular station is disabled from access 
            capacity = request.form['capacity']
            sponsBuilding = request.form.get('sponsBuilding')
            if stationName != "" and capacity != "" and sponsBuilding != "" and update_station(stationName, capacity, sponsBuilding):
                print("STATION UPDATED")
                return render_template('home.html')
            else:
                print("STATION NOT UPDATED")
                buildings = get_available_buildings()
                return render_template('screen8.html', title='Screen8', stationName = stationName,  currSponsBuilding = sponsBuilding, data = buildings, capacity = capacity)
    return render_template('screen8.html', title='Screen8')

@app.route('/screen9.html', methods=['POST', 'GET'])
def screen9():
    if request.method == 'POST':
        if request.form['submit_button'] == 'Filter':
            foodName = request.form.get('foodName')
            sort = 'name' # can be: 'name', 'menuCount', 'purchaseCount'
            order = 'ASC' # can be: 'ASC', 'DESC'

            foodNamesList = get_food_names()
            foodNamesList.insert(0, "")
            resultTable = filter_food(foodName, sort, order)

            return render_template('screen9.html', title='Screen9', data = resultTable, foodNames = foodNamesList)

        elif request.form['submit_button'] == 'Delete Food':
            rowFoodName = request.form.get('rowFoodName')
            if rowFoodName != "" and rowFoodName != "None" and delete_food(rowFoodName):
                print("DELETED FOOD") 
            foodNamesList = get_food_names()
            foodNamesList.insert(0, "")
            return render_template('screen9.html', title='Screen9', foodNames = foodNamesList)
        
        elif request.form['submit_button'] == 'Create Food':
            return redirect(url_for('screen10'))

    foodNamesList = get_food_names()
    foodNamesList.insert(0, "")
    return render_template('screen9.html', title='Screen9', foodNames = foodNamesList)

@app.route('/screen10.html', methods=['POST', 'GET'])
def screen10():
    if request.method == 'POST':
        if request.form['submit_button'] == 'Create Food':
            foodName = request.form['foodName']  
            if create_food(foodName):
                print("FOOD CREATED")
    return render_template('screen10.html', title='Screen10')

@app.route('/screen11.html')
def screen11():
    return render_template('screen11.html', title='Screen11')

@app.route('/screen12.html')
def screen12():
    return render_template('screen12.html', title='Screen12')

@app.route('/screen13.html')
def screen13():
    return render_template('screen13.html', title='Screen13')

@app.route('/screen14.html')
def screen14():
    return render_template('screen14.html', title='Screen14')

@app.route('/screen15.html')
def screen15():
    return render_template('screen15.html', title='Screen15')

@app.route('/screen16.html')
def screen16():
    return render_template('screen16.html', title='Screen16')

@app.route('/screen17.html')
def screen17():
    return render_template('screen17.html', title='Screen17')

@app.route('/screen18.html')
def screen18():
    return render_template('screen18.html', title='Screen18')

@app.route('/screen19.html')
def screen19():
    return render_template('screen19.html', title='Screen19')



'''
-------------------------------------------------------------------------------------
functional methods
-------------------------------------------------------------------------------------
'''
#validates the login credentials
def validate_login(username, password): 
    global mycursor
    sql_Q = (f'call login("{username}", "{password}")') # calls the login() procedure
    mycursor.execute(sql_Q)
    return 1 == mycursor._affected_rows

# TODO: possibly imporve error notification to end user
# SCREEN 2 (validates the registeration)
def register_user(username, email, firstName, lastName, password, balance, user_type): 
    global mycursor
    sqlErrorOccured = False
    try:
        mycursor.callproc('register',args=(username, email, firstName, lastName, password, balance, user_type))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        sqlErrorOccured = True
    else:
        mydb.commit()
    finally:
        if sqlErrorOccured:
            return False
        else:
            return True

# SCREEN 4 (filters buildings and stations)
def filter_building_station(buildingName=None, buildingTagContain=None, stationName=None, minCapacity=None, maxCapacity=None): 
    global mycursor
    sqlErrorOccured = False
    try:
        mycursor.callproc('ad_filter_building_station',args=(buildingName, buildingTagContain, stationName, minCapacity, maxCapacity ))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        sqlErrorOccured = True
    else:
        #mydb.commit()
        pass
    finally:
        if sqlErrorOccured:
            print("failed")
            return None
        else:
            #return 1 == mycursor._affected_rows
            sql_Q = 'SELECT * FROM cs4400spring2020.ad_filter_building_station_result'
            mycursor.execute(sql_Q)
            result = mycursor.fetchall()
            for a in result:
                print(a)
            return result

# SCREEN 5 (creates building)
def create_building(buildingName, description): 
    global mycursor
    sqlErrorOccured = False
    try:
        mycursor.callproc('ad_create_building',args=(buildingName, description))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        Mbox('WARNING', "Building already exists", 0)
        sqlErrorOccured = True
    else:
        mydb.commit()
    finally:
        if sqlErrorOccured:
            return False
        else:
            return True

def add_building_tag(buildingName, tag): 
    global mycursor
    sqlErrorOccured = False
    try:
        mycursor.callproc('ad_add_building_tag',args=(buildingName, tag))
        mydb.commit()
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        Mbox('WARNING', "Tag already exists", 0)
        sqlErrorOccured = True
    finally:
        if sqlErrorOccured:
            return False
        else:
            return True

def delete_building_tag(buildingName, tag): 
    global mycursor
    sqlErrorOccured = False
    try:
        mycursor.callproc('ad_remove_building_tag',args=(buildingName, tag))
        mydb.commit()
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        Mbox('WARNING', "Tag doesn't exist", 0)
        sqlErrorOccured = True
    finally:
        if sqlErrorOccured:
            return False
        else:
            return True

def get_tags(buildingName): 
    global mycursor
    sqlErrorOccured = False
    try:
        sql_Q = (f'call ad_view_building_tags("{buildingName}")')
        mycursor.execute(sql_Q)
        #mycursor.callproc('ad_view_building_tags',args=(buildingName))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        sqlErrorOccured = True
    else:
        mydb.commit()
        pass
    finally:
        if sqlErrorOccured:
            return None
        else:
            #return 1 == mycursor._affected_rows
            sql_Q = 'SELECT * FROM cs4400spring2020.ad_view_building_tags_result'
            mycursor.execute(sql_Q)
            result = mycursor.fetchall()
            for a in result:
                print(a)
            return result

def get_building_info(buildingName): 
    global mycursor
    sqlErrorOccured = False
    try:
        sql_Q = (f'call ad_view_building_general("{buildingName}")')
        mycursor.execute(sql_Q)
        # mycursor.callproc('call ad_view_building_general',args=(buildingName))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        sqlErrorOccured = True
    else:
        mydb.commit()
        pass
    finally:
        if sqlErrorOccured:
            return None
        else:
            #return 1 == mycursor._affected_rows
            sql_Q = 'SELECT description FROM cs4400spring2020.ad_view_building_general_result'
            mycursor.execute(sql_Q)
            result = mycursor.fetchall()
            for a in result:
                print(a)
            return result

#Screen 6 (update building)
def update_building(buildingName, newBuildingName, description): 
    global mycursor
    sqlErrorOccured = False
    try:
        if newBuildingName == "":
            mycursor.callproc('ad_update_building',args=(buildingName, buildingName, description))
        else:
            mycursor.callproc('ad_update_building',args=(buildingName, newBuildingName, description))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        Mbox('WARNING', "Building doesn't exist", 0)
        sqlErrorOccured = True
    else:
        mydb.commit()
    finally:
        if sqlErrorOccured:
            return False
        else:
            return True

# Screen 7 (create station)
def create_station(stationName, sponsBuilding, capacity): 
    global mycursor
    sqlErrorOccured = False
    try:
        mycursor.callproc('ad_create_station',args=(stationName, sponsBuilding, capacity))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        Mbox('WARNING', "Station already exists", 0)
        sqlErrorOccured = True
    else:
        mydb.commit()
    finally:
        if sqlErrorOccured:
            return False
        else:
            return True

def get_available_buildings(): 
    global mycursor
    sqlErrorOccured = False
    try:
        sql_Q = "call ad_get_available_building()"
        mycursor.execute(sql_Q)
        #mycursor.callproc('ad_view_building_tags',args=(buildingName))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        sqlErrorOccured = True
    else:
        mydb.commit()
        pass
    finally:
        if sqlErrorOccured:
            return None
        else:
            #return 1 == mycursor._affected_rows
            sql_Q = 'SELECT * FROM cs4400spring2020.ad_get_available_building_result'
            mycursor.execute(sql_Q)
            result = mycursor.fetchall()
            for a in result:
                print(a)
            return result

def get_station_info(stationName): 
    global mycursor
    sqlErrorOccured = False
    try:
        sql_Q = (f'call ad_view_station("{stationName}")')
        mycursor.execute(sql_Q)
        # mycursor.callproc('call ad_view_building_general',args=(buildingName))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        sqlErrorOccured = True
    else:
        mydb.commit()
        pass
    finally:
        if sqlErrorOccured:
            return None
        else:
            #return 1 == mycursor._affected_rows
            sql_Q = 'SELECT * FROM cs4400spring2020.ad_view_station_result'
            mycursor.execute(sql_Q)
            result = mycursor.fetchall()
            for a in result:
                print(a)
            return result

# Screen 8
def update_station(stationName, capacity, buildingName): 
    global mycursor
    sqlErrorOccured = False
    try:
        mycursor.callproc('ad_update_station',args=(stationName, capacity, buildingName))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        Mbox('WARNING', "Station doesn't exist??", 0)
        sqlErrorOccured = True
    else:
        mydb.commit()
    finally:
        if sqlErrorOccured:
            return False
        else:
            return True

def delete_building(buildingName): 
    global mycursor
    sqlErrorOccured = False
    try:
        sql_Q = (f'call ad_delete_building("{buildingName}")')
        mycursor.execute(sql_Q)

        # mycursor.callproc('ad_delete_building',args=(buildingName))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        Mbox('WARNING', "Building doesn't exist or can't be deleted due to constraint", 0)
        sqlErrorOccured = True
    else:
        mydb.commit()
    finally:
        if sqlErrorOccured:
            return False
        else:
            return True

def delete_station(stationName): 
    global mycursor
    sqlErrorOccured = False
    try:
        sql_Q = (f'call ad_delete_station("{stationName}")')
        mycursor.execute(sql_Q)

        # mycursor.callproc('ad_delete_station',args=(stationName))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        Mbox('WARNING', "Station doesn't exist or can't be deleted due to constraint", 0)
        sqlErrorOccured = True
    else:
        mydb.commit()
    finally:
        if sqlErrorOccured:
            return False
        else:
            return True

# screen 9
def delete_food(foodName): 
    global mycursor
    sqlErrorOccured = False
    try:
        sql_Q = (f'call ad_delete_food("{foodName}")')
        mycursor.execute(sql_Q)

    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        Mbox('WARNING', "Food doesn't exist or can't be deleted due to constraint", 0)
        sqlErrorOccured = True
    else:
        mydb.commit()
    finally:
        if sqlErrorOccured:
            return False
        else:
            return True

def filter_food(foodName, sort, order): 
    global mycursor
    sqlErrorOccured = False
    try:
        # print(f'foodName={foodName}, sort={sort}, order={order}')
        # mycursor.callproc('ad_filter_food',args=(foodName, sort, order))

        mycursor.callproc('ad_filter_food',args=(foodName, sort, order))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        sqlErrorOccured = True
    else:
        mydb.commit()
        pass
    finally:
        if sqlErrorOccured:
            print("failed")
            return None
        else:
            #return 1 == mycursor._affected_rows
            sql_Q = 'SELECT * FROM cs4400spring2020.ad_filter_food_result'
            mycursor.execute(sql_Q)
            result = mycursor.fetchall()
            for a in result:
                print(a)
            return result

def get_food_names(): 
    global mycursor
    sqlErrorOccured = False
    try:
        foodName = None
        sort = 'name'
        order = 'ASC'
        mycursor.callproc('ad_filter_food',args=(foodName, sort, order))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        sqlErrorOccured = True
    else:
        mydb.commit()
        pass
    finally:
        if sqlErrorOccured:
            print("failed")
            return None
        else:
            #return 1 == mycursor._affected_rows
            sql_Q = 'SELECT foodName FROM cs4400spring2020.ad_filter_food_result'
            mycursor.execute(sql_Q)
            result = mycursor.fetchall()
            for a in result:
                print(a)
            return result

# Screen 10 
def create_food(foodName): 
    global mycursor
    sqlErrorOccured = False
    try:
        sql_Q = (f'call ad_create_food("{foodName}")')
        mycursor.execute(sql_Q)

        # mycursor.callproc('ad_create_food',args=(foodName))
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)
        Mbox('WARNING', "Food already exists", 0)
        sqlErrorOccured = True
    else:
        mydb.commit()
    finally:
        if sqlErrorOccured:
            return False
        else:
            return True
'''
-------------------------------------------------------------------------------------
 technical methods
 -------------------------------------------------------------------------------------
'''

def emptyStringToNone(s):
    if s is '':
        return None
    return str(s)

def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

@app.before_request #runs this request prior to each page request
def require_login():
    non_logged_routes = ['home', 'login', 'register']
    do_not_allow_relog = ['login']
    customer_only_routes = []
    admin_only_routes = []
    manager_only_routes = []
    staff_only_routes = []

    if request.endpoint not in non_logged_routes and 'username' not in session:
        flash('Please log in first.', 'error')
        return redirect('/login.html')

    #prevents relogging in while active session
    if request.endpoint in do_not_allow_relog and 'username' in session:
        flash('Cannot relog until logged out', 'error')
        print("CANNOT RELOG UNTIL LOGGED OUT")
        return redirect('/home.html')
    
    # restricts pages based on user type
    elif 'user_type' in session:
        if request.endpoint in customer_only_routes and not(session['user_type'] == 'Customer' or session['user_type'] == 'Admin-Customer' or session['user_type'] == 'Staff-Customer' or session['user_type'] == 'Manager-Customer'):
            print("ONLY ACCESSIBLE FOR CUSTOMERS")
            return redirect(url_for('home'))
        
        if request.endpoint in admin_only_routes and not(session['user_type'] == 'Admin' or session['user_type'] == 'Admin-Customer'):            
            print("ONLY ACCESSIBLE FOR ADMINS")
            return redirect(url_for('home'))

        if request.endpoint in admin_only_routes and not(session['user_type'] == 'Manager' or session['user_type'] == 'Manager-Customer'):            
            print("ONLY ACCESSIBLE FOR MANAGER")
            return redirect(url_for('home'))

        if request.endpoint in admin_only_routes and not(session['user_type'] == 'Staff' or session['user_type'] == 'Staff-Customer'):            
            print("ONLY ACCESSIBLE FOR STAFF")
            return redirect(url_for('home'))


