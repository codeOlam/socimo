import os
from flask import Flask, render_template, redirect, request, session, json, jsonify
from werkzeug.utils import secure_filename
from config import Config
from sqlalchemy import create_engine
import pandas as pd

#code added by codeOlam
from flask import Blueprint, redirect, render_template, flash, request, session, url_for
from flask_login import login_required, current_user
from app import db, app
from app import class_cluster as cc
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
        users_in_heal_cluster = suggestUser()
        form = PostForm()
        #Get all post to news feeds
        newsfeeds = Post.query.all()

        # suggestUser()
        #ToDo: send all new post to update pd dataframe

        #get id of clicked users
        #Todo: select post for user based on following user
        FUform = FollowUnfollowForm()
        return render_template('newsfeed.html', 
                            form=form, 
                            FUform=FUform,
                            newsfeeds=newsfeeds, 
                            users=users,
                            users_in_heal_cluster=users_in_heal_cluster)
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
        return redirect(url_for('newsfeed'))


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


def suggestUser():
    """
    This function will sugget user based on post made
    """
    print("\nIn suggestion Function")
    user_in_heal_list = []
    u_id = current_user.id

    #check if users post is in health cluster
    #get health cluster
    heal_cluster = cc.get_heal_cluster
    #get user_id column and save to list
    col_id_list = heal_cluster.user_id.to_list()
    print('col_id_list: ', col_id_list)
    #Check if user_id is in list
    if u_id in col_id_list:
        all_user_id = pd.unique(col_id_list).tolist()
        print('all_user_id, :', all_user_id)
        for i in all_user_id:
            if u_id != i:
                users_in_heal = User.query.filter_by(id=i).first()
                print("users_in_heal: ", users_in_heal)
                user_in_heal_list.append(users_in_heal)
        print('user_in_heal_list: ', user_in_heal_list)
        print('users_in_heal: ', users_in_heal)

    return user_in_heal_list

