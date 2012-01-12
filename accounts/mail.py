import smtplib

#MAILHOST = 'mail.eecis.udel.edu'
MAILHOST = 'mail.udel.edu'

def send(from_addr, from_name, to_list, subject, message, mailhost='mail.eecis.udel.edu'):
    """
    This will send an e-mail from the address from_addr, with the name from_name,
    to all the users in to_list.
    ex: send('root@mail.eecis.udel.edu', 'Super User', ['rdeaton@udel.edu'], 'Hi there', 'You're awesome')
    """    
    s = smtplib.SMTP(mailhost)
    s.helo(mailhost)
    data =  'To: %s\n' % (','.join(to_list))
    data += 'From: "%s" <%s>\n' % (from_name, from_addr)
    data += 'Subject: %s\n' % (subject)
    data += message
    data += "\n\n"
    s.sendmail(from_addr, to_list, data)

def send_token(user):
    """
    This will use mail.send (above) to send a user's password reset token to them
    """
    if 'research' in user.get_domains():
        domain = 'research'
    else: domain = 'academic'
    subject = "ECE/CIS Password Reset"
    url = "https://www.eecis.udel.edu/accounts/reset_password/token/%s" % user.token
    message = "A request has been made for a password reset for your ECE/CIS %s account: %s\n\n" % (domain, user.username)
    message += "To reset your password, please visit the follow the reset link below:\n\n%s\n" % url
    message += "This token will expire 30 minutes after the initial request was made\n\n"
    message += "If this is not your ECE/CIS username, or you did not request a password reset, please\n"
    message += "submit a Help Request at https://www.eecis.udel.edu/helprequest\n\nECE/CIS Labstaff"

    send('account@eecis.udel.edu', 'ECE/CIS Account System', \
            [user.email], subject, message, MAILHOST)

def create_email(user):
    """
    Send an email to a user notifying them that their account has been created.
    """
    if 'research' in user.get_domains():
        domain = 'research'
    else: domain = 'academic'
    subject = "ECE/CIS Account Created"
    helprequest = "https://www.eecis.udel.edu/service"
    
    message = "Your ECE/CIS %s account has been created with the username: %s\n\n" % (domain, user.username)
    message += "Please do not reply to this message.  If you need assistance with your account, please visit:\n"
    message += "%s\n\n" % helprequest
    message += "-- EE/CIS Labstaff\n"

    send('account@eecis.udel.edu', 'ECE/CIS Account System', \
            [user.email], subject, message, MAILHOST) 

def change_email(user):
    """
    Send an email to a user notifying them that their login info has changed.
    """
    if 'research' in user.get_domains():
        domain = 'research'
    else: domain = 'academic'
    subject = "ECE/CIS Account - Login Changed"
    helprequest = "https://www.eecis.udel.edu/service"

    message = "A request has been made to change the login information for your ECE/CIS %s account: %s.\n" % (domain, user.username)
    message = "This request may have been a change to any of the following: password, login shell, or GECOS information\n\n"
    message += "If you did not make this request or feel this messag was sent in error, \n"
    message += "please contact ECE/CIS Labstaff immediately at: %s\n\n" % helprequest
    message += "If you are unable to log into your account, you my post a ticket as an outsider\n\n"
    message += "-- EE/CIS Labstaff\n"

    send('account@eecis.udel.edu', 'ECE/CIS Account System', \
            [user.email], subject, message, MAILHOST) 

def sponsor_reject(user):
    """
    Sends rejection emails to a user if their sponsor has rejected their application.
    Does not send an email if the user's comment field is empty.
    """
    if user.comments in (None or ""):
        return

    subject = "ECE/CIS Account - Account Application rejected for %s" % user.username
    application = "https://www.eecis.udel.edu/NewAccount/"
    
    message = "Your ECE/CIS Account has been rejected by the faculty sponsor you selected (%s).\n" % user.sponsor
    message += "The reason given for rejection was:\n\n%s\n\n" % user.comments
    message += "You may re-apply with corrected information at %s\n" % application
    message += "Please don't reply to this email.  If have any questions, please contact\n"
    message += "the faculty member you listed as sponsor or labstaff.\n\n"
    message += "-- ECE\CIS Labstaff"
    
    send('account@eecis.udel.edu', 'ECE/CIS Account System', \
            [user.email], subject, message, MAILHOST) 

def admin_reject(user):
    """
    Sends rejection emails to a user if their sponsor has rejected their application.
    Does not send an email if the user's comment field is empty.
    """
    if user.comments in (None or ""):
        return

    subject = "ECE/CIS Account - Account Application rejected for %s" % user.username
    application = "https://www.eecis.udel.edu/NewAccount/"
    helprequest = "https://www.eecis.udel.edu/service"
    sponsor = "%s@eecis.udel.edu" % user.sponsor
    
    message = "Your ECE/CIS Account has been rejected by ECE/CIS faculty adminstrators.\n" % user.sponsor
    message += "The reason given for rejection was:\n\n%s\n\n" % user.comments
    message += "You may re-apply with corrected information at %s\n" % application
    message += "Please don't reply to this email.  If have any questions, please \n"
    message += "please post a ticket as an outsider at %s" % helprequest
    message += "-- ECE\CIS Labstaff"


    send('account@eecis.udel.edu', 'ECE/CIS Account System', \
            [user.email, sponsor], subject, message, MAILHOST) 

