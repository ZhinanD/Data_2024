import os
import pymysql.cursors
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_required, current_user
import db
from datetime import date
from auth import create_auth_blueprint
from db import get_db
from flask import Flask, render_template, request, session, url_for, redirect, flash

#Configure MySQL
mysql = MySQL()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        MYSQL_HOST='localhost',
        MYSQL_USER='root',
        MYSQL_PASSWORD='root',
        MYSQL_DB='newtest',
        MYSQL_PORT=3306,
    )
    app.config['MYSQL_DATABASE_SOCKET'] = None
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    db.init_app(app)
    auth_bp = create_auth_blueprint(login_manager)
    app.register_blueprint(auth_bp)
    app.add_url_rule('/', endpoint='auth.login')

    #  a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    

    @app.route('/findItem', methods=['GET', 'POST'])
    @login_required
    def findItem():
        pieces = []
        db = get_db()
        if request.method == 'POST':
            item_id = request.form['itemID']

            cursor = db.cursor(buffered=True)
            cursor.execute("SELECT * FROM item NATURAL JOIN piece WHERE item.itemID = %s", (item_id,))
            pieces = cursor.fetchall()
            cursor.close()

            if not pieces:
                flash("Item not found", "danger")

        return render_template('findItem.html', pieces=pieces)
    
    @app.route('/findOrder', methods=['GET', 'POST'])
    @login_required
    def findOrder():
        orders = []
        db = get_db()
        if request.method == 'POST':
            order_id = request.form['orderID'] 

            cursor = db.cursor(buffered=True)
            cursor.execute("SELECT * FROM item JOIN itemin ON item.itemID = itemin.itemID LEFT JOIN piece ON item.itemID = piece.itemID WHERE orderID = %s", (order_id,))
            orders = cursor.fetchall() 
            cursor.close()

            if not orders:
                flash("Order not found", "danger")

        return render_template('findOrder.html', orders=orders)
    
    @app.route('/orderHistory', methods=['GET', 'POST'])
    @login_required
    def orderHistory():
        orders = []
        db = get_db()
        cursor = db.cursor(buffered=True)
        cursor.execute(
    "SELECT * FROM ordered WHERE supervisor = %s OR client = %s", 
    (current_user.username, current_user.username)
)
        orders = cursor.fetchall() 
        cursor.close()
        if not orders:
            flash("No History Orders", "danger")
        return render_template('orderHistory.html', orders=orders)
    

    @app.route('/acceptDonation', methods=['GET', 'POST'])
    @login_required
    def acceptDonation():
        db = get_db()
        cursor = db.cursor()
        print(current_user.username)
        cursor.execute("SELECT roleID FROM act WHERE userName = %s", (current_user.username,))
        roleID = cursor.fetchone()
        roleID = int(roleID[0])
        print(roleID)
        cursor.close()

        if roleID != 5:
            flash("Only staff members can accept donations.", "danger")
            return redirect(url_for('auth.main'))
        
        cursor = get_db().cursor()
        cursor.execute("SELECT DISTINCT mainCategory, subCategory FROM category")
        data = cursor.fetchall()
        cursor.close()
        categories = {}
        for main, sub in data:
            if main not in categories:
                categories[main] = []
            categories[main].append(sub)

        if request.method == 'POST':
            donor_id = request.form['donorID']
            item_description = request.form['itemDescription']
            item_color = request.form['itemColor']
            isNew = request.form['isNew']
            hasPieces = request.form['hasPieces']
            itemMaterial = request.form['itemMaterial']
            mainCategory = request.form['mainCategory']
            subCategory = request.form['subCategory']
            has_pieces = request.form['hasPieces']
            pieces = request.form.getlist('pieces')

            cursor = db.cursor()

            try:
                cursor.execute("SELECT roleID FROM act WHERE userName = %s", (donor_id,))
                donor = cursor.fetchone()
                if not donor:
                    flash("Donor not found. Please check the Donor ID.", "danger")
                    return redirect(url_for('acceptDonation'))
                if int(donor[0]) != 6:
                    flash("This userID does not belong to a donor. Please check again.", "danger")
                    return redirect(url_for('acceptDonation'))
                cursor.execute(
                    "INSERT INTO item (iDescription, color, isNew, hasPieces, material, mainCategory, subCategory) VALUES (%s, %s, %s,%s, %s, %s,%s)",
                    (item_description, item_color, isNew, hasPieces, itemMaterial, mainCategory, subCategory)
                )
                db.commit()
                item_id = cursor.lastrowid 
                cursor.execute(
                    "INSERT INTO donatedBy (itemID, userName, donateDate) VALUES (%s, %s, %s)",
                    (item_id, donor_id, date.today())
                )
                db.commit()

                if has_pieces == "0": 
                    location = request.form['location']
                    room_id, shelf_id = location.split(',') if ',' in location else (None, None)
                    cursor.execute(
                        "INSERT INTO piece (itemID, pieceNum, roomNum, shelfNum) VALUES (%s, %s, %s, %s)",
                        (item_id, 0, room_id, shelf_id)
                    )
                elif has_pieces == "1":
                    pieces = request.form.getlist('pieces')
                    for piece in pieces:
                        room_id, shelf_id = piece.split(',') if ',' in piece else (None, None)
                        cursor.execute(
                            "INSERT INTO piece (itemID, roomNum, shelfNum) VALUES (%s, %s, %s)",
                            (item_id, room_id, shelf_id)
                        )

                db.commit()
                cursor.close()
                flash("Donation accepted and recorded successfully.", "success")
            except Exception as e:
                db.rollback()
                flash(f"An error occurred: {e}", "danger")
            finally:
                cursor.close()

        return render_template('acceptDonation.html', categories=categories)

    @app.route('/phoneNumbers', methods=['GET', 'POST'])
    @login_required
    def phoneNumbers():
        phones = []
        db = get_db()

        if request.method == 'POST':
            phone = request.form['phoneNumber']
            cursor = db.cursor(buffered=True)
            cursor.execute("INSERT INTO personphone(userName, phone) VALUES (%s, %s)", (current_user.username,phone,))
            db.commit()
            flash("Phone Number Added Successfully.", "success")
            cursor.close()

        cursor = db.cursor(buffered=True)
        cursor.execute("SELECT phone FROM personphone WHERE userName =  %s", (current_user.username,))
        phones = cursor.fetchall() 
        phones = [int(phone[0]) for phone in phones]
        cursor.close()
        if not phones:
            flash("No Phone Numbers", "danger")
        return render_template('phoneNumbers.html', phones=phones)
    


    @app.route('/addToCurrentOrder', methods=['GET', 'POST'])
    @login_required
    def addToCurrentOrder():
        db = get_db()
        cursor = db.cursor(buffered=True)
        cursor.execute("SELECT DISTINCT mainCategory, subCategory FROM category")
        categories_data = cursor.fetchall()
        categories = {}
        for main, sub in categories_data:
            if main not in categories:
                categories[main] = []
            categories[main].append(sub)

        items = []
        current_order = []

        if request.method == 'POST':
            order_id = request.form.get('orderID')
            if not order_id:
                flash("Order ID is required.", "danger")
                return redirect(url_for('addToCurrentOrder'))
            cursor.execute("SELECT COUNT(*) FROM ordered WHERE orderID = %s", (order_id,))
            order_exists = cursor.fetchone()[0]
            if not order_exists:
                flash(f"Order ID {order_id} does not exist. Please create the order first.", "danger")
                return redirect(url_for('addToCurrentOrder'))

            if 'filterItems' in request.form:
                main_category = request.form['mainCategory']
                sub_category = request.form['subCategory']

                cursor.execute(
                    """
                    SELECT itemID, iDescription, color, material
                    FROM item
                    WHERE mainCategory = %s AND subCategory = %s
                    AND itemID NOT IN (
                        SELECT itemID FROM itemin
                    )
                    """,
                    (main_category, sub_category)
                )
                items = cursor.fetchall()

            elif 'addItem' in request.form:
                item_id = request.form['itemID']
                try:
                    cursor.execute(
                        """
                        INSERT INTO itemin (orderID, itemID)
                        VALUES (%s, %s)
                        """,
                        (order_id, item_id)
                    )
                    db.commit()
                    flash("Item added to the order.", "success")
                except Exception as e:
                    db.rollback()
                    flash(f"Error adding item: {e}", "danger")
            cursor.execute(
                """
                SELECT item.itemID, iDescription, color, material
                FROM item
                JOIN itemin ON item.itemID = itemin.itemID
                WHERE orderID = %s
                """,
                (order_id,)
            )
            current_order = cursor.fetchall()

        cursor.close()

        return render_template(
            'addToCurrentOrder.html',
            categories=categories,
            items=items,
            current_order=current_order
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.run('127.0.0.1', 5000, debug=True)