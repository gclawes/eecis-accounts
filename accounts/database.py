# This file really needs a better name. We'll discuss later
from accounts import db, config
import sqlalchemy
from flaskext.sqlalchemy import SQLAlchemy
from collections import defaultdict
from sqlalchemy.sql.expression import asc
import hash
from datetime import datetime
from mail import create_email, change_email

# Domains which need to handle stuff.
# domains = ['research', 'acad']
domains = ['account'] # TODO: for testing, change back later

status_paths = defaultdict(lambda: (set(), 'error', None), {
    'pending_sponsor' : ({'sponsor_approved'}, 'pending_admin', None),
    'pending_admin' : ({'admin_approved'}, 'pending_create', None),
    'pending_create' : ({domain+'_created' for domain in domains}, 'active', create_email),
    'pw_reset' : ({domain+'_reset_password' for domain in domains}, 'active', change_email),
    'pending_disable' : ({domain+'_noaccess' for domain in domains}, 'disabled', None),
    'disabled' : ({'labstaff_enable'}, 'reactivate', None),
    'pending_enable' : ({domain+'_return_access' for domain in domains}, 'active', None),
})

def name_sort(u1, u2):
    if u1.last_name < u2.last_name:
        return -1
    elif u1.last_name > u2.last_name:
        return 1
    else:
        if u1.first_name < u2.first_name:
            return -1
        elif u1.first_name > u2.first_name:
            return 1
        else:
            return 0

def get_sponsors(labstaff = False):
    """
    This gets all the available sponsors, in alphabetical order.
    If a user is labstaff, they get to see the EECIS Staff sponsor,
    who bypasses the normal approval process.
    """
    l = [d.user for d in UserDomain.query.filter_by(domain='sponsor').all()]
    l.sort(cmp=name_sort)
    if not labstaff:
        l = [u for u in l if u.username != 'staff']
    return l

def get_with_status(s):
    return User.query.filter_by(status=s).all()

