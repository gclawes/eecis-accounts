from accounts import app, db, database
from flaskext.sqlalchemy import SQLAlchemy
from accounts.database import *
from flask import Flask, request, flash, redirect, url_for, render_template, g
from flaskext.wtf import Form, PasswordField, validators
from werkzeug.datastructures import ImmutableMultiDict

class PasswordForm(Form):
    old_password = PasswordField('Old Password', 
                        validators = [validators.Length(min=8, max=50)])
    password = PasswordField('Password', 
                        validators = [validators.LengthOrEmpty(min=8, max=50)])
    pw_confirm = PasswordField('Confirm Password',
                                            validators = [validators.LengthOrEmpty(min=8, max=50),
                                                            validators.EqualTo('password', message='Passwords do not match.')])

@app.route('/change_password/', methods=['GET', 'POST'])
@app.allow('logged_in')
def change_password():
    user = g.user
    form = PasswordForm()
    if form.is_submitted():
        if form.validate_on_submit():
            if user.verify_password(form.old_password.data):
                if form.password.data != '':
                    user.password = form.password.data
                db.session.add(user)
                db.session.commit()
                flash("Password changed successfully. Please allow a few minutes for the change to propogate to the login servers.")
            else:
                flash("Old Password is incorrect")
        else:
            return render_template("change_password.html", form=form, error="There was an error with your submission")
    form = PasswordForm(ImmutableMultiDict())
    
    return render_template("change_password.html", form=form)

app.add_url_rule('/change_password/', 'change_password', methods=['GET', 'POST'])
