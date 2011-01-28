#!/usr/bin/env python
"""Crawler settings, using Redis as in-memory cache and MongoDB as storage by 
default"""

from redis import Redis
import pymongo

DEBUG = False

################################################################################
### MongoDB-specific settings ##################################################
################################################################################

MONGO_HOST = "localhost"
MONGO_PORT = 20002
MONGO_DBNAME = "mixcloud"
MONGO_COLLECTION_NAME = "user"
MONGO_USER = None
MONGO_PASSWORD = None

MONGO_SLAVE_OK = False #whether or not  
MONGO_TIMEOUT = None #network timeout for the connection in seconds

MONGO_CONNECTION = pymongo.Connection(host=MONGO_HOST,
                                      port=MONGO_PORT,
                                      slave_okay=MONGO_SLAVE_OK,
                                      network_timeout=MONGO_TIMEOUT)

MONGO_DB = MONGO_CONNECTION[MONGO_DBNAME]
MONGO_COLLECTION = MONGO_DB[MONGO_COLLECTION_NAME]

################################################################################
### Redis-specific settings ####################################################
################################################################################

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

REDIS_CONNECTION = Redis(host=REDIS_HOST,
                         port=REDIS_PORT,
                         db=REDIS_DB,
                         password=REDIS_PASSWORD)

CACHE = REDIS_CONNECTION

# Prep cache keys for user queue (to-do list) and user set (done list)
CACHE_KEY_PREFIX = "mc:crawl2:"
USER_QUEUE = CACHE_KEY_PREFIX + "userq"
USER_TODO = CACHE_KEY_PREFIX + "usertodo"
USER_SET = CACHE_KEY_PREFIX + "userset"


_CONN_TYPES = ["cloudcast", "follower", "following", "favorite", "listen"]
CONNS = {}
for each in _CONN_TYPES:
    if each != "following":
        CONNS[each+"s"] = each+"_count"
    else:
        CONNS[each] = each+"_count"
