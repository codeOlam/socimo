import os
from flask import Flask, render_template, redirect, request, session, json, jsonify
from werkzeug.utils import secure_filename
from config import Config
from sqlalchemy import create_engine, desc
import pandas as pd

#code added by codeOlam
from flask import Blueprint, redirect, render_template, flash, request, session, url_for
from flask_login import login_required, current_user
from app import db, app
from app.cluster import kmean_clst, post_to_df
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
        u_id = current_user.id
        #all users
        users = get_users()

        #call class_cluster module 
        gh, gp, gs, ge = kmean_clst()


        users_in_heal_cluster = suggestUser(u_id, gh) or None
        users_in_poli_cluster = suggestUser(u_id, gp) or None
        users_in_sec_cluster = suggestUser(u_id, gs) or None
        user_in_eco_cluster = suggestUser(u_id, ge) or None


        form = PostForm()
        #Get all post to news feeds
        newsfeeds = Post.query.order_by(desc(Post.created_on)).all()

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
                            clusterd_user=users_in_heal_cluster,
                            users_in_poli_cluster=users_in_poli_cluster,
                            users_in_sec_cluster=users_in_sec_cluster,
                            user_in_eco_cluster=user_in_eco_cluster
                            )
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


def suggestUser(u_id, get_cluster):
    """
    This function will sugget user based on post made
    """
    # print("\nIn suggestion Function")
    user_in_clust_list = []

    #check if users post is in health cluster
    # get cluster
    cluster = get_cluster
    #get user_id column and save to list
    if cluster is not None:
        col_id_list = cluster.user_id.to_list()
        #Check if user_id is in list
        if u_id in col_id_list:
            all_user_id = pd.unique(col_id_list).tolist()
            for i in all_user_id:
                if u_id != i:
                    users_in_cluster = User.query.filter_by(id=i).first()
                    user_in_clust_list.append(users_in_cluster)

    return user_in_clust_list


def cluster_table(get_clst, klas_):
    if get_clst is not None:
        data = {'user_id': get_clst.user_id.to_list(),
                'User': get_clst.User_name.to_list(),
                'Post': get_clst.Post2.to_list(),
                }

        table_df = pd.DataFrame(data)
        tdf_html = table_df.to_html(classes=klas_)

        return tdf_html
    return '<h2> Opps No Post found under {} Cluster Yet!<h2>'.format(klas_)


@app.route('/news_feed/health_cluster', methods=['GET'])
def health_table():
    heal_clst, poli_clst, sec_clst, eco_clst = kmean_clst()

    clst_tbl = cluster_table(heal_clst, 'health')
    tables_clst = [clst_tbl]

    return render_template('health_cluster.html', tables=tables_clst, titles=['user_id', 'User', 'Post'])


@app.route('/news_feed/politics_cluster', methods=['GET'])
def politics_table():
    heal_clst, poli_clst, sec_clst, eco_clst = kmean_clst()

    clst_tbl = cluster_table(poli_clst, 'politics')
    tables_clst = [clst_tbl]

    return render_template('politics_cluster.html', tables=tables_clst, titles=['user_id', 'User', 'Post'])


@app.route('/news_feed/security_cluster', methods=['GET'])
def security_table():
    heal_clst, poli_clst, sec_clst, eco_clst = kmean_clst()

    clst_tbl = cluster_table(sec_clst, 'security')
    tables_clst = [clst_tbl]

    return render_template('security_cluster.html', tables=tables_clst, titles=['user_id', 'User', 'Post'])


@app.route('/news_feed/economic_cluster', methods=['GET'])
def economic_table():
    heal_clst, poli_clst, sec_clst, eco_clst = kmean_clst()

    clst_tbl = cluster_table(eco_clst, 'economy')
    tables_clst = [clst_tbl]

    return render_template('economic_cluster.html', tables=tables_clst, titles=['user_id', 'User', 'Post'])