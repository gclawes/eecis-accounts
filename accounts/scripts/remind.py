"""
This program sends notification/reminder emails to sponsors
"""

from accounts.database import User, get_with_status
from accounts import mail
from sys import stderr, exit
import subprocess
import os

# Settings
HOST="account.acad"
DOMAIN="account" # CHANGEME
MAILDOMAIN="@account.acad.ece.udel.edu" # CHANGEME
#MAILHOST='mail.eecis.udel.edu'
MAILHOST='mail.udel.edu' # CHANGEME
MAILTO=['gclawes@udel.edu'] # CHANGEME
#LOCKFILE="/usa/account/lock/remind.lock"
LOCKFILE="./remind.lock" # CHANGEME
USER='account'
UID=202

def format_columns(data):
    """formats columns from a 3-tuple"""
    first_width = max([len(x[0]) for x in data])
    second_width = max([len(x[1]) for x in data])
    third_width = max([len(x[2]) for x in data])

    # calculate a format string for the output lines
    format_str= "%%-%ds  %%-%ds  %%-%ds" % (first_width, second_width, third_width)

    str = ""
    for x in data:
        str += format_str % x

def gen_userlist(users):
    """Generates neatly formatted list of users with usernames and type"""
    names = ["Name", "----\n"] + \
            [' '.join((u.first_name, u.last_name)) for u in users]
    
    usernames = ["Username", "--------\n"] + \
            [u.username for u in users]
    
    types = ["Type", "----\n"] + \
            [("Research" if u.in_domain('research') else "Academic") for u in users]

    return format_columns((names, usernames, types))

def generate_email(users):
    """somewhat messy function that generates the text
    of notification emails to sponsors"""
    num_users = len(users)

    subject = "You have new ECE/CIS accounts awaiting your approval"
    message+="""
    Your currently have %d ECE/CIS user account applications awaiting your approval.
    
    Please visit https://www.eecis.udel.edu/accounts/users/sponsored to approve pending accounts

    List of pending users:
    %s

    ECE/CIS Labstaff
    """ % gen_userlist(users)

    return (subject, message)


def main():
    # Security checks
    # if this is run as root for some reason, drop to "account"
    if os.getuid() == 0:
        os.setgid(UID)
        os.setuid(UID)
        stderr.write("ERROR: remind.py must be run as root!")

    # very fancy list comprehensions to get dict of users 
    # by sponsor (maps sponsors to the users they sponsor)
    # collisions are not possible, a user can not be in multiple sponsor lists
    users = User.query.filter_by(status='pending_sponsor').all()
    sponsors = map(lambda s: User.query.get(s), {user.sponsor for user in users})
    users_by_sponsor = {sponsor : [user for user in users if user.sponsor == sponsor.username] for sponsor in sponsors}

    for sponsor, users in users_by_sponsor.iteritems(): # for key, value in dict.iteritems()
        subject, message = generate_email(users)
        mail.send("staff@eecis.udel.edu", "ECE/CIS Labstaff", \
                "%s@eecis.udel.edu" % sponsor.username,
                subject, message, MAILHOST)

if __name__ == "__main__":
    if not os.path.isfile(LOCKFILE):
        os.mknod(LOCKFILE)
        main()
        os.remove(LOCKFILE)
    else:
        error = "ERROR: %s still exists, remind.py is still running on %s\n\n" % (LOCKFILE, HOST)
        mail.send("account@mail.eecis.udel.edu", "Account-user", MAILTO, \
                "Sponsor Reminder ERROR - %s" % DOMAIN, error, MAILHOST)

