#!/usr/bin/env python

import json
import pymongo
from redis import Redis
from mixcloud import user, api

# Connect to and setup redis
cache = Redis()
# Prep redis keys for user queue (to-do list) and user set (done list)
rd_prefix = "mcapi:test:"
user_q = rd_prefix + "userq"
user_set = rd_prefix + "userset"

# Connect to mixcloud db on Mongo
mongo_conn = pymongo.Connection()
mcdb = mongo_conn.mixcloud

def storeUser(user):
    user_id = user.getUserID()
    user.mongoSave(mcdb.user)
    cache.sadd(user_set,user_id)
    print user_id ####

def enqueueFollowers(username):
    parent = user.MCUser(username)
    storeUser(parent)
    # enqueue all followers in cache by looping over follower list ...
    # ... there must be a better way? multi-push?
    followers = parent.getFollowers()
    for f in followers:
        cache.rpush(user_q, f)
        
def crawler(init_user):
    cache.rpush(user_q, init_user)
    while (cache.llen(user_q) > 0):
        enqueueFollowers(cache.lpop(user_q))

if __name__ == "__main__":
    import sys
    try:
        crawler(sys.argv[1])
    except KeyboardInterrupt:
        print "BYE!"
        print
        print "Set:", cache.scard(user_set) ####
        print "Queued:", cache.llen(user_q) ####
