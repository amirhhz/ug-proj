#!/usr/bin/env python


from mongomix import MixcloudDataset


class Similarity:
    def __init__(self, dataset):
        if isinstance(dataset, MixcloudDataset):
            self.ds = dataset
    
    def social_similarity(self, user1, user2):
        return self.intersection_size(user1, user2)
    
    def intersection_size(self, user1, user2):
        user1 = self.ds.get_user(user1)
        user2 = self.ds.get_user(user2)
    
        if (not user1) or (not user2):
            return 0.0
        user1_net, user2_net = set(), set()
        user1_net.update(user1.neighbours())
        user2_net.update(user2.neighbours())

        return (len(user1_net & user2_net))
        
    
    def mod_jaccard(self, user1, user2):
        user1 = self.ds.get_user(user1)
        user2 = self.ds.get_user(user2)

        if (not user1) or (not user2):
            return 0.0

        user1_net, user2_net = set(), set()
        user1_net.update(user1.neighbours())
        user2_net.update(user2.neighbours())
        
        # Distance is equal to the number of common friends (intersection) 
        # divided by the maximum number of common friends (min of sizes)
        sim = float((len(user1_net & user2_net))) / (min(len(user1_net),
                                                         len(user2_net))+1)
        
        return sim