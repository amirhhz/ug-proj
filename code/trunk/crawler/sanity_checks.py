#!/usr/bin/env python

# VERY UNFINISHED!

from settings import MONGO_COLLECTION, CONNS

user_coll = MONGO_COLLECTION

def correct_counts(conn_list):
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

		  
if __name__ == "__main__":
	import sys
	correct_counts(CONNS.keys())
