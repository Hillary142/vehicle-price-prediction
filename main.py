from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask import Flask, request, render_template
import joblib
import numpy as np
import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'any-secret-key-you-choose'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# CREATE TABLE IN DB
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
# Line below only required once, when creating DB.
# db.create_all()


@app.route('/')
def home():
    return render_template("index.html", logged_in=current_user.is_authenticated)

def contact():
    return render_template("contact.html", logged_in=current_user.is_authenticated)

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if User.query.filter_by(email=request.form.get('email')).first():
            # User already exists
            flash("You've already signed up with that email, log in instead")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=hash_and_salted_password
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("prediction"))

    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        # Find user by email entered
        user = User.query.filter_by(email=email).first()

        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
        else:
            login_user(user)
            return redirect(url_for('prediction'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/prediction')
@login_required
def predict():
    print(current_user.name)
    return render_template("prediction.html", name=current_user.name, logged_in=True)

model  = joblib.load('Prediction_Model')

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def prediction():
    if request.method == 'POST':
        price = float(request.form['price'])
        kms = float(request.form['kms'])
        fuel = request.form['fuel']
        seller = request.form['seller']
        mode = request.form['mode']
        own = int(request.form['own'])
        year = request.form['year']
        current_year = datetime.datetime.now().year
        age = current_year - int(year)

        # fuel

        if (fuel == 'Hybrid'):
            fuel = 2
        elif (fuel == 'Diesel'):
            fuel = 1
        else:
            fuel = 0

        # seller

        if (seller == 'Dealer'):
            seller = 0
        else:
            seller = 1

        # mode

        if (mode == 'Manual'):
            mode = 0
        else:
            mode = 1

        prediction = model.predict([[price, kms, fuel, seller, mode, own, age]])
        final_price = round(prediction[0], 2)

        return render_template("prediction.html", prediction_text=" {}".format(final_price))

    else:
        return render_template("prediction.html")


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))





if __name__ == "__main__":
    app.run(debug=True)
