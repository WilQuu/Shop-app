from flask import Flask, render_template, flash, redirect, request, session, logging, url_for
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = '!9m@S-dThyIlW[pHQbN^'

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:123@localhost/fk_shop_db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.permanent_session_lifetime = timedelta(minutes=5)
bootstrap = Bootstrap(app)

db = SQLAlchemy(app)
db.create_all()

@app.route('/')
@app.route('/index.html')
def home():
    return render_template("index.html")


@app.route("/login.html", methods=['POST', 'GET'])
def login():
    from models import User
    # Creating Login form object
    form = LoginForm(request.form)
    # verifying that method is post and form is valid
    if request.method == 'POST' and form.validate:
        # checking that user is exist or not by email
        user = User.query.filter_by(username=form.username.data).first()

        if user:
            # if user exist in database than we will compare our database hased password and password come from login form
            if check_password_hash(user.password, form.password.data):
                # if password is matched, allow user to access and save email and username inside the session
                flash('You have successfully logged in.', "success")

                session['logged_in'] = True

                session['username'] = user.username
                # After successful login, redirecting to home page
                return redirect(url_for('index.html'))

            else:

                # if password is in correct , redirect to login page
                flash('Username or Password Incorrect', "Danger")

                return redirect(url_for('login.html'))
    # rendering login page
    return render_template('login.html', form=form)


@app.route("/register.html", methods=['POST', 'GET'])
def register():
    from models import User
    # Creating RegistrationForm class object
    form = RegisterForm(request.form)

    # Cheking that method is post and form is valid or not.
    if request.method == 'POST' and form.validate():

        # if all is fine, generate hashed password
        hashed_password = generate_password_hash(form.password.data, method='sha256')

        # create new user model object
        new_user = User(

            name=form.name.data,

            username=form.username.data,

            email=form.email.data,

            password=hashed_password)

        # saving user object into data base with hashed password
        db.session.add(new_user)

        db.session.commit()

        flash('You have successfully registered', 'success')

        # if registration successful, then redirecting to login Api
        return redirect(url_for('login.html'))

    else:

        # if method is Get, than render registration form
        return render_template('register.html', form=form)


@app.route("/cart.html")
def cart():
    return render_template("cart.html")


@app.route("/product.html")
def product():
    return render_template("product.html")


@app.route("/product-details.html")
def product_details():
    return render_template("product-details.html")


if __name__ == '__main__':
    app.run(debug=True)
