#!/usr/bin/env python

"""A simple recommender engine."""

import pymongo
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
    
    def get_social_network(self, username):
        user = self.coll.find_one({"_id": username},
                                  fields=["following", "followers"])
        if not user:
            raise RecommenderException()
        
        social_set = set()
        social_set.update(user["following"],user["followers"])
        
        # This is used in the loop below to avoid processing users more than once
        done_set = set()
        for hop in xrange(0,self.hops-1):
            working_set = set()
            for each in social_set:
                if each not in done_set:
                    temp_user = self.coll.find_one({"_id": username},
                                                   fields=["following", 
                                                           "followers"])
                    working_set.update(temp_user["following"],
                                       temp_user["followers"])
                    done_set.add(each)
            social_set.update(working_set)
            
        return social_set
        
    def get_interaction_network(self, username):
        user = self.coll.find_one(spec={"_id": username},
                                  fields=["following", "followers",
                                          "favorites", "listens"])
        if not user:
            raise RecommenderException()
    
    def set_hop_value(self, hops):
        sefl.hops = hops
    
    
class Similarity:
    def __init__(self, mongo_collection):
        self.coll = mongo_collection
    
    def social_similarity(self, user1, user2):
        user1 = self.coll.find_one({"_id": user1},
                                   fields=["following", "followers"])
    
        user2 = self.coll.find_one({"_id": user2},
                                   fields=["following", "followers"])

        user1_net, user2_net = set(), set()
        user1_net.update(user1["following"], user1["followers"])
        user2_net.update(user2["following"], user2["followers"])
        
        # Distance is equal to the number of common friends (intersection) 
        # divided by the total number of friends (union) - Jaccard Index
        dist = float((len(user1_net & user2_net))) / (len(user1_net | user2_net))
        
        return dist