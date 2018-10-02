#coding=utf-8
import os
import string
import enum
import random
import datetime
import io
import json

# other published packages
from flask import Flask, request, send_file, render_template, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from httplib2 import Http
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import file, client, tools
from google.oauth2 import service_account

DATABASE_URL = None
if os.environ.get('DATABASE_URL') != None:
    print("123")
    DATABASE_URL = os.environ.get('DATABASE_URL')

credentialRaw = os.environ.get('GOOGLE_APP_CREDENTIAL')
credentials = service_account.Credentials.from_service_account_info(json.loads(credentialRaw))


app = Flask(__name__, static_url_path = '/static')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
CORS(app)
db = SQLAlchemy(app)

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

def getService():
    service = build('drive', 'v3', credentials = credentials)

    return service

chars = string.ascii_uppercase + string.digits
def getShortLink():
    while True:
        print("getlink")
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
        print("get post")
        f = request.files.get("resume")
        if f == None:
            return err(400, "Can not find attached file. It should be a pdf file.")
        fio = io.BytesIO()
        f.save(fio)
        data = request.json

        try:
            email = "test@example.com"
            note  = "testtest"
        except:
            return err(400, "Wrong parameters")

        # Google Drive part
        service = getService()
        shortLink = getShortLink()
        fileMetadata = {'name': shortLink}
        media = MediaIoBaseUpload(fio, mimetype='application/pdf')
        gDriveFile = service.files().create(body = fileMetadata, media_body = media, fields = 'id').execute()
        print(gDriveFile.get('id'))
        t = TaskDb()
        t.short_link = shortLink
        t.file_link = gDriveFile.get('id')
        t.email = email
        t.status = statusEnum.sent
        t.note = note
        
        db.session.add(t)
        db.session.commit()
    return success({"msg":"success"})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug = True)
