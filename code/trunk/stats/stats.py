#!/usr/bin/env python

# script to get some simple statistics on users
# the save_aggregate_counts() function takes a user connection type and produces simple
# aggregate stats

import csv

from settings import (MONGO_COLLECTION, CONNS, 
                      GENERAL_STATS, AGGR_STATS, MISMATCH_STATS)

user_coll = MONGO_COLLECTION


#def find_dead_user_refs():
#
#    dead_users = set([])
#    dead_user_ref = {}
#    # Find users with empty documents
#    cursor = user_coll.find(
#        spec={"username": {"$exists": False} }, timeout=False)
#    for each in cursor:
#        dead_users.add(each["_id"])
#
#    dead_users = frozenset(dead_users)
#
#    for each in dead_users:
#        dead_user_ref[each] = {}
#        for conn in conn_types_bare[0:3]:
#            dead_user_ref[each][conn] = []
#
#    # Find users with complete documents
#    cursor = user_coll.find(
#        spec={"username": {"$exists": True} }, 
#        fields=conn_types_bare[0:3],
#        timeout=False)
#
#    # Go through the list of complete users
#    for user in cursor:
#        # Scan the social connections for references to the dead user
#        for soc_conn in conn_types_bare[0:2]:
#            for link in user[soc_conn]:
#                if link in dead_users:
#                    dead_user_ref[link][soc_conn].append(user["_id"])
#
#        # Only scan favorites for references
#        # "Cloudcasts" obviously only refer to the user himself
#        for item in user["favorites"]:
#            if item["user"] in dead_users:
#                dead_user_ref[item["user"]]["favorites"].append(user["_id"])
#                
#
#    deadfile = csv.writer(open("deads.csv", "w"), delimiter=";")
#    deadfile.writerow(["username","ref_as_follower", "ref_as_following", "ref_as_faved"])
#    
#    for each in dead_user_ref.keys():
#        deadfile.writerow([
#            each, 
#            len(dead_user_ref[each]["followers"]), 
#            len(dead_user_ref[each]["following"]),
#            len(set(dead_user_ref[each]["favorites"]))
#        ])


def save_user_counts():
    statfile = csv.writer(open(GENERAL_STATS, "w"))
    
    full_ones = user_coll.find(
        spec={"username": {"$exists": True} }, 
        fields=CONNS.values(),
        timeout=False)

    # Write CSV header
    statfile.writerow(["username"] + CONNS.values() )    
    for each in full_ones:
        row = []
        row.append(each["_id"])
        for field in CONNS:
            row.append(each[CONNS[field]])
        statfile.writerow(row)
    
def save_aggregate_counts(conn_type):
    if conn_type not in CONNS:
        print "Invalid connection type."
        return
    count_field = CONNS[conn_type]
    statfile = csv.writer(open(AGGR_STATS[conn_type], "w"))

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


def save_count_mismatch():
    
    field_names = CONNS.keys() + CONNS.values()
    # Find users with complete documents
    cursor = user_coll.find(
                            spec={"username": {"$exists": True} }, 
                            fields=field_names,
                            timeout=False)

    statfile = csv.writer(open(MISMATCH_STATS, "w"))
    # CSV header
    statfile.writerow(["username", "connection", "real_count", "stored_count"])           
    for user in cursor:
        for conn in CONNS:
            if ( len(user[conn]) != user[CONNS[conn]] ):
                row = []
                row.append(user["_id"])
                row.append(conn)
                row.append(len(user[conn]))
                row.append(user[CONNS[conn]])

                statfile.writerow(row)

if __name__ == "__main__":
    import sys
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-m", "--find-mismatches", dest="mismatch",
                      action="store_true", default=False)
    parser.add_option("-a", "--aggregates", dest="aggr",
                      action="store_true", default=False)
    parser.add_option("-g", "--general-stats", dest="general",
                      action="store_true", default=False)
    
    options, args = parser.parse_args()
    if options.general:
        save_user_counts()
        print "Saved general stats to " + GENERAL_STATS + "."
    if options.mismatch:
        save_count_mismatch()
        print "Saved mismatch stats to " + MISMATCH_STATS + "."
    if options.aggr:
        for each in CONNS:
            save_aggregate_counts(each)
            print "Saved aggregate stats for " + each + " in " + AGGR_STATS[each] + "."

        
