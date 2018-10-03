#coding=utf-8
import os
import string
import enum
import random
import datetime
import io
import json
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase

# other published packages
from flask import Flask, request, send_file, render_template, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from httplib2 import Http
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import file, client, tools
from google.oauth2 import service_account

DATABASE_URL = None
if os.environ.get('DATABASE_URL') != None:
    DATABASE_URL = os.environ.get('DATABASE_URL')

credentialRaw = os.environ.get('GOOGLE_APP_CREDENTIAL')
credentials = service_account.Credentials.from_service_account_info(json.loads(credentialRaw))


app = Flask(__name__, static_url_path = '/static')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('GMAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('GMAIL_PASSWORD')
CORS(app)
db = SQLAlchemy(app)
mail = Mail(app)

class statusEnum(enum.Enum):
    sent = 1
    browse = 2
    paid = 3
    reviewed = 4
    review_again = 5
    finish = 6

class TaskDb(db.Model):
    __tablename__ = 'task'
    id         = db.Column(db.Integer, primary_key = True)
    short_link = db.Column(db.String(10))
    add_time   = db.Column(db.DateTime, server_default = db.func.now())
    edit_time  = db.Column(db.DateTime, onupdate = db.func.now())
    email      = db.Column(db.String(128))
    status     = db.Column(db.Enum(statusEnum))
    review_time = db.Column(db.Integer)
    file_link  = db.Column(db.String(256))
    review     = db.Column(db.Text)
    note       = db.Column(db.Text)

db.create_all()

def getDriveService():
    service = build('drive', 'v3', credentials = credentials)

    return service

def getGmailService():
    service = build('gmail', 'v1', credentials = credentials)

    return service

def sendEmail(pdfRaw, email):
    message = Message("Resume review from EECSResume",
            sender="eecsresume@gmail.com",
            recipients=["eecsresume@gmail.com"])

    message.body = "Email: {}\n".format(email)

    message.attach("resume.pdf", 'application/pdf', pdfRaw)

    try:
        mail.send(message)
        print("Got a resume from {}".format(email))
    except Exception as e:
        print(e)

def sendConfirmEmail(email):
    print(type(email))
    print(email)
    message = Message("Resume review confirmation from EECSResume",
            sender="eecsresume@gmail.com",
            recipients=[email])
    message.body = "您好！\n您的Resume我已经收到，我会在数个工作日内给您回复。如果有什么问题，可以直接回复这条消息。\n\n- EECSResume"

    try:
        mail.send(message)
        print("Send confirmation to {}".format(email))
    except Exception as e:
        print(e)

chars = string.ascii_uppercase + string.digits
def getShortLink():
    while True:
        s = ''.join(random.choice(chars) for _ in range(6))
        check = TaskDb.query.filter_by(short_link = s).first()
        if check == None:
            return s
def success(dct):
    return make_response(jsonify(dct), 200)

def err(err_code, err_msg):
    return make_response(jsonify({"err_msg":err_msg}), err_code)

@app.route('/api/v1/task', methods = ['GET', 'POST'])
def task():
    if request.method == 'POST':
        f = request.files.get("resume")
        formData = dict(request.form)

        if f == None:
            return err(400, "Can not find attached file. It should be a pdf file.")
        data = request.json

        try:
            email = formData["email"][0]
        except:
            return err(400, "Wrong parameters")

        shortLink = getShortLink()

        # Google Drive part
        #service = getDriveService()
        #fileMetadata = {'name': shortLink}
        #media = MediaIoBaseUpload(fio, mimetype='application/pdf')
        #gDriveFile = service.files().create(body = fileMetadata, media_body = media, fields = 'id').execute()

        # Gmail part
        sendEmail(f.read(), email)
        sendConfirmEmail(email)

        t = TaskDb()
        t.short_link = shortLink
        t.email = email
        t.status = statusEnum.sent
        t.note = ""
        
        db.session.add(t)
        db.session.commit()
    return success({"msg":"success"})

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/procedure')
def procedure():
    return render_template('procedure.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/submit')
def submit():
    return render_template('submit.html')

if __name__ == '__main__':
    app.run(debug = True)
