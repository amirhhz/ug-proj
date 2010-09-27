#!/usr/bin/env python

import json
import pymongo

from mixcloud import user

users_todo = user.UserSet([])
users_done = user.UserSet([])

conn = pymongo.Connection()
mcdb = conn.mixcloud

def storeUser(username):
	if (username not in users_done):
		u = user.MCUser(username)
		u.mongoSave(mcdb.user)
		users_done.add(username)
		if username in users_todo: users_todo.remove(username)
		return u
	

def crawler(username, depth=1):
	"""Attempting to perform a depth first search from a seed upto a given depth"""

	current_user = storeUser(username)
	if (current_user != None):
		followers = current_user.getFollowers()
		users_todo.update(followers)
		if (depth != 0):
			for each in followers:
#store the children's names but also save their MCUser instances for traversal below
				crawler(each, depth-1)

		print "User Set (size = %d)" % (len(users_done))

if __name__ == "__main__":
	import sys
	crawler(sys.argv[1])
