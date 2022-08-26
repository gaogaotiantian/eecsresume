#coding=utf-8
import math
import os
import string
import enum
import random
import datetime
import re

# other published packages
from flask import Flask, request, render_template, make_response, jsonify, Response, Markup, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_admin import Admin
from flask_admin.contrib import sqla
from flask_basicauth import BasicAuth
from werkzeug.exceptions import HTTPException

import markdown

# My modules
from challenge import Challenge
from curse import randomCurse

DATABASE_URL = None
if os.environ.get('DATABASE_URL') != None:
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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

chars = string.ascii_uppercase + string.digits
def getShortLink():
    while True:
        s = ''.join(random.choice(chars) for _ in range(8))
        check = TaskDb.query.filter_by(short_link = s).first()
        if check == None:
            return s

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

class ArticleModelView(ModelView):
    column_formatters = dict(content=lambda v,c,m,p: m.content[:100] + '...')

class ChallengeModelView(ModelView):
    column_formatters = dict(description=lambda v,c,m,p: m.description[:100] + '...', questions=lambda v,c,m,p: m.questions[:40] + '...')

class SolutionModelView(ModelView):
    column_formatters = dict(answers=lambda v,c,m,p: m.answers[:30] + '...')
    column_filters = ('ques_id',"version")

class TaskDb(db.Model):
    __tablename__ = 'task'
    id         = db.Column(db.Integer, primary_key = True)
    short_link = db.Column(db.String(10))
    add_time   = db.Column(db.DateTime, server_default = db.func.now())
    edit_time  = db.Column(db.DateTime, server_default = db.func.now(), onupdate = db.func.now())
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
                if len(lst[0]) == 1:
                    lst[0] = '*'
                elif len(lst[0]) == 2:
                    lst[0] = '**'
                else:
                    lst[0] = lst[0][0] +'*'*(len(lst[0])-2) + lst[0][-1]
                email = '@'.join(lst)
            return {"email":email, "type":self.type.name, 'comment':self.comment, 'edit_time': self.edit_time, 'score':self.score}
        except:
            return None

class ArticleDb(db.Model):
    __tablename__ = 'article'
    id            = db.Column(db.Integer, primary_key = True)
    link          = db.Column(db.String(128))
    title         = db.Column(db.String(256))
    content       = db.Column(db.Text)
    priority      = db.Column(db.Integer, server_default = "1")
    edit_time     = db.Column(db.DateTime, server_default = db.func.now(), onupdate = db.func.now())

    def toBrowse(self):
        return {"link":self.link, "title":self.title}
    def toContent(self):
        return {"link":self.link, "title":self.title, "content":Markup(markdown.markdown(self.content))}

class ProblemDb(db.Model):
    __tablename__ = 'problem'
    id            = db.Column(db.Integer, primary_key = True)
    link          = db.Column(db.String(128))
    title         = db.Column(db.String(256))
    priority      = db.Column(db.Integer, server_default = "1")
    version       = db.Column(db.Integer, server_default = "1")
    description   = db.Column(db.Text)
    questions     = db.Column(db.Text)

    def toBrowse(self):
        return {"link":self.link, "title":self.title}
    def toContent(self):
        return {"id": self.id, "link":self.link, "title":self.title, "description":Markup(markdown.markdown(self.description, extensions=["fenced_code"]))}

class SolutionDb(db.Model):
    __tablename__ = 'solution'
    id            = db.Column(db.Integer, primary_key = True)
    ques_id       = db.Column(db.Integer)
    ques_title    = db.Column(db.String(256))
    user          = db.Column(db.String(128))
    answers       = db.Column(db.Text)
    version       = db.Column(db.Integer, server_default = "1")
    score         = db.Column(db.Float, server_default = "1")
    results       = db.Column(db.Text)
    edit_time     = db.Column(db.DateTime, server_default = db.func.now(), onupdate = db.func.now())

    def toDict(self, link):
        return {"user":self.user, "score":int(self.score), "results":self.results}

class MazeDb(db.Model):
    __tablename__ = 'maze'
    id            = db.Column(db.Integer, primary_key = True)
    title         = db.Column(db.String(256))
    question      = db.Column(db.Text)
    visit         = db.Column(db.Integer, server_default = "0")
    success       = db.Column(db.Integer, server_default = "0")
    path_first    = db.Column(db.String(256))
    visit_first   = db.Column(db.Integer, server_default = "0")
    path_second   = db.Column(db.String(256))
    visit_second  = db.Column(db.Integer, server_default = "0")
    path_third    = db.Column(db.String(256))
    visit_third   = db.Column(db.Integer, server_default = "0")
    path_fourth   = db.Column(db.String(256))
    visit_fourth  = db.Column(db.Integer, server_default = "0")

    def toDict(self):
        return {"title":self.title, "question":self.question,
                "visit":self.visit, "success":self.success}

