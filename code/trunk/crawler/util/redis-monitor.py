#!/usr/bin/env python

from redis import Redis
from time import sleep
from datetime import datetime

# Connect to and setup redis
cache = Redis()
# Prep redis keys for user queue (to-do list) and user set (done list)
rd_prefix = "mc:crawl2:"
user_q = rd_prefix + "userq"
user_todo = rd_prefix + "usertodo"
user_set = rd_prefix + "userset"

# uq = userq, ut = usertodo, us=userset
curr_uq_cnt = cache.llen(user_q)
curr_ut_cnt = cache.scard(user_todo)
curr_us_cnt = cache.scard(user_set)
curr_expected = curr_us_cnt+curr_ut_cnt
prev_uq_cnt = 0
prev_ut_cnt = 0
prev_us_cnt = 0
prev_expected = 0
try:
    while True:
        print "-"*10, datetime.now(), "-"*20

        prev_us_cnt = curr_us_cnt
        curr_us_cnt = cache.scard(user_set)    
        print "Set:".rjust(8), str(curr_us_cnt).rjust(8), "| delta:", curr_us_cnt-prev_us_cnt

        prev_ut_cnt = curr_ut_cnt
        curr_ut_cnt = cache.scard(user_todo) 
        print "Todo:".rjust(8), str(curr_ut_cnt).rjust(8), "| delta:", curr_ut_cnt-prev_ut_cnt

        prev_uq_cnt = curr_uq_cnt
        curr_uq_cnt = cache.llen(user_q)
        print "Queued:".rjust(8), str(curr_uq_cnt).rjust(8), "| delta:", curr_uq_cnt-prev_uq_cnt
        prev_expected = curr_expected
        curr_expected = curr_us_cnt+curr_ut_cnt
        print "Current Expected Total:", curr_expected, "| delta:", curr_expected-prev_expected
        print "Last save:", cache.lastsave()
        print 
        sleep(30)
except KeyboardInterrupt:
    exit()
