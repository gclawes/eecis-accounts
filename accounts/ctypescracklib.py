#  Cracklib using ctypes
#  Original credit to:
# Author: Sean Reifschneider
# Maintainer: Sean Reifschneider
# Home Page: https://github.com/linsomniac/python-ctypescracklib 
# 
# Modifications by Graeme Lawes (gclawes@udel.edu)
# and Robert Deaton (rdeaton@udel.edu)

import os

def FascistCheck(passwd, username = None):
	from ctypes import CDLL, c_char_p
	cracklib = CDLL('accounts/cracklib/libcrack.so.2')
	cracklib.FascistCheck.argtypes = [c_char_p, c_char_p]
	cracklib.FascistCheck.restype = c_char_p

	dictionary = 'accounts/cracklib/cracklib_dict'
	#if not os.path.exists(dictionary + '.pwd'):
	if not os.path.exists(dictionary):
		raise ValueError('Unable to find dictionary file: "%s"' % dictionary)

	ret = cracklib.FascistCheck(passwd, dictionary)
	if ret is not None: return str(ret)

	#  check password against username
	if username is not None:
		if (username.lower() in passwd.lower()
				or ''.join(reversed(username.lower())) in passwd.lower()):
			return 'it is based on your username' 
		usernamechars = {}
		for c in username.lower(): usernamechars[c] = 1
		usernamechars = ''.join(usernamechars.keys())
		passwdchars = {}
		for c in passwd.lower(): passwdchars[c] = 1
		passwdchars = ''.join([ x for x in passwdchars.keys()
				if x not in usernamechars ])
		if ((len(usernamechars) < 5 and len(passwdchars) < 4)
				or (len(usernamechars) < 10 and len(passwdchars) < 2)):
			return 'it is too similar to your username'

	return None
