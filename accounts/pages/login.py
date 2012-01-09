from accounts import app, db, database
from flaskext.sqlalchemy import SQLAlchemy

from flask import Flask, request, flash, redirect, url_for, render_template
from flask import session
from flaskext.wtf import Form, TextField, PasswordField, validators
from werkzeug.datastructures import ImmutableMultiDict

import hashlib

class LoginForm(Form):
    username = TextField('Username',
                         validators=[validators.Required(),
                                     validators.Length(min=3,max=8)])
    password = PasswordField('Password',
                         validators=[validators.Required(),
                                     validators.Length(max=50)])
                                     
def render_error():
    form = LoginForm(ImmutableMultiDict())
    return render_template("login.html", form=form, error="Wrong username or password.")

@app.route("/login", methods=['GET', 'POST'])
@app.route("/login/", methods=['GET', 'POST'])
@app.allow('all')
def login():
    form = LoginForm()
    if form.is_submitted():
        if form.validate_on_submit():
            user = database.User.query.get(form.username.data)
            if user is None:
                return render_error()
            if not user.verify_password(form.password.data):
                return render_error()
            flash("Login successful.")
            session['username'] = form.username.data
            return redirect(url_for("index"))
        else:
            return render_error()
    return render_template("login.html", form=form)
