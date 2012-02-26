#coding=utf-8

import re

from flask import Flask, request, render_template
from flaskext.sqlalchemy import SQLAlchemy
from datetime import datetime
from markdown import markdown

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:helloleo@localhost/flask?charset=utf8'
db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
        backref=db.backref('posts', lazy='dynamic'))

    def __init__(self, title, body, category, pub_date=None):
        self.title = title
        self.body = body
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.category = category

    def __repr__(self):
        return '<Post %r>' % self.title

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Category %r>' % self.name

def read(content):
    meta_regex = re.compile(
        r"^\s*(?:-|=){3,}\s*\n((?:.|\n)+?)\n\s*(?:-|=){3,}\s*\n*",
        re.MULTILINE
    )
    match = re.match(meta_regex, content)
    if not match:
        logger.error("No metadata in: %s" % self.filepath)
        return None
    meta = match.group(1)
    meta = re.sub(r'\r\n|\r|\n', '\n', meta)
    dct = {}
    k = v = None
    for meta in meta.split('\n'):
        meta = meta.replace('\t', '    ')
        if meta.startswith('  ') and k:
            dct[k] = dct[k] + '\n' + meta.lstrip()
        if ':' in meta and not meta.startswith(' '):
            index = meta.find(':')
            k, v = meta[:index], meta[index + 1:]
            k, v = k.rstrip(), v.lstrip()
            dct[k] = v
    text = content[match.end():]
    dct['content'] = markdown(text)
    dct['origin'] = content
    return dct

@app.route('/add/', methods=['POST', 'GET'])
def add():
    if request.method == 'GET':
        return render_template('add.html')
    if request.method == 'POST':
        data = read(request.form['content'])
        categorys = db.session.query(Category).all()
        new_category = None
        for category in categorys:
            if data['category'] == category.name:
                new_category = category
        if new_category != None:
            new_post = Post(data['title'], data['content'], new_category)
            db.session.add(new_post)
            db.session.commit()
        else:
            new_category = Category(data['category'])
            new_post = Post(data['title'], data['content'], new_category)
            db.session.add(new_category)
            db.session.add(new_post)
            db.session.commit()
        return 'all ok'

@app.route("/")
def hello():
    return render_template('index.html', tips=u"十年之前change")

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
