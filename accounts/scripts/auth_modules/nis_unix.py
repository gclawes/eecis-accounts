"""
auth_module for NIS

create_logins() must be called as root, as it adds lines 
to /var/yp/src/{passwd+,group+} files.
"""

import subprocess


# NIS specific settings
#NISHOME="/var/yp/src/"
NISHOME="" # use this dir for testing
PWPLUS=NISHOME+"passwd+" 
PWLOCAL=NISHOME+"passwd.local"
GRPLUS=NISHOME+"group+"
GRLOCAL=NISHOME+"group.local"
HASHTYPE='openldap_ssha' # TODO: use something other than md5 hashes
SHELL='/bin/tcsh'

#these must be in list format for python's subproces.call()
RCS_CO=["/usr/local/gnu/bin/co", "-l"]
RCS_CI=["/usr/local/gnu/bin/ci", "-u"]

# Helper Functions
#####################################

def rcs_co(filename):
    if RCS_CO != 'FALSE': # For test scripts
        subprocess.call(RCS_CO.append(filename))

def rcs_ci(filename, message):
    msg_arg = "-m\"%s\"" % message
    if RCS_CI != 'FALSE': # For test scripts
        subprocess.call(RCS_CI.append(filename))

def change_passwd_file(entries, message):
    """
    takes a list of password entries in the form of a 7-list of:
    [username, hash, uid, gid, gecos, home, shell]
    all of these values are strings 

    changes are applied by UID
    
    uses this entry to change the passwd.local file
    message is the header of the RCS checkin message, 
    usernames are appended to it after a newline 
    """
    from fcntl import lockf, LOCK_EX, LOCK_UN
    rcs_co(PWLOCAL)
   
    # map uids to entries
    changes = {entry[2] : entry for entry in entries}

    try: 
        pwfile = open(PWLOCAL, "r+")
    except IOError: # if passwd+ file doesn't exist (shouldn't happen)
        print "ERROR: Cannot open %s, exiting" % PWLOCAL
        return
    lockf(pwfile, LOCK_EX)

    pwlines = []
    usernames = []
    for line in pwfile:
        username, hash, uid, gid, gecos, home_dir, shell = line.split(':')
        if uid in changes: # if it's a change
            # hack to preserve old hash
            if changes[uid][1] == 'NOCHANGE':
                changes[uid][1] = hash
            pwlines.append(':'.join(changes[uid]))
            usernames.append(username)
        else: # otherwise, just re-add entry
            pwlines.append(':'.join([username, hash, uid, gid, gecos, home_dir, shell]))

    # open file for writing, truncate contents, 
    # re-write them with the contests of pwlines
    pwfile = open(PWLOCAL, "w+")
    pwfile.writelines(pwlines)

    ci_message = message + "\n%s" % ', '.join(usernames)
    rcs_ci(PWLOCAL, ci_message)

    lockf(pwfile, LOCK_UN)
    pwfile.close()


# Auth module interface 
#####################################

