"""
Auth module for Unix LDAP
"""

HASHTYPE='ssha'
SHELL='/bin/tcsh'

LDAPUSER="uid=account_update,ou=People,dc=eecis,dc=udel,dc=edu"
LDAPPASSWD="SECRET"
#LDAPSERVER="-H ldaps://devil-rays.acad.ece.udel.edu:636"
#LDAPSERVER="-H ldaps://smb-ldap1.eecis.udel.edu:636"
LDAPSERVER="-H ldaps://account.acad.cis.udel.edu:636"

LDAPADD="/usr/local/openldap/bin/ldapadd -c -x %s -D %s -w %s" % (LDAPSERVER, LDAPUSER, LDAPPASSWD)
LDAPMODIFY="/usr/local/openldap/bin/ldapmodify -x -c %s -D %s -w %s" % (LDAPSERVER, LDAPUSER, LDAPPASSWD)
LDAPSEARCH="/usr/local/openldap/bin/ldapsearch -x %s -b" % (LDAPSERVER)

PWSUFFIX="ou=People,dc=eecis,dc=udel,dc=edu"
GRSUFFIX="ou=Group,dc=eecis,dc=udel,dc=edu"


# Helper Functions
#####################################
def ldap_add_string(user):
    """
    generates the string to feed to
    ldapadd for adding a user
    """
    gecos = "%s %s,,,%s" % (user.first_name, user.last_name, ','.join(user.get_domains()))
    sid = 2*user.uid+1000
    pw_hash = user.get_hashes()[HASHTYPE]
    ldapstr = ""
    ldapstr += "dn: uid=%s,%s\n" % (user.username, PWSUFFIX)
    ldapstr += "objectClass: account\n"
    ldapstr += "objectClass: posixAccount\n"
    ldapstr += "objectClass: top\n"
    ldapstr += "objectClass: shadowAccount\n"
    ldapstr += "objectClass: sambaSAMAccount\n"
    ldapstr += "uid: %s\n" % (user.username)
    ldapstr += "cn: %s\n" % (" ".join([user.first_name, user.last_name]))
    ldapstr += "userPassword: {crypt}%s\n" % (pw_hash)
    ldapstr += "sambaAcctFlags: [U          ]\n"
    ldapstr += "loginShell: %s" % (SHELL)
    ldapstr += "uidNumber: %d\n" % (user.uid)
    ldapstr += "gidNumber: %d\n" % (user.gid)
    ldapstr += "homeDirectory: %s\n" % ("/usa/"+user.username)
    ldapstr += "gecos: %s\n" % (gecos)
    ldapstr += "sambaSID: S-1-0-0-%d\n" % (sid)
    ldapstr += "sambaPwdMustChange: 2147483647\n"
    ldapstr += "sambaPasswordHistory: 0000000000000000000000000000000000000000000000000000000000000000\n"
    ldapstr += "sambaPwdCanChange: 1178291445\n"
    ldapstr += "\n" # group entry
    ldapstr += "dn: cn=%s,%s\n" % (user.username, GRSUFFIX)
    ldapstr += "objectClass: posixGroup\n"
    ldapstr += "objectClass: top\n"
    ldapstr += "cn: %s\n" % (user.username)
    ldapstr += "userPassword: {%s}%s\n" % (HASHTYPE, pw_hash)
    ldapstr += "gidNumber: %d\n" % (user.gid)
    ldapstr += "\n"

    return ldapstr

def ldap_chpw_string(user, newhash):
    # default is to get the hash from user object
    # this can be changed for rollof 
    if newhash == "": 
        print "ERROR: New password hash for %s cannot be blank, not changing" % (user.username)
        return "\n" # newline in ldapmodify
    else:
        ldapstr = ""
        ldapstr += "dn: uid=%s,%s\n" % (user.username, PWSUFFIX)
        ldapstr += "changetype: modify\n"
        ldapstr += "replace: userPassword\n"
        ldapstr += "userPassword: {crypt}%s\n" % (newhash)
        ldapstr += "\n"
        return ldapstr

def ldap_chsh_string(user, new_shell):
    if new_shell == "":
        print "ERROR: New shell for %s cannot be blank, not changing" % (user.username)
        return "\n" # newline in ldapmodify
    else: 
        ldapstr = ""
        ldapstr += "dn: uid=%s,%s\n" % (user.username, PWSUFFIX)
        ldapstr += "changetype: modify\n"
        ldapstr += "replace: loginShell\n"
        ldapstr += "loginShell: %s\n" % (new_shell)
        ldapstr += "\n"
        return ldapstr

