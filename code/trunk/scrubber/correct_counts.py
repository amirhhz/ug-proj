#!/usr/bin/env python

from settings import MONGO_COLLECTION, CONNS

user_coll = MONGO_COLLECTION

def correct_counts(conn_list):
	"""Find and fix incorrect counts for the given connection type for all 
	users."""
	for conn in conn_list:
		if conn not in CONNS:
			print "ERROR: One of the metaconnections given is not valid:", conn
			return

		cursor = user_coll.find(
			spec={"username": {"$exists": True} }, 
			fields=[conn, CONNS[conn]],
			timeout=False)
		
		correct_counts = {}
		
		for user in cursor:
			real_count = len(user[conn])
			if ( real_count != user[CONNS[conn]] ):
				correct_counts[user["_id"]] = real_count
	
		for each_id in correct_counts:
			user_coll.update(
				spec={"_id": each_id},
				document={"$set": {CONNS[conn]: correct_counts[each_id]} }
			)	

def correct_count(username, conn):
	if conn not in CONNS:
		print "ERROR: One of the metaconnections given is not valid:", conn
		return
	user = user_coll.find_one(
							spec={"username": username}, 
							fields=[conn,CONNS[conn]]
							)
	
	if not (len(user[conn]) == user[CONNS[conn]]):
		user_coll.update(
						spec={"_id": user["_id"]},
						document={"$set": {CONNS[conn]: len(user[conn])} }
						)
		
	
		  
if __name__ == "__main__":
	import sys
	correct_counts(CONNS.keys())
