#!/usr/bin/env python
"""A Python interface for accessing mixcloud data stored in a MongoDB."""

import json
import pymongo
import random
from collections import defaultdict

REGISTRY_SIZE = 25
MUTILATE_RATIO = 0.05
SOC_SIM_COLLECTION = "soc_sim_cache"
HIDDEN_FOLLOWING = "_hidden_following_"
HIDDEN_FOLLOWERS = "_hidden_followers_"


class MongoMixException(Exception):
    def __init__(self, *args):
        Exception.__init__(self, args)


class MixcloudDataset(object):
    """At the moment interfacing with one particular collection in a db, assumed
    to be holding user data in the given collection."""
    def __init__(self, 
                 host="localhost", port=27017, 
                 db="mixcloud", collection="user"):
        try:
            self.conn = pymongo.Connection(host=host,
                                           port=port)
            self.db = self.conn[db]
            self.collection = self.db[collection]
        finally:
            pass
        # To be one of "reference", "test", "training"
        # self.type = type
        # Approxmiation of an LRU cache to keep track of recent MixcloudUser's
        self.cache = {}
        self.similarity = Similarity(self)
        
    def _register_user(self, mcuser):
        """Register a MixcloudUser object with the Dataset instance."""
        if not isinstance(mcuser, MixcloudUser):
            raise MongoMixException("User registration: not a MixcloudUser.")
        if len(self.cache) > REGISTRY_SIZE:
            ejected = random.choice(self.cache.keys())
            ejected = self.cache.pop(ejected)
        self.cache[mcuser["_id"]] = mcuser
            
    def _fetch_user(self, id):
        """Fetch the user with the given id from the Mongo collection."""
        data = self.collection.find_one(id)
        if not data:
            raise MongoMixException("_fetch_user: no such user found.", id)
        return data

    def _update_similarity_engine(self):
        pass
    
    def cache_list(self):
        return self.cache.keys()

    def get_user(self, id):
        """Returns a MixcloudUser instance containing the `id`'s data. Use cache
        (registry) if a recently accessed id, if not fetch and register it."""
        if id in self.cache:
            return self.cache[id]
        else:
            user_data = self._fetch_user(id)
            if not user_data:
                return None
            user = MixcloudUser(user_data, origin=self)
            self._register_user(user)
            return user

    def get_similarity(self, item1, item2):
        return self.similarity.social_similarity(item1, item2)
        
    def save_user(self, mcuser):
        """Write the contents of the MixcloudUser instance to the collection.
        Assumes a complete user document, so be careful!"""
        if not isinstance(mcuser, MixcloudUser):
            raise MongoMixException("Could not save_user: not a MixcloudUser.")
        self.collection.save(mcuser, safe=True)
    
    def hide(self, ratio=MUTILATE_RATIO):
        """Remove `ratio` proportion of outgoing links ("following") for all 
        users. Users with "small enough" outlinks won't be affected."""         
        # Any users with count values below this threshold won't be affected by
        # the mutilation, so we can avoid processing them.
        count_threshold = int(1/ratio)         
        # Find all users eligible for mutilation
        eligible = self.collection.find(spec={"following_count": 
                                              {"$gt": count_threshold}},
                                        fields=["_id"],
                                        timeout=False)        
        obituaries = {}
        victim_list = []
        for each in eligible:
            victim_list.append(each["_id"])

        while victim_list:
            print "INFO:hide:todo:", len(victim_list)
            victim = self.get_user(random.choice(victim_list))
            obituaries.update({
                               victim["_id"]: victim.hide_random_follows(ratio)
                               })
            victim_list.remove(victim["_id"])
            print victim["_id"]         
        return obituaries        

    def repair(self, reference):
        pass

    def stats(self): 
        pass
    
    def scrub(self):
        pass
    
    def sanity(self):
        pass

class MixcloudUser(dict):
    def __init__(self, data, origin):
        dict.__init__(self)
        self.update(data)
        if not isinstance(origin, MixcloudDataset):
            raise MongoMixException("MixcloudUser init'ed with invalid origin.")
        # Origin is expect to be a MixcloudDataset instance
        self.origin = origin

    def __getattribute__(self, name):
        """Try to get attribute as normal, then try dictionary lookup."""
        try:
            return dict.__getattribute__(self, name)
        except AttributeError:
            try:
                return self[name]
            except KeyError:
                raise AttributeError()
        
    def save(self):
        self.origin.save_user(self)
   
    def follow(self, user):
        target = self.origin.get_user(user)
        if target["_id"] not in self["following"]:
            self["following"].append(target["_id"])
            self["following_count"] += 1
            self.save()
        if self["_id"] not in target["followers"]:
            target["followers"].append(self["_id"])
            target["follower_count"] += 1
            target.save()
        # Return the user just followed for further manipulation, if any
        return target

    def unfollow(self, user):
        target = self.origin.get_user(user)
        if target["_id"] in self["following"]:
            self["following"].remove(target["_id"])
            self["following_count"] -= 1
            self.save()
        if self["_id"] in target["followers"]:
            target["followers"].remove(self["_id"])
            target["follower_count"] -= 1
            target.save()
        # Return the user just followed for further manipulation, if any
        return target
    
    def friend(self, user):
        """Create social links in both directions."""
        new_friend = self.follow(user)
        new_friend.follow(self["_id"])
            
    def unfriend(self, user):
        """Remove social links in both directions."""
        old_friend = self.unfollow(user)
        old_friend.unfollow(self["_id"])

