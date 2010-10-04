#!/usr/bin/env python

from mixcloud import api, user

def run(username):

    u = user.MCUser(username)
    f = u.getListenedTo()
    print f
    print len(f)
    
if __name__ == "__main__":
	import sys
	run(sys.argv[1])
