from flask import Flask, render_template, flash, redirect, request, session, logging, url_for
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.sql import exists
from flask_bootstrap import Bootstrap
from forms import LoginForm, RegisterForm, PasswordForm, UsernameForm, SelectForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, logout_user, login_required, current_user, login_user, UserMixin
import psycopg2
from sqlalchemy import create_engine

try:
    conn = psycopg2.connect(database="postgres", user="postgres",
                            password="123", host="localhost")
    print("connected")
except:
    print("I am unable to connect to the database")
mycursor = conn.cursor()

app = Flask(__name__)
app.config['SECRET_KEY'] = '!9m@S-dThyIlW[pHQbN^'

app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://postgres:123@localhost/fk_shop_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.permanent_session_lifetime = timedelta(hours=5)
bootstrap = Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app)

admin = Admin(app, template_mode="bootstrap3")

main_order = []


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(256), unique=False)

    def __init__(self, username=None, email=None, password=None):
        self.username = username
        self.email = email
        self.password = password


class Categories(db.Model):
    id_category = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(50))
    category_sex = db.Column(db.CHAR)
    product = db.relationship('Products', backref='category')


class Brands(db.Model):
    id_brand = db.Column(db.Integer, primary_key=True)
    brand_name = db.Column(db.String(50), unique=True)
    product = db.relationship('Products', backref="brand")


class Products(db.Model):
    id_product = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(50), unique=True)
    description = db.Column(db.Text)
    price = db.Column(db.Integer)
    id_brand = db.Column(db.Integer, db.ForeignKey('brands.id_brand'))
    id_category = db.Column(db.Integer, db.ForeignKey('categories.id_category'))
    main_photo = db.Column(db.String(50))


class Orders(db.Model):
    id_order = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer)
    price = db.Column(db.Integer)


class UsersModelView(ModelView):
    def is_accessible(self):
        if session['username'] == 'admin':
            return True
        else:
            return False


class MyModelView(ModelView):
    def is_accessible(self):
        if session['username'] == 'admin' or session['username'] == 'moderator':
            return True
        else:
            return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('home'))


admin.add_view(UsersModelView(Users, db.session))
admin.add_view(UsersModelView(Orders,db.session))
admin.add_view(MyModelView(Products, db.session))


class Order():
    product = Products()

    def __init__(self, Products, quantity, total_price):
        self.product = Products
        self.quantity = quantity
        self.total_price = total_price


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route('/')
@app.route('/index.html')
def home():
    session['orders'] = []
    return render_template("index.html")


@app.route("/login", methods=['POST', 'GET'])
def login():
    # Creating Login form object
    form = LoginForm(request.form)
    # verifying that method is post and form is valid
    if request.method == 'POST' and form.validate:
        # checking that user is exist or not by email
        user = Users.query.filter_by(username=form.username.data).first()

        if user:
            # if user exist in database than we will compare our database hased password and password come from login form
            if check_password_hash(user.password, form.password.data):
                # if password is matched, allow user to access and save email and username inside the session
                # flash('You have successfully logged in.', "success")

                session['logged_in'] = True

                session['username'] = user.username

                login_user(user)
                # After successful login, redirecting to home page
                # if user.username == 'admin' or user.username =='moderator':
                #   return redirect(url_for('admin'))
                # else:
                return redirect(url_for('home'))

        else:

            # if password is in correct , redirect to login page
            flash('Username or Password Incorrect', "info")

            return redirect(url_for('product'))

    # rendering login page
    return render_template('login.html', form=form)


@app.route("/admin.html")
@login_required
def admin():
    return render_template("admin.html")


@app.route("/admin-panel.html")
@login_required
def admin_panel():
    return render_template("admin-panel.html")


@app.route("/register", methods=['POST', 'GET'])
def register():
    # Creating RegistrationForm class object
    form = RegisterForm(request.form)

    # Cheking that method is post and form is valid or not.
    if request.method == 'POST' and form.validate():

        # if all is fine, generate hashed password
        hashed_password = generate_password_hash(form.password.data, method='sha256')

        # create new user model object
        new_user = Users(

            username=form.username.data,

            email=form.email.data,

            password=hashed_password)

        # saving user object into data base with hashed password
        db.session.add(new_user)

        db.session.commit()

        # if registration successful, then redirecting to login Api
        return redirect(url_for('login'))

    else:

        # if method is Get, than render registration form
        return render_template('register.html', form=form)


@app.route('/logout/')
@login_required
def logout():
    # Removing data from session by setting logged_flag to False.
    logout_user()
    session['logged_in'] = False
    # redirecting to home page
    return redirect(url_for('home'))


@app.route("/buy-items")
@login_required
def buy_items():
    total_price = 0
    for item in main_order:
        total_price += item.product.price

    username = session['username']
    user = Users().query.filter_by(username=username).first()
    id_user = user.id

    new_order = Orders(id_user=id_user,price=total_price)

    db.session.add(new_order)
    db.session.commit()
    main_order.clear()

    return redirect(url_for('home'))


@app.route("/add-items/<product_name>/<quantity>", methods=['GET', 'POST'])
def add_items(product_name, quantity):
    product = Products().query.filter_by(product_name=product_name).first()
    if request.method == 'GET':
        print(product.price)
        total_price = quantity * product.price
        new_order = Order(product, quantity, total_price)
        main_order.append(new_order)

    return redirect(url_for('product_details', product_name=product_name))


@app.route("/cart", methods=['GET', 'POST'])
def cart():
    return render_template("cart.html", order=main_order)


@app.route("/product.html", methods=["POST", "GET"])
def product():
    form = SelectForm(request.form)
    data = Products.query.all()

    # mycursor.execute("select products.product_name, products.main_photo, products.price from Products")

    # data = mycursor.fetchall()

    return render_template("product.html", data=data, form=form)


@app.route("/product-details/<product_name>", methods=["POST", "GET"])
def product_details(product_name):
    form = SelectForm(request.form)
    product = Products.query.filter_by(product_name=product_name).first()

    return render_template("product-details.html", product=product, form=form)


@app.route("/new-password.html", methods=["GET", "POST"])
@login_required
def user_password_change():
    form = PasswordForm(request.form)
    if request.method == 'POST':
        if form.validate():
            user = current_user
            user.password = generate_password_hash(form.password.data, method='sha256')
            db.session.add(user)
            db.session.commit()
            flash("Password changed !", "INFO")
            return redirect(url_for('account'))

    return render_template('new-password.html', form=form)


@app.route("/account/")
@login_required
def account():
    return render_template('account.html')


@app.route("/new-username.html", methods=["GET", "POST"])
@login_required
def user_username_change():
    form = UsernameForm(request.form)
    if request.method == "POST":
        if form.validate():
            user = current_user
            exists = db.session.query(db.exists().where(Users.username == form.username.data)).scalar()
            session.pop('_flashes', None)
            if exists:
                flash("Username used, try new one!", "info")
                return redirect(url_for('account'))
            else:
                session.pop('_flashes', None)
                user.username = form.username.data
                db.session.add(user)
                db.session.commit()
                flash("Username changed!", "INFO")
                return redirect(url_for('account'))

    return render_template('new-username.html', form=form)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