class User(db.Model):
    @property
    def password(self):
        raise Exception("Plaintext passwords are not stored!")
        
    @password.setter
    def password(self, value):
        # TODO: Verify password strength!
        
        # TODO: Add more hash types
        # TODO: Add salts to the hashes
        # TODO: add User.verify_password() to verify with hashes
        for name, hash_func in hash.supported_hashes.iteritems():
            h = AccountHash(self.username, hash_func(value), name)
            db.session.add(h)
        
    @property
    def uid(self):
        return self._uid
        
    @uid.setter
    def uid(self, uid):
        uid = int(uid)
        if uid < 0:
            return
        if self._uid > 0:
            old_map = UIDMap.query.get(self._uid)
            old_map.used = False
            db.session.add(old_map)
        map = UIDMap.query.get(uid)
        if uid > 1000 and map.used == True:
                raise ValueError("The uid %d is already in use." % uid)
        map.used = True
        db.session.add(map)
        db.session.commit()
        self._uid = uid
        
    @property
    def grad_date(self):
        return self._grad_date.strftime('%m/%Y')

    def default_gecos(self):
        name = " ".join([self.first_name, self.last_name])
        if 'research' in self.get_domains():
            return ",".join([name, "", "", "eecis"])
        elif 'acad' in self.get_domains():
            return ",".join([name, "", "", "acad.ece"])
        else:
            return ",".join([name, "", "", ",".join(self.get_domains())])
    
    @grad_date.setter
    def grad_date(self, date):
        self._grad_date = datetime.strptime(date,'%m/%Y')
        
    def auto_assign_uid(self):
        """
        This should be called when a user account goes to be activated.
        """
        map = UIDMap.query.filter(UIDMap.used == False).order_by(asc(UIDMap.uid)).limit(1)[0]
        self.uid = map.uid
        self.gid = map.uid
        map.used = True
        db.session.add(self)
        db.session.add(map)
        #db.session.commit()
        
    def free_uid(self):
        map = UIDMap.query.get(self._uid)
        map.used = False
        db.session.add(map)
        db.session.commit()
        self._uid = -1
    
    def get_hash(self):
        with open(config.htpath + '/htpasswd') as f:
            for line in f:
                username, userhash, uid, gid, gecos, home, shell = line.split(':')
                if username == self.username:
                    return userhash
        return None
        
    def verify_password(self, password):
        """
        This function verifies that a user-supplied password is valid.
        TODO: This should verify through NIS at some later date.
        """
        userhash = self.get_hash()
        if userhash is None:
            return False
        return hash.verify(password, userhash)
        
        
    def get_hashes(self):
        return {d.hash_type : d.hash for d in self.hashes}
        
    def get_domains(self):
        return [d.domain for d in self.domains]
        
    def add_domain(self, domain):
        if domain in self.get_domains():
            return
        new = UserDomain(self.username, domain)
        db.session.add(new)
    
    def remove_domain(self, domain):
        if domain in self.get_domains():
            old = UserDomain(self.username, domain)
            db.session.remove(old)
        return
        
    def add_domains(self, *domains):
        for domain in domains:
            self.add_domain(domain)
            
    def in_domain(self, domain):
        return domain in self.get_domains()
        
    def get_flags(self):
        return {str(d.flag) for d in self.flags}

    def add_flag(self, flag):
        if flag in self.get_flags():
            return
        flags = set(self.get_flags()) | {flag}
        path = status_paths[self.status]
        needed_flags, upgrade_status, hook = path
        if flags == needed_flags:
            self.status = upgrade_status
            db.session.add(self)
            for flag in self.flags:
                db.session.delete(flag)
            if hook != None:
                hook(self)
            db.session.commit()
            return

        
        new = UserFlag(self.username, flag)
        db.session.add(new)
        db.session.add(self)
        # We commit here so that subsequent get_flags calls give the correct results
        db.session.commit()

    def has_flag(self, flag):
        return domain in self.get_domains()
        
    def account_details_complete(self):
        if self.email is None:
            return False
        if self.birth_city is None:
            return False
        return True
        
    
    username = db.Column(db.String(8), unique = True, primary_key = True, nullable = False)
    first_name = db.Column(db.String(30), nullable = False)
    last_name = db.Column(db.String(30), nullable = False)
    dob = db.Column(db.String(10), nullable = False)
    birth_city = db.Column(db.String(80))
    hashes = db.relationship("AccountHash", backref='user')
    shell = db.Column(db.String(50), nullable = True)
    gecos = db.Column(db.String(50), nullable = True)
    
    sponsor = db.Column(db.String(8), db.ForeignKey('user.username'))
    _uid = db.Column('uid', db.Integer(32))
    gid = db.Column(db.Integer(32))
    udel_id = db.Column(db.String(8), nullable = True, unique = True)
    email = db.Column(db.String(30), unique = False)
    _grad_date = db.Column('grad_date', db.Date(format='%m/%Y'), nullable = False, unique = False)
    comments = db.Column(db.Text(1000), nullable = True)
    
    domains = db.relationship("UserDomain", backref=db.backref('user', lazy='joined'))
    flags = db.relationship("UserFlag", backref=db.backref('user', lazy='joined'))
    status = db.Column(db.String, db.ForeignKey('account_status.status'))
    reset_token = db.Column(db.String(36), nullable = True, unique = True)
    reset_token_time = db.Column(db.Integer(64))
    register_date = db.Column(db.Date(format='%m/%d/%Y'), nullable = True, unique = False)
    
    def __init__(self, user, password = '', first_name = 'test', last_name = 'user'):
        self.username = user
        if password != '':
            self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.gecos = self.default_gecos()
        self.dob = '01/01/1990'
        self.gid = -1
        self.pending = True
        self.grad_date = '01/1900'
        self.shell = "/bin/tcsh"
        self.auto_assign_uid()
        self.reset_token_time = 0
        
    def __repr__(self):
        return '<User %s>' % self.username
    
    def is_disabled(self):
        return self.status in ('pending_disable', 'disabled')
    
    def is_active(self):
        return self.status == 'active'


class UserDomain(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(8), db.ForeignKey('user.username'))
    domain = db.Column(db.String(20))
    
    def __init__(self, username, domain):
        self.username = username
        self.domain = domain
        
class UserFlag(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(8), db.ForeignKey('user.username'))
    flag = db.Column(db.String(20))

    def __init__(self, username, flag):
        self.username = username
        self.flag = flag        

class AccountStatus(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    status = db.Column(db.String(20), nullable = False)

    def __init__(self, status):
        self.status = status

class AccountHash(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(8), db.ForeignKey('user.username'))
    hash = db.Column(db.String(64), nullable=False)
    hash_type = db.Column(db.String(20), nullable=False)
    
    def __init__(self, username, hash, type):
        self.username = username
        self.hash = hash
        self.hash_type = type

class UIDMap(db.Model):
    uid = db.Column(db.Integer, primary_key = True)
    used = db.Column(db.Boolean())
    
    def __init__(self, uid, used):
        self.uid = uid
        self.used = used

