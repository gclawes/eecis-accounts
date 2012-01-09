"""
This script is run by /var/yp/Makefile
It processes pending changes (passwd, shell, gecos) from
the web database and makes those changes in the login systems
"""
#import auth_modules
import test_modules as auth_modules
from accounts.database import User, get_with_status
from accounts import mail
from sys import stderr, exit
import subprocess
import os

# Settings
HOST="ACCOUNT.ACAD"
DOMAIN="account" # CHANGEME
MAILDOMAIN="@account.acad.ece.udel.edu" # CHANGEME
MAIL="gclawes@udel.edu"
USER="account"
UID=202
#LOCKFILE="/var/yp/process-changes.lock"
LOCKFILE="./process-changes.lock" # CHANGE ME

def main():
    # Security checks
    # if this is run as root for some reason, drop root to "account"
    """if os.getuid() != 0:
        os.setgid(UID)
        os.setuid(UID)
        stderr.write("ERROR: process-nis-files.py must be run as root!")"""
    
    # load login modules
    modules = auth_modules.load_modules()
   
    # select users with pending password changes
    pw_changes = [u for u in get_with_status('pw_reset') if u.in_domain(DOMAIN)]

    # get pending disables
    pending_disables = [u for u in get_with_status('pending_disable') if u.in_domain(DOMAIN)]

    # get pending enables
    pending_enables = [u for u in get_with_status('pending_enable') if u.in_domain(DOMAIN)]

    # get pending rolloffs
    pending_rolloffs = [u for u in get_with_status('pending_rolloff') if u.in_domain(DOMAIN)]


    # process changes, and set flags after each change
    
    # change password and shell (both use same flag)
    if pw_changes != []:
        print "Changing passwords for:\n%s\n" % [u.username for u in pw_changes]
        for user in pw_changes:
            for name, module in modules.iteritems():
                module.change_password(pw_changes)
                module.change_shell(pw_changes)
                user.add_flag(DOMAIN+"_reset_password")
    
    # disable accounts, set DOMAIN_noaccess flag
    if pending_disables != []:
        print "Disabling accounts:\n%s\n" % [u.username for u in pending_disables]
        for user in pending_disables:
            for name, module in modules.iteritems():
                module.disable_logins(pending_disables)
                user.add_flag(DOMAIN+"_noaccess")
 
    # enable accounts, set DOMAIN_return_access flag
    if pending_enables != []:
        print "Enabling accounts:\n%s\n" % [u.username for u in pending_enables]
        for user in pending_enables:
            for name, module in modules.iteritems():
                module.enable_logins(pending_enables)
                user.add_flag(DOMAIN+"_return_access")
    
    # rolloff accounts (star pw), set DOMAIN_rolloff flag
    if pending_rolloffs != []:
        print "Staring passwords for:\n%s\n" % [u.username for u in pending_rolloffs]
        for user in pending_rolloffs:
            for name, module in modules.iteritems():
                module.rolloff_disable(pending_rolloffs)
                user.add_flag(DOMAIN+"_rolloff")

    # Changes have been processed
    print "Processed login changes"

if __name__ == "__main__":
    if not os.path.isfile(LOCKFILE):
        os.mknod(LOCKFILE)
        main()
        os.remove(LOCKFILE)
    else:
        print "ERROR: %s still exists, process-changes.py is still running!" % LOCKFILE

