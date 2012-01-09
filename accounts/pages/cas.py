from accounts import app
from flask import request, redirect, session
import urllib
from xml.dom import minidom

CAS_HOST = 'https://cas.nss.udel.edu/cas'
CAS_SERVICE = 'http://account.acad.cis.udel.edu:5050/cas/'

@app.route('/cas')
@app.route('/cas/')
@app.allow('all')
def cas():
    if 'ticket' in request.args:
        p = urllib.urlencode({'ticket' : request.args.get('ticket'),
                              'service' : CAS_SERVICE})
        response = urllib.urlopen(CAS_HOST + '/serviceValidate?' + p).read()
        xml = minidom.parseString(response)
        if not xml.getElementsByTagName('cas:authenticationSuccess'):
            # Their CAS login failed. Redirect them again
            p = urllib.urlencode({'renew' : 'true', 'service' : CAS_SERVICE})
            return redirect(CAS_HOST + '/login?' + p)
        udel_id = xml.getElementsByTagName('cas:udelnetid')[0].firstChild.data
        session['cas_id'] = udel_id
        location = session.pop('cas_redirect', None)
        if location is None:
            return 'Why are you here?'
        return redirect(location)
    else:
        p = urllib.urlencode({'renew' : 'true', 'service' : CAS_SERVICE})
        return redirect(CAS_HOST + '/login?' + p)