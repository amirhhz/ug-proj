#!/usr/bin/env python

# VERY UNFINISHED!

import csv
import pymongo

conn = pymongo.Connection()
db = conn.mixcloud
user_coll = db.user
conn_types_bare = ["followers","following","favorites","cloudcasts"]
conn_types = [
	("cloudcasts", "cloudcast_count"), 
	("followers", "follower_count"), 
	("following", "following_count"), 
	("favorites", "favorite_count")
]


def findDeadUserRefs():

	dead_users = set([])
	dead_user_ref = {}
	# Find users with empty documents
	cursor = user_coll.find(
		spec={"username": {"$exists": False} }, timeout=False)
	for each in cursor:
		dead_users.add(each["_id"])

	dead_users = frozenset(dead_users)

	for each in dead_users:
		dead_user_ref[each] = {}
		for conn in conn_types_bare[0:3]:
			dead_user_ref[each][conn] = []

	# Find users with complete documents
	cursor = user_coll.find(
		spec={"username": {"$exists": True} }, 
		fields=conn_types_bare[0:3],
		timeout=False)

	# Go through the list of complete users
	for user in cursor:
		# Scan the social connections for references to the dead user
		for soc_conn in conn_types_bare[0:2]:
			for link in user[soc_conn]:
				if link in dead_users:
					dead_user_ref[link][soc_conn].append(user["_id"])

		# Only scan favorites for references
		# "Cloudcasts" obviously only refer to the user himself
		for item in user["favorites"]:
			if item["user"] in dead_users:
				dead_user_ref[item["user"]]["favorites"].append(user["_id"])
				

	deadfile = csv.writer(open("deads.csv", "w"), delimiter=";")
	deadfile.writerow(["username","ref_as_follower", "ref_as_following", "ref_as_faved"])
	
	for each in dead_user_ref.keys():
		deadfile.writerow([
			each, 
			len(dead_user_ref[each]["followers"]), 
			len(dead_user_ref[each]["following"]),
			len(set(dead_user_ref[each]["favorites"]))
		])

def findCountMismatch():
	
	# Find users with complete documents
	cursor = user_coll.find(
		spec={"username": {"$exists": True} }, 
		ds=["cloudcasts", "cloudcast_count", 
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

def correctFavCount():
	# unzips the conn_types tuple list
#	just_conns = zip(*conn_types)
#	if conn not in just_conns[0]:
#		print "Incorrect metaconnection type used."
#		return
	cursor = user_coll.find(
		spec={"username": {"$exists": True} }, 
		fields=["favorites", "favorite_count"],
		timeout=False)

	correct_counts = {}

	for user in cursor:
		if ( len(user["favorites"]) != user["favorite_count"] ):
			correct_counts[user["_id"]] = len(user["favorites"])

	for each_id in correct_counts.keys():
		user_coll.update(
			spec={"_id": each_id},
			document={"$set": {"favorite_count": correct_counts[each_id]} }
		)

def correctZeroCloudCount():
	user_coll.update(
		spec={"cloudcast_count": 0 },
		document={"$set": { "cloudcasts": []} }
	)

if __name__ == "__main__":
	import sys
	findDeadUserRefs()

