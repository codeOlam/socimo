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
from app.forms import PostForm
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
    #codeOlam fixed news feed view function
    session['user'] = current_user.name
    form = PostForm()
    #Get all post to news feeds
    newsfeeds = Post.query.all()

    #Todo: select post for user based on following user

    return render_template('newsfeed.html', form=form, newsfeeds=newsfeeds)


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