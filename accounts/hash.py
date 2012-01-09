from random import randrange
import base64
import hashlib
from hashlib import sha1, md5
import crypt
import binascii
import passlib.hash

def openldap_sha(password):
    password = str(password)
    return base64.encodestring(sha1(password).digest()).strip()

def openldap_ssha(password):
    password = str(password)
    salt = ''.join(chr(randrange(0,255)) for i in range(8))
    return base64.encodestring(sha1(password+salt).digest()+salt).strip()
    
def openldap_md5(password):
    password = str(password)
    return base64.encodestring(md5(password).digest()).strip()
    
def openldap_smd5(password):
    password = str(password)
    salt = ''.join(chr(randrange(0,255)) for i in range(8))    
    return base64.encodestring(md5(password+salt).digest()+salt).strip()
    
def make_hash_func(type):
    def hash(password):
        f = getattr(passlib.hash, type)
        return f.encrypt(password)
    return hash
    
supported_hashes = {
    'openldap_sha' : openldap_sha,
    'openldap_ssha' : openldap_ssha,
    'openldap_md5' : openldap_md5,
    'openldap_smd5' : openldap_smd5,
    'crypt' : make_hash_func('des_crypt'),
    'ntlm' : make_hash_func('nthash'),
    'md5' : make_hash_func('md5_crypt'),
    'sha1' : make_hash_func('sha1_crypt'),
    'sha256' : make_hash_func('sha256_crypt'),
    'sha512' : make_hash_func('sha512_crypt')
}

def verify(password, hash):
    types = ['des_crypt', 'md5_crypt', 'sha1_crypt', 'sha256_crypt', 'sha512_crypt']
    for type in types:
        f = getattr(passlib.hash, type)
        if f.identify(hash):
            print type
            return f.verify(password, hash)
    return False
