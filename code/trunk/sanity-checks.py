#!/usr/bin/env python

# VERY UNFINISHED!

import csv
import pymongo

conn = pymongo.Connection()
db = conn.mixcloud
user_coll = db.user
conn_types = [
	("cloudcasts", "cloudcast_count"), 
	("followers", "follower_count"), 
	("following", "following_count"), 
	("favorites", "favorite_count")
]

full_users = {}
count_mismatch = []

dead_users = set([])
dead_user_ref = {}

def findDeadUserRefs():
    # Find users with empty documents
    cursor = user_coll.find(
	    spec={"username": {"$exists": False} }, timeout=False)

    for each in cursor:
    	dead_users.add(each["_id"])
    dead_users = frozenset(dead_users)
    for each in dead_users:
        dead_user_ref[each] = {}

    # Find users with complete documents
    cursor = user_coll.find(
	    spec={"username": {"$exists": True} }, 
	    fields=["cloudcasts", "cloudcast_count", 
		    "followers", "follower_count", 
		    "following", "following_count", 
		    "favorites", "favorite_count"],
	    timeout=False)

    for user in cursor:
        dead_user_ref[user["_id"]] = None


def findCountMismatch():
    # Find users with complete documents
    cursor = user_coll.find(
	    spec={"username": {"$exists": True} }, 
	    fields=["cloudcasts", "cloudcast_count", 
		    "followers", "follower_count", 
		    "following", "following_count", 
		    "favorites", "favorite_count"],
	    timeout=False)

    statfile = csv.writer(open("user-count-matching.csv", "w"))
    for user in cursor:
        for conn in conn_types:
            if ( len(user[conn[0]]) != user[conn[1]] ):
                row = []
                row.append(user["_id"])
                row.append(conn[0])
                row.append(len(user[conn[0]]))
                row.append(user[conn[1]])
               
                statfile.writerow(row)

if __name__ == "__main__":
    import sys
    findCountMismatch()

