"""
This script can be used to import account data from passwd files. It is hardcoded
to look for two files, acad.txt and research.txt, in the current directory, and
add those users to the database with the proper domains. Information contained
within the passwd files is incomplete, but can be augmented with data from the
MySQL database (or replaced entirely later on). This is more because we do not
have credentials to access the old accounts database.

You can get acad and research passwd files from research and acad machines using
ypcat.
"""

from accounts import db
from accounts.database import *

def add_user(line, domain):
    username, hash, uid, gid, gecos, home_dir, shell = line.split(':')
    try:
        name, address, phone, acct_type = gecos.split(',')
        name_parts = name.split(" ")
    
        if len(name_parts) == 2:
            first_name, last_name = name_parts
        elif len(name_parts) == 1:
            first_name = name_parts[0]
            last_name = "Unknown?"
        else:
            first_name = ' '.join(name_parts[:-1])
            last_name = name_parts[-1]
    except ValueError:
        first_name = gecos
        last_name = 'Unknown?'
    
    u = User.query.get(username[:8])
    if u is not None:
        d = UserDomain(username, domain)
        db.session.add(d)
        return -1
    u = User(username)
    uid = int(uid)
    gid = int(gid)
    u.uid = uid
    u.gid = gid
    if uid != gid and gid != 0:
        m = UIDMap.query.get(gid)
        m.used = True
        db.session.add(m)
    u.first_name = first_name
    u.last_name = last_name
    u.pending = False
    u.status = 'active'
    d = UserDomain(username, domain)
    db.session.add(u)
    db.session.add(d)
    db.session.commit()
    return 1

def main():
    f = open("acad.txt")
    updated, added = 0,0
    for line in f:
        k = add_user(line, 'acad')
        if k == -1:
            updated += 1
        elif k == 1:
            added += 1
    db.session.commit()
    f = open("research.txt")
    for line in f:
        k = add_user(line, 'research')
        if k == -1:
            updated += 1
        elif k == 1:
            added += 1
    db.session.commit()
    print 'Added %d academic users, %d research users.' % (added, updated)