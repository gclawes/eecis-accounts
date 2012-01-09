from accounts import app, db, database
from flaskext.sqlalchemy import SQLAlchemy
from accounts.database import *
from flask import Flask, request, flash, redirect, url_for, render_template, g
from flask import jsonify, session
from flaskext.wtf import Form, TextField, PasswordField, validators, DateField
from flaskext.wtf import SelectField, TextAreaField, SelectMultipleField
from flaskext.wtf import widgets, RadioField, BooleanField
from wtfrecaptcha.fields import RecaptchaField
from werkzeug.datastructures import ImmutableMultiDict
from jinja2 import Markup, escape

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class RegisterForm(Form):
    username = TextField('Username',
                         validators=[validators.Required(),
                                     validators.Length(min=3,max=8),
                                     validators.UniqueColumn(database.User, database.User.username, message='This username is taken.')])
    password = PasswordField('Password',
                         validators=[validators.Required(),
                                     validators.Length(min=8,max=50)])                                     
    first_name = TextField('First Name',
                         validators=[validators.Required()])
    last_name = TextField('Last Name',
                         validators=[validators.Required()])
    pw_confirm = PasswordField('Confirm Password',
                         validators=[validators.Required(),
                                     validators.Length(min=8,max=50),
                                     validators.EqualTo('password', message='Passwords do not match.')])
    dob = TextField('Date of Birth (MM/DD/YYYY)',
                         validators=[validators.Required(),
                                     validators.Date(format='%m/%d/%Y', message='Invalid format. Please use mm/dd/yyyy.')])
    email = TextField('E-mail Address',
                         validators=[validators.Email(),
                                    validators.Required(),
                                    validators.UniqueColumn(database.User, database.User.email, message='This e-mail is in use by another account.')])
    sponsor = SelectField('Sponsor',
                         choices=[(s.username, ''.join((s.last_name, ', ', s.first_name))) for s in database.get_sponsors()],
                         validators=[validators.Required()])
    grad_date = TextField('Graduation Date (MM/YYYY)',
                         validators=[validators.Required(),
                                     validators.Date(format = '%m/%Y', message = 'Invalid format. Please use mm/yyyy')])
    description = TextAreaField('Description of Usage')
    acct_type = RadioField(choices=[('acad', 'Academic'), ('research', 'Research & Academic')],
                         validators=[validators.Required()])
    captcha = RecaptchaField(public_key='6LdeFcwSAAAAAJF1ccPQ4j5Y0Q0iVULdXpRArpcp',
                             private_key='6LdeFcwSAAAAAFv_xLOVLCPAyUQ_abubmG8oUdOw',
                             secure=True)
                         
class RegisterIntroForm(Form):
    has_udelid = RadioField('Do you have a UDelNet ID?',
                         choices=[('yes', 'Yes'), ('no', 'No')],
                         validators=[validators.Required()])

@app.route("/register", methods=['GET', 'POST'])
@app.route("/register/", methods=['GET', 'POST'])
@app.allow('all')
def register():
    if session.get('cas_id') is None:
        form = RegisterIntroForm()
        if form.is_submitted() and form.validate_on_submit():
            if form.has_udelid.data == "yes":
                if 'cas_id' in session:
                    session.pop('cas_id')
                session['cas_redirect'] = url_for('register2')
                return redirect(url_for('cas'))
            else:
                session['cas_id'] = None
                return redirect(url_for('register2'))
        else:
            return render_template('register_intro.html', form=form)
    else:
        session.pop('cas_id')
        return redirect(url_for('register'))

@app.route("/register_2/", methods=['GET', 'POST'])
def register2():
    form = RegisterForm(captcha={'ip_address' : request.remote_addr})
    if session.get('cas_id', None) is not None:
        if database.User.query.filter(database.User.udel_id == session['cas_id']).count() > 0:
            flash("That UDelNet ID has already registered an account.")
            session.pop('cas_id')
            return redirect(url_for('register'))
        form.email.data = session['cas_id'] + '@udel.edu'
        
    if form.is_submitted():
        if form.validate_on_submit():
            user = database.User(form.username.data, form.password.data)
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.dob = form.dob.data
            user.email = form.email.data
            user.sponsor = form.sponsor.data
            user.grad_date = form.grad_date.data
            user.status = 'pending_sponsor'
            if form.acct_type.data == 'acad':
                user.add_domain('acad')
            else:
                user.add_domains('acad', 'research')
            if session['cas_id'] is not None:
                user.udel_id = session['cas_id']
            db.session.add(user)
            db.session.commit()
            flash('Registration successful!')
            return redirect(url_for("index"))
        else:
            return render_template("register.html", form=form, error="There was an error with your submission")
    return render_template("register.html", form=form)
    
