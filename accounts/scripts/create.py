"""
This program reads the accounts web database, gets pending users
and adds their login each login system in auth_modules

auth_modules provide a list of authentication modules, one for each auth system
Current modules are: NIS, ldap, Samba ldap
additionaly, auth_stub.py defines the interface new modules must provide

This script must be run as root, as it  adds lines 
to /var/yp/src/{passwd+,group+} and calls the
mk-zfs.sh external scripts to create filesystems.
"""
#import auth_modules
import test_modules as auth_modules
from accounts.database import User, get_with_status
from accounts import mail
from sys import stderr, exit
import subprocess
import os

# Settings
HOST="account.acad"
DOMAIN="account" # CHANGEME
MAILDOMAIN="@account.acad.ece.udel.edu" # CHANGEME
MAILTO=['gclawes@udel.edu']
#MAILHOST='mail.eecis.udel.edu'
MAILHOST='mail.udel.edu' # CHANGEME
USER="account"
UID=202
#LOCKFILE="/usa/account/lock/create.lock"
LOCKFILE="./create.lock" # CHANGEME

def zfs_create(user):
    """
    runs the mk-zfs.sh script 
    these scripts are different on dilbert and devil-rays
    the acad script handles mail tasks as well
    """
    # system("/usa/root/bin/mk-zfs.sh $login acad $status $uid $gid $email");
    MKZFS = "/usa/root/bin/mk-zfs.sh"
    email = user.username+MAILDOMAIN
    args = [MKZFS, user.username, DOMAIN, DOMAIN, str(user.uid), str(user.gid), email]
    # call mk-zfs.sh and return it's output
    mk_zfs = subprocess.Popen(args, stdout=subprocess.PIPE, shell=False)
    output = mk_zfs.communcate()
    mk_zfs.terminate()
    return output

def research_mail(user):
    """
    research has additional mail tasks
    in addition to the mk-zfs.sh script
    """
    SSH="/usr/local/bin/sshq -n".split(" ")
    MAILHOST = 'mail.eecis.udel.edu'
    MAILSETUP = '/usa/root/bin/mk-zfs.sh'
    email = user.username+MAILDOMAIN
    #system( "$ssh $mailhost /usa/root/bin/mk-zfs.sh $login research $status $uid $gid $email" );
    if user.in_domain('research'):
        args = SSH + [MAILHOST, MAILSETUP, user.username, 'research', 'research', 
                user.uid, user.gid, email]
        # call mail setup script 
        mailcall = subprocess.Popen(args, stdout=subprocess.PIPE, shell=False)
        output = mailcall.communicate()
        mailcall.terminate()
        return output


def main():
    # message to use for sending mail logs
    MESSAGE = ""

    MESSAGE += "MAKING ACCOUNTS ON %s FOR %s\n\n" % (HOST, DOMAIN)
    
    # get authentication modules
    modules = auth_modules.load_modules()
    
    # fancy python list comprehension to:
    # select users with the pending_create status that don't have
    # the DOMAIN_created flag for this domain
    pending_users = [u for u in User.query.filter_by(status='pending_create').all()
            if u.in_domain(DOMAIN) and "%s_created" % DOMAIN not in u.get_flags() ]
    usernames = [u.username for u in pending_users]

    # if no pending accounts, do nothing
    if pending_users == []: 
        sys.exit()

    MESSAGE += "New Accounts\n------------\n"

    # create login entries for each login method
    MESSAGE += "Creating logins for:\n%s\n\n" % ", ".join(usernames)
    for name, module in modules.iteritems():
        MESSAGE += module.create_logins(pending_users)
        MESSAGE += "\n\n"

    # call ZFS create scripts, and mail scripts on louie if it's research
    MESSAGE += "Creating %s ZFS filesystems for:\n%s\n\n" % (DOMAIN, ", ".join(usernames))
    for user in pending_users:
        MESSAGE += "DEBUG: zfs_create(user)\n"
        #zfs_create(user)
        if user.in_domain('research'):
            MESSAGE += "DEBUG: research_mail(user)\n"
            #research_mail(user)

    # Creating users is complete, add the flag for creation in the DB
    for user in pending_users:
        user.add_flag(DOMAIN+"_created")

    MESSAGE += "\n\nDONE MAKING ACCOUNTS ON %s FOR %s\n" % (HOST, DOMAIN)

    print MESSAGE 
    mail.send("root@mail.eecis.udel.edu", "Super-User", MAILTO, \
            "New Accounts - %s" % DOMAIN, MESSAGE, MAILHOST)

if __name__ == "__main__":
    if not os.path.isfile(LOCKFILE):
        os.mknod(LOCKFILE)
        main()
        os.remove(LOCKFILE)
    else:
        error = "ERROR: %s still exists, create.py is still running on %s\n\n" % (LOCKFILE, HOST)
        mail.send("root@mail.eecis.udel.edu", "Super-User", MAILTO, \
                "New Accounts ERROR - %s" % DOMAIN, error, MAILHOST)


