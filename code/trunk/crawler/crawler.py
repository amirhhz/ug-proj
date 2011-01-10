#!/usr/bin/env python

from mixcloud.api import MixcloudAPI, MixcloudAPIException
from mixcloud.resources import User
from settings import MONGO_COLLECTION, CACHE, USER_QUEUE, USER_TODO, USER_SET
from settings import DEBUG


# Get the Mixcloud API
mcapi = MixcloudAPI()

# Get the reference to the collection in the database as specified in settings
crawl_store = MONGO_COLLECTION

# Connect to Redis cache
crawl_cache = CACHE


class UserCrawler:
    """Take a list of seed users, a storage object (MongoDB database) and a 
    cache object (Redis cache), ready to begin a breadth-first search, with the 
    search queue pre-populated with the seeds. It is assumed that all seed items
    are valid ones.
    !!! FIX: store and cache have to MongoDB or Redis, maybe fix this with some 
    refactoring - make it possible to plug in a pure Python cache, perhaps."""
    def __init__(self, seed_list, api, store, cache, 
                 todo_queue=USER_QUEUE,
                 todo_set=USER_TODO,
                 done_set=USER_SET):
        self.api = api
        self.store = store
        self.cache = cache
        #These are key values (strings) to use in the cache.
        self.todo_queue = todo_queue
        self.todo_set = todo_set
        self.done_set = done_set
        
        self.sync_cache_with_store()
        
        for each in seed_list:
            items_added = 0
            if self.add_to_todo(each):
                items_added += 1
        print items_added, "seed users were added to the to-do list."
        
    def __str__(self):
        done = self.cache.scard(self.done_set)
        todo = self.cache.scard(self.todo_set)
        return "Crawler - done: " + str(done) + ", todo: " + str(todo) 
    
    def start(self):
        while not self.is_todo_empty():
            parent = self.get_next_user()
            self.enqueue_user_connections(parent)
            self.store_user(parent)

    def get_next_user(self):
        next = self.pop_from_todo()
        try:
            next_user = User(self.api, next)
            next_user.populate()
        except MixcloudAPIException, mce:
            # This handles the case of a missing/renamed user, by just skipping
            # it and returning the next user 
            try:
                if mce.status == 404:
                    return self.get_next_user()
                else:
                    raise mce
            except AttributeError, ae:
                print "AttributeError: problem handling API Exception!"
                print ae.message, ae.args
                raise mce
        return next_user
    
    def enqueue_user_connections(self, user_obj):
        conn_list = user_obj.get_social_connections()
        for each in conn_list:
            self.add_to_todo(each)

    def store_user(self, user_obj):
        to_store = user_obj.get_user_id()
        try:
            if not DEBUG:
                self.store.save(user_obj.get_data(), safe=True)
        except Exception, error:
            print error
            print "Could not save " + to_store + ", re-queuing it."
            self.add_to_todo(to_store)
            raise error
        self.cache.sadd(self.done_set, to_store)
        print to_store

    def add_to_todo(self, item):
        """Only update the todo set and queue if item is not already in to-do 
        set."""
        if not self.cache.sismember(self.done_set, item):
            if not self.cache.sismember(self.todo_set, item):
                self.cache.sadd(self.todo_set, item)
                self.cache.rpush(self.todo_queue, item)
                return True
        return False
    
    def pop_from_todo(self):
        item = self.cache.lpop(self.todo_queue)
        self.cache.srem(self.todo_set, item)
        return item
    
    def is_todo_empty(self):
        if self.check_and_fix_internals():
            condition = (self.cache.scard(self.todo_set) == 0 and
                         self.cache.llen(self.todo_queue) == 0 )
            if condition:
                return True
        return False
    
    def check_and_fix_internals(self):
        """This method does a simple check to see if there is a one-to-one 
        mapping between the to-do structures."""
        #!!!FIX: check against DB, too!
        if self.cache.scard(self.todo_set) == self.cache.llen(self.todo_queue):
            return True
        else:
            ## !!!FIX: do some fixing!
            self.sync_cache_todo_structs()
            return True
        return False
        
    def sync_cache_with_store(self):
        cursor = self.store.find(spec={"username": {"$exists": True}},
                                 fields=["username"],
                                 timeout=False)
        stored_users = set([each["username"] for each in cursor])
        
        cached_done_users = self.cache.smembers(self.done_set)
        if stored_users != cached_done_users:
            # Some stored users are missing from the cache
            if stored_users > cached_done_users:
                for each in (stored_users - cached_done_users):
                    self.cache.sadd(self.done_set, each)
            # Unlikely case that there are items in the cache that aren't in the
            # store - we trust the store and see update the cache
            elif stored_users < cached_done_users:
                for each in (cached_done_users - stored_users):
                    self.cache.srem(self.done_set, each)
            # The very unlikely case that the sets overlap but not cover each 
            # other - again trust the store 
            else:
                self.cache.delete(self.done_set)
                for each in stored_users:
                    self.cache.sadd(self.done_set, each)
            
    
    def sync_cache_todo_structs(self):
        curr_queue = self.cache.lrange(self.todo_queue, 0, -1)
        curr_set = self.cache.smembers(self.todo_set)
        

if __name__ == "__main__":
    import sys
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-f", "--input-file", dest="input",
                      help="Text file from which to read seed items from. "
                      "The file is expected to contain an item id per line.")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      default=True)
    options, args = parser.parse_args()

    inlist = None
    try:
        with open(options.input, "r") as infile:
            inlist = infile.read()
            inlist = inlist.strip().splitlines()
    except IOError, io:
        print io
        print "Invalid filename."
        exit()

    try:
        crawler = UserCrawler(inlist, mcapi, crawl_store, crawl_cache)        
        crawler.start()
    except KeyboardInterrupt, k:
        print k
        print str(crawler)
        print "Bye!"
        exit()
    except Exception, error:
        print str(crawler)
        raise error
