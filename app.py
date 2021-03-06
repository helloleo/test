#!/usr/bin/env python
#coding=utf-8

import os, re

import time
from flask import Flask, request, render_template, session, flash, redirect, url_for, _request_ctx_stack
from flaskext.sqlalchemy import SQLAlchemy
from datetime import datetime
from markdown import markdown

SQLALCHEMY_DATABASE_URI = 'mysql://root:helloleo@localhost/text?charset=utf8'
SECRET_KEY = os.urandom(24)
USERNAME = 'leo'
PASSWORD = 'helloleo'

app = Flask(__name__)
app.config.from_object(__name__)
db = SQLAlchemy(app)

@app.before_request
def before_request():
    method = request.form.get('_method', '').upper()
    if method:
        request.environ['REQUEST_METHOD'] = method
        ctx = _request_ctx_stack.top
        ctx.url_adapter.default_method = method
        assert request.method == method

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    origin = db.Column(db.Text)
    title = db.Column(db.String(80))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
        backref=db.backref('posts', lazy='dynamic'))

    def __init__(self, origin, title, body, category, pub_date=None):
        self.origin = origin
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
    dct = {}
    meta_regex = re.compile(
        r"^\s*(?:-|=){3,}\s*\n((?:.|\n)+?)\n\s*(?:-|=){3,}\s*\n*",
        re.MULTILINE
    )
    match = re.match(meta_regex, content)
    if not match:
        dct['body'] = markdown(content)
    else:
        meta = match.group(1)
        meta = re.sub(r'\r\n|\r|\n', '\n', meta)
        k = v = None
        for meta in meta.split('\n'):
            meta = meta.replace('\t', '    ')
            if meta.startswith('  ') and k:
                dct[k] = dct[k] + '\n' + meta.strip()
            if ':' in meta and not meta.startswith(' '):
                index = meta.find(':')
                k, v = meta[:index], meta[index + 1:]
                k, v = k.strip(), v.strip()
                dct[k] = v
        text = content[match.end():].strip()
        dct['body'] = markdown(text)
    return dct

@app.route('/note/', methods=['POST', 'GET'])
def add():
    if request.method == 'GET':
        return render_template('add.html')
    if request.method == 'POST':
        """
        data = read(request.form['content'])
        new_category = None
        categorys = db.session.query(Category).all()
        for category in categorys:
            if data['category'] == category.name:
                new_category = category
        if new_category == None:
            new_category = Category(data['category'])
            db.session.add(new_category)
        new_post = Post(request.form['content'], data['title'], data['body'], new_category)
        db.session.add(new_post)
        db.session.commit()
        return 'all ok'
        """
        data = read(request.form['content'])
        post.origin = request.form['content']
        post.body = data['body']
        if not data.has_key('title') or data['title'] == '':
            data['title'] = datetime.utcnow()
        post.title = data['title']
        if not data.has_key('category') or data['category'] == '':
            data['category'] = 'uncategorized'
        new_category = None
        categorys = Category.query.all()
        for category in categorys:
            if data['category'] == category.name:
                new_category = category
        if new_category == None:
            new_category = Category(data['category'])
            db.session.add(new_category)
        post.category = new_category
        if data.has_key('date') and data['date'] != '':
            try:
                post.pub_date = datetime.strptime(data['date'], "%Y-%m-%d")
            except:
                pass
        db.session.add(post)
        db.session.commit()
        return render_template('note.html', post=post)

@app.route('/note/<int:id>/', methods=['POST', 'GET', 'PUT', 'DELETE'])
def note(id):
    post = Post.query.filter_by(id=id).first_or_404()
    if request.method == 'POST':
        pass
    if request.method == 'GET':
        return render_template('note.html', post = post)
    if request.method == 'PUT':
        data = read(request.form['content'])
        post.origin = request.form['content']
        post.body = data['body']
        if not data.has_key('title') or data['title'] == '':
            data['title'] = datetime.utcnow()
        post.title = data['title']
        if not data.has_key('category') or data['category'] == '':
            data['category'] = 'uncategorized'
        new_category = None
        categorys = Category.query.all()
        for category in categorys:
            if data['category'] == category.name:
                new_category = category
        if new_category == None:
            new_category = Category(data['category'])
            db.session.add(new_category)
        post.category = new_category
        if data.has_key('date') and data['date'] != '':
            try:
                post.pub_date = datetime.strptime(data['date'], "%Y-%m-%d")
            except:
                pass
        db.session.add(post)
        db.session.commit()
        return render_template('note.html', post=post)
    if request.method == 'DELETE':
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('list'))

@app.route('/login/', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME'] or request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid username or password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('list'))
    return render_template('login.html', error=error)

@app.route('/')
def list():
    posts = Post.query.all()
    return render_template('list.html', list=posts)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
