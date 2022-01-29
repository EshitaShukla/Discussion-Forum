# !/usr/bin/env python
import json
import os
import shutil
import sys

# from flask import Flask, render_template, request, Response, send_file, redirect, url_for
from flask import Flask, render_template, url_for, request, session, redirect, send_from_directory, jsonify, flash
from flask_pymongo import PyMongo, MongoClient


from bson import json_util
import pandas
import bcrypt
import os.path

import logging    # first of all import the module
from datetime import datetime

# logging.basicConfig(filename='std.log', filemode='w',
#                     format='%(asctime)s %(levelname)-8s %(message)s',
#                     level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
# logging.info('Basic App')
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'testSwing'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/social_media'
app.config['UPLOAD_FOLDER'] = 'static/post_images'
app.secret_key = 'hi'

mongo = PyMongo(app)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
print(APP_ROOT)


@app.route('/')
def index():
    print("Redirecing now...")
    if 'username' not in session:
        return redirect('/userlogin')
    return redirect('/home')


@app.route('/home')
def home():
    return "Home Page"


@app.route('/register', methods=['POST', 'GET'])
def register():
    if 'username' in session:
        print("In Session")
        return redirect('/')

    if request.method == 'POST':
        print("Using db")
        users = mongo.db.users
        name = request.form.get('firstname')
        username = request.form.get('username')
        email = request.form.get('email')

        print("Searching for existing user...")
        existing_user = users.find_one({'username': request.form.get('username')})
        if existing_user is None:
            print("user doesn't already exist")
            hashpass = bcrypt.hashpw(request.form.get('password').encode('utf-8'), bcrypt.gensalt())
            users.insert_one(
                {'name': name,
                 'email': email,
                 'username': username,
                 'password': hashpass})

            session['username'] = username
            # session['type'] = "alumni"

            print('go home')
            return redirect('/home')

        print('user exists')
        flash("The username is taken, please enter a different username")
        return render_template('register.html',
                               msg="The username is taken, please enter a different username")

    print('send to register')
    return render_template('register.html', msg="")


@app.route('/userlogin', methods=['POST', 'GET'])
def userlogin():
    if 'username' in session:
        print("Not IN Session")
        return redirect('/')

    return render_template('login.html', msg="")


@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'username': request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form.get('password').encode('utf-8'), login_user['password']) == login_user[
            'password']:
            session['username'] = request.form['username']
            return redirect('/')
    flash("Invalid Username/Password")
    return render_template('login.html', msg="Invalid Username/Password")


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')


def find_tags(description):
    description = description.replace(",", " ").replace(".", " ").replace("'", " ").replace("\"", " ").replace("!", " ").replace("?", " ").replace("-", " ")
    return {tag.strip("#") for tag in description.split() if tag.startswith("#")}

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    if 'username' not in session:
        print("Not in Session")
        return redirect('/')
    username = session['username']
    if request.method == 'POST':
        print("Using db")
        print("POST Method")
        # Getting Collections
        posts = mongo.db.posts
        users = mongo.db.users
        tags = mongo.db.tags

        print("Now Retrieving Everything...")
        # Getting Data
        title = request.form.get("title")
        description = request.form.get("description")
        post_tags = find_tags(description)
        # Getting File Data
        file = request.files['image']
        filename = secure_filename(file.filename)
        # Getting Post Count Data
        user = users.find_one({"username": username})
        if "post_count" in user:
            post_count = user["post_count"]+1
        else:
            post_count = 0
        post_id = username + "_" + str(post_count)

        print("Now Saving Everything...",
              {'username': username,
             'title': title,
             'description': description,
             'post_id':post_id,
             'tags':list(post_tags),
             'image':filename})
        # Adding Post
        posts.insert_one(
            {'username': username,
             'title': title,
             'description': description,
             'post_id':post_id,
             'tags':list(post_tags),
             'image':filename,
             'votes':0})
        # Updating post_num
        users.update_one({'username': username}, {"$set": {"post_count": post_count}})
        # Saving File
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Adding Tags
        for hashtag in post_tags:
            tag_doc = tags.find_one({"username": username})
            if tag_doc:
                posts_list = tag_doc["posts"]
                posts_list.append(post_id)
                tags.update({'name': hashtag}, {"$set": {"posts": posts_list}})
            else:
                tags.insert_one({'name': hashtag, "posts": [post_id]})
        return redirect("/dashboard")

    posts = mongo.db.posts
    my_posts = posts.find({'username': username}).sort("votes")
    all_posts = posts.find({})
    object = {"post_id": 1, "comments": [{"id": 1, "children": [{"id": 2, "children": [5]}, {"id": 3}, {"id": 4}]}]}
    data = json.dumps(object)
    return render_template("dashboard.html", data = object, posts = my_posts, upload_folder = "../../../"+app.config['UPLOAD_FOLDER']+"/")

@app.route('/view_comments', methods = ['POST', 'GET'])
def view_comments():
    object = {"post_id":1, "comments": [{"id":1, "children":[{"id":2, "children":[5]},{"id":3},{"id":4}]}]}
    data = json.dumps(object)
    print(type(data))
    return render_template('blank_page.html', data = object)

if __name__ == '__main__':
    # data = pandas.read_csv('Apparel_Dummy_Database.csv').values.tolist()
    # context = ('sensitive/test.cert', 'sensitive/test.key')

    app.run(host='0.0.0.0', debug=True)  # , ssl_context=context, threaded=True, debug=False)