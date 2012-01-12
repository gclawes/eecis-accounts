def populate():
    from accounts import database
    from accounts import db
    
    # Generate the base UID map
    for i in xrange(1001):
        u = database.UIDMap(i, True)
        db.session.add(u)
    #for i in xrange(1001,4000):
    for i in xrange(1001,2**16-1):
        u = database.UIDMap(i, False)
        db.session.add(u)
        if i % 1000 == 0:
            print i
            db.session.commit()
    
    # possible statuses an account can have
    # pending accounts
    s = database.AccountStatus("pending_sponsor")
    db.session.add(s)
    s = database.AccountStatus("pending_labstaff")
    db.session.add(s)
    s = database.AccountStatus("pending_create")
    db.session.add(s)
   
    # account is being upgraded
    s = database.AccountStatus("upgrade_sponsor")
    db.session.add(s)
    
    s = database.AccountStatus("upgrade_labstaff")
    db.session.add(s)
    
    s = database.AccountStatus("upgrade_create")
    db.session.add(s)

    # account has been created, this is the "normal" status
    s = database.AccountStatus("active")
    db.session.add(s)
    
    # account has pending password reset, hashes stored in DB
    s = database.AccountStatus("password_reset")
    db.session.add(s)
   
    # for disable and re-enable status
    s = database.AccountStatus("pending_disable")
    db.session.add(s)
    s = database.AccountStatus("pending_enable")
    db.session.add(s)

    # account is marked for rolloff
    s = database.AccountStatus("rolloff")
    db.session.add(s)

    # web-only accounts (for mail aliases, etc)
    s = database.AccountStatus("web_only")
    db.session.add(s)

    
    # Actual data which will need to be used
    u = database.User('staff', 'notavalidpassword')
    u.first_name = 'EECIS'
    u.last_name = 'Staff'
    u.email = 'staff@eecis.udel.edu'
    u.add_domain('sponsor')
    u.status = 'web_only'
    
    u = database.User('admin', 'password2')
    u.first_name = 'Admin'
    u.last_name = 'User'
    u.email = 'test2@domain'
    u.add_domain('labstaff')
    u.add_domain('sponsor')
    u.add_domain('admin')
    u.add_domain('research')
    u.add_domain('acad')
    u.status = 'active'
    db.session.add(u)

    u = database.User('joe1', 'notapassword')
    u.first_name = 'Joe'
    u.last_name = 'Pending'
    u.email = 'joe@account.acad.cis.udel.edu'
    u.add_domain('account')
    u.status = 'pending_create'
    db.session.add(u)

    u = database.User('joe2', 'notapassword')
    u.first_name = 'Joe'
    u.last_name = 'Password'
    u.email = 'joe@account.acad.cis.udel.edu'
    u.add_domain('account')
    u.status = 'pw_reset'
    db.session.add(u)

    u = database.User('joe3', 'notapassword')
    u.first_name = 'Joe'
    u.last_name = 'Disable'
    u.email = 'joe@account.acad.cis.udel.edu'
    u.add_domain('account')
    u.status = 'pending_disable'
    db.session.add(u)

    u = database.User('joe4', 'notapassword')
    u.first_name = 'Joe'
    u.last_name = 'enable'
    u.email = 'joe@account.acad.cis.udel.edu'
    u.add_domain('account')
    u.status = 'pending_enable'
    db.session.add(u)

    u = database.User('joe5', 'notapassword')
    u.first_name = 'Joe'
    u.last_name = 'rolloff'
    u.email = 'joe@account.acad.cis.udel.edu'
    u.add_domain('account')
    u.status = 'pending_rolloff'
    db.session.add(u)

    db.session.commit()
    db.session.close()    
