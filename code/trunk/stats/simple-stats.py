#!/usr/bin/env python

# script to get some simple statistics on users
# the aggrCount() function takes a user connection type and produces simple
# aggregate stats

import csv
import pymongo

conn = pymongo.Connection()
db = conn.mixcloud
user_coll = db.user
conn_types = ["cloudcast", "follower", "following", "favorite"]

def userCounts():
    statfile = csv.writer(open("stat.csv", "w"))

    full_ones = user_coll.find(
        spec={"username": {"$exists": True} }, 
        fields=["cloudcast_count", "follower_count", "following_count", "favorite_count"],
        timeout=False)

    # Write CSV header
    statfile.writerow(["username", "cloudcast_count", "follower_count", "following_count", "favorite_count"])    
    for each in full_ones:
        # Doing the below because of non-deterministic dictionary listing behaviour
        row = []
        row.append(each["_id"])
        row.append(each["cloudcast_count"])
        row.append(each["follower_count"])
        row.append(each["following_count"])
        row.append(each["favorite_count"])    
        statfile.writerow(row)

def aggrCount(conn_type):
    if conn_type not in conn_types:
        print "Invalid connection type."
        return
    count_field = conn_type+"_count"
    filename = "stat-" + conn_type + ".csv"
    statfile = csv.writer(open(filename, "w"))

    aggr_counts = user_coll.group(
        [count_field], 
        {"username": {"$exists": True} }, 
        {"freq": 0}, 
        "function(row,prev) {prev.freq++;}")

    # Write CSV header
    statfile.writerow([count_field, "freq"])    
    for each in aggr_counts:
        # Doing the below because of non-deterministic dictionary listing behaviour
        row = []
        row.append(each[count_field])
        row.append(each["freq"])
        statfile.writerow(row)    

if __name__ == "__main__":
    import sys
    aggrCount(sys.argv[1])
    
        
