"""
Each auth_module must provide at least this interface:
"""

def create_logins(users):
    """create login in AUTH, login must not exist"""
    pass

def disable_logins(users):
    """
    disable a user's login by changing their shell to
    /usr/local/bin/no_access"""
    pass

def enable_logins(users):
    """
    disable a user's login by changing their shell to
    /usr/local/bin/no_access"""
    pass

def rolloff_disable(rolloff_users):
    """stronger disable for account rolloff,
    removes user password to permanently disable login"""
    pass

def delete_logins(users):
    """deletes a login from AUTH"""
    pass

def change_password(users):
    """changes a user's password in AUTH based on 
    hashes stored in web DB"""
    pass

def change_shell(users):
    """changes a user's shell in AUTH based on 
    shell stored in web DB"""
    pass

def describe():
    """describe this module, for testing mostly"""
    print 'stub_auth module'
