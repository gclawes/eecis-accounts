"""
This module provides facilities for writing scripts which are intended to be
used from the command line. They must follow a simple interface, namely that
their code be encapsulated within a main function. This is subject to change.

The scripts contained within this module are:
| *create* - creates users (?)
"""

import os

def load_scripts():
    dir = os.listdir("accounts/scripts")
    return {d[:-3] : __import__("scripts." + d[:-3], fromlist = ["*"]) for d in dir if d[-3:] == '.py' and d != '__init__.py'}