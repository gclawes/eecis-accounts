"""
This file includes code which is important for implementing a permissions system
within the web application.
"""

from flask import session, g, redirect, url_for, flash
from accounts.database import User
from functools import wraps
from accounts import app
from accounts import config

def allow(*permissions):
    """
    Allows a user with any of a list of permissions to access a page.
    To restrict to multiple permissions, use the decorator repeatedly.
    Use 'all' to allow any person access to that page.
    Use 'logged_in' to allow any logged in user access to the page.
    This function is available via app.allow
    """
    def wrap(f):
        @wraps(f)
        def wrapped_f(*args, **kwargs):
            if 'username' in session:
                username = session['username']
                u = User.query.get(username)
                if u is None: # This will only happen during development.
                    session.pop('username')
                    return redirect(url_for('login'))
                g.user = u
                if username in ('bmiller', 'davis', 'admin'):
                    g.user_is_admin = True
                    g.user_is_labstaff = True
                else:
                    g.user_is_admin = False
                    with open(config.htpath + '/htgroup') as htgroup:
                        for line in htgroup:
                            group, star, gid, users = line.split(':')
                            if group == 'staff':
                                g.user_is_labstaff = username in users.split(',')
                                break
                        
                if 'all' in permissions or 'logged_in' in permissions:
                    return f(*args, **kwargs)
                if 'admin' in permissions and g.user_is_admin:
                    return f(*args, **kwargs)
                if 'labstaff' in permissions and g.user_is_labstaff:
                    return f(*args, **kwargs)
                if 'sponsor' in permissions and 'sponsor' in u.get_domains():
                    return f(*args, **kwargs)
                    
                # This user is not authorized to do what they wish.
                flash('You are not authorized to view that page.')
                return redirect(url_for('index'))
            else:
                g.user = None
                g.user_is_admin = False
                g.user_is_labstaff = False
                if 'all' == permissions[0] and len(permissions) == 1:
                    return f(*args, **kwargs)
                return redirect(url_for('login'))
        return wrapped_f
    return wrap
    
app.allow = allow