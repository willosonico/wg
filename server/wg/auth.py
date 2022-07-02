# auth.py

import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User
from . import db
import redis

auth = Blueprint('auth', __name__)
redis = redis = redis.StrictRedis.from_url(os.environ['REDIS_URL'])

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password): 
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.dashboard'))

@auth.route('/signup')
def signup():
    if os.environ['DEVELOPMENT'] == '1':
        return render_template('signup.html')
    else:
        return redirect('/login')

@auth.route('/preview/<readerId>')
@login_required
def preview(readerId):
    try:
        # reading from redis
        key = str(readerId)
        img1_bytes_ = redis.get(key)

        response = make_response(img1_bytes_)
        response.headers['Content-Type'] = 'image/jpeg'
    except Exception as e:
        print(e)
        filename = 'preview_not_available.png'
        return send_file(filename, mimetype='image/png')

    return response

@auth.route('/signup', methods=['POST'])
def signup_post():
    if os.environ['DEVELOPMENT'] == '0':
        return redirect('/login')
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again  
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))