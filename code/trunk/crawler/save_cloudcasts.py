#!/usr/bin/env python

# Script to retrieve and save the cloudcasts associated with users already in 
# the database. Only had to use this when I had a list of users without metas.


import json
import pymongo
from redis import Redis
from mixcloud import user
from mixcloud.api import MixcloudAPI

# Get the Mixcloud API
mcapi = MixcloudAPI()

# Connect to mixcloud db on Mongo
mongo_conn = pymongo.Connection()
mcdb = mongo_conn.mixcloud
admindb = mongo_conn.admin
        
def save_cloudcasts():
    # Timeout is False so that when api blocks, cursor is not lost
    cursor = mcdb.user.find({"cloudcast_count": {"$gt":0} },timeout=False,fields=["_id","cloudcast_count", "cloudcasts"], sort=[("cloudcast_count", pymongo.ASCENDING)])
    print cursor.count(), "users to go through."
    print
    for u in cursor:
        db_cc_count = u["cloudcast_count"]
        # Only attempt to save use if cloudcasts is empty or its size doesn't
        # match cloudcast_count
        if (
            (u["cloudcasts"] != []) and
            (len(u["cloudcasts"]) == db_cc_count)
        ): 
            continue

        # create a user object if the above test is passed
        curr_user = user.User(u["_id"], mcapi)

        live_count = curr_user.getUserData()["cloudcast_count"]

        print u["_id"], ":" ####
        print "cloudcast_count in DB:", db_cc_count
        print "len(cloudcasts) in DB:", len(u["cloudcasts"])
        print "cloudcast_count LIVE:", live_count
        print

        # if there are no cloudcasts for the user, skip        
        if (live_count == 0):
            continue

        # if count stored in db is the same as the live count            
        elif (db_cc_count == live_count):
            print u["_id"], "still has only", db_cc_count, "Cloudcasts ..."
            # check that the cloudcasts are all stored and act if not
            if (len(u["cloudcasts"]) != live_count):
                print " ... but they are not all saved, wait for retrieval..."
                ccs = curr_user.getCloudcasts()
                # update db record appropriately
                mcdb.user.save( 
                    {"_id":u["_id"]}, 
                    {"$addToSet": {"cloudcasts": ccs}, "cloudcast_count":live_count} 
                )
                print "Saved."
                admindb.command("fsync",async=1)
            print "Up to date."
            print
            
        # If here, then stored count and live count differ, so get cloudcasts
        else:
            print u["_id"], "has uploaded more ..."
            print "Saving ..."
            ccs = curr_user.getCloudcasts()
            mcdb.user.save(
                {"_id":u["_id"]}, 
                {"$addToSet": {"cloudcasts": ccs}, "cloudcast_count": live_count}
            )
            print "Saved."
            admindb.command("fsync",async=1)
            print
        

if __name__ == "__main__":
    import sys
    try:
        save_cloudcasts()
    except KeyboardInterrupt:
        admindb.command("fsync")
        print "\nBYE!"