#    def hide_follow(self, user):
#        target = self.origin.get_user(user)
#        if target["_id"] in self["following"]:
#            self["following"].remove(target["_id"])
#            self["following_count"] -= 1
#            if HIDDEN_FOLLOWING not in self.keys():
#                self[HIDDEN_FOLLOWING] = []
#            self[HIDDEN_FOLLOWING].append(target["_id"])    
#            self.save()
#        if self["_id"] in target["followers"]:
#            target["followers"].remove(self["_id"])
#            target["follower_count"] -= 1
#            if HIDDEN_FOLLOWERS not in target.keys():
#                target[HIDDEN_FOLLOWERS] = []
#            target[HIDDEN_FOLLOWERS].append(self["_id"])            
#            target.save()
#        # Return the user just followed for further manipulation, if any
#        return target

#    def unhide_follow(self, user):
#        target = self.origin.get_user(user)
#        if target["_id"] in self[HIDDEN_FOLLOWING]:
#            self[HIDDEN_FOLLOWING].remove(target["_id"])
#            self["following"].append(target["_id"])
#            self["following_count"] += 1
#            self.save()            
#        if self["_id"] in target[HIDDEN_FOLLOWERS]:
#            target[HIDDEN_FOLLOWERS].remove(self["_id"])
#            target["followers"].append(self["_id"])
#            target["follower_count"] += 1
#            target.save()            
#         Return the user just followed for further manipulation, if any
#        return target
#
#    def unhide_all_follows(self):
#        for each in self[HIDDEN_FOLLOWING]:
#            self.unhide_follow(each)
#        
#        ## For some reason the above sometimes doesn't do all the items so
#         recurse until empty - TO FIX
#        if self[HIDDEN_FOLLOWING]:
#            self.unhide_all_follows()

    def hide_random_follows(self, ratio):
        if ratio >= 1.0:
            raise MongoMixException("MixcloudUser: mutilation ratio must be "
                                    "less than 1.0.")        
        pop_size = len(self.following)
        sample_size = int(pop_size*ratio)
        # Take a random sample of the outlinks to be victims
        victim_links = random.sample(self.following, sample_size)
        if not victim_links:
            return None
        for each in victim_links:
            self.unfollow(each)
        return victim_links

    def friends(self):
        """Return the set followers who are also following."""
        return (set(self["followers"]) & set(self["following"]))

    def neighbours(self):
        """Return the set of all social links, followers or following."""
        return set(self["followers"] + self["following"])

    def get_similarity(self, other_user):
        return self.origin.get_similarity(self, other_user)
    
    def social_hop(self, hops):
        """Return dictionary of users in `hops` hops away in the network. 

The dictionary keys are integers from 0 upwards, and the values are sets of 
users reachable in as many hops."""
        network = defaultdict(set)
        network[0] = set((self._id,))   
        for h in xrange(0, hops):
            for each in network[h]:
                current_user = self.origin.get_user(each)
                network[h+1].update(set(current_user.following) - network[h])                
        return network                


class Similarity(object):
    def __init__(self, dataset):
        if isinstance(dataset, MixcloudDataset):
            self.ds = dataset        
        self.soc_sim_alg = self.intersection_size
        self._configure_cache()

    def _configure_cache(self):
        if  SOC_SIM_COLLECTION in self.ds.db.collection_names():
            self.ss_cache = self.ds.db[SOC_SIM_COLLECTION]
        else:
            self.ss_cache = self.ds.db.create_collection(
                                                         SOC_SIM_COLLECTION,
                                                         size=(100*1024*1024),
                                                         capped=True)
            print "INFO: User similarity cache created."
        
    def _change_soc_sim_alg(self, alg_func):
        self.soc_sim_alg = alg_func
        self._clear_cache()
        
    def _clear_cache(self):
        # drop cached values upon changing similarity metric 
        self.ss_cache.remove(None)
        
    def get_cached_soc_sim(self, userid1, userid2):
        found = None
        for id in [(userid1+"-"+userid2), (userid2+"-"+userid1)]:            
            found = self.ss_cache.find_one(id)
            if found: 
                return found["value"]
        # After checking both possible locations for the cached value ...            
        if not found:
            return None
    
    def set_cached_soc_sim(self, userid1, userid2, value):
        self.ss_cache.save({"_id": (userid1+"-"+userid2), "value": value})
        
    def social_similarity(self, user1, user2):
        if not isinstance(user1, MixcloudUser):
            user1 = self.ds.get_user(user1)
        if not isinstance(user2, MixcloudUser):
            user2 = self.ds.get_user(user2)
        
        cached_value = self.get_cached_soc_sim(user1._id, user2._id)
        if cached_value:
            return cached_value
        else:
            value = self.soc_sim_alg(user1, user2)
            if value:
                self.set_cached_soc_sim(user1._id, user2._id, value)
            return value
            
    def intersection_size(self, user1, user2):
        if (not user1) or (not user2):
            return 0.0
        if (not user1.following_count or not user2.following_count):
            return 0.0
        
        user1_net = set(user1.following)
        user2_net = set(user2.following)

        return (len(user1_net & user2_net))
        
    def jaccard(self, user1, user2):
        if (not user1) or (not user2):
            return 0.0
        user1_net = user1.neighbours()
        user2_net = user2.neighbours()        
        # Distance is equal to the number of common friends (intersection) 
        # divided by the maximum number of common friends (min of sizes)
        sim = float((len(user1_net & user2_net))) / (min(len(user1_net),
                                                         len(user2_net))+1)        
        return sim
    

class Evaluator(object):
    def __init__(self, rec, test_dataset, ref_dataset):
        pass
    
    