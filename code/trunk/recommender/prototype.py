#!/usr/bin/env python

"""A simple recommender engine."""

import pymongo
import random
from operator import itemgetter

class RecommenderException(Exception):
    def __init__(self, *args):
        Exception.__init__(self, args)

class Recommender:
    """"""
    def __init__(self, mongo_collection):
        if isinstance(mongo_collection, pymongo.collection.Collection):
            self.coll = mongo_collection
        else:
            raise RecommenderException("Invalid MongoDB collection.") 
        self.sampler = Sampler(self.coll, 2)
        self.similarity = Similarity(self.coll)

    def recommend_social(self, user):
        network = self.sampler.get_social_network(user)
        recs = {}
        for each in network:
            recs[each] = self.similarity.social_similarity(user, each)
        
        # See PEP-265 - return top similar users
        return sorted(recs.iteritems(), key=itemgetter(1), reverse=True)[:10]
    
    def recommend_content(self, user):
        pass
    

class Sampler:
    def __init__(self, mongo_collection, hops):
        self.hops = hops
        self.coll = mongo_collection
        
    def deep_sample(self, dest_coll, username):
        """Sample from the main collection to another collection, but only the 
        graph surrounding the user given."""
        if isinstance(dest_coll, pymongo.collection.Collection):
            self.sampled_coll = dest_coll
        else:
            raise RecommenderException()

        user = self.coll.find_one(username)
        if not user:
            raise RecommenderException()
        
        connected = user["following"] + user["followers"]
        print "Social graph size of", username,":", len(connected)
        social_set = set()
        social_set.update(connected)

        self.sampled_coll.save(user)
        done_set = set()
        done_set.add(username)

        for hop in xrange(0, self.hops):
            working_set = set()
            for each in social_set:
                if each not in done_set:
                    temp_user = self.coll.find_one(each)
                    if hop != self.hops-1:                    
                        working_set.update(temp_user["following"],
                                           temp_user["followers"])
                    self.sampled_coll.save(temp_user)
                    print "Copied", temp_user["_id"], "to sample."
                    done_set.add(each)
                    
            social_set.update(working_set)
            print "Anticipated sample size:", len(social_set)
            print "Current sample size:", len(done_set)
            print "HOP", hop, "DONE..."    
        
        return self.sampled_coll
    
    def mutilate_sample(self, p=0.1):
        pass
        
    def break_social_connections(self, coll, user1, user2):
        user1_data = coll.find_one(user1)
        user2_data = coll.find_one(user2)
        if user1 in user2_data["following"]:
            user2_data["following"].remove(user1)

        if user2 in user1_data["followers"]:
            user1_data["followers"].remove(user2)

        print user2, "no longer a follower of", user1

        if user2 in user1_data["following"]:
            user1_data["following"].remove(user2)

        if user1 in user2_data["followers"]:
            user2_data["followers"].remove(user1)

        print user1, "no longer a follower of", user2

        
        coll.save(user1_data)
        coll.save(user2_data)
            
    
    def get_social_network(self, username, exclude_existing=True):
        user = self.coll.find_one({"_id": username},
                                  fields=["following", "followers"])
        if not user:
            raise RecommenderException()
        connected = user["following"] + user["followers"]
        social_set = set()
        social_set.update(connected)
        
        # This is used in the loop below to avoid processing users more than once
        done_set = set()
        for hop in xrange(0, self.hops):
            working_set = set()
            for each in social_set:
                if each not in done_set:
                    temp_user = self.coll.find_one({"_id": each},
                                                   fields=["following", 
                                                           "followers"])
                    if not temp_user:
                        continue
                    working_set.update(temp_user["following"],
                                       temp_user["followers"])
                    done_set.add(each)
            social_set.update(working_set)
            
            if exclude_existing:
                # Remove people who are already connected to the user
                for c in connected:
                    social_set.discard(c)
                social_set.discard(username)

        return social_set
        
    def get_interaction_network(self, username):
        user = self.coll.find_one(spec={"_id": username},
                                  fields=["following", "followers",
                                          "favorites", "listens"])
        if not user:
            raise RecommenderException()
    
    def set_hop_value(self, hops):
        self.hops = hops
    
    
class Similarity:
    def __init__(self, mongo_collection):
        self.coll = mongo_collection
    
    def social_similarity(self, user1, user2):
        return self.intersection_size(user1, user2)
    
    def intersection_size(self, user1, user2):
        user1 = self.coll.find_one({"_id": user1},
                                   fields=["following", "followers"])
    
        user2 = self.coll.find_one({"_id": user2},
                                   fields=["following", "followers"])

        if (not user1) or (not user2):
            return 0.0
        user1_net, user2_net = set(), set()
        user1_net.update(user1["following"])#, user1["followers"])
        user2_net.update(user2["following"])#, user1["followers"])

        return (len(user1_net & user2_net))
        
    
    def mod_jaccard(self, user1, user2):
        user1 = self.coll.find_one({"_id": user1},
                                   fields=["following", "followers"])
    
        user2 = self.coll.find_one({"_id": user2},
                                   fields=["following", "followers"])

        if (not user1) or (not user2):
            return 0.0

        user1_net, user2_net = set(), set()
        user1_net.update(user1["following"])#, user1["followers"])
        user2_net.update(user2["following"])#, user2["followers"])
        
        # Distance is equal to the number of common friends (intersection) 
        # divided by the maximum number of common friends (min of sizes)
        sim = float((len(user1_net & user2_net))) / (min(len(user1_net),len(user2_net))+1)
        
        return sim