class TreasureDb(db.Model):
    __tablename__ = 'treasure'
    id            = db.Column(db.Integer, primary_key = True)
    treasure_type = db.Column(db.String(256))
    description   = db.Column(db.Text)
    link          = db.Column(db.String(128), default=getShortLink)
    enabled       = db.Column(db.Boolean, server_default = "f")
    closed        = db.Column(db.Boolean, server_default = "t")
    maze_title    = db.Column(db.String(256))
    rate          = db.Column(db.Float, server_default = "1")
    content       = db.Column(db.Text)

    def toDict(self):
        return {"link":self.link,
                "type":self.treasure_type, 
                "description":self.description}

db.create_all()

admin.add_view(TaskModelView(TaskDb, db.session))
admin.add_view(ModelView(CommentDb, db.session))
admin.add_view(ArticleModelView(ArticleDb, db.session))
admin.add_view(ChallengeModelView(ProblemDb, db.session))
admin.add_view(SolutionModelView(SolutionDb, db.session))
admin.add_view(ModelView(MazeDb, db.session))
admin.add_view(ModelView(TreasureDb, db.session))

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

def success(dct):
    return make_response(jsonify(dct), 200)

def err(err_code, err_msg):
    return make_response(jsonify({"err_msg":err_msg}), err_code)

def getStat():
    def toActivity(task):
        ret = {}
        if task.edit_time:
            ret["time"] = task.edit_time.strftime("%Y/%m/%d")
        else:
            ret["time"] = None
        lst = task.email.split('@')
        if len(lst[0]) == 1:
            lst[0] = '*'
        elif len(lst[0]) == 2:
            lst[0] = '**'
        else:
            middle = '*'*(len(lst[0])-2)
            lst[0] = lst[0][0] + middle + lst[0][-1]
        ret["email"] = '@'.join(lst)
        if (task.status == statusEnum.sent):
            ret["tag"] = "等待点评"
            ret["tag_type"] = "danger"
        elif (task.status == statusEnum.browse):
            ret["tag"] = "点评完毕"
            ret["tag_type"] = "warning"
        elif (task.status == statusEnum.reviewed):
            ret["tag"] = "第{}次修改".format(task.review_time or 1)
            ret["tag_type"] = "primary"
        elif (task.status == statusEnum.finish):
            ret["tag"] = "完稿"
            ret["tag_type"] = "success"
        return ret

    stat = {}

    weekTime = datetime.datetime.utcnow() - datetime.timedelta(days = 7)
    monthTime = datetime.datetime.utcnow() - datetime.timedelta(days = 30)
    weekReviewCount = TaskDb.query.filter(TaskDb.edit_time > weekTime).filter(TaskDb.status >= statusEnum.browse).count()
    weekModifyCount = TaskDb.query.filter(TaskDb.edit_time > weekTime).filter(TaskDb.status >= statusEnum.reviewed).count()
    monthReviewCount = TaskDb.query.filter(TaskDb.edit_time > monthTime).filter(TaskDb.status >= statusEnum.browse).count()
    monthModifyCount = TaskDb.query.filter(TaskDb.edit_time > monthTime).filter(TaskDb.status >= statusEnum.reviewed).count()
    totalReviewCount = TaskDb.query.filter(TaskDb.status >= statusEnum.browse).count()
    totalModifyCount = TaskDb.query.filter(TaskDb.status >= statusEnum.reviewed).count()
    latestTime = TaskDb.query.filter(TaskDb.edit_time.isnot(None)).order_by(TaskDb.edit_time.desc()).first().edit_time

    latestTasks = TaskDb.query.filter(TaskDb.edit_time > monthTime).order_by(TaskDb.edit_time.desc())
    latestActivities = map(toActivity, latestTasks)
    
    stat['week'] = [weekReviewCount, weekModifyCount]
    stat['month'] = [monthReviewCount, monthModifyCount]
    stat['total'] = [totalReviewCount, totalModifyCount]
    stat['latest'] = "{}".format(latestTime.strftime("%Y年%m月%d日"))
    stat['activities'] = list(latestActivities)

    return stat

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
            print("Can not find attached file")
            return err(401, "Can not find attached file. It should be a pdf file.")

        try:
            email = formData["email"]
        except:
            print(f"Wrong parameters: {formData}")
            return err(400, "Wrong parameters")

        one_day_ago = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        t = TaskDb.query.filter_by(email = email).filter(TaskDb.add_time > one_day_ago).first()

        if t:
            print("Resume is submitted in 24 hours")
            return err(429, "You already submitted resume in 24 hours")

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

