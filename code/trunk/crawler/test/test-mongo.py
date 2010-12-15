#!/usr/bin/env python

import json
import pymongo

from mixcloud import user, api
from collections import deque

users_q = deque()
users_done = user.UserSet([])

mongo_conn = pymongo.Connection()
mcdb = mongo_conn.mixcloud

def storeUser(user):
    user_id = user.getUserID()
    user.mongoSave(mcdb.user)
    users_done.add(user_id)
    print user_id ####

def enqueueFollowers(username):
    parent = user.MCUser(username)
    storeUser(parent)
    users_q.extend(parent.getFollowers())

def crawler(init_user):
    users_q.append(init_user)
    while (len(users_q) > 0):
        enqueueFollowers(users_q.popleft())

if __name__ == "__main__":
    import sys
    try:
        crawler(sys.argv[1])
    except KeyboardInterrupt:
        print users_done
        print
        print "Set:", len(users_done) ####
        print "Queued:", len(users_q) ####

