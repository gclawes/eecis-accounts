from accounts import app
from flask import render_template, request, redirect, flash, g, session, url_for
from accounts.database import *
from accounts.mail import send_token
from flaskext.wtf import Form, TextField, PasswordField, validators
from werkzeug.datastructures import ImmutableMultiDict
from uuid import uuid4
from time import time

class ResetForm(Form):
    password = PasswordField('Password',
                         validators=[validators.Required(),
                                     validators.Length(min=8,max=50),
                                     validators.CrackLib()])
    pw_confirm = PasswordField('Confirm Password',
                         validators=[validators.Required(),
                                     validators.Length(min=8,max=50),
                                     validators.EqualTo('password', message='Passwords do not match.')])
                                     
# This should probably request some other verification, like DOB.
class RequestResetForm(Form):
    username = TextField('Username',
                         validators=[validators.Required(),
                                     validators.Length(min=3,max=8),
                                     validators.EntryExists(User, User.username)])
    dob = TextField('Date of Birth (DD/MM/YYYY)',
                        validators=[validators.Required(),
                                    validators.Date(format='%m/%d/%Y', message='Invalid format. Please use mm/dd/yy.')])
    birth_city = TextField('Birth City',
                        validators=[validators.Required()])

@app.route('/reset_password/', methods=['GET', 'POST'])
@app.route('/reset_password/token/<string:token>/', methods=['GET', 'POST'])
@app.allow('all')
def reset_password(token = None):
    if 'reset_password' in session:
        user = User.query.get(session['reset_password'])
        okay = False
        if token is not None:
            print user.reset_token
            print token
            if token != user.reset_token:
                session.pop('cas_id', None)
                session.pop('reset_password')
                flash("There was an error when trying to reset your password. Make sure you are using the same browser you requested the password reset in.")
                return redirect(url_for('index'))
            elif user.reset_token_time != 0 and (int(time()) - 1800) > user.reset_token_time:
                print "reset_token_time: %d %d " % (user.reset_token_time, int(time()))
                session.pop('cas_id', None)
                session.pop('reset_password')
                flash("You are attempting to reset with an invalid or expired token, please re-submit your request.")
                return redirect(url_for("reset_password"))
        elif 'cas_id' in session:
            if session['cas_id'] != user.udel_id:
                flash("Invalid UDel ID")
                session.pop('reset_password')
                session.pop('cas_id', None)
                return redirect(url_for("reset_password"))
        else:
            session.pop('reset_password')
            flash("You seem to be lost.")
            return redirect(url_for('index'))

        form = ResetForm()
        if form.is_submitted():
            if form.validate():
                user.password = form.password.data
                user.status = 'reset_password'
                print "reset_token_time: %d" % user.reset_token_time
                user.reset_token_time = 0
                db.session.add(user)
                db.session.commit()
                flash("Your password has been reset. Please allow time for the servers to reflect the changes.")
                session.pop('cas_id', None)
                session.pop('reset_password')
                return redirect(url_for('index'))
            else:
                form = ResetForm(ImmutableMultiDict())
                return render_template('reset_password_final.html', form=form)
        return render_template('reset_password_final.html', form=form)
    else:
        form = RequestResetForm()
        if form.is_submitted():
            if form.validate():
                user = User.query.get(form.username.data)
                if not user.account_details_complete():
                    form = RequestResetForm(ImmutableMultiDict())
                    return render_template('reset_password.html', form=form, error="This account is missing information needed to reset the password. Please contact labstaff to have your password reset.")
                if user.dob != form.dob.data or user.birth_city != form.birth_city.data:
                    form = RequestResetForm(ImmutableMultiDict())
                    return render_template('reset_password.html', form=form, error="Invalid information.")
                session['reset_password'] = form.username.data
                if user.udel_id is None:
                    token = str(uuid4())
                    user.reset_token = token
                    user.reset_token_time = time()
                    print "reset_token_time: %d" % user.reset_token_time
                    db.session.add(user)
                    db.session.commit()
                    # Print this for now so we can test it
                    print token
                    # send the user an email with the token
                    send_token(user.username, user.email, user.reset_token)
                    return render_template('reset_password_in_mail.html')
                else:
                    session['cas_redirect'] = url_for('reset_password')
                    return redirect(url_for('cas'))
            else:
                form = RequestResetForm(ImmutableMultiDict())
                return render_template('reset_password.html', form=form, error="Invalid information.")
        return render_template('reset_password.html', form=form)        
