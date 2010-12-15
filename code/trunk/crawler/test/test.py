#!/usr/bin/env python

import json

# from mixcloud.api import getFromAPI, api_url, r_api_url
from mixcloud import user, artist, category, cloudcast, search, tag, track

def run(username):
	userData = user.getUser(username)
	print json.dumps(userData, indent=4)

	followers = user.getUserFollowers(username)
	print "Followers %d:\n %s" % (len(followers), followers)	

if __name__ == "__main__":
	import sys
	run(sys.argv[1])
