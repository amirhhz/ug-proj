#!/usr/bin/env python

from similarity import Similarity
from mongomix import MixcloudDataset
from operator import itemgetter

class RecommenderException(Exception):
    def __init__(self, *args):
        Exception.__init__(self, args)

class Recommender:
    """"""
    def __init__(self, dataset):
        if isinstance(dataset, MixcloudDataset):
            self.ds = dataset
        else:
            raise RecommenderException("Invalid Mixcloud Dataset.") 
        self.sampler = Sampler(self.ds, 2)
        self.similarity = Similarity(self.ds)

    def recommend_social(self, user):
        network = self.ds.get_user(user).get_social_graph(hops=2,
                                                          exclude_existing=True)
        recs = {}
        for each in network:
            recs[each] = self.similarity.social_similarity(user, each)
        
        # See PEP-265 - return top similar users
        return sorted(recs.iteritems(), key=itemgetter(1), reverse=True)[:10]
    
    def recommend_content(self, user):
        pass
    