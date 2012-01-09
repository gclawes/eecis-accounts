from accounts import app
from flask import render_template

@app.route('/')
@app.allow('all')
def index():
    return render_template('index.html')