# Add user functionality for labstaff/admin. Account bypasses approval process and is instantly active
@app.route("/labstaff_add_user", methods=['GET', 'POST'])
@app.route("/labstaff_add_user/", methods=['GET', 'POST'])
@app.allow('admin', 'labstaff')
def labstaff_add_user():
    # Labstaff have the ability to choose 'staff' as a sponsor
    RegisterForm.sponsor = SelectField('Sponsor',
                         choices=[(s.username, ''.join((s.last_name, ', ', s.first_name))) for s in database.get_sponsors(True)],
                         validators=[validators.Required()])
    form = RegisterForm()        
    if form.is_submitted():
        if form.validate_on_submit():
            user = database.User(form.username.data, form.password.data)
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.dob = form.dob.data
            user.email = form.email.data
            user.sponsor = form.sponsor.data
            user.grad_date = form.grad_date.data
            user.status = 'pending_create'
            if form.acct_type.data == 'acad':
                user.add_domain('acad')
            else:
                user.add_domains('acad', 'research')
            db.session.add(user)
            db.session.commit()
            flash('User account created.')
            return redirect(url_for("index"))
        else:
            return render_template("labstaff_add_user.html", form=form, error="There was an error with your submission")
    return render_template("labstaff_add_user.html", form=form)
    
