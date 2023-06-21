from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_bootstrap import Bootstrap

from flask_sqlalchemy import SQLAlchemy

from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

from wtforms.validators import DataRequired, URL
from wtforms import StringField, SubmitField, SelectField, PasswordField
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

Bootstrap(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)


# Cafe model
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    city_name = db.Column(db.String(250), nullable=False)
    map_url = db.Column(db.String(250), nullable=False)
    open_time = db.Column(db.String(250), nullable=False)
    closing_time = db.Column(db.String(250), nullable=False)
    coffee_rating = db.Column(db.String(10), nullable=False)
    wifi_rating = db.Column(db.String(10), nullable=False)
    power_outlet = db.Column(db.String(10), nullable=False)


# Create database tables
# db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Forms
# Login Form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# Registration From
class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')


# Add Cafe Form
class AddCafeForm(FlaskForm):
    cafe = StringField('Cafe name', validators=[DataRequired()])
    city = StringField('City name', validators=[DataRequired()])
    location = StringField('Cafe Location on Google Maps (URL)', validators=[DataRequired(), URL()])
    open_time = StringField('Open time e.g. 8AM', validators=[DataRequired()])
    closing_time = StringField('Closing time e.g. 8PM', validators=[DataRequired()])
    coffee_rating = SelectField('Coffee rating', choices=["☕️", "☕☕", "☕☕☕", "☕☕☕☕", "☕☕☕☕☕"],
                                validators=[DataRequired()])
    wifi_rating = SelectField('wifi rating', choices=["✘", "💪", "💪💪", "💪💪💪", "💪💪💪💪", "💪💪💪💪💪"],
                              validators=[DataRequired()])
    power_outlet = SelectField('Power Socket availability',
                               choices=["✘", "🔌", "🔌🔌", "🔌🔌🔌", "🔌🔌🔌🔌", "🔌🔌🔌🔌🔌"],
                               validators=[DataRequired()])
    submit = SubmitField('Submit')


# Search Cafe Form
class SearchCafeForm(FlaskForm):
    name = StringField("City or Cafe Name", validators=[DataRequired()])
    submit = SubmitField("Search")


# Routes
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('add_new_cafe'))
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        # Check if the email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.')
            return redirect(url_for('login'))

        # Create a new user
        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('add_new_cafe'))

    return render_template("register.html", form=form)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_new_cafe():
    form = AddCafeForm()
    if form.validate_on_submit():
        cafe_name = form.cafe.data
        city_name = form.city.data
        location = form.location.data
        open_time = form.open_time.data
        closing_time = form.closing_time.data
        coffee_rating = form.coffee_rating.data
        wifi_rating = form.wifi_rating.data
        power_outlet = form.power_outlet.data

        # Create a new cafe entry
        new_cafe = Cafe(
            name=cafe_name,
            city_name=city_name,
            map_url=location,
            open_time=open_time,
            closing_time=closing_time,
            coffee_rating=coffee_rating,
            wifi_rating=wifi_rating,
            power_outlet=power_outlet
        )

        db.session.add(new_cafe)
        db.session.commit()
        return jsonify(response={"success": "Successfully added the new cafe."})

    return render_template("add.html", form=form)


@app.route("/cafes")
def show_all_cafes():
    cafes = Cafe.query.all()
    return render_template("cafes.html", cafes=cafes)


@app.route('/search', methods=['GET', 'POST'])
def search_cafes():
    form = SearchCafeForm()
    if form.validate_on_submit():
        query = form.name.data

        # Perform the search query
        results = Cafe.query.filter(
            (Cafe.name.ilike(f'%{query}%')) | (Cafe.city_name.ilike(f'%{query}%'))
        ).all()
        return render_template('search.html', query=query, results=results, form=form)

    return render_template('search.html', form=form)


if __name__ == '__main__':
    app.run()
