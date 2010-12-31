#!/usr/bin/env python
"""Test script that takes a filename and a list of users as arguments and saves
the users' data to the file."""

from mixcloud.api import MixcloudAPI
from mixcloud.resources import User
import json

def fetch_users(userlist, filename):
    mix = MixcloudAPI()
    testfile = open(filename,"w")
    for each in userlist:
        print each, "(current user)"
        current_user = User(mix, each)
        print each, "(populating...)"
        current_user.populate()
        print each, "(populated, dumping to file)"
        json.dump(current_user.get_data(),testfile, indent=2)
        print each, "(OK)"

if __name__ == "__main__":
    import sys
    try:
        userlist = sys.argv[2:]
        fetch_users(userlist, sys.argv[1])
    except KeyboardInterrupt:
        print "\nBYE!"
