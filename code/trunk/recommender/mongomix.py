#!/usr/bin/env python
"""A Python interface for accessing mixcloud data stored in a MongoDB."""

import pymongo

REGISTRY_SIZE = 10

class MongoMixException(Exception):
    def __init__(self, *args):
        Exception.__init__(self, args)


class MixcloudDataset(object):
    """At the moment interfacing with one particular collection in a db, assumed
    to be holding user data."""
    def __init__(self, host, port, db, collection, type=None):
        try:
            self.conn = pymongo.Connection(host=host,
                                           port=port)
            self.db = self.conn[db]
            self.collection = self.db[collection]
        finally:
            pass
        # To be one of "reference", "test", "training"
        self.type = type
        # Approxmiation of an LRU cache to keep track of recent MixcloudUser's
        self.cache = {}
        
    def _register_user(self, mcuser):
        """Register a MixcloudUser object with the Dataset instance."""
        if len(self.registry) > REGISTRY_SIZE:
            ejected = self.registry.popitem()
        self.registry[mcuser["_id"]] = mcuser
            
    def _fetch_user(self, id):
        """Fetch the user with the given id from the Mongo collection."""
        return self.collection.find_one(id)
        
    def get_user(self, id):
        """Returns a MixcloudUser instance containing the `id`'s data. Use cache
        (registry) if a recently accessed id, if not fetch and register it."""
        if id in self.registry:
            return self.registry[id]
        else:
            user = MixcloudUser(self._fetch_user(id), origin=self)
            self._register_user(user)
            return user
    
    def save_user(self, mcuser):
        """Write the contents of the MixcloudUser instance to the collection.
        Assumes a complete user document, so be careful!"""
        if not isintance(mcuser, MixcloudUser):
            return None
        self.collection.save(mcuser.data, safe=True)
    
    def mutilate(self, ratio=0.05):
        ### TODO
        cursor = self.collection.find(spec={"following_count": {"$gt": 0},
                                            "follower_count": {"$gt": 0}},
                                      fields=["_id"])
        
        victim_list = []
        for each in cursor:
            victim_list.append(each["_id"])

        
    def repair(self, reference):
        pass

    def collect_stats(self): 
        pass
    
    def scrub(self):
        pass
        

class MixcloudUser(object):
    def __init__(self, data, origin):
        self.data = data
        # Origin is expect to be a MixcloudDataset instance
        if not isinstance(origin, MixcloudDataset):
            raise MongoMixException("MixcloudUser init'ed with invalid origin.")
        self.origin = origin
        
    def save(self):
        if self.origin:
            self.origin.save_user(self)
    
    def get(self, field):
        return self.data[field]
    
    def follow(self, user):
        target = self.origin.get_user(user)
        if target["_id"] not in self.data["following"]:
            self.data["following"].append(target["_id"])
            self.data["following_count"] += 1
            self.save()
        if self.data["_id"] not in target["followers"]:
            target.data["followers"].append(self.data["_id"])
            target.data["follower_count"] += 1
            target.save()
        # Return the user just followed for further manipulation, if any
        return target

    def unfollow(self, user):
        target = self.origin.get_user(user)
        if target["_id"] in self.data["following"]:
            self.data["following"].remove(target["_id"])
            self.data["following_count"] -= 1
            self.save()
        if self.data["_id"] in target["followers"]:
            target.data["followers"].remove(self.data["_id"])
            target.data["follower_count"] -= 1
            target.save()
        # Return the user just followed for further manipulation, if any
        return target
    
    def friend(self, user):
        new_friend = self.follow(user)
        new_friend.follow(self["_id"])
            
    def unfriend(self, user):
        old_friend = self.unfollow(user)
        old_friend.unfollow(self["_id"])

    def neighbours(self):
        return self.data["followers"] + self.data["following"]
    