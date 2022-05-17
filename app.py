#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for, make_response
from markupsafe import escape
import pymongo
import datetime
from bson.objectid import ObjectId
import os
import subprocess

# instantiate the app
app = Flask(__name__)

# load credentials and configuration options from .env file
# if you do not yet have a file named .env, make one based on the template in env.example
import credentials
config = credentials.get()

# turn on debugging if in development mode
if config['FLASK_ENV'] == 'development':
    # turn on debugging, if in development
    app.debug = True # debug mnode

# make one persistent connection to the database
connection = pymongo.MongoClient(config['MONGO_HOST'], 27017, 
                                username=config['MONGO_USER'],
                                password=config['MONGO_PASSWORD'],
                                authSource=config['MONGO_DBNAME'])
db = connection[config['MONGO_DBNAME']] # store a reference to the database

# set up the routes

@app.route('/')
def home():
    docs = db.app.find({}).sort("deadline", 1) 
    docs_count = db.app.find({}).count()
    return render_template('index.html', docs=docs, docs_count = docs_count) 


@app.route('/add')
def add():
    return render_template('add.html')


@app.route('/add', methods=['POST'])
def add_post():
    todo_item = request.form['ftodo']
    deadline = request.form['fdeadline']

    doc = {
        "todo_item": todo_item, 
        "deadline": deadline
    }

    db.app.insert_one(doc)

    return redirect(url_for('home'))


@app.route('/edit/<mongoid>')
def edit(mongoid):
    doc = db.app.find_one({"_id": ObjectId(mongoid)})
    return render_template('edit.html', mongoid=mongoid, doc=doc)


@app.route('/edit/<mongoid>', methods=['POST'])
def edit_post(mongoid):
    todo_item = request.form['ftodo']
    deadline = request.form['fdeadline']

    doc = {
        "todo_item": todo_item, 
        "deadline": deadline
    }

    db.app.update_one(
        {"_id": ObjectId(mongoid)},
        { "$set": doc }
    )

    return redirect(url_for('home'))


@app.route('/delete/<mongoid>')
def delete(mongoid):
    db.app.delete_one({"_id": ObjectId(mongoid)})
    return redirect(url_for('home'))


@app.route('/deleteall')
def delete_all():
    db.app.remove({})
    return redirect(url_for('home'))


@app.route('/searchresult', methods=['POST'])
def search_post():
    query = request.form['fsearch']
    search_results = db.app.find({"todo_item":query})
    return render_template('searchresult.html', search_results=search_results)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    GitHub can be configured such that each time a push is made to a repository, GitHub will make a request to a particular web URL... this is called a webhook.
    This function is set up such that if the /webhook route is requested, Python will execute a git pull command from the command line to update this app's codebase.
    You will need to configure your own repository to have a webhook that requests this route in GitHub's settings.
    Note that this webhook does do any verification that the request is coming from GitHub... this should be added in a production environment.
    """
    # run a git pull command
    process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE)
    pull_output = process.communicate()[0]
    # pull_output = str(pull_output).strip() # remove whitespace
    process = subprocess.Popen(["chmod", "a+x", "flask.cgi"], stdout=subprocess.PIPE)
    chmod_output = process.communicate()[0]
    # send a success response
    response = make_response('output: {}'.format(pull_output), 200)
    response.mimetype = "text/plain"
    return response

@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template('error.html', error=e)


if __name__ == "__main__":
    #import logging
    #logging.basicConfig(filename='/home/ak8257/error.log',level=logging.DEBUG)
    app.run(debug = True)
