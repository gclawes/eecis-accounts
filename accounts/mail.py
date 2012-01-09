import smtplib

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

def send_token(username, to_addr, token):
    """
    This will use mail.send (above) to send a user's password reset token to them
    """
    subject = "ECE/CIS Password Reset"
    url = "https://www.eecis.udel.edu/accounts/reset_password/token/%s" % token
    message = "A request has been made for a password reset for your ECE/CIS account: %s\n\n" % username
    message += "To reset your password, please visit the follow the reset link below:\n\n%s\n\n" % url
    message += "If this is not your ECE/CIS username, or you did not request a password reset, please\n"
    message += "submit a Help Request at https://www.eecis.udel.edu/helprequest\n\nECE/CIS Labstaff"

    mail('staff@eecis.udel.edu', 'ECE/CIS Account System', \
            [to_addr], subject, message, mailhost='mail.eecis.udel.edu')