@app.route('/api/v1/maze/answer', methods=['POST'])
def mazeAnswer():
    data = request.json
    if data == None:
        return err(400, "No json data")
    try:
        title  = data['title']
        answer = data['answer'].lower()
    except:
        return err(400, "Wrong parameters")
    if len(answer) == 0:
        return err(400, "Empty answer")
    m = MazeDb.query.filter_by(title = title).with_for_update().first()
    if m == None:
        db.session.commit()
        return err(400, "Wrong question")
    if m.path_first == answer:
        m.visit_first += 1
        m.success += 1
    elif m.path_second == answer:
        m.visit_second += 1
        m.success += 1
    elif m.path_third == answer:
        m.visit_third += 1
        m.success += 1
    elif m.path_fourth == answer:
        m.visit_fourth += 1
        m.success += 1
    else:
        db.session.commit()
        return err(400, randomCurse())
    db.session.commit()

    n = MazeDb.query.filter_by(title = answer).with_for_update().first()
    if n == None:
        db.session.commit()
        return err(400, "Hmm, 服务器出现了一些故障，请联系管理员")
    n.visit += 1
    db.session.commit()

    # Check for treasures
    t = TreasureDb.query.filter_by(maze_title = answer, closed = False).with_for_update().first()
    if t != None:
        try:
            if random.uniform(0,1) < t.rate:
                db.session.commit()
                return success({"msg":"success", "data":n.toDict(), "treasure":t.toDict()})
        except:
            pass
        
    db.session.commit()
    return success({"msg":"success", "data":n.toDict()})

@app.route('/api/v1/maze/jump', methods=['POST'])
def mazeJump():
    data = request.json
    if data == None:
        return err(400, "No json data")
    try:
        title = data['title']
    except:
        return err(400, "Wrong parameters")
    m = MazeDb.query.filter_by(title = title).with_for_update().first()
    if m == None:
        db.session.commit()
        return err(400, "根本没这个题，骗谁啊")
    m.visit += 1
    db.session.commit()
    return success({"msg":"success", "data":m.toDict()})
        
@app.route('/api/v1/maze/treasure', methods=['POST'])
def mazeTreasure():
    data = request.json
    if data == None:
        return err(400, "No json data")
    try:
        link = data['link']
        content = data['content']
    except:
        return err(400, "Wrong parameters")

    t = TreasureDb.query.filter_by(link = link, enabled = True, closed = False).with_for_update().first()
    if t == None:
        return err(400, "这宝藏可能已经被人拿走了")
    t.content = content
    t.enabled = False
    t.closed = True
    db.session.commit()
    return success({"msg":"success"})

@app.route('/api/v1/challenge/answer/<link>', methods=['POST'])
def challengeAnswer(link):
    challenge = ProblemDb.query.filter_by(link = link).first()
    if challenge == None:
        return err(400, "Wrong questions")
    data = request.json
    if data == None:
        return err(400, "No json data")
    try:
        user = data['user']
        answers = data['answer']
        if len(user) == 0:
            return err(400, "请输入用户名")
    except:
        return err(400, "Wrong parameters")

    if len(answers) > 1000000:
        return err(400, "Answer is too long")

    questions = challenge.questions

    try:
        c = Challenge()
        score, results, err_msg = c.evaluate(link, questions, answers)
        if score == None:
            return err(400, err_msg)
    except Exception as e:
        print (e)
        return err(400, "Something is wrong but I don't know why")

    s = SolutionDb.query.filter_by(user = user, ques_id = challenge.id, version = challenge.version).first()
    if s == None:
        s = SolutionDb()
    elif s.score > score:
        return success({"msg":"success", "score":score})

    s.ques_id = challenge.id
    s.ques_title = challenge.title
    s.user = user
    s.answers = answers
    s.version = challenge.version
    s.score = score
    s.results = results
    db.session.add(s)
    db.session.commit()
    
    return success({"msg":"success", "score":score})

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/')
@app.route('/index')
def index():
    resp = make_response(render_template('index.html', footer=getFooter(), stat=getStat()))
    resp.cache_control.max_age = 300
    resp.cache_control.public  = True
    return resp

@app.route('/procedure')
def procedure():
    resp = make_response(render_template('procedure.html'))
    resp.cache_control.max_age = 360000
    resp.cache_control.public  = True
    return resp

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/example')
def example():
    resp = make_response(render_template('example.html'))
    resp.cache_control.max_age = 360000
    resp.cache_control.public  = True
    return resp

