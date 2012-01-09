from accounts import db, database
from accounts.database import *
from flask import url_for
from random import randrange

def main():
    print database.get_sponsors()
    # users = User.query.filter_by(status='pending_sponsor').all()
    # sponsors = map(lambda s: User.query.get(s), {user.sponsor for user in users})
    # users_by_sponsor = {sponsor : [user for user in users if user.sponsor == sponsor.username] for sponsor in sponsors}
    # print users_by_sponsor
    # u = User('test' + str(randrange(12341234)), 'test')
    # u.status = 'pw_reset'
    # db.session.add(u)
    # db.session.commit()
    # 
    # u.add_flag('account_reset_password')
    # print u.status
    # 
    # db.session.commit()