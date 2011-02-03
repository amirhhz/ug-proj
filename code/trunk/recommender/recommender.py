#!/usr/bin/env python

from mongomix import MixcloudDataset
from operator import itemgetter

TOP_N = 10

class RecommenderException(Exception):
    def __init__(self, *args):
        Exception.__init__(self, args)

class Recommender(object):
    """"""
    def __init__(self, dataset):
        if isinstance(dataset, MixcloudDataset):
            self.ds = dataset
        else:
            raise RecommenderException("Rec init: Invalid Mixcloud Dataset.") 

    def recommend_social(self, userid):
        user = self.ds.get_user(userid)
        network = user.social_hop(hops=2)
        recs = {}
        print "INFO:RECOMMENDER: friends of friends count:", len(network[2])
        for each in network[2]:
            sim_value = user.get_similarity(each)
            if sim_value:
                recs[each] = sim_value
        
        # See PEP-265 - return top similar users
        return sorted(recs.iteritems(), key=itemgetter(1), reverse=True)[:TOP_N]
    
    def recommend_content(self, userid):
        pass
    
if __name__ == "__main__":
    import sys
    userid = sys.argv[1]
    ds = MixcloudDataset(host="nigela")
    rec = Recommender(ds)
    try:
        results = rec.recommend_social(userid)
    finally:
        pass
    for user, value in results:
        print user, ":", value
    
