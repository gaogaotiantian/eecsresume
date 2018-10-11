#coding=utf-8
import math
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
from flask import Flask, request, send_file, render_template, make_response, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_admin import Admin
from flask_admin.contrib import sqla
from flask_basicauth import BasicAuth
from werkzeug.exceptions import HTTPException

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
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('GMAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('GMAIL_PASSWORD')
app.config['BASIC_AUTH_USERNAME'] = os.environ.get("ADMIN_USERNAME")
app.config['BASIC_AUTH_PASSWORD'] = os.environ.get("ADMIN_PASSWORD")
CORS(app)
db = SQLAlchemy(app)
mail = Mail(app)
basicAuth = BasicAuth(app)
admin = Admin(app, name = 'eecsresume', template_mode='bootstrap3')

class statusEnum(enum.Enum):
    sent = 1
    browse = 2
    paid = 3
    reviewed = 4
    review_again = 5
    finish = 6
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

class commentTypeEnum(enum.Enum):
    anonymous = 1
    browse = 2
    review = 3

class AuthException(HTTPException):
    def __init__(self, message):
        # python 3
        super().__init__(message, Response(
            message, 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'}
        ))

class ModelView(sqla.ModelView):
    def is_accessible(self):
        if not basicAuth.authenticate():
            raise AuthException('Not authenticated. Refresh the page.')
        else:
            return True

    def inaccessible_callback(self, name, **kwargs):
        return redirect(basicAuth.challenge())

class TaskModelView(ModelView):
    column_default_sort = ('add_time', True)
    column_filters = ('status',)
    column_searchable_list = ('email',)

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

class CommentDb(db.Model):
    __tablename__ = 'comment'
    id         = db.Column(db.Integer, primary_key = True)
    email      = db.Column(db.String(128))
    comment    = db.Column(db.Text)
    score      = db.Column(db.Float)
    type       = db.Column(db.Enum(commentTypeEnum))
    edit_time  = db.Column(db.DateTime, server_default = db.func.now(), onupdate = db.func.now())

    def toDict(self):
        try:
            if self.email == "anonymous":
                email = "anonymous"
            else:
                lst = self.email.split('@')
                lst[0] = lst[0][0] +'*'*(len(lst[0])-2) + lst[0][-1]
                email = '@'.join(lst)
            return {"email":email, "type":self.type.name, 'comment':self.comment, 'edit_time': self.edit_time, 'score':self.score}
        except:
            return None

db.create_all()

admin.add_view(TaskModelView(TaskDb, db.session))
admin.add_view(ModelView(CommentDb, db.session))

def getDriveService():
    service = build('drive', 'v3', credentials = credentials)

    return service

def getGmailService():
    service = build('gmail', 'v1', credentials = credentials)

    return service

def sendEmail(pdfRaw, email):
    message = Message("Resume review from EECSResume",
            sender=("EECSResume", "eecsresume@gmail.com"),
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
            sender=("EECSResume", "eecsresume@gmail.com"),
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

def getFooter():
    footer = {}
    weekTime = datetime.datetime.utcnow() - datetime.timedelta(days = 7)
    monthTime = datetime.datetime.utcnow() - datetime.timedelta(days = 30)
    weekReviewCount = TaskDb.query.filter(TaskDb.edit_time > weekTime).filter(TaskDb.status >= statusEnum.browse).count()
    weekModifyCount = TaskDb.query.filter(TaskDb.edit_time > weekTime).filter(TaskDb.status >= statusEnum.reviewed).count()
    monthReviewCount = TaskDb.query.filter(TaskDb.edit_time > monthTime).filter(TaskDb.status >= statusEnum.browse).count()
    monthModifyCount = TaskDb.query.filter(TaskDb.edit_time > monthTime).filter(TaskDb.status >= statusEnum.reviewed).count()
    latestTime = TaskDb.query.filter(TaskDb.edit_time.isnot(None)).order_by(TaskDb.edit_time.desc()).first().edit_time
    footer['stat'] = "近一周免费点评简历{}篇，修改简历{}篇。近一月免费点评简历{}篇，修改简历{}篇。".format(weekReviewCount, weekModifyCount, monthReviewCount, monthModifyCount)
    footer['latest'] = "最近一次活跃于{}, UTC。".format(latestTime.strftime("%x"))
    return footer

def getAvrScore():
    score = CommentDb.query.with_entities(db.func.avg(CommentDb.score).label('average')).filter(CommentDb.type != commentTypeEnum.anonymous).first()[0]
    return score

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

@app.route('/api/v1/comment', methods = ['GET', 'POST'])
def comment():
    if request.method == 'POST':
        data = request.json
        if data == None:
            return err(400, "No json data")
        try:
            email  = data['email']
            comment = data['comment']
            score   = data['score']
        except:
            return err(400, "Wrong parameters")

        if email != "anonymous":
            t = TaskDb.query.filter_by(email = email).order_by(TaskDb.status.desc()).first()

            if t == None or t.status < statusEnum.browse:
                return err(403, "这个Email没有使用过EECSResume的服务")

        c = CommentDb.query.filter_by(email = email).first()
        if c == None or email == "anonymous":
            newc = CommentDb()
            newc.email = email
            newc.comment = comment
            newc.score = score

            if email == "anonymous":
                newc.type = commentTypeEnum.anonymous
            elif t.status < statusEnum.reviewed:
                newc.type = commentTypeEnum.browse
            else:
                newc.type = commentTypeEnum.review
            db.session.add(newc)
            db.session.commit()
        else:
            c.comment = comment
            c.score = score
            if t.status < statusEnum.reviewed:
                c.type = commentTypeEnum.browse
            else:
                c.type = commentTypeEnum.review
            db.session.commit(c)
        return success({"msg":"success"})
    elif request.method == 'GET':
        page = request.args.get("page")
        if page == None:
            page = 1
        else:
            try:
                page = int(page)
            except:
                return err(400, "Wrong page argument")
        total = CommentDb.query.count()
        resultsPerPage = 10
        results = CommentDb.query.order_by(CommentDb.edit_time.desc()).limit(resultsPerPage).offset((page-1)*resultsPerPage)

        return success({"results":[r.toDict() for r in results if r.toDict()], "totalPage":math.ceil(total/resultsPerPage), "avrScore":getAvrScore()})
        


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', footer=getFooter())

@app.route('/procedure')
def procedure():
    return render_template('procedure.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/example')
def example():
    return render_template('example.html')

@app.route('/submit')
def submit():
    return render_template('submit.html')

@app.route('/comment')
def route_comment():
    return render_template('comment.html')

if __name__ == '__main__':
    app.run(debug = True)
