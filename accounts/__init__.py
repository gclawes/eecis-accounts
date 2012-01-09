"""
This file is the heart of the code which will be run. See the top-level README
for details on how to set the system up.

As this is the module __init__ file, it specifies which names are available
to be imported with the module. The following gives a synopsis of those names.
Many of these names are to be imported from here, which is the standard Python
way of doing singleton-style classes via import, without the code or indirection
overhead. In addition to providing these names for import, this file contains
the basic setup code to run the application under any condition.

| *app* is an instance of flask.Flask() which is to handling the application.
| *config* is the imported config module.
| *db* is an instance of flaskext.sqlalchemy.SQLAlchemy which is used for all
  database configuration and querying.
| *database* is the imported database module. This in particular must be imported
  only from the name accounts.database, as it relies on this code having been
  run to do some setup on the *app* object.
"""

from flask import Flask, render_template
from flaskext.sqlalchemy import SQLAlchemy
from optparse import OptionParser
import config
import sys
import unittest
from tests import dataset

# Make sure that we have confirguration setup for our application
try:
    from . import config
except ImportError:
    print "Configuration file missing. See README for details on configuration."
    exit(-1)
    
def main():
    global app, db, web, database, pages
    parser = OptionParser()
    parser.add_option("-t", "--test-all", action="store_true", default=False, dest="test_all", help="Run all the tests.")
    parser.add_option("-d", "--test-db", action="store_true", default=False, dest="test_db", help="Run the database tests.")
    parser.add_option("-w", "--test-web", action="store_true", default=False, dest="test_web", help="Run the web tests.")
    parser.add_option("-r", "--reset-db", action="store_true", default=False, dest="reset_db", help="Reset the database.")
    parser.add_option("-s", "--script", metavar="SCRIPT", dest="script", default=None)
    parser.add_option("--server",  action="store_true", default=False, dest="start_server", help="Run the test webserver.")
    (options, args) = parser.parse_args()
    
    if options.test_all or options.test_db or options.test_web:
        app = Flask(__name__.split('.')[0])
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db = SQLAlchemy(app)
        suite = unittest.TestSuite()
        if options.test_all or options.test_db:
            import tests.database
            suite.addTest(tests.database.suite)
        if options.test_all or options.test_web:
            import tests.web
            suite.addTest(tests.web.suite)
        unittest.TextTestRunner(verbosity=2).run(suite)
    elif options.script is not None:
        app = Flask(__name__.split('.')[0])
        app.config.from_object(config.FlaskConfig)
        db = SQLAlchemy(app)
        import scripts
        scripts = scripts.load_scripts()
        if options.script in scripts:
            scripts[options.script].main()
    elif options.reset_db or options.start_server:
        # Setup the application and database
        app = Flask(__name__.split('.')[0])
        app.config.from_object(config.FlaskConfig)
        app.jinja_env.add_extension('jinja2.ext.do')
        db = SQLAlchemy(app)
        import database
        import web
        if options.reset_db:
            db.drop_all()
            db.create_all()
            dataset.populate()
            print 'Database reset.'
            exit(0)
        import pages
        app.run(host='0.0.0.0', port=config.dev_port, use_reloader=True)
    else:
        parser.print_help()
        
def wsgi():
    global app, db, web, database, pages
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config.FlaskConfig)
    app.jinja_env.add_extension('jinja2.ext.do')
    db = SQLAlchemy(app)
    import database
    import web
    import pages