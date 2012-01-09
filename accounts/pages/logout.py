from accounts import app
from flask import session, flash, redirect, url_for

@app.route('/logout')
@app.route('/logout/')
@app.allow('all')
def logout():
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('index'))