@app.route('/submit')
def submit():
    resp = make_response(render_template('submit.html'))
    resp.cache_control.max_age = 360000
    resp.cache_control.public  = True
    return resp

@app.route('/comment')
def route_comment():
    resp = make_response(render_template('comment.html'))
    resp.cache_control.max_age = 3600
    resp.cache_control.public  = True
    return resp

@app.route('/privacy')
def privacy():
    resp = make_response(render_template('privacy.html'))
    resp.cache_control.max_age = 360000
    resp.cache_control.public  = True
    return resp

@app.route('/terms_of_service')
def terms_of_service():
    resp = make_response(render_template('terms_of_service.html'))
    resp.cache_control.max_age = 360000
    resp.cache_control.public  = True
    return resp

# For challenge
@app.route('/challenge')
@app.route('/challenge/')
def route_challenge():
    challengesRaw = ProblemDb.query.filter(ProblemDb.version > 0).order_by(ProblemDb.priority).all()
    challenges = [c.toBrowse() for c in challengesRaw]
    return render_template('challenge.html', challenges = challenges)

@app.route('/challenge/<link>')
@app.route('/challenge/<link>/')
def challengeContent(link):
    challengeRaw = ProblemDb.query.filter_by(link = link).first()
    if challengeRaw == None:
        return "不许瞎跑，哪儿有这个链接"
    challenge = challengeRaw.toContent()
    title = challenge['title']
    description = challenge['description']

    return render_template("challengeContent.html", title = title, description = description, ques_link = link)

@app.route('/challenge/<link>/question.txt')
def challengeQuestion(link):
    challengeRaw = ProblemDb.query.filter_by(link = link).first()
    if challengeRaw == None:
        return "不许瞎跑，哪儿有这个链接"
    else:
        return Response(challengeRaw.questions, mimetype='text/csv')

@app.route('/challenge/<link>/rank')
def challengeRank(link):
    challenge = ProblemDb.query.filter_by(link = link).first()
    if challenge == None:
        return "不许瞎跑，哪儿有这个链接"
    else:
        solutions = SolutionDb.query.filter_by(ques_id = challenge.id, version = challenge.version).order_by(SolutionDb.score.desc()).limit(50).all()
        if link == "black_and_white":
            solutions.sort(key = lambda x: (-x.score, float(re.search("\((.*?)\)",x.results.split('|')[-1]).groups()[0])))

        return render_template("challengeRank.html", data = [s.toDict(link) for s in solutions])


# For the maze
@app.route('/maze/')
def route_maze():
    return render_template("maze.html")

@app.route('/maze/treasure/<link>')
def route_maze_treasure(link):
    t = TreasureDb.query.filter_by(link = link).with_for_update().first()
    if t != None and t.closed == False:
        t.enabled = True
        db.session.commit()
        return render_template("treasure.html", description = t.description, link = t.link)
    return "并没有这个宝藏，你是不是想钱想疯了？"

@app.route('/maze/validate')
def mazeValidate():
    titleDict = {}
    titles = [(None, "1")]
    invalidTitles = []
    while titles:
        before, title = titles.pop()
        if title in titleDict:
            titleDict[title] += 1
            continue
        else:
            titleDict[title] = 1
        m = MazeDb.query.filter_by(title = title).first()
        if m == None:
            invalidTitles.append((before, title))
        else:
            if m.path_first:
                titles.append((title, m.path_first))
            if m.path_second:
                titles.append((title, m.path_second))
            if m.path_third:
                titles.append((title, m.path_third))
            if m.path_fourth:
                titles.append((title, m.path_fourth))
        db.session.commit()
    return "<pre>Titles: {}\nInvalid: {}\n</pre>".format(titleDict, invalidTitles)


@app.route('/article/<link>')
def articleContent(link):
    articleRaw = ArticleDb.query.filter_by(link = link).first()
    if articleRaw == None:
        title = "没有这篇文章。"
        content = ""
    else:
        article = articleRaw.toContent()
        title = article["title"]
        content = article["content"]
    resp = make_response(render_template('articleContent.html', title=title, content=content))
    resp.cache_control.max_age = 36000
    resp.cache_control.public  = True
    return resp

@app.route('/article')
def article():
    articlesRaw = ArticleDb.query.order_by(ArticleDb.priority, ArticleDb.edit_time.desc()).all()
    articles = [a.toBrowse() for a in articlesRaw]
    resp = make_response(render_template('article.html', articles = articles))
    resp.cache_control.max_age = 36000
    resp.cache_control.public  = True
    return resp

if __name__ == '__main__':
    app.run(debug = True)
