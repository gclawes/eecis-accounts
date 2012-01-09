"""
Auth module for Samba LDAP
"""

HASHTYPE='ntlm'
SHELL='/bin/tcsh'

LDAPUSER="uid=account_update,ou=People,dc=eecis,dc=udel,dc=edu"
LDAPPASSWD="SECRET"
#SMBSERVER="-H ldaps://smb-ldap1.eecis.udel.edu:636"
LDAPSERVER="-H ldaps://account.acad.cis.udel.edu:636"

LDAPADD="/usr/local/openldap/bin/ldapadd -c -x %s -D %s -w %s" % (LDAPSERVER, LDAPUSER, LDAPPASSWD)
LDAPMODIFY="/usr/local/openldap/bin/ldapmodify -x -c %s -D %s -w %s" % (LDAPSERVER, LDAPUSER, LDAPPASSWD)
LDAPSEARCH="/usr/local/openldap/bin/ldapsearch -x %s -b" % (LDAPSERVER)

PWSUFFIX="ou=People,dc=eecis,dc=udel,dc=edu"
GRSUFFIX="ou=Group,dc=eecis,dc=udel,dc=edu"

DEFAULTFLAGS="[U          ]"
DISABLEFLAGS="[UD         ]"

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
    ldapstr += "dn: uid=%s ,%s\n" % (user.username, PWSUFFIX)
    ldapstr += "objectClass: account\n"
    ldapstr += "objectClass: posixAccount\n"
    ldapstr += "objectClass: top\n"
    ldapstr += "objectClass: shadowAccount\n"
    ldapstr += "objectClass: sambaSAMAccount\n"
    ldapstr += "uid: %s\n" % user.username
    ldapstr += "cn: %s\n" % user.username
    ldapstr += "sambaAcctFlags: %s\n" % DEFAULTFLAGS
    ldapstr += "uidNumber: %s\n" % user.uid
    ldapstr += "gidNumber: %s\n" % user.gid
    ldapstr += "homeDirectory: /usa/%s\n" % user.username
    ldapstr += "sambaSID: S-1-5-21-27105391-1648776033-2601101416-${sid}\n" % sid
    ldapstr += "sambaPwdMustChange: 2147483647\n"
    ldapstr += "sambaPasswordHistory: 0000000000000000000000000000000000000000000000000000000000000000\n"
    ldapstr += "sambaPwdCanChange: 1178291445\n"
    ldapstr += "sambaPwdLastSet: 1239220774\n"
    ldapstr += "sambaNTPassword: %s\n" % pw_hash
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
        ldapstr += "replace: sambaNTPassword\n"
        ldapstr += "sambaNTPassword: %s\n" % (newhash)
        ldapstr += "\n"
        return ldapstr

def ldap_rm_string(user):
    ldapstr = ""
    ldapstr += "dn: uid=%s,%s\n" % (user.username, PWSUFFIX)
    ldapstr += "changetype: delete\n"
    ldapstr += "\n"
    return ldapstr

def ldap_chflags_string(user, flags):
    ldapstr = ""
    ldapstr += "dn: uid=%s,%s\n" % (user.username, PWSUFFIX)
    ldapstr += "changetype modify\n"
    ldapstr += "replace sambaAcctFlags\n"
    ldapstr += "sambaAcctFlags: %s\n" % flags
    ldapstr += "\n"
    return ldapstr


# Auth module interface 
#####################################

def create_logins(users):
    """
    create login in samba LDAP, login must not exist
    returns a string for email logs
    """
    MESSAGE = ""
    if users == []:
        MESSAGE += "ERROR: No users to disable LDAP login for!"
        return

    MESSAGE += "Adding users to Samba LDAP:\n"
    MESSAGE += ", ".join([u.username for u in users])

    import subprocess
    ldapargs = LDAPMODIFY.split(" ")
    ldapmod = subprocess.Popen(ldapargs, stdin=subprocess.PIPE, shell=False)
    for user in users:
        ldapstr =  ldap_add_string(user)
        ldapmod.communicate(ldapstr)
    ldapmod.communicate("\n")
    ldapmod.terminate()

    return MESSAGE

    """ LEGACY CODE - only works on dilbert (trusted root)
    import subprocess
    for user in users:
        nt_hash = user.get_hashes()[HASHTYPE]
        print "Adding to samba LDAP: %s %d %d\n" % (user.username, user.uid, user.gid)
        subprocess.call(SSH+['smb-ldap1', '/var/openldap/bin/ldap-mknew-smbaccts.pl' \
                user.username, str(user.uid), str(user.gid), nt_hash], stdout=None)
    """    

def disable_logins(users):
    """
    disable a user's samba by changing their smbAcctFlags
    """
    if users == []:
        print "ERRO: No users to disable Samba login for"
        return
    
    import subprocess
    ldapargs = LDAPMODIFY.split(" ")
    ldapmod = subprocess.Popen(ldapargs, stdin=subprocess.PIPE, shell=False)
    for user in users:
        ldapstr = ldap_chflags_string(user, DISABLEFLAGS)
        ldapmod.communicate(ldapstr)
    ldapmod.communicate("\n")
    ldapmod.terminate()

def enable_logins(users):
    """
    enable a user's samba login by changing their smbAcctFlags
    """
    if users == []:
        print "ERRO: No users to disable Samba login for"
        return
    
    import subprocess
    ldapargs = LDAPMODIFY.split(" ")
    ldapmod = subprocess.Popen(ldapargs, stdin=subprocess.PIPE, shell=False)
    for user in users:
        ldapstr =  ldap_chflags_string(user, DEFAULTFLAGS)
        ldapmod.communicate(ldapstr)
    ldapmod.communicate("\n")
    ldapmod.terminate()

def rolloff_disable(rolloff_users):
    """stronger disable for account rolloff,
    removes user password to permanently disable login
    in the case of samba, wrapper for disable_logins
    """
    disable_logins(rolloff_users)

def delete_logins(users):
    """deletes a login from Samba LDAP"""
    if users == []:
        print "ERROR: No users to remove from Samba LDAP!"
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
    """changes a user's password in Samba LDAP based on 
    hashes stored in web DB"""
    if users == []:
        print "ERROR: No users to change LDAP NT password for!"
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
    """SAMBA HAS NO CONCEPT OF SHELL"""
    print "ERROR: Samba has no shell to change!"
    return

def describe():
    """describe this module, for testing mostly"""
    print 'smb_ldap module'
