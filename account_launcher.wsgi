import sys
activate_this = '/Users/rdeaton/py2.7/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
sys.path.insert(0, '/var/www')
import accounts
accounts.wsgi()
application = accounts.app