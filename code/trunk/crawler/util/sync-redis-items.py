#!/usr/bin/env python

# A script to sync the redis userq list with the usertodo set

import json
from redis import Redis

# Connect to and setup redis
cache = Redis()
# Prep redis keys for user queue (to-do list) and user set (done list)
rd_prefix = "mc:snowball:"
user_todo = rd_prefix + "usertodo"
user_q = rd_prefix + "userq"

# Helpful pre-message
print "Before sync..."
print "*" * 80
print "REDIS STATS"
print "No. of users in " + user_q + ":", cache.llen(user_q)
print
print "REDIS STATS"
print "No. of users in " + user_todo + ":", cache.scard(user_todo)

# Add mongo-stored users to user_set in redis store
uset = cache.smembers(user_todo)
cache.ltrim(user_q,0,0)
for u in uset:
    cache.rpush(user_q, u)

# Helpful pre-message
print "Before sync..."
print "*" * 80
print "REDIS STATS"
print "No. of users in " + user_q + ":", cache.llen(user_q)
print
print "REDIS STATS"
print "No. of users in " + user_todo + ":", cache.scard(user_todo)

