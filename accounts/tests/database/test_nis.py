"""
This script tests the NIS module.
"""
from accounts.database import User
from unittest import TestCase, TestSuite, TestLoader
from accounts import app, db
from accounts.tests import dataset

from accounts.scripts.auth_modules import nis_unix

nis_unix.NISHOME="./accounts/tests/"
nis_unix.PWPLUS=nis_unix.NISHOME+"passwd+" 
nis_unix.PWLOCAL=nis_unix.NISHOME+"passwd.local"
nis_unix.GRPLUS=nis_unix.NISHOME+"group+"
nis_unix.GRLOCAL=nis_unix.NISHOME+"group.local"
nis_unix.RCS_CO='FALSE'
nis_unix.RCS_CI='FALSE'



def pw_line(u):
    gecos = "%s %s,,,acad" % (u.first_name, u.last_name)
    home = "/usa/%s" % u.username
    l = [u.username, u.get_hashes()['openldap_ssha'], str(u.uid), str(u.gid), gecos, home, u.shell ]
    return ':'.join(l).strip() + '\n'
        
def roll_line(u):
    gecos = "%s %s,,,acad" % (u.first_name, u.last_name)
    home = "/usa/%s" % u.username
    l = [u.username, "*", str(u.uid), str(u.gid), gecos, home, "/bin/tcsh" ]
    return ':'.join(l) + '\n'

def gr_line(u):
    return ':'.join([u.username, "*", str(u.gid), u.username]) + '\n'


