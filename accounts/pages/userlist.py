from accounts import app
from flask import render_template, request, redirect, flash, g
from accounts.database import *
from flaskext.sqlalchemy import get_debug_queries
from sqlalchemy.sql.expression import asc, desc
from flaskext.wtf import Form, BooleanField
from werkzeug.datastructures import ImmutableMultiDict
from sqlalchemy.sql import or_
from flaskext.wtf import Form, TextField, RadioField, validators
from datetime import date

@app.route('/users', methods=['GET', 'POST'])
@app.route('/users/page/<int:page>', methods=['GET', 'POST'])
@app.allow('admin', 'labstaff', 'sponsor')
def userlist(page = 1, pending = False, sponsored = False, rolloffs = False):
    # We need to make sure sponsors without admin/labstaff permissions don't go
    # browsing through all the users data
    domains = g.user.get_domains()
    if ((sponsored and 'sponsor' not in domains) or
       (not sponsored and (not g.user_is_labstaff) and (not g.user_is_admin)) or
       (rolloffs and (not g.user_is_labstaff) and (not g.user_is_admin))):  
        flash("Unauthorized.")
        return redirect('index')
    if (pending or rolloffs) and request.method == "POST":
        form = Form(request.form)
        if not form.validate():
            flash("There was an error with your submission.")
            redirect(request.url)
        users = [user for user, value in request.form.iteritems() if value == 'approve']
        if rolloffs:
             users = [user for user, value in request.form.iteritems()]
        users = [User.username == user for user in users]
        if len(users) > 0:
            query = User.query.filter(or_(*users))
            if sponsored:
                # Filter and make sure we only get this sponsors users, for security
                query = query.filter(User.sponsor == g.user.username)
            users = query.all()
            for user in users:
                if sponsored:
                    user.status = 'pending_labstaff'
                elif rolloffs:
                    user.status = 'pending_rolloff'
                else:
                    user.status = 'pending_create'
                db.session.add(user)
            db.session.commit()
        # here we handle denying accounts:
        users = [user for user, value in request.form.iteritems() if value == 'deny']
        users = [User.username == user for user in users]
        if len(users) > 0:
            query = User.query.filter(or_(*users))
            if sponsored:
                query = query.filter(User.sponsor == g.user.username)
            users = query.all()
            for user in users:
                db.session.delete(user)
            db.session.commit()

    query = User.query
    sort = 'username'
    sort_col = User.username
    sort_dir = asc
    cols = {'username' : User.username,
            'uid' : User._uid,
            'sponsor' : User.sponsor,
            'email' : User.email,
            'name' : User.last_name,
            'last_name' : User.last_name,
            'first_name' : User.first_name,
            'status' : User.status,
            'grad_date' : User._grad_date}
    # Let's make the filter form
    class FilterForm(Form):
        pass
    for field, col in cols.iteritems():
        setattr(FilterForm, field, TextField())
    filter_form = FilterForm(request.args)
           
    if 'sort' in request.args:
        if request.args['sort'] in cols:
            sort = request.args['sort']
            sort_col = cols[request.args['sort']]
    if 'dir' in request.args and request.args['dir'] == 'desc':
        sort_dir = desc
    
    if sponsored:
        query = query.filter(User.sponsor == g.user.username)
        if pending:
            query = query.filter(User.status == 'pending_sponsor')
        else:
            query = query.filter(User.status != 'pending_sponsor')
    elif rolloffs:
        now = date.today()
        query = query.filter(User._grad_date <= now)
        query = query.filter(User.status != 'pending_sponsor')
        query = query.filter(User.status != 'pending_labstaff')
        query = query.filter(User.status != 'pending_rolloff')
    else:
        if pending:
        	query = query.filter(User.status == 'pending_labstaff')
#        else:
#            query = query.filter(User.status != 'pending_labstaff')
#            query = query.filter(User.status != 'pending_sponsor')
    for field, col in cols.iteritems():
        if field in request.args:
            if request.args[field].strip() == "":
                continue
            query = query.filter(col.like(request.args[field].strip()))
    query = query.order_by(sort_dir(sort_col))
    page = query.paginate(page)
    if pending:
        # Patch a Form. This allows us to keep our CSRF protection
        class F(Form):
            pass
        for user in page.items:
            setattr(F, user.username, RadioField(choices=[('approve', 'Approve'), ('postpone', 'Postpone'), ('deny', 'Deny')], validators=[validators.Required()]))
        # Flask-WTForms likes to pull data from request.form. Force it not to.
        form = F(ImmutableMultiDict())
        # We do this after the fact so WTForms can do some of its binding
        for user in page.items:
            user.radio = getattr(form, user.username)
            user.radio.data = 'postpone'
        if sponsored:
            template = 'sponsorship_requests.html'
        else:
            template = 'list_pending_users.html'
    elif rolloffs:
        class rolloffCheckbox(Form):
            pass
        for user in page.items:
            setattr(rolloffCheckbox, user.username, BooleanField())
        form = rolloffCheckbox(ImmutableMultiDict())
        for user in page.items:
            user.checkbox = getattr(form, user.username)
        template = 'list_upcoming_rolloffs.html'
    else:
        form = Form()
        if sponsored:
            template = 'sponsored_users.html'
        else:
            template = 'userlist.html'
    return render_template(template, page=page, sort=sort, sort_dir='asc' if sort_dir == asc else 'desc', form=form, filter_form=filter_form)


app.add_url_rule('/users/pending', 'list_pending_users', userlist, defaults={'pending' : True}, methods=['GET', 'POST'])
app.add_url_rule('/users/pending/page/<int:page>', 'list_pending_users', userlist, defaults={'pending' : True}, methods=['GET', 'POST'])
app.add_url_rule('/users/sponsored', 'list_sponsored_users', userlist, defaults={'sponsored' : True}, methods=['GET', 'POST'])
app.add_url_rule('/users/sponsored/page/<int:page>', 'list_sponsored_users', userlist, defaults={'sponsored' : True}, methods=['GET', 'POST'])
app.add_url_rule('/users/sponsored/pending', 'list_sponsored_pending_users', userlist, defaults={'sponsored' : True, 'pending' : True}, methods=['GET', 'POST'])
app.add_url_rule('/users/sponsored/pending/page/<int:page>', 'list_sponsored_pending_users', userlist, defaults={'sponsored' : True, 'pending' : True}, methods=['GET', 'POST'])
app.add_url_rule('/users/rolloffs', 'list_upcoming_rolloffs', userlist, defaults={'rolloffs' : True}, methods=['GET', 'POST'])
