#!/usr/bin/env python

# A script to update the redis cache with any missing usernames already stored
# in MongoDB. Shouldn't need to run this very often.

import json
import pymongo
from redis import Redis

# Connect to and setup redis
cache = Redis()
# Prep redis keys for user queue (to-do list) and user set (done list)
rd_prefix = "mcapi:test:"
user_q = rd_prefix + "userq"
user_set = rd_prefix + "userset"

# Connect to mixcloud db on Mongo
mongo_conn = pymongo.Connection()
mcdb = mongo_conn.mixcloud

# Helpful pre-message
print "Before sync..."
print "MONGO STATS"
print "No. of users:",  mcdb.user.count()
print
print "REDIS STATS"
print "No. of users in " + user_set + ":", cache.scard(user_set)

# Iterable cursor return by mongo API._id is the same as username
users_cursor = mcdb.user.find(fields="_id")
# List comprehension over dict cursor to store just the usernames
stored_users = [user["_id"] for user in users_cursor]

# Add mongo-stored users to user_set in redis store
for u in stored_users:
    cache.sadd(user_set, u)

# Helpful pre-message
print
print
print "...After sync:"
print "MONGO STATS"
print "No. of users:",  mcdb.user.count()
print
print "REDIS STATS"
print "No. of users in " + user_set + ":", cache.scard(user_set)

