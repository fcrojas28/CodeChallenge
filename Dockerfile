FROM centos:latest

RUN yum install -y python-pip python-setuptools gcc python-devel git
RUN easy_install pip

RUN pip install launchkey
RUN pip install flask
RUN pip install flask_wtf
RUN pip install wtforms

RUN mkdir /opt/myapp
WORKDIR /opt/myapp
ADD . /opt/myapp

# Define working directory.
#WORKDIR /opt/myapp

# Define default command.
#CMD ["python", "--version"]
#CMD ["python", "/opt/myapp/app.py"]
#ENTRYPOINT["python", "/opt/myapp/app.py"]