@app.route('/edit/', methods=['GET', 'POST'])
@app.route('/edit/<int:uid>/', methods=['GET', 'POST'])
@app.allow('logged_in')
def edit_user(uid = -1):
    if uid == -1:
        return redirect(url_for('edit_user', uid=g.user.uid))
    user = User.query.filter(User._uid == uid).all()
    if len(user) == 0:
        flash('User not found!')
        return redirect(url_for("index"))
    user = user[0]
    self_editing = False
    sponsor_editing = False
    labstaff_editing = g.user_is_labstaff
    admin_editing = g.user_is_admin
    
    if not (g.user_is_admin or g.user_is_labstaff):
        # If a user isn't an admin or a sponsor, they can only see their own page
        if 'sponsor' not in g.user.get_domains():
            if g.user.uid != user.uid:
                flash("You have wandered somewhere you do not belong.")
                return redirect(url_for('index'))
            else:
                self_editing = True
        else:
            # If they're not an admin but are a sponsor, they need to be this user's sponsor
            if g.user.username != user.sponsor:
                flash("You have wandered somewhere you do not belong.")
                return redirect(url_for('index'))
            else:
                sponsor_editing = True
    
    enabled_fields = []
    
    class EditForm(Form):
        username = TextField('Username',
                            validators = [validators.LengthOrEmpty(min=3, max=8)])
        first_name = TextField('First Name')
        last_name = TextField('Last Name')
        dob = TextField('Date of Birth (MM/DD/YYYY)',
                            validators=[validators.Date(format='%m/%d/%Y', message='Invalid format. Please use mm/dd/yyyy.')])
        email = TextField('E-mail Address',
                            validators=[validators.Email()])
        sponsor = SelectField('Sponsor', 
                            choices=[(s.username, ''.join((s.last_name, ', ', s.first_name))) for s in database.get_sponsors(True)])
        grad_date = TextField('Graduation Date (MM/YYYY)',
                            validators=[validators.Date(format = '%m/%Y', message = 'Invalid format. Please use mm/yyyy')])
        acct_type = RadioField(choices=[('acad', 'Academic'), ('research', 'Research & Academic')])
        comments = TextAreaField('Comments')
        status = TextField('Status')
        
    
    
    
    # First Name and Last Name
    # if labstaff_editing or admin_editing:
        

    if user.status in ('pending_sponsor', 'pending_labstaff') and g.user_is_admin:
        enabled_fields.extend(['admin_approval', 'acct_type'])
        EditForm.admin_approval = RadioField(choices=[('approve', 'Approve'), ('deny', 'Deny'), ('postpone', 'Postpone')])
    elif user.status == 'pending_sponsor' and 'sponsor' in g.user.get_domains():
        enabled_fields.append('sponsor_approval')
        EditForm.sponsor_approval = RadioField(choices=[('approve', 'Approve'), ('deny', 'Deny'), ('postpone', 'Postpone')])
    else:
        pass

    if g.user_is_admin or g.user_is_labstaff:
        enabled_fields.extend(['comments','sponsor', 'email', 'dob', 'first_name', 'last_name'])
        
    if g.user_is_admin or g.user_is_labstaff:
        enabled_fields.extend(['password', 'pw_confirm'])
        EditForm.password = PasswordField('Password', 
                        validators = [validators.LengthOrEmpty(min=8, max=50)])                                    
        EditForm.pw_confirm = PasswordField('Confirm Password',
                        validators = [validators.LengthOrEmpty(min=8, max=50),
                                        validators.EqualTo('password', message='Passwords do not match.')])
    if self_editing:
        EditForm.current_password = PasswordField('Current Password',
                    validators = [validators.LengthOrEmpty(max=50),
                                  validators.Required()])

    form = EditForm()
    
    if form.is_submitted():
        if form.validate_on_submit():
            
            
            if form.username.data != '':
                user.username = form.username.data
            if form.password.data != '':
                user.password = form.password.data
            if form.first_name.data != '':
                user.first_name = form.first_name.data
            if form.last_name.data != '':
                user.last_name = form.last_name.data
            if form.dob.data != '':
                user.dob = form.dob.data # TODO: Extra validation on birth date?
            if form.email.data != '':
                user.email = form.email.data # TODO: More validation on email
                                            # Auto-fill udel id field.
                                            # Make sure email isn't used
            if form.sponsor.data != '':
                user.sponsor = form.sponsor.data
            if form.grad_date.data != '':
                user.grad_date = form.grad_date.data
            # if form.description.data != '': #not implemented in the user object yet.
            #     user.comments = form.description.data
            if user.is_active() and form.disable.data:
                user.status = 'pending_disable'
            if user.is_disabled() and not form.disable.data:
                user.status = 'reactivate'
            if form.acct_type.data == 'acad':
                user.add_domain('acad')
            else:
                user.add_domains('acad', 'research')
            db.session.add(user)
            db.session.commit()
            flash("User updated.")
        else:
            return render_template("edit_user.html", form=form, error="There was an error with your submission", edit_user = user)

    form = EditForm(ImmutableMultiDict())
    form.username.data = user.username
    form.first_name.data = user.first_name
    form.last_name.data = user.last_name
    form.dob.data = user.dob
    form.email.data = user.email
    form.sponsor.data = user.sponsor
    form.grad_date.data = user.grad_date
    form.status.data = user.status
    if 'acad' in user.get_domains() and not 'research' in user.get_domains():
        form.acct_type.data = 'acad'
    if 'acad' in user.get_domains() and 'research' in user.get_domains():
        form.acct_type.data = 'research'
    if 'other' in user.get_domains():
        form.acct_type.data = 'other'
        
    ajax_fields = []
    # Let's build the display form
    sections = ['Account Details']
    display = {'Account Details' : []}
    d = display['Account Details']
    # The tuple will go label, field, errors (list)
    d.append(('Username', Markup('<label>%s</label>' % user.username), 'username', None))
    d.append(('UID', Markup('<label>%s</label>' % user.uid), 'uid', None))

    # First Name and Last Name
    if labstaff_editing or admin_editing:
        d.append(('First Name', form.first_name(), 'first_name', form.first_name.errors))
        ajax_fields.append('first_name')
        d.append(('Last Name', form.last_name(), 'last_name', form.last_name.errors))
        ajax_fields.append('last_name')
    else:
        d.append(('First Name', Markup('<label>%s</label>' % user.first_name), 'first_name', None))
        d.append(('Last Name', Markup('<label>%s</label>' % user.last_name), 'last_name', None))

    # Date of Birth
    if self_editing or labstaff_editing or admin_editing:
        d.append(('Date of Birth (MM/DD/YYYY)', form.dob(), 'dob', form.dob.errors))
        ajax_fields.append('dob')
    else:
        d.append(('Date of Birth (MM/DD/YYYY)', user.dob, 'dob', None))
        
    # Change Password
    if self_editing or labstaff_editing or admin_editing:
        sections.append('Change Password')
        pw_block = []
        display['Change Password'] = pw_block
        if self_editing:
            pw_block.append(('Current Password', form.current_password(), 'current_password', form.current_password.errors))
            ajax_fields.append('current_password')
        pw_block.append(('New Password', form.password(), 'password', form.password.errors))
        pw_block.append(('Confirm New Password', form.password(), 'pw_confirm', form.pw_confirm     .errors))
        ajax_fields.append('password')
        ajax_fields.append('pw_confirm')
        
            
    
        
    
    if self_editing:
        d.append(('Current Password:', form.current_password(), 'current_password', form.current_password.errors))
    d.append(('Test', Markup('<a href="test">Test</a>'), 'test', None))

    # form.description.data = user.comments
    # if user.is_disabled():
    #     form.disable.data = True
    # else:
    #     form.disable.data = False
    
    return render_template("edit_user.html", form=form, edit_user = user, enabled_fields = enabled_fields, display=display, sections=sections)

@app.route('/json/register/validate/')
@app.route('/json/register/validate/<string:field>')
@app.allow('all')
def json_register_validate(field = 'test'):
    # Let's assume that everyone is able to choose staff.
    # The option won't appear in the dropdown, and will also not be allowed
    # once the form is submitted. Nobody who is not messing with things
    # will be affected.
    RegisterForm.sponsor = SelectField('Sponsor',
                         choices=[(s.username, ''.join((s.last_name, ', ', s.first_name))) for s in database.get_sponsors(True)],
                         validators=[validators.Required()])
    form = RegisterForm()
    try:
        field = getattr(form, field)
    except AttributeError:
        return jsonify(okay=False, error='What?')
    field.data = request.args.get('data', '', type=str)
    if field.validate(form):
        return jsonify(okay=True)
    else:
        return jsonify(okay=False, error=field.errors[0])
		
app.add_url_rule('/edit/<int:uid>/', 'edit_user', methods=['GET', 'POST'])
