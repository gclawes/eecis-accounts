import pymysql
from accounts import database, db
from datetime import datetime

staff_sponsors = ['ECE-StaffCheck', 'ECE-Chair', 'ECE-Chair', 'CIS-Chair']
sponsor_map = {
    # 'garcia': 
    'Chester' : 'chester',
    'Barner' : 'barner',
    'shanker' : 'vijay',
    'garcia' : 'jgarcia',
    'Dr. Weile' : 'weile',
    'gao' : 'ggao',
    'Dr. Bohacek' : 'bohacek',
    'Dr. Saunders' : 'saunders',
    'Mike Davis' : 'davis'
}

def format_columns(message, data, file = None):
    first_width = max([len(x[0]) for x in data])
    second_width = max([len(x[1]) for x in data])

    # calculate a format string for the output lines
    format_str= "%%-%ds        %%-%ds" % (first_width, second_width)

    if file is None:
        print message
        print "=" * (first_width + second_width + 8)
        for x in data:
            print format_str % x
    else:
        f = open(file, "w")
        format_str = format_str + "\n"
        f.write(message + "\n")
        f.write("=" * (first_width + second_width + 8) + "\n")
        for x in data:
            f.write(format_str % x)
        f.close()
        
def main():
    skipped = 0
    updated = 0
    datab = pymysql.connect("localhost", "accounts", "not_password", "accounts")
    cur = datab.cursor()
    cur.execute("SELECT * FROM accounts")
    skipped_file = open('skipped.txt', 'w')
    for r in cur.fetchall():
        acad = False
        username, name, sponsor, uid, rolloff, machines, dob, birthplace, type, requested, home, comments, pwhint, no_access, rolloff_flagged, udel_id = r
        if name == "MAIL FORWARDER":
            last_name, first_name = "FORWARDER", "MAIL"
        else:
            try:
                last_name, first_name = map(lambda x: x.strip(), name.split(','))
            except ValueError:
                name_parts = name.split(" ")

                if len(name_parts) == 2:
                    first_name, last_name = name_parts
                elif len(name_parts) == 1:
                    first_name = name_parts[0]
                    last_name = "Unknown?"
                else:
                    first_name = ' '.join(name_parts[:-1])
                    last_name = name_parts[-1]
                    printme = True
                
        no_access = no_access == 'T'
        rolloff_flagged = rolloff_flagged == 'T'
        machines = map(lambda x: x.strip().lower(), machines.split(','))
        domains = []
        ok = True
        for machine in machines:
            if machine in ('acad', 'acad.ece'):
                domains.append('acad')
                continue
            if machine in ('dilbert.eecis', 'dilbert.eecus', 'dilbert', 'eecis', 'research'):
                domains.append('research')
                continue
            if machine in ('porsche.cis'):
                domains.append('porsche')
                porche = True
                continue
            if machine in ('svn'):
                domains.append('svn')
                svn = True
                continue
            if machine in ('image.ece'):
                # This is legacy
                skipped_file.write('%s\tUser has macine "%s" which is not known. We add them anyways.\n' % (username, machine))
                continue
            skipped += 1
            ok = False
            skipped_file.write('%s\tUser has macine "%s" which is not known.\n' % (username, machine))
        if not ok:
            continue

        user = database.User.query.get(username)
        if user is None:
            user = database.User(username)
            user.first_name = first_name
            user.last_name = last_name
            user.status = 'web_only'
            user.birth_city = birthplace
        
        if sponsor in staff_sponsors or sponsor == '':
            sponsor = 'staff'
            skipped_file.write("%s sponsor changed from empty to staff\n" % (username))
        if sponsor in sponsor_map:
            skipped_file.write("%s sponsor changed from to %s to %s\n" % (username, sponsor, sponsor_map[sponsor]))
            sponsor = sponsor_map[sponsor]
        s = database.User.query.get(sponsor)
        if s is None:
            skipped_file.write('%s\tUser\'s sponsor "%s" does not exist in the NIS maps\n' % (username, sponsor))
            skipped += 1
            continue
        # We can tentatively use this to get a list of sponsors
        if 'sponsor' not in s.get_domains():
            s.add_domain('sponsor')
            db.session.add(s)
            db.session.commit()
        user.sponsor = sponsor
            
        # Add any newly discovered domains to the list
        user_domains = user.get_domains()
        for domain in domains:
            if domain not in user_domains:
                user.add_domain(domain)
        if udel_id is not None and udel_id != '':
            user.udel_id = udel_id
            user.email = udel_id + '@udel.edu'
            print 'udel-id'
        # Maybe we should use the other validators here.
        if dob != '':
            try:
                d = datetime.strptime(dob, '%m/%d/%Y')
                user.dob = dob
            except ValueError, e:
                skipped_file.write('%s\tUser\'s dob "%s" is not valid, they get set to empty.\n' % (username, dob))
        
        rolloff = str(rolloff)
        if len(rolloff) == '6':
            user.grad_date = rolloff[4:6] + '/' + rolloff[0:4]
        
        db.session.add(user)
        updated += 1
        
    db.session.commit()
    print '%d users updated, %d users skipped' % (updated, skipped)    