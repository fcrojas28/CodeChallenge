from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators
from wtforms.validators import ValidationError
from launchkey.exceptions import RequestTimedOut, EntityNotFound
from launchkey.factories.service import ServiceFactory
from launchkey.entities.service import AuthorizationResponse, SessionEndRequest
from time import sleep
import sqlite3
import datetime
import re, traceback
import platform

# This is SQLite db file
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

#organization_factory = OrganizationFactory(organization_id, organization_private_key) # I don't need this for now leaving it here for reference
#directory_client = organization_factory.make_directory_client(directory_id)           # I don't need this for now leaving it here for reference
#service_client = organization_factory.make_service_client(service_id)                 # I don't need this for now leaving it here for reference

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])
    
# Since there is a requirement when creating an user from Launchkey mobile app
# I am making sure that this same requirement is apply to the user 
# filed form in the app
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
    form = LoginForm(request.form)
    return render_template('home.html', form=form, pythonVer=platform.python_version())

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm(request.form)
    
    if request.method == 'GET':
        return render_template('home.html', form=form, pythonVer=platform.python_version())
    
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
                            db = connect_db()
                            db.execute("INSERT INTO users VALUES(?,?,?,?,?,?)", (username, auth_request_id, datetime.datetime.now(), "granted" if response.authorized is True else "denied",None,None))
                            db.commit()
                            db.close()
                            
                            # get all user activity from the DB
                            db = connect_db()
                            myResultSet = db.execute("SELECT username, auth_req_id, dt, access, webhook_acess_granted_dt, webhook_acess_denied_dt FROM users WHERE username=:targetUsername",{'targetUsername':username})
                            users = [dict(username=row[0],userReqId=row[1],dateTime=row[2],access=row[3],webhookGranted=row[4],webhookDenied=row[5]) for row in myResultSet.fetchall()]
                            db.close()
                                
                            if response.authorized is True:
                                service_client.session_start(username, auth_request_id)
                                return render_template('dashboard.html', isLogIn=True, users=users, username=username, form=form)
                            else:
                                return render_template('dashboard.html', isLogIn=False, users=users, username=username, form=form)
                        else:
                            sleep(1)
                except RequestTimedOut:
                    errorMsg = {'msg' : 'Timed Out. Please try again.', 'stackTrace' : traceback.format_exc()}
                    return render_template('home.html', form=form, errorMsg=errorMsg, pythonVer=platform.python_version())
        except EntityNotFound:
            errorMsg = {'msg' : 'Sorry, this username cannot be found.', 'stackTrace' : traceback.format_exc()}
            return render_template('home.html', form=form, errorMsg=errorMsg, pythonVer=platform.python_version())

    return render_template('home.html', form=form, pythonVer=platform.python_version())

@app.route('/logout', methods=['POST'])
def logout():
    username = request.form['username']
    service_client.session_end(username)
    form = LoginForm(request.form)
    return render_template('home.html', form=form, pythonVer=platform.python_version())


@app.route('/dashboard', methods=['POST'])
def dashboard():
    username = request.form['username']
    isLogInAsString = request.form['islogin']
    db = connect_db()
    myResultSet = db.execute("SELECT username, auth_req_id, dt, access, webhook_acess_granted_dt, webhook_acess_denied_dt FROM users WHERE username=:targetUsername",{'targetUsername':username})
    users = [dict(username=row[0],userReqId=row[1],dateTime=row[2],access=row[3],webhookGranted=row[4],webhookDenied=row[5]) for row in myResultSet.fetchall()]
    db.close()
    form = LoginForm(request.form)
    return render_template('dashboard.html', isLogIn=str_to_bool(isLogInAsString), users=users, username=username, form=form)

    
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# This function will detect the webhook from the launchkey server
# The authorization_request_id will be extract it from the request
# and I will update the user request response from the server to
# local database      
@app.route('/webhook', methods=['POST'])
def webhook():
    package = service_client.handle_webhook(request.data, request.headers)
    actionFromWebhook="testing the webhook"
    
    db = connect_db()
    if isinstance(package, AuthorizationResponse):
        if package.authorized is True:
            # User accepted the auth, now create a session
            actionFromWebhook = "webhook-access-granted"
            db.execute("UPDATE users SET webhook_acess_granted_dt=? WHERE auth_req_id=?", (datetime.datetime.now(),package.authorization_request_id))
        else:
            # User denied the auth
            actionFromWebhook = "webhook-access-denied"
            db.execute("UPDATE users SET webhook_acess_denied_dt=? WHERE auth_req_id=?", (datetime.datetime.now(),package.authorization_request_id))
    elif isinstance(package, SessionEndRequest):
        actionFromWebhook = "webhook-log-out"
    
    
    db.commit()
    db.close() 
    
    return actionFromWebhook

def str_to_bool(strToEval):
    if strToEval == 'True':
        return True
    else:
        return False

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
