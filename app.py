from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators
from wtforms.validators import ValidationError
from launchkey.factories import ServiceFactory, OrganizationFactory
from launchkey.exceptions import RequestTimedOut, EntityNotFound
from time import sleep
import re

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'not so secret key'

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

organization_id = "2cd1360e-ff2e-11e8-911c-0a3c3cadd4fd"
organization_private_key = open('organization_private_key.key').read()
directory_id = "0172917a-ff69-11e8-ae69-4a5e312d9ab1"
service_id = "b3f8ddb2-ff33-11e8-871a-4a5e312d9ab1"
service_private_key = open('service_private_key.key').read()

service_factory = ServiceFactory(service_id, service_private_key)
organization_factory = OrganizationFactory(organization_id, organization_private_key)
directory_client = organization_factory.make_directory_client(directory_id)
service_client = organization_factory.make_service_client(service_id)

@app.route('/')
def index():
    form = LoginForm()
    return render_template('home.html', form=form)

@app.route('/login', methods=['POST'])
def login():
    form = LoginForm(request.form)
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
                            if response.authorized is True:
                                service_client.session_start(username, auth_request_id)
                                return render_template('dashboard.html', isLogIn=True)
                            else:
                                return render_template('dashboard.html', isLogIn=False)
                        else:
                            sleep(1)
                except RequestTimedOut:
                    return 'Timed Out. Please try again.'
        except EntityNotFound:
            return 'Sorry, User cannot be found. (The \'service_client.get_authorization_response\' throws an error when the user cannot be found, so I am catching this error (launchkey.exceptions.EntityNotFound) and displaying a more friendly message )'

    return render_template('home.html', form=form)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    print "inside the contact controller"
    return render_template('contact.html')

@app.route('/webhook')
def webhook():
    print 'Inside login'
    print '###############'
    print 'request data'
    print request.data
    print '###############'
    print 'request headers'
    print request.headers
    print '###############'
    print 'request method'
    print request.method
    print '###############'
    print 'request path'
    print request.path
    return "webhook page"


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