def create_logins(users):
    """
    takes a list of (1 or more) pending users, generates NIS entry
    add entry to passwd+ holding file, removing an existing entry by that name or UID,
    duplicates are re-written with info from the web DB
    returns a string for email logs
    """
    MESSAGE = ""
    if users == []:
        MESSAGE += "ERROR: No users to add to NIS!"
        return

    from fcntl import lockf, LOCK_EX, LOCK_UN
    
    # generate NIS entry
    ypentries = []
    shadowed = []
    uids = [u.uid for u in users]
    usernames = [u.username for u in users]
    for user in users:
        yphash = user.get_hashes()[HASHTYPE]
        gecos = "%s %s,,,%s" % (user.first_name, user.last_name, ','.join(user.get_domains()))
        ypentry = { "passwd" : [user.username, yphash, str(user.uid), str(user.gid), gecos, "/usa/%s" % (user.username), SHELL], \
                "group" : [user.username, "*", str(user.gid), user.username] }
        shadow = ':'.join([user.username, yphash, str(user.uid), str(user.gid), gecos, "/usa/%s" % (user.username), SHELL])
        ypentries.append(ypentry)
        shadowed.append(shadow)

    # open file read only, lock it
    try: 
        pwfile = open(PWPLUS, "a+")
    except IOError: # if passwd+ file doesn't exist (shouldn't happen)
        MESSAGE += "ERROR: %s does not exist, creating it." % PWPLUS
        pwfile = open(PWPLUS, "w+")
    try: 
        grfile = open(GRPLUS, "a+")
    except IOError: # if passwd+ file doesn't exist (shouldn't happen)
        MESSAGE += "ERROR: %s does not exist, creating it." % PWPLUS
        grfile = open(GRPLUS, "w+")
    
    # acquire exclusive lock on passwd+
    lockf(pwfile, LOCK_EX)
    lockf(grfile, LOCK_EX)

    pwplus = []
    grplus = []
    for line in pwfile:
        username, hash, uid, gid, gecos, home_dir, shell = line.split(':')
        if int(uid) not in uids: # detect remove duplicates
            pwplus.append(line) # create list containing existing passwd+ entries
            grline = ":".join([username, "*", gid, username])
            grplus.append(grline) # assume lines in passwd+ are in group+

    # add entry to list
    MESSAGE += "Adding users to %s and %s\n" % (PWPLUS, GRPLUS)
    MESSAGE += "\n".join(shadowed) + "\n"
    for entry in ypentries:
        pwplus.append(':'.join(entry["passwd"])+'\n')
        grplus.append(':'.join(entry["group"])+'\n')

    # open file for writing, truncate contents, 
    # re-write them with the contests of pluslines
    pwfile = open(PWPLUS, "w+")
    grfile = open(GRPLUS, "w+")
    pwfile.writelines(pwplus)
    grfile.writelines(grplus)

    #unlock and close file
    lockf(pwfile, LOCK_UN)
    lockf(grfile, LOCK_UN)
    pwfile.close()
    grfile.close()

    return MESSAGE

def disable_logins(users):
    """
    disable a user's login by changing their shell to
    /usr/local/bin/no_access
    """
    MESSAGE = 'Changed shell to "/usr/local/bin/no_access" for:'
    if users == []:
        print "ERROR: No users to disable login in NIS!"
        return
    
    # form list of passwd entries in the format:
    # (username, hash, uid, gid, gecos, home, shell)
    # these are the accounts to be disabled
    # set hash to "NOCHANGE" so change_passwd_file uses old one entries = []
    entries = []
    for u in users:
        gecos = "%s %s,,,%s" % (u.first_name, u.last_name, \
                ','.join(u.get_domains()))
        entries.append([u.username, 'NOCHANGE', str(u.uid), str(u.uid), gecos, \
                "/usa/"+u.username, '/usr/local/bin/no_access\n'])
    
    # commit these changes to the passwd.local file
    change_passwd_file(entries, MESSAGE)

def enable_logins(users):
    """
    re-enable a user's login by changing their shell
    from /usr/local/bin/no_access" the shell stored in their account
    merely a wrapper for change_shells, restores shell to one stored in web db
    """
    change_shell(users)

def rolloff_disable(rolloff_users):
    """stronger disable for account rolloff,
    removes user password to permanently disable login
    """
    MESSAGE = "Starred password in passwdd.local for:"
    if rolloff_users == []:
        print "ERROR: No users to star passwords in NIS!"
        return

    # form list of passwd entries in the format:
    # (username, hash, uid, gid, gecos, home, shell)
    # thesea are the changes to make
    entries = []
    for u in rolloff_users:
        gecos = "%s %s,,,%s" % (u.first_name, u.last_name, \
                ','.join(u.get_domains()))
        entries.append([u.username, "*", str(u.uid), str(u.uid), gecos, \
                "/usa/"+u.username, u.shell+'\n'])
    
    # commit these changes to the passwd.local file
    change_passwd_file(entries, MESSAGE)

