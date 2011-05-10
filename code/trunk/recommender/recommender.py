#!/usr/bin/env python

from mongomix import MixcloudDataset
from operator import itemgetter
import logging

reclog = logging.getLogger(__name__)
reclog.setLevel(logging.DEBUG)
reclog.addHandler(logging.StreamHandler())

TOP_N = 50

class RecommenderException(Exception):
    def __init__(self, *args):
        Exception.__init__(self, args)


class Recommender(object):
    """
    """
    def __init__(self, dataset):
        if not isinstance(dataset, MixcloudDataset):
            raise RecommenderException("Rec init: Invalid Mixcloud Dataset.") 
        self.ds = dataset

    def recommend_social(self, userid):
        user = self.ds.get_user(userid)
        network = user.fofs()
        reclog.info("rec_soc:{0} friends of friends count: {1}".format(userid, len(network)))
        recs = {}
        for each in network:
            sim_value = user.get_social_similarity(each)
            if sim_value:
                recs[each] = sim_value        
        # See PEP-265 - return top similar users
        return sorted(recs.iteritems(), key=itemgetter(1), reverse=True)[:50]

    def change_soc_sim_alg(self, alg_name):
        self.ds.similarity._change_soc_sim_alg(alg_name)

    
class Evaluator(object):
    """
    TODO
    """
    def __init__(self, test_dataset, ref_dataset):
        if not isinstance(test_dataset, MixcloudDataset):
            raise RecommenderException("Evaluator init: Invalid Dataset.") 
        if not isinstance(ref_dataset, MixcloudDataset):
            raise RecommenderException("Evaluator init: Invalid Dataset.") 
        self.rec = Recommender(test_dataset)
        self.test = test_dataset
        self.ref = ref_dataset
        
    
    def evaluate(self, test_user_list):
        per_user_measures = {}
        for item in test_user_list:
            results = self.rec.recommend_social(item)                

            max_positives = (
                set(self.ref._get_user_follows(item)) - 
                set(self.test._get_user_follows(item)))

            true_positives = set()
            for name, value in results:
                if name in max_positives:
                    true_positives.add(name)

            precision = 0
            recall = 0 
            if max_positives and true_positives:
                precision = float(len(true_positives))/len(results)
                recall = float(len(true_positives))/len(max_positives)

            per_user_measures[item] = {
                "precision": precision,
                "recall": recall,
                }
            
        return per_user_measures
            
    
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
    
