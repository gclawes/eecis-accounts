from accounts import db
from accounts import database

def main():
    print 'All users currently in the database:'
    for user in database.User.query.all():
        print user.username