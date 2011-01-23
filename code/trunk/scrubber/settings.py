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
MONGO_PORT = 20001
MONGO_DBNAME = "mixcloud"
MONGO_COLLECTION_NAME = "user"
MONGO_USER = None
MONGO_PASSWORD = None

MONGO_SLAVE_OK = True #whether or not  
MONGO_TIMEOUT = None #network timeout for the connection in seconds

MONGO_CONNECTION = pymongo.Connection(host=MONGO_HOST,
                                      port=MONGO_PORT,
                                      slave_okay=MONGO_SLAVE_OK,
                                      network_timeout=MONGO_TIMEOUT)

MONGO_DB = MONGO_CONNECTION[MONGO_DBNAME]
MONGO_COLLECTION = MONGO_DB[MONGO_COLLECTION_NAME]


_CONN_TYPES = ["cloudcast", "follower", "following", "favorite", "listen"]
CONNS = {}
for each in _CONN_TYPES:
    if each != "following":
        CONNS[each+"s"] = each+"_count"
    else:
        CONNS[each] = each+"_count"
