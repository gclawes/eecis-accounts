"""
Each auth_module must provide at least this interface:
"""

def create_logins(users):
    """create login in AUTH, login must not exist"""
    MESSAGE = "DEBUG: Creating accounts in test_auth for:"
    MESSAGE += ', '.join([u.username for u in users])
    return MESSAGE

def disable_logins(users):
    """
    disable a user's login by changing their shell to
    /usr/local/bin/no_access"""
    print "DEBUG: Disabling accounts in test_auth for:"
    print ', '.join([u.username for u in users])

def enable_logins(users):
    """
    disable a user's login by changing their shell to
    /usr/local/bin/no_access"""
    print "DEBUG: Enabling accounts in test_auth for:"
    print ', '.join([u.username for u in users])

def rolloff_disable(rolloff_users):
    """stronger disable for account rolloff,
    removes user password to permanently disable login"""
    print "DEBUG: Setting password to * accounts in test_auth for:"
    print ', '.join([u.username for u in rolloff_users])

def delete_logins(users):
    """deletes a login from AUTH"""
    print "DEBUG: Deleting accounts in test_auth for:"
    print ', '.join([u.username for u in users])

def change_password(users):
    """changes a user's password in AUTH based on 
    hashes stored in web DB"""
    print "DEBUG: Changing passwords in test_auth for:"
    print ', '.join([u.username for u in users])

def change_shell(users):
    """changes a user's shell in AUTH based on 
    shell stored in web DB"""
    print "DEBUG: Changing shells in test_auth for:"
    print ', '.join([u.username for u in users])

def describe():
    """describe this module, for testing mostly"""
    print 'test_auth module'
