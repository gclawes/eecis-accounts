from accounts import app
from flask import render_template

@app.route('/view_pending_applications')
@app.allow('labstaff')
def view_pending_applications():
    return render_template('view_pending_applications.html')