def delete_logins(users):
    """deletes a login from /var/yp/src/passwd.local and /var/yp/src/group.local"""
    if users == []:
        print "ERROR: No users to delete from NIS!"
        return

    from fcntl import lockf, LOCK_EX, LOCK_UN

    # form list of UIDs to disable, usernames for RCS message
    rm_uids = []
    usernames = []
    for user in users:
        rm_uids.append(user.uid)
        usernames.append(user.username)

    # check out, open, and lock the passwd.local file
    rcs_co(PWLOCAL)
    rcs_co(GRLOCAL)

    try: 
        pwfile = open(PWLOCAL, "r+")
        lockf(pwfile, LOCK_EX)
    except IOError: # if passwd+ file doesn't exist (shouldn't happen)
        print "ERROR: Cannot open %s, exiting" % PWLOCAL
        return
    
    try: 
        grfile = open(GRLOCAL, "r+")
        lockf(grfile, LOCK_EX)
    except IOError: # if passwd+ file doesn't exist (shouldn't happen)
        print "ERROR: Cannot open %s, exiting" % GRLOCAL
        return

    # create list of all lines in passwd.local
    pwlines = pwfile.readlines()
    # iterate through all lines, change UIDs that are in list to disable
    for line in pwlines:
        username, hash, uid, gid, gecos, home_dir, shell = line.split(':')
        if int(uid) in rm_uids:
            pwlines.remove(line)
    
    # create list of all lines in group.local
    grlines = grfile.readlines()
    for line in grlines:
        username, star, gid, gname = line.split(':')
        if int(uid) in rm_uids:
            grlines.remove(line)
    
    
    # open file for writing, truncate contents, 
    # re-write them with the contests of pluslines
    pwfile = open(PWLOCAL, "w+")
    grfile = open(GRLOCAL, "w+")
    pwfile.writelines(pwlines)
    grfile.writelines(grlines)
    
    #unlock and close file
    lockf(pwfile, LOCK_UN)
    pwfile.close()

    ci_message = "Removed users from passwd.local:\n%s." % (", ".join(usernames))
    rcs_ci(PWLOCAL, ci_message)
    pwfile.close()
    ci_message = "Removed users from group.local:\n%s." % (", ".join(usernames))
    rcs_ci(GRLOCAL, ci_message)
    grfile.close()

def change_password(users):
    """
    changes a user's password in AUTH based on 
    hashes stored in web DB
    """
    MESSAGE = "Changed password in passwd.local for:"
    if users == []:
        print "ERROR: No users to change NIS password for!"
        return

    entries = []
    # form dict of new hashes, keyed by uids
    for u in users:
        hash = u.get_hashes()[HASHTYPE]
        gecos = "%s %s,,,%s" % (u.first_name, u.last_name, \
                ','.join(u.get_domains()))
        entries.append([u.username, hash, str(u.uid), str(u.uid), gecos, \
                "/usa/"+u.username, u.shell+'\n'])
    
    # commit these changes to the passwd.local file
    change_passwd_file(entries, MESSAGE)

def change_shell(users):
    """changes a user's shell in AUTH based on 
    shell stored in web DB"""
    MESSAGE = "Changed shell for:"
    if users == []:
        print "ERROR: No users to change NIS for!"
        return

    # form list of passwd entries in the format:
    # (username, hash, uid, gid, gecos, home, shell)
    # these are the accounts to be disabled
    # set hash to "NOCHANGE" so change_passwd_file uses old one
    entries = []
    for u in users:
        gecos = "%s %s,,,%s" % (u.first_name, u.last_name, \
                ','.join(u.get_domains()))
        entries.append([u.username, 'NOCHANGE', str(u.uid), str(u.uid), gecos, \
                "/usa/"+u.username, u.shell.strip()+'\n'])
    
    # commit these changes to the passwd.local file
    change_passwd_file(entries, MESSAGE)

