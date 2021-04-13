import os
from flask import Flask, render_template, redirect, request, session, json, jsonify
from werkzeug.utils import secure_filename
from config import Config


import pandas as pd
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy
from pandas.io import sql
from sqlalchemy import create_engine

#code added by codeOlam
from flask import Blueprint, redirect, render_template, flash, request, session, url_for
from flask_login import login_required, current_user
from app import db, app
from app.forms import PostForm, FollowUnfollowForm
from app.models import User, Post


# APP_ROOT = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = '/static/photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_TYPE'] = 'filesystem'


e = []

@app.route('/')
def index():
    # recommendation_process(e)
    return redirect('login')


@app.route('/news_feed', methods=['GET', 'POST'])
def newsfeed():
    if current_user.is_authenticated:
        #codeOlam fixed news feed view function
        session['user'] = current_user.name
        #all users
        users = get_users()
        form = PostForm()
        #Get all post to news feeds
        newsfeeds = Post.query.all()

        #ToDo: send all new post to update pd dataframe

        #get id of clicked users
        #Todo: select post for user based on following user
        FUform = FollowUnfollowForm()
        return render_template('newsfeed.html', 
                            form=form, 
                            FUform=FUform,
                            newsfeeds=newsfeeds, 
                            users=users)
    else:
        return redirect(url_for('login'))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/add_post', methods=['POST'])
def add_post():
    """
    Save post to db matching it with user id (one-many-relationship)
    """
    if current_user.is_authenticated:
        user_id = current_user.id # get user id

        form = PostForm()
        if form.validate_on_submit():
            new_post = Post(user_id=user_id, content=form.content.data)
            db.session.add(new_post)
            db.session.commit()
            flash('Post Created Succefully!')
        return redirect(url_for('newsfeed'))
    return redirect(url_for('login'))


def get_users():
    #This function will query the db to get all users
    users = User.query.all()
    return users

@app.route('/follow/<email>', methods=['POST'])
@login_required
def follow(email):
    form = FollowUnfollowForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first() #get the specific user
        print('user: ', user)
        if user is None:
            flash('User {} not found.'.format(email))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You can not follow yourself!')
            return redirect(url_for('newsfeed'))
        current_user.follow(user)
        flash('You are now following {}!'.format(email))
        #Todo: change redirect to profile when it is created 
        return redirect(url_for('newsfeed'))
    else:
        return redirect(url_for('newsfeeds'))


@app.route('/unfollow/<email>', methods=['POST'])
@login_required
def unfollow(email):
    form = FollowUnfollowForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        print('user: ', user)
        if user is None:
            flash('User {} not found!'.format(email))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You can not unfollow yourself!')
            return redirect(url_for('index'))
            #Todo: change return redirect to profile of user when created
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(email))
        return redirect(url_for('newsfeed'))
    else:
        return redirect(url_for('index'))