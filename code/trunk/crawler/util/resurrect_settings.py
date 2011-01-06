#!/usr/bin/env python
"""Settings used by the resurrect script to fill in the gaps for the dead users 
in MongoDB."""
import pymongo
import time

###############################################################################
### MongoDB-specific settings ##################################################
################################################################################

MONGO_HOST = "localhost"
MONGO_PORT = 27017
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

### UNTIL TIME - get information up to this point 
UNTIL_YEAR = 2010
UNTIL_MONTH = 10 #in 1-12 range
UNTIL_DAY = 22
UNTIL_TIME = int(time.mktime(
                         (UNTIL_YEAR, UNTIL_MONTH, UNTIL_DAY, 0, 0, 0, 0, 0 ,0)
                         ))