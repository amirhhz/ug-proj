#!/usr/bin/env python

import json
import pymongo
from redis import Redis
from mixcloud import user
from mixcloud.api import MixcloudAPI

# Get the Mixcloud API
mcapi = MixcloudAPI()

# Connect to and setup redis
cache = Redis()
# Prep redis keys for user queue (to-do list) and user set (done list)
rd_prefix = "mcapi:test:"
user_q = rd_prefix + "userq"
user_todo = rd_prefix + "usertodo"
user_set = rd_prefix + "userset"

# Connect to mixcloud db on Mongo
mongo_conn = pymongo.Connection()
mcdb = mongo_conn.mixcloud

def storeUser(user_obj):
    user_id = user_obj.getUserID()
    mcdb.user.save(user_obj.getUserData())
    cache.sadd(user_set,user_id)
    cache.srem(user_todo,user_id)
    print user_id ####

def enqueueFollowers(username):
    parent = user.MCUser(username, mcapi)
    storeUser(parent)
    # enqueue all followers in cache by looping over follower list ...
    followers = parent.getFollowers()
    for f in followers:
        if (not cache.sismember(user_set, f)
            and
            not cache.sismember(user_todo, f)):
            cache.rpush(user_q, f)
            cache.sadd(user_todo, f)
        
def crawler(init_user):
    if (not cache.sismember(user_set, init_user) 
        and 
        not cache.sismember(user_todo, init_user)):
        cache.rpush(user_q, init_user)
        cache.sadd(user_todo,init_user)
    while (cache.llen(user_q) > 0):
        enqueueFollowers(cache.lpop(user_q))

if __name__ == "__main__":
    import sys
    try:
        crawler(sys.argv[1])
    except KeyboardInterrupt:
        print "\nBYE!"
        print
        print "Set:", cache.scard(user_set) ####
        print "Todo:", cache.scard(user_todo) ####
        print "Queued:", cache.llen(user_q) ####

