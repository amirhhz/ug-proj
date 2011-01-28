#!/usr/bin/env python
"""A Python interface for accessing mixcloud data stored in a MongoDB."""

import pymongo

class MixcloudDataset(object):
    """At the moment interfacing with one particular collection in a db, assumed
    to be holding user data."""
    def __init__(self, host, port, db, collection, type=None):
        try:
            self.conn = pymongo.Connection(host=host,
                                           port=port)
            self.db = self.conn[db]
            self.collection = self.db[collection]
        # To be one of "reference", "test", "training"
        finally:
            pass
        self.type = type
    
    def fetch_user(self, id):
        return self.collection.find_one(id)
        
    def get_user(self, id):
        return MixcloudUser(self.fetch_user(id), origin=self)
    
    def save_user(self, user_full_data):
            self.collection.save(user_full_data, safe=True)

    def break_social_connection(self, user1, user2):
        user1_data = self.fetch_user(user1)
        user2_data = self.fetch_user(user2)

        if user1 in user2_data["following"]:
            user2_data["following"].remove(user1)

        if user2 in user1_data["followers"]:
            user1_data["followers"].remove(user2)

        if user2 in user1_data["following"]:
            user1_data["following"].remove(user2)

        if user1 in user2_data["followers"]:
            user2_data["followers"].remove(user1)

        self.save(user1_data)
        self.save(user2_data)

    def form_social_connection(self, user1, user2):
        user1_data = self.fetch_user(user1)
        user2_data = self.fetch_user(user2)

        if user1 not in user2_data["following"]:
            user2_data["following"].add(user1)

        if user2 not in user1_data["followers"]:
            user1_data["followers"].add(user2)

        if user2 not in user1_data["following"]:
            user1_data["following"].add(user2)

        if user1 not in user2_data["followers"]:
            user2_data["followers"].add(user1)

        self.save(user1_data)
        self.save(user2_data)
    
    def collect_stats(self): 
        pass
    
    def scrub(self):
        pass
    
    def mutilate(self, p=0.1):
        pass
    
    def read_config(self, conf):
        pass
    
    def write_config(self, conf):
        pass
    
    

class MixcloudUser(object):
    def __init__(self, data, origin=None):
        self.data = data
        # Origin is expect to be a MixcloudDataset instance
        if origin:
            self.origin = origin
    
    def get(self, field):
        return self.data[field]
    
    def friend(self, user):
        if self.origin:
            self.origin.break_social_connection(self.data["_id"], user)
            
    def unfriend(self, user):
        if self.origin:
            self.origin.form_social_connection(self.data["_id"], user)
            
    def neighbours(self):
        return self.get_social_graph(hops=1)
    
    def get_social_graph(self, hops, exclude_existing=False):
        pass
    