def ldap_rm_string(user):
    # default is to get the hash from user object
    # this can be changed for rollof 
    ldapstr = ""
    ldapstr += "dn: uid=%s,%s\n" % (user.username, PWSUFFIX)
    ldapstr += "changetype: delete\n"
    ldapstr += "\n"
    return ldapstr


# Auth module interface 
#####################################

def create_logins(users):
    """
    create login in LDAP, login must not exist
    returns a string for email logs
    """
    MESSAGE = ""
    if users == []:
        MESSAGE += "ERROR: No users to add to LDAP!"
        return
    
    MESSAGE += "Adding users to LDAP:\n"
    MESSAGE += ", ".join([u.username for u in users])

    import subprocess
    ldapargs = LDAPADD.split(" ")
    ldapadd = subprocess.Popen(ldapargs, stdin=subprocess.PIPE, shell=False)
    for user in users:
        ldapstr = ldap_add_string(user)
        ldapadd.communicate(ldapstr)
    print >> ldapadd.stdin, "\n"
    ldapadd.terminate()

    return MESSAGE

def disable_logins(users):
    """
    disable a user's login by changing their shell to
    /usr/local/bin/no_access"""
    if users == []:
        print "ERROR: No users to disable LDAP login for!"
        return

    import subprocess
    ldapargs = LDAPMODIFY.split(" ")
    ldapmod = subprocess.Popen(ldapargs, stdin=subprocess.PIPE, shell=False)
    for user in users:
        ldapstr =  ldap_chsh_string(user, "/usr/local/bin/no_access")
        ldapmod.communicate(ldapstr)
    ldapmod.communicate("\n")
    ldapmod.terminate()

def enable_logins(users):
    """
    re-enable a group of users accounts, by changing shells back
    uses shells from web DB
    wrapper for change spells for LDAP
    """
    change_shell(users)


def rolloff_disable(rolloff_users):
    """stronger disable for account rolloff,
    removes user password to permanently disable login"""
    if rolloff_users == []:
        print "ERROR: No users to star LDAP password for!"
        return

    import subprocess
    ldapargs = LDAPMODIFY.split(" ")
    ldapmod = subprocess.Popen(ldapargs, stdin=subprocess.PIPE, shell=False)
    for user in rolloff_users:
        ldapstr =  ldap_chpw_string(user, "*")
        ldapmod.communicate(ldapstr)
    ldapmod.communicate("\n")
    ldapmod.terminate()


def delete_logins(users):
    """deletes a login from LDAP"""
    if users == []:
        print "ERROR: No users to remove from unix LDAP!"
        return

    import subprocess
    ldapargs = LDAPMODIFY.split(" ")
    ldapmod = subprocess.Popen(ldapargs, stdin=subprocess.PIPE, shell=False)
    for user in users:
        ldapstr =  ldap_rm_string(user)
        ldapmod.communicate(ldapstr)
    ldapmod.communicate("\n")
    ldapmod.terminate()

def change_password(users):
    """changes list of user's password in LDAP based on 
    hashes stored in web DB"""
    if users == []:
        print "ERROR: No users to change LDAP password for!"
        return

    import subprocess
    ldapargs = LDAPMODIFY.split(" ")
    ldapmod = subprocess.Popen(ldapargs, stdin=subprocess.PIPE, shell=False)
    for user in users:
        ldapstr =  ldap_chpw_string(user, user.get_hashes()[HASHTYPE])
        ldapmod.communicate(ldapstr)
    ldapmod.communicate("\n")
    ldapmod.terminate()

def change_shell(users):
    """changes a user's shell in LDAP based on 
    shell stored in web DB"""
    if users == []:
        print "ERROR: No users to change LDAP shell for!"
        return

    import subprocess
    ldapargs = LDAPMODIFY.split(" ")
    ldapmod = subprocess.Popen(ldapargs, stdin=subprocess.PIPE, shell=False)
    for user in users:
        ldapstr =  ldap_chsh_string(user, user.shell)
        ldapmod.communicate(ldapstr)
    ldapmod.communicate("\n")
    ldapmod.terminate()

def describe():
    """describe this module, for testing mostly"""
    print 'ldap_unix module'
