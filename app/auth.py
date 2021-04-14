import os
from flask import Flask, render_template, redirect, request, session, json, jsonify
from flask import Blueprint, redirect, render_template, flash, request, session, url_for
from flask_login import login_required, logout_user, current_user, login_user


from app import db, login_manager, app
from app.forms import LoginForm, SignupForm, PostForm
from app.models import User, Post


# Blueprint Configuration
auth_bp = Blueprint(
    'auth_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Log-in page for registered users.

    GET requests serve Log-in page.
    POST requests validate and redirect user to dashboard.
    """
    # Bypass if user is logged in
    if current_user.is_authenticated:
        return redirect(url_for('newsfeed'))

    form = LoginForm()
    # Validate login attempt
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(password=form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(url_for('newsfeed'))
        flash('Invalid username/password combination')
        return redirect(url_for('login'))
    return render_template('login.html', title='Log in.', form=form)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    User sign-up page.

    GET requests serve sign-up page.
    POST requests validate form & user creation.
    """
    if current_user.is_authenticated:
        print('Checking if current user is_authenticated')
        print('current_user :', current_user)
        return redirect(url_for('newsfeed'))

    form = SignupForm()
    # if request.method == 'POST':
    #     #This is to help store files in b'' and save directly to db
    #     pic = request.files['photo'].read()

    if form.validate_on_submit():
        print('validating...')
        user = User(name=form.name.data, email=form.email.data) #, photo=pic
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account Succefully Created!')
        login_user(user)
        return redirect(url_for('newsfeed'))
    return render_template('sign-up.html', title='Create an Account.', form=form)


@login_manager.user_loader
def load_user(user_id):
    """Check if user is logged-in on every page load."""
    if user_id is not None:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('You must be logged in to view that page.')
    return redirect(url_for('auth_bp.login'))

@app.route('/logout')
def logout():
    # codeOlam modified this code function now working
    logout_user()
    return redirect('/')