from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from functools import wraps
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import datetime

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly
    # logout, let's strip out the information before the equals sign in our
    # token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# Disconnect based on provider


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalog'))

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        flash("Please log in to add, edit and delete content")
        return redirect('/login')
    return decorated_function


# JSON APIs to view Restaurant Information
@app.route('/catalog')
def catalogJSON():
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return jsonify(
        Categories=[
            category.serialize for category in categories], Items=[
            item.serialize for item in items])

# Show all categories and latest items


@app.route('/')
def showCatalog():
    categories = session.query(Category).order_by(asc(Category.name))
    latestItems = session.query(Item).order_by(Item.created.desc())
    return render_template(
        'catalog.html',
        categories=categories,
        latestItems=latestItems)

# Show all items in a specific category


@app.route('/catalog/<int:category_id>/items')
def showItems(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    return render_template('items.html', items=items, category=category)


# Show an items's details
@app.route('/catalog/<int:category_id>/<int:item_id>')
def itemDetails(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('item.html', item=item, category=category)

# Add a new item


@app.route('/catalog/items/new', methods=['GET', 'POST'])
@login_required
def newItem():
    categories = session.query(Category).order_by(asc(Category.name))
    user_id = login_session['user_id']
    if request.method == 'POST':
        category = session.query(Category).filter_by(
            name=request.form['category']).one()
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            category_id=category.id,
            created=datetime.datetime.now(),
            user_id=user_id)
        session.add(newItem)
        session.commit()
        flash('New Item -  %s  Successfully Created' % (newItem.name))
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newitem.html', categories=categories)

# Edit an item


@app.route('/catalog/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def editItem(item_id):
    categories = session.query(Category).order_by(asc(Category.name))
    item = session.query(Item).filter_by(id=item_id).one()
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit other users' items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            category = session.query(Category).filter_by(
                name=request.form['category']).one()
            item.name = request.form['name']
            item.description = request.form['description']
            item.price = request.form['price']

            item.category_id = category.id
            flash('%s Successfully Edited' % item.name)
            return redirect(url_for('showItems', category_id=item.category.id))
    else:
        return render_template(
            'edititem.html',
            categories=categories,
            item=item)


# Delete an item
@app.route('/catalog/<int:item_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteItem(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete other users' items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(item)
        flash('%s Successfully Deleted' % item.name)
        session.commit()
        return redirect(url_for('showItems', category_id=item.category.id))
    else:
        return render_template('deleteitem.html', item=item)

# Add a new category


@app.route('/catalog/new', methods=['GET', 'POST'])
@login_required
def newCategory():
    user_id = login_session['user_id']
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'], user_id=user_id)
        session.add(newCategory)
        session.commit()
        flash('New Category %s Successfully Created' % (newCategory.name))
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newcategory.html')


# Edit a category
@app.route('/catalog/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit other users' categories.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            category.name = request.form['name']
            flash('%s Successfully Edited' % category.name)
            return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('editCategory.html', category=category)


# Delete a category and all of the items associated with it
@app.route(
    '/catalog/category/<int:category_id>/delete',
    methods=[
        'GET',
        'POST'])
@login_required
def deleteCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete other users' categories.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        for item in items:
            session.delete(item)
        session.delete(category)
        flash(
            '%s Category and All Items Associated with this Category Successfully Deleted' %
            category.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html', category=category)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
