import json
from urllib import urlencode
import urllib2
from getpass import getpass, getuser
import sys
import nis

def passwd():
    # TODO: Use a custom socket for urllib2 so that we can do https cert verification
    # username = getuser()
    username = 'admin'
    tries = 3
    while True:
        old_pass = getpass('Current Password: ')
        data = urlencode({'username' : username, 'old_password' : old_pass})
        res = json.loads(urllib2.urlopen('http://localhost:5002/api/reset_password/', data).read())
        if res['password_okay']:
            break
        tries -= 1
        if tries == 0:
            print 'Too many invalid attempts.'
            exit(0)
    while True:
        new_pass = getpass('New Password: ')
        new_pass2 = getpass('Confirm New Password: ')
        if new_pass != new_pass2:
            print 'Passwords did not match.'
            continue
        data = urlencode({'username' : username, 'old_password' : old_pass, 'new_password' : new_pass})
        res = json.loads(urllib2.urlopen('http://localhost:5002/api/reset_password/', data).read())
        if res['password_reset']:
            print 'Password changed. It may take a few minutes to propogate to all services'
            exit(0)
        else:
            print res['message']
           
def chsh():
    print "Change shell not yet implemented!"

def chfn():
    print "GECOS Change not yet implemented"

if __name__ == "__main__":
    pname = sys.argv[1]
    if "passwd" in pname:
        passwd()
    elif "chsh" in pname:
        chsh()
    elif "chfn" in pname:
        chfn()
