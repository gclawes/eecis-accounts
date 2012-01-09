from accounts import app, db, database
from flaskext.sqlalchemy import SQLAlchemy
from accounts.database import *
from flask import Flask, request, flash, redirect, url_for, render_template, g
from flaskext.wtf import Form, PasswordField, validators, SelectField, TextAreaField
from werkzeug.datastructures import ImmutableMultiDict

class UpgradeForm(Form):
    sponsor = SelectField('Sponsor',
                         choices=[(s.username, ''.join((s.last_name, ', ', s.first_name))) for s in database.get_sponsors()],
                         validators=[validators.Required()])
    reason = TextAreaField('Reason for Upgrade', validators=[validators.Required()])

@app.route('/upgrade_account/', methods=['GET', 'POST'])
@app.allow('logged_in')
def upgrade_account():
    user = g.user
    form = UpgradeForm()
    if form.is_submitted():
        if form.validate_on_submit():
            user.sponsor = form.sponsor.data
            if user.comments is None:
                user.comments = '\nUser provided upgrade reason:\n' + form.reason.data
            else:
                user.comments += '\nUser provided upgrade reason:\n' + form.reason.data
            user.status = 'pending_sponsor'
            db.session.add(user)
            db.session.commit()
            flash("Upgrade request sent!")
        else:
            return render_template("upgrade_account.html", form=form, error="There was an error with your submission")
    form = UpgradeForm(ImmutableMultiDict())
    return render_template("upgrade_account.html", form=form)

app.add_url_rule('/upgrade_account/', 'upgrade_account', methods=['GET', 'POST'])