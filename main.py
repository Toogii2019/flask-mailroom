import os
import base64

from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from passlib.hash import pbkdf2_sha256

from model import Donation, Donor, User

app = Flask(__name__)
app.secret_key = os.environ.get("SEC_KEY", "You wont guess").encode()

def check_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in', False):
            return redirect(url_for('login'))
        else:
            return func(*args, **kwargs)
    return wrapper

@app.route('/create', methods=['GET','POST'])
@check_login
def create():
    if request.method == 'POST':
        if not request.form['donation'] or not request.form['name']:
            return render_template('add.jinja2', error="Please fill out all forms!")
        try:
            Donor(name=request.form['name']).save()
        except:
            return render_template('create.jinja2', error=f"Donor {request.form['name']} already exist!!!")
        new_donor = Donor.select().where(Donor.name == request.form['name']).get()
        try:
            Donation(value=int(request.form['donation']), donor=new_donor.id).save()
        except ValueError:
            Donor.get(Donor.name == new_donor.name).delete_instance()
            return render_template('create.jinja2', session=session, error=f"{request.form['donation']} not a valid donation amount!")
        donations = Donation.select()
        return render_template('donations.jinja2', msg=f"New Donor {new_donor.name} has been added successfully", donations=donations)
    else:
        return render_template('create.jinja2')

@app.route('/view_single_donor_info')
def single_donor_info():
    name = request.args.get("name", None)
    if not name:
        return render_template('single_donor.jinja2')
    try:
        donor = Donor.select().where(Donor.name == name).get()
    except Donor.DoesNotExist:
        return render_template('single_donor.jinja2', error=f"Donor {name} doesn't exist!!!")
    donations = Donation.select().where(Donation.donor == donor.id)

    return render_template('donations.jinja2', donations=donations)

@app.route('/logout')
def logout():
    if session.get('logged_in', False):
        del session['logged_in']
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in', False):
        return redirect(url_for('home'))
    if request.method == 'POST':
        try:
            user = User.select().where(User.user == request.form['username']).get()
        except User.DoesNotExist:
            return render_template('login.jinja2', error='Username or Password is incorrect!!!')
        if user and pbkdf2_sha256.verify(request.form['password'], user.password):
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            session['logged_in'] = False
            return render_template('login.jinja2', error='Username or Password is incorrect!!!', session=session)
    else:
        return render_template('login.jinja2', session=session)

@app.route('/')
@check_login
def home():
    return redirect(url_for('all'))

@app.route('/add', methods=['GET', 'POST'])
@check_login
def add():
    if request.method == 'POST':
        if not request.form['donation'] or not request.form['name']:
            return render_template('add.jinja2', error="Please fill out all forms!")
        try:
            donor = Donor.select().where(Donor.name == request.form['name']).get()
        except Donor.DoesNotExist:
            return render_template('add.jinja2', error=f"Donor {request.form['name']} Doesn't Exist in Database!!!")
        try:
            donate = Donation(value=int(request.form['donation']), donor=donor.id)
        except ValueError:
            return render_template('add.jinja2', session=session, error=f"{request.form['donation']} is not a valid donation amount!")
        donate.save()
        return redirect(url_for('all'))
    elif request.method == 'GET':
        return render_template('add.jinja2', session=session)

@app.route('/donations/')
@check_login
def all():
    donations = Donation.select()
    return render_template('donations.jinja2', donations=donations, session=session)
    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 6738))
    app.run(host='0.0.0.0', port=port)

