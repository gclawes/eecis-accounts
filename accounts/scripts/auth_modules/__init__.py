import os

def load_modules():
    dir = os.listdir("accounts/scripts/auth_modules")
    dir.remove("stub_auth.py") # never ever import the stub auth, it's just the interface definition
    return { d[:-3] : __import__("scripts.auth_modules." + d[:-3], fromlist = ["*"]) for d in dir if d[-3:] == '.py' and d != '__init__.py'}