class TestSetup(TestCase):
    def setUp(self):
        pwplus = open("accounts/tests/passwd+", "w")
        grplus = open("accounts/tests/group+", "w")
        pwplus.close()
        grplus.close()
        
        pwplus_gold = open("accounts/tests/passwd+.gold", "w")
        grplus_gold = open("accounts/tests/group+.gold", "w")

        pw_file = open("accounts/tests/passwd.local", 'w')
        gr_file = open("accounts/tests/group.local", 'w')
        
        pw_gold = open("accounts/tests/passwd.local.gold", 'w')
        gr_gold = open("accounts/tests/group.local.gold", 'w')

        db.create_all()
        dataset.populate()

        # test users for NIS
        u = User('nis_create', 'password')
        u.first_name = 'create'
        u.last_name = 'NIS_tests'
        u.email = 'nis@tests'
        u.add_domain('acad')
        u.status = 'pending_create'
        db.session.add(u)
        db.session.commit()
        # only add to gold file
        pwplus_gold.write(pw_line(u))
        grplus_gold.write(gr_line(u))
   
        # change shell to no_access
        u = User('nis_disable', 'password')
        u.first_name = 'disable'
        u.last_name = 'NIS_tests'
        u.email = 'nis@tests'
        u.add_domain('acad')
        u.status = 'pending_create'
        db.session.add(u)
        db.session.commit()
        # add to gold and test file
        pw_file.write(pw_line(u))
        gr_file.write(gr_line(u))
        
        u.shell = "/usr/local/bin/no_access\n"
        db.session.commit()
        pw_gold.write(pw_line(u))
        gr_gold.write(gr_line(u))
   
        # re-enable
        u = User('nis_enable', 'password')
        u.first_name = 'enable'
        u.last_name = 'NIS_tests'
        u.email = 'nis@tests'
        u.add_domain('acad')
        u.status = 'pending_enable'
        u.shell = "/bin/noaccess"
        db.session.add(u)
        db.session.commit()
        # add to gold and test file
        pw_file.write(pw_line(u))
        gr_file.write(gr_line(u))
        
        u.shell = "/bin/tcsh"
        db.session.commit()
        pw_gold.write(pw_line(u))
        gr_gold.write(gr_line(u))

        # rolloffs 
        u = User('nis_rolloff', 'password')
        u.first_name = 'rolloff'
        u.last_name = 'NIS_tests'
        u.email = 'nis@tests'
        u.add_domain('acad')
        u.status = 'rolloff'
        db.session.add(u)
        db.session.commit()
        # add to gold and test file
        pw_file.write(pw_line(u))
        gr_file.write(gr_line(u))
        pw_gold.write(roll_line(u))
        gr_gold.write(gr_line(u))
       
        # delete from nis
        u = User('nis_delete', 'password')
        u.first_name = 'delete'
        u.last_name = 'NIS_tests'
        u.email = 'nis@tests'
        u.add_domain('acad')
        u.status = 'pending_rolloff'
        db.session.add(u)
        db.session.commit()
        pw_file.write(pw_line(u))
        gr_file.write(gr_line(u))
       
        # change pw and shell
        u = User('nis_change', 'changeme')
        u.first_name = 'change'
        u.last_name = 'NIS_tests'
        u.email = 'nis@tests'
        u.add_domain('acad')
        u.status = 'pw_reset'
        db.session.add(u)
        db.session.commit()
        pw_file.write(pw_line(u))
        gr_file.write(gr_line(u))

        u.password = 'changed'
        u.shell = '/bin/bash'
        db.session.commit()
        pw_gold.write(pw_line(u))
        gr_gold.write(gr_line(u))
       
        pw_file.close()
        gr_file.close()
        pw_gold.close()
        gr_gold.close()
        pwplus_gold.close()
        grplus_gold.close()
        

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        
class TestNIS(TestSetup):
    def test_create(self):
        nis_unix.create_logins([User.query.get("nis_create")])
        
        with open(nis_unix.PWPLUS) as pwplus:
            pwplus_lines = pwplus.readlines()[:]
        with open(nis_unix.PWPLUS+".gold") as pwplus_gold:
            pwplus_gold_lines = pwplus_gold.readlines()[:]
        with open(nis_unix.GRPLUS) as grplus:
            grplus_lines = grplus.readlines()[:]
        with open(nis_unix.GRPLUS+".gold") as grplus_gold:
            grplus_gold_lines = grplus_gold.readlines()[:]

        self.assertEqual(pwplus_lines, pwplus_gold_lines)
        self.assertEqual(grplus_lines, grplus_gold_lines)
      
    
    def test_disable(self):
        nis_unix.disable_logins([User.query.get("nis_disable")])
        self.assert_entry("nis_disable")
    
    def test_enable(self):
        nis_unix.enable_logins([User.query.get("nis_enable")])
        self.assert_entry('nis_enable')
    
    def test_rolloff(self):
        nis_unix.rolloff_disable([User.query.get("nis_rolloff")])
        self.assert_entry('nis_rolloff')
    
    def test_delete(self):
        nis_unix.delete_logins([User.query.get("nis_delete")])
    
        with open(nis_unix.PWPLUS) as pwplus:
            pwplus_lines = pwplus.readlines()[:]
        with open(nis_unix.GRPLUS) as grplus:
            grplus_lines = grplus.readlines()[:]
        
        for line in pwplus_lines:
            assertNotEqual(line[0].split(":"), 'nis_delete')
        for line in grplus_lines:
            assertNotEqual(line[0].split(":"), 'nis_delete')
    
    def test_change_pw(self):
        # ch_pw and ch_sh need the other's operation to happen as well
        nis_unix.change_shell([User.query.get("nis_change")])
        nis_unix.change_password([User.query.get("nis_change")])
        self.assert_entry("nis_change")
    
    def test_change_sh(self):
        # ch_pw and ch_sh need the other's operation to happen as well
        nis_unix.change_password([User.query.get("nis_change")])
        nis_unix.change_shell([User.query.get("nis_change")])
        self.assert_entry("nis_change")

    def assert_entry(self, username):
        with open(nis_unix.PWLOCAL) as pw:
            pw_lines = pw.readlines()[:]
        with open(nis_unix.PWLOCAL+".gold") as pw_gold:
            pw_gold_lines = pw_gold.readlines()[:]
        
        with open(nis_unix.GRLOCAL) as gr:
            gr_lines = gr.readlines()[:]
        with open(nis_unix.GRLOCAL+".gold") as gr_gold:
            gr_gold_lines = gr_gold.readlines()[:]
       
        pw_entry = []
        pw_gold_entry = []
        gr_entry = []
        gr_gold_entry = []

        for line in pw_lines:
            if line.split(':')[0] == username:
                pw_entry = line
        for line in pw_gold_lines:
            if line.split(':')[0] == username:
                pw_gold_entry = line
        
        for line in gr_lines:
            if line.split(':')[0] == username:
                gr_entry = line
        for line in gr_gold_lines:
            if line.split(':')[0] == username:
                gr_gold_entry = line
        
        self.assertEqual(pw_entry, pw_gold_entry)
        self.assertEqual(gr_entry, gr_gold_entry)
      

       

suite = TestSuite()
suite.addTest(TestLoader().loadTestsFromTestCase(TestNIS))

