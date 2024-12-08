import mysql.connector
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db
from flask_login import LoginManager, UserMixin
from flask_login import login_user, logout_user, current_user, login_required
# Define your User class that extends UserMixin
class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username
def create_auth_blueprint(login_manager: LoginManager):
    bp = Blueprint('auth', __name__, url_prefix='/auth')

    #login_manager.init_app(current_app)

    @login_manager.user_loader
    def load_user(user_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM person WHERE cid = %s', (user_id,))
        columns = [column[0] for column in cursor.description]
        res = cursor.fetchone()
        res_dict = dict(zip(columns, res))
        if len(res_dict) == 0:
            return None
        else:
            user_id = res_dict.get("cid")
            username = res_dict.get("userName")
            return User(user_id, username)



    @bp.route('/register', methods=('GET', 'POST'))
    def register():
        if request.method == 'POST':
            username = request.form['userName']
            password = request.form['password']
            first_name = request.form['fname']
            last_name = request.form['lname']
            email = request.form['email']
            person_type = request.form['personType']
            db = get_db()
            print(db)
            error = None
            cursor = db.cursor()
            cursor.execute("SELECT 1 FROM person WHERE userName = %s", (username,))
            existing_user = cursor.fetchone()
            if not username:
                error = 'Username is required.'
            elif not password:
                error = 'Password is required.'
            elif (not first_name) or (not last_name):
                error = 'Name is required.'
            elif not email:
                error = 'Email is required.'
            elif not person_type:
                error = 'Person type is required.'
            elif existing_user:
                error = f"User {username} is already registered."

            if error is None:
                print("here")
                try:
                    
                    cursor.execute(
                        "INSERT INTO person (fname, lname, userName, password, email) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (first_name, last_name, username, generate_password_hash(password), email),
                    )
                    db.commit()

                    cursor.execute(
                        "INSERT INTO act (userName, roleID) "
                        "VALUES (%s, (SELECT roleID FROM role WHERE rDescription = %s))",
                        (username, person_type),
                    )
                    db.commit()
                except mysql.connector.IntegrityError:
                    error = f"User {username} is already registered."
                else:
                    flash('Registration Successful! Please Log In.', 'success')
                    return redirect(url_for("auth.login"))

            flash(error)

        return render_template('auth/register.html')



    @bp.route('/login', methods=('GET', 'POST'))
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('auth.main'))

        if request.method == 'POST':
            username = request.form['userName']
            password = request.form['password']
            db = get_db()
            cursor = db.cursor()
            error = None
            cursor.execute(
                'SELECT * FROM person WHERE userName = %s', (username,)
            )
            columns = [column[0] for column in cursor.description]
            print(columns)
            user = cursor.fetchone()
            if user is None:
                error = 'Non-existing username'
            elif not check_password_hash(user[2], password):
                error = 'Incorrect password.'
            if error is None:
                res_dict = dict(zip(columns, user))
                user_id = res_dict.get("cid")
                username = res_dict.get("userName")
                wrapped_user=User(user_id, username)
                login_user(wrapped_user)
                return redirect(url_for('auth.main'))
            flash(error)

        return render_template('auth/login.html')

    @bp.route('/logout',methods=('GET', 'POST'))
    def logout():
        logout_user()
        return redirect(url_for('auth.login'))
    
    @bp.route('/main',methods=('GET', 'POST'))
    @login_required
    def main():
        return render_template('auth/main.html', username=current_user.username)

    return bp


