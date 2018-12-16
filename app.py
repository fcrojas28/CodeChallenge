from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators
from wtforms.validators import ValidationError
from launchkey.exceptions import RequestTimedOut, EntityNotFound
from launchkey.factories.service import ServiceFactory
#from launchkey.entities.service import AuthorizationResponse, SessionEndRequest  # this is for the webhook
from time import sleep
import sqlite3
import datetime
import re, traceback
import platform

print(platform.python_version())

DATABASE = 'users.db'

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'not so secret key'

organization_id = "2cd1360e-ff2e-11e8-911c-0a3c3cadd4fd"
organization_private_key = open('organization_private_key.key').read()
directory_id = "0172917a-ff69-11e8-ae69-4a5e312d9ab1"
service_id = "b3f8ddb2-ff33-11e8-871a-4a5e312d9ab1"
service_private_key = open('service_private_key.key').read()  

# per the instruction: use serviceFactory to create a serviceClient
service_factory = ServiceFactory(service_id, service_private_key)
service_client = service_factory.make_service_client()

#organization_factory = OrganizationFactory(organization_id, organization_private_key) # dont need this for now leaving it here for reference
#directory_client = organization_factory.make_directory_client(directory_id)           # dont need this for now leaving it here for reference
#service_client = organization_factory.make_service_client(service_id)                 # dont need this for now leaving it here for reference

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])
    
# Since there is a req when creating an user from Launchkey mobile app
# i am making sure that validation is apply before submitting the auth request
def validChar(form, field):
    regex = re.compile("[\s<>:;()@&\"/\']")
    match = regex.search(field.data)
    if match:
        raise ValidationError('Invalid Character <>:;()@&"/\' and no whitespaces')


class LoginForm(FlaskForm):
    username = StringField("username", [validators.Length(min=4, max=46), validChar])
    submit = SubmitField('Log In')

@app.route('/')
def index():
    form = LoginForm()
    return render_template('home.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm(request.form)
    
    if request.method == 'GET':
        return render_template('home.html', form=form)
    
    username = request.form['username']
    if username and form.validate():
        try:
            auth_request_id = service_client.authorize(username)
            if auth_request_id:
                response = None
                try:
                    while response is None:
                        response = service_client.get_authorization_response(auth_request_id)
                        if response is not None:
                            
                            # Write into the db the user activity
                            if response.authorized is True:
                                db = connect_db()
                                db.execute("INSERT INTO users VALUES(?,?,?)", (username, datetime.datetime.now(), "granted"))
                                db.commit()
                                db.close()
                            else:
                                db = connect_db()
                                db = connect_db()
                                db.execute("INSERT INTO users VALUES(?,?,?)", (username, datetime.datetime.now(), "denied"))
                                db.commit()
                                db.close()
                            
                            # get all user activity from the DB
                            db = connect_db()
                            myResultSet = db.execute("SELECT username, dt, access FROM users WHERE username=:targetUsername",{'targetUsername':username})
                            users = [dict(username=row[0],dateTime=row[1],access=row[2]) for row in myResultSet.fetchall()]
                            db.close()
                                
                            if response.authorized is True:
                                service_client.session_start(username, auth_request_id)
                                return render_template('dashboard.html', isLogIn=True, users=users, username=username)
                            else:
                                return render_template('dashboard.html', isLogIn=False, users=users, username=username)
                        else:
                            sleep(1)
                except RequestTimedOut:
                    errorMsg = {'msg' : 'Timed Out. Please try again.', 'stackTrace' : traceback.format_exc()}
                    return render_template('home.html', form=form, errorMsg=errorMsg)
        except EntityNotFound:
            errorMsg = {'msg' : 'Sorry, this username cannot be found.', 'stackTrace' : traceback.format_exc()}
            return render_template('home.html', form=form, errorMsg=errorMsg)

    return render_template('home.html', form=form)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

        
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    print('Inside the Webhook Method')
    print('###############')
    print('###############')
    print('request method')
    print(request.method)
    print('###############')
    print('###############')
    print('request path')
    print(request.path)
    
    doSomething = "testing the webhook"
    
#     package = service_client.handle_webhook(request.data, request.headers, request.method, request.path)
#     if isinstance(package, AuthorizationResponse):
#         if package.authorized is True:
#             # User accepted the auth, now create a session
#             doSomething = "access granted"
#         else:
#             # User denied the auth
#             doSomething = "access denied"
#     elif isinstance(package, SessionEndRequest):
#         doSomething = "log out"
        
    return doSomething


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
