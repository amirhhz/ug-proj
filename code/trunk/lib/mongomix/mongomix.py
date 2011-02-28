#!/usr/bin/env python
"""A Python interface for accessing mixcloud data stored in a MongoDB."""

import json
import pymongo
import random
import math
from collections import defaultdict

CACHE_SIZE = 25
MUTILATE_RATIO = 0.05
SOC_SIM_COLLECTION = "soc_sim_cache"
HIDDEN_FOLLOWING = "_hidden_following_"
HIDDEN_FOLLOWERS = "_hidden_followers_"

_CONN_TYPES = ["cloudcast", "follower", "following", "favorite", "listen"]
CONNS = {}
for each in _CONN_TYPES:
    if each != "following":
        CONNS[each+"s"] = each+"_count"
    else:
        CONNS[each] = each+"_count"


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
        if len(self.cache) > CACHE_SIZE:
            ejected = random.choice(self.cache.keys())
            ejected = self.cache.pop(ejected)
        self.cache[mcuser["_id"]] = mcuser
            
    def _fetch_user(self, id):
        """Fetch the user with the given id from the Mongo collection."""
        data = self.collection.find_one(id)
        if not data:
            raise MongoMixException("_fetch_user: no such user found.", id)
        return data

    def get_user(self, id, fresh=False):
        """Returns a MixcloudUser instance containing the `id`'s data. Use cache
        (registry) if a recently accessed id, if not fetch and register it."""
        if not fresh:
            if id in self.cache:
                return self.cache[id]
        user_data = self._fetch_user(id)
        if not user_data:
            return None
        user = MixcloudUser(user_data, origin=self)
        self._register_user(user)
        return user
            
    def save_user(self, mcuser):
        """Write the contents of the MixcloudUser instance to the collection.
        Assumes a complete user document, so be careful!"""
        if not isinstance(mcuser, MixcloudUser):
            raise MongoMixException("Could not save_user: not a MixcloudUser.")
        self.collection.save(mcuser, safe=True)    

    def _add_follow(self, from_user, to_user):
        # Assumption: follow lists for both users are clean and consistent,
        # hence no checking as to whether they already contain the thing before
        # incrementing
        
        # update from_user's following data
        self.collection.update(
            spec={
                "_id": from_user
                },
            document={
                "$addToSet": {"following": to_user},
                "$inc": {"following_count": 1}
                },
            upsert=False,
            safe=True
            )
        # update to_user's follower data
        self.collection.update(
            spec={
                "_id": to_user
                },
            document={
                "$addToSet": {"followers": from_user},
                "$inc": {"follower_count": 1}
                },
            upsert=False,
            safe=True
            )

    def _remove_follow(self, from_user, to_user):
        # update from_user's following data
        self.collection.update(
            spec={
                "_id": from_user,
                "following": to_user                
                },
            document={
                "$pull": {"following": to_user},
                "$inc": {"following_count": -1}
                },
            upsert=False,
            safe=True
            )
        # update to_user's follower data
        self.collection.update(
            spec={
                "_id": to_user,
                "followers": from_user
                },
            document={
                "$pull": {"followers": from_user},
                "$inc": {"follower_count": -1}
                },
            upsert=False,
            safe=True
            )

    def _get_user_follows(self, user):
        if user in self.cache:
            return self.cache[user]["following"]
        try:
            return self.collection.find_one(
                user,
                fields=["following"]                
                )["following"]
        except TypeError:
            return None
    
    def _get_user_followers(self, user):
        if user in self.cache:
            return self.cache[user]["followers"]
        try:
            return self.collection.find_one(
                user,
                fields=["followers"]                
                )["followers"]
        except TypeError:
            return None

    def _get_user_friends(self, user):
        friends = set()
        try:
            friends.update(self._get_user_follows(user))
            friends.intersection_update(self._get_user_followers(user))
        except TypeError:
            friends = set()
        finally:
            return friends

    def _get_social_neighbours(self, user):
        neighbours = set()
        try:
            neighbours.update(self._get_user_follows(user))
            neighbours.update(self._get_user_followers(user))
        except TypeError:
            neighbours = set()
        finally:
            return neighbours

    def _add_user_favorite(self, user, fave_user, cloudcast_slug):
        pass
    
    def _remove_user_favorite(self, user, fave_user, cloudcast_slug):
        pass

    def _get_favorited_users(self, user):
        favorites = self.collection.find_one(
            user,
            fields=["favorites"]                
            )["favorites"]
        return set([f["user"] for f in favorites])

    def _get_listened_users(self, user):
        listens = self.collection.find_one(
            user,
            fields=["listens"]                
            )["listens"]
        return set([l["user"] for l in listens])
    
    def _get_content_neighbours(self, user, include_listens=False):
        neighbours = self._get_favorited_users(user)
        if include_listens:
            neighbours.update(self._get_listened_users(user))
        return neighbours
    
    def cache_list(self):
        return self.cache.keys()

    def is_follower(self, followee, follower):
        query = self.coll.find(
            spec={"_id":followee, "followers": follower},
            fields=[]            
            )
        
        if query.count() == 1:
            return True
        else:
            return False

    def get_social_similarity(self, item1, item2):
        return self.similarity.social_similarity(item1, item2)
    
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
            victim = self.get_user(random.choice(victim_list))
            obituaries.update({
                               victim["_id"]: victim.hide_random_follows(ratio)
                               })
            victim_list.remove(victim["_id"])
            print "INFO:hide:done:", victim["_id"]," :todo:", len(victim_list)         
        return obituaries        
    
    def _correct_count(self, username, features):
        """Correct any incorrect counts for the features given in the document
for the given user."""
        for f in features:
            if f not in CONNS:
                raise MongoMixException(
                    "Feature/connection given is not valid.", f
                    )
        fields = list(features)
        fields += [CONNS[feature] for feature in fields]

        user = self.collection.find_one(
            spec_or_id=username, 
            fields=fields
            )
        
        update_doc = {}
        for feature in features:
            if (len(user[feature]) != user[CONNS[feature]]):
                update_doc[CONNS[feature]] = len(user[feature])

        self.collection.update(
            spec={"_id": user["_id"]},
            document={
                "$set": update_doc
                }
            )        

    def correct_feature_counts(self, username):
        self._correct_count(username, CONNS.keys())
        print "INFO:scrub:corrected feature counts for", username

################################################################################
## IMPORTANT: ALL ASYMMETRY FUNCTIONS ASSUME THAT COUNTS HAVE BEEN CORRECTED!
################################################################################
        
    def _find_asymmetric_following(self, user):    
        result = []
        if not isinstance(user, dict):
            user = self.collection.find_one(
                spec={"_id": user}, 
                fields=["following", "following_count"]
                )
        
        for person in user["following"]:
            followee = self.collection.find(
                spec={"_id": person, "followers": user["_id"]},
                fields=[]
                )
            if not (followee.count() == 1):
                result.append(person)
        return result        
        
    def _find_asymmetric_followers(self, user):    
        result = []
        if not isinstance(user, dict):
            user = self.collection.find_one(
                spec={"_id": user}, 
                fields=["followers", "followers_count"]
                )

        for person in user["followers"]:
            follower = self.collection.find(
                spec={"_id": person, "following": user["_id"]},
                fields=[]
                )
            if not (follower.count() == 1):
                result.append(person)
        return result
    
    def _find_missing_cloudcasts(self, user):
        """Return a list of cloudcasts that the user's data refers to, in either
the favorites or listens field, which don't exist in the dataset."""
        result = []
        if not isinstance(user, dict):        
            user = self.collection.find_one(
                spec={"_id": user}, 
                fields=["listens", "listen_count", 
                        "favorites", "favorite_count"]
                )
        cc_list = user["listens"]
        # Only add favorites if they weren't in the listens list
        for f in user["favorites"]:
            if f not in cc_list:
                cc_list.append(f)
        
        for cc in cc_list:
            match = self.collection.find(
                spec={"_id": cc["user"], 
                      "cloudcasts.slug": cc["cloudcast_slug"]}
                )
            if not (match.count() == 1):
                result.append(cc)
        return result

    def fix_social_asymmetry(self, user):
        if not isinstance(user, dict):
            user = self.collection.find_one(
                spec={"_id": user}, 
                fields=["following", "following_count" 
                        "followers", "follower_count"]
                )
        asym_following = self._find_asymmetric_following(user)
        asym_followers = self._find_asymmetric_followers(user)
        
        for dud in asym_following:
            self.collection.update(
                spec={
                    "_id": user["_id"],
                    "following": dud                
                    },
                document={
                    "$pull": {"following": dud},
                    ## REMEMBER ASSUMING COUNTS ARE CORRECT
                    "$inc": {"following_count": -1}
                    },
                upsert=False,
                safe=True
                )

        for dud in asym_followers:
            self.collection.update(
                spec={
                    "_id": user["_id"],
                    "followers": dud                
                    },
                document={
                    "$pull": {"followers": dud},
                    ## REMEMBER ASSUMING COUNTS ARE CORRECT
                    "$inc": {"follower_count": -1}
                    },
                upsert=False,
                safe=True
                )
            
        print "INFO:scrub:Fixed social asymmetry for", user["_id"]
            
    def fix_content_asymmetry(self, user):
        if not isinstance(user, dict):
            user = self.collection.find_one(
                spec={"_id": user}, 
                fields=["listens", "listen_count", 
                        "favorites", "favorite_count"]
                )        
        missing = self._find_missing_cloudcasts(user)

        if missing:
            for dud in missing:
                if dud in user["listens"]:
                    user["listens"].remove(dud)
                if dud in user["favorites"]:
                    user["favorites"].remove(dud)
            user["listen_count"] = len(user["listens"])
            user["favorite_count"] = len(user["favorites"])
    
            self.collection.update(
                spec={"_id": user["_id"]},
                document={
                    "$set": {
                        "listens": user["listens"],
                        "listen_count": user["listen_count"],
                        "favorites": user["favorites"],
                        "favorite_count": user["favorite_count"]
                        } 
                    },
                safe=True)

        print "INFO:scrub:Fixed content asymmetry for", user["_id"]
            
    def fix_asymmetry(self, user):
        self.fix_social_asymmetry(user)
        self.fix_content_asymmetry(user)                

        
    def scrub(self, feature_counts=False, asymmetry=False):
        """Scrub the dataset as indicated by the given arguments.
        
IMPORTANT: the asymmetry fixes assume that feature counts are correct."""
        if feature_counts:
            cursor = self.collection.find(
                spec={"username": {"$exists": True} },
                fields=["_id"],
                timeout=False                
                )
            for each in cursor:
                self.correct_feature_counts(each["_id"])
        
        if asymmetry:
            cursor = self.collection.find(
                spec={
                    "$or": [
                        {"following_count": {"$gt": 0}},
                        {"follower_count": {"$gt": 0}},
                        {"listen_count": {"$gt": 0}},
                        {"favorite_count": {"$gt": 0}},
                        ]
                },
                fields=[
                    "_id", 
                    "following_count", "follower_count",
                    "following", "followers",
                    "favorite_count", "listen_count",
                    "favorites", "listens"
                    ],
                timeout=False
                )
            for each in cursor:
                self.fix_asymmetry(each)
        
    def sanity(self):
        pass

    def repair(self, reference):
        pass

    def census(self, aggregate=False, format="csv"):
        ###TODO: aggregate
        import csv
        
        file_name = "mmstat-{0}-{1}.csv".format(self.conn.host, self.conn.port)

        print "INFO:stats:writing stats to {0}...".format(file_name)
        
        with open(file_name,"w") as statfile:
            csv_out = csv.writer(statfile)
            users = self.collection.find(
                spec={"username": {"$exists": True} }, 
                fields=CONNS.values(),
                timeout=False)
        
            # Write CSV header
            csv_out.writerow(["username"] + CONNS.values())    
            for each in users:
                row = [each["_id"]]
                for field in CONNS:
                    row.append(each[CONNS[field]])
                csv_out.writerow(row)          


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

    def refresh(self):
        self.update(self.origin._fetch_user(self["_id"]))
        
    def save(self):
        self.origin.save_user(self)

################################################################################
## METHODS TO DO WITH SOCIAL
################################################################################            
   
    def follow(self, target):
        if target not in self["following"]:
            self.origin._add_follow(self["_id"], target)
            self["following"].append(target)
            self["following_count"] += 1
            return True

    def unfollow(self, target):
        if target in self["following"]:
            self.origin._remove_follow(self["_id"], target)
            self["following"].remove(target)
            self["following_count"] -= 1
            return True
    
    def friend(self, user):
        """Create social links in both directions."""
        if user not in self["following"]: 
            self.follow(user)
        if user not in self["followers"]: 
            self.origin._add_follow(user, self["_id"])
            self["followers"].append(user)
            self["follower_count"] += 1
            
    def unfriend(self, user):
        """Remove social links in both directions."""
        if user in self["following"]: 
            self.unfollow(user)
        if user in self["followers"]: 
            self.origin._remove_follow(user, self["_id"])
            self["followers"].remove(user)
            self["follower_count"] -= 1

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

    def social_neighbours(self):
        """Return the set of all social links, followers or following."""
        return set(self["followers"] + self["following"])

    #### DO NOT USE THIS METHOD, NEEDS FIXING/MIGHT BE USELESS ANYWAY    
    def social_hop_out(self, hops):
        """Return dictionary of users in `hops` hops away in the network. 

The dictionary keys are integers from 0 upwards, and the values are sets of 
users reachable in as many hops on "following" (outwards) edges."""
        network = defaultdict(set)
        network[0] = set((self._id,))   
        for h in xrange(0, hops):
            # The first for-loop is to avoid including users reachable earlier
            # in the later hops 
            already_in = set()
            for i in xrange(0, h):
                already_in.update(network[i])                
            for each in network[h]:
                each_follows = set(self.origin._get_user_follows(each))
                network[h+1].update(each_follows - already_in)                
        return network      

    def fofs(self, strictness=1):
        """Return the users friends of friends, only on outward links (default).

Strictness: 0 - friends only, 1 - following, 2 - all neighbours, 3 - followers.
        """ 
        friends = None
        if strictness == 0:
            friends = self.friends()
        elif strictness == 1:
            friends = set(self.following)
        elif strictness == 2:
            friends = self.social_neighbours()
        elif strictness == 3:
            friends = set(self.followers) 

        fof_list = set()
        if friends:
            for each in friends:
                if strictness == 0:
                    fof_list.update(self.origin._get_user_friends(each))
                elif strictness == 1:
                    fof_list.update(self.origin._get_user_follows(each))
                elif strictness == 2:
                    fof_list.update(self.origin._get_social_neighbours(each))
                elif strictness == 3:
                    fof_list.update(self.origin._get_user_followers(each))            
        return (fof_list - friends)

################################################################################
## METHODS TO DO WITH CONTENT
################################################################################            

    def favorite(self, user, cloudcast_slug):
        pass
    
    def unfavorite(self, user, cloudcast_slug):
        pass

    def favorited_users(self):
        return set([f["user"] for f in self["favorites"]])

    def listened_users(self):
        return set([f["user"] for f in self["listens"]])

    def content_neighbours(self, include_listens=False):
        neighbours = self.favorited_users()
        if include_listens:
            neighbours.update(self.listened_users())
        return neighbours
        
    def content_fofs(self, include_listens=False):
        neighbours = self.content_neighbours(include_listens)
        
        content_fofs = set()
        for each in neighbours:
            content_fofs.update(
                self.origin._get_content_neighbours(
                    each, include_listens=False))
        return (content_fofs - neighbours)

    def get_social_similarity(self, other_user):
        return self.origin.get_social_similarity(self["_id"], other_user)          

    def correct_counts(self):
        self.origin.correct_feature_counts(self["_id"])        
        self.refresh()

    def fix_asymmetry(self):
        self.origin.fix_asymmetry(self)
        self.refresh()
        

class Similarity(object):
    def __init__(self, dataset):
        if isinstance(dataset, MixcloudDataset):
            self.ds = dataset        
        self.soc_sim_alg = self.jaccard_custom
        self._configure_cache()

    def _configure_cache(self):
        pass

    def _clear_cache(self):
        pass
    
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

    def _change_soc_sim_alg(self, alg_func):
        self.soc_sim_alg = alg_func
        self._clear_cache()
        
    def social_similarity(self, user1, user2):
        return self.soc_sim_alg(user1, user2)

################################################################################
## SIMILARITY MEASURES
################################################################################
            
    def intersection_size(self, user1, user2):
        if (not user1) or (not user2):
            return 0.0
        f1 = set(self.ds._get_user_follows(user1))
        if not f1:
            return 0.0
        f2 = set(self.ds._get_user_follows(user2))
        if not f2:
            return 0.0
        return (len(f1 & f2))

    def jaccard(self, user1, user2):
        if (not user1) or (not user2):
            return 0.0
        f1 = set(self.ds._get_user_follows(user1))
        if not f1:
            return 0.0
        f2 = set(self.ds._get_user_follows(user2))
        if not f2:
            return 0.0
        # Distance is equal to the number of common friends (intersection) 
        # divided by the maximum number of common friends (min of sizes)
        sim = (
            len(f1 & f2) / 
            float(len(f1 | f2))
            )
        return sim
        
    def jaccard_custom(self, user1, user2):
        if (not user1) or (not user2):
            return 0.0
        f1 = set(self.ds._get_user_follows(user1))
        if not f1:
            return 0.0
        f2 = set(self.ds._get_user_follows(user2))
        if not f2:
            return 0.0
        # Distance is equal to the number of common friends (intersection) 
        # divided by the maximum number of common friends (min of sizes)
        sim = (
            len(f1 & f2) / 
            float(min(len(f1), len(f2))+1)
                )
        return sim

    def adamic_adar(self, user1, user2):
        if (not user1) or (not user2):
            return 0.0
        f1 = set(self.ds._get_user_follows(user1))
        if not f1:
            return 0.0
        f2 = set(self.ds._get_user_follows(user2))
        if not f2:
            return 0.0        

        common = f1 & f2
        ad_ad_value = 0.0
        for each in common:
            fo_count = self.ds.collection.find_one(
                spec_or_id=each,
                fields=["following_count"])["following_count"]
            if fo_count > 1:
                try:
                    ad_ad_value += 1.0/(math.log(fo_count))
                except ValueError:
                    continue
        return ad_ad_value
    
    def pref_attachment(self, user1, user2):
        f1_count = self.ds.collection.find_one(
            spec_or_id=user1,
            fields=["following_count"])["following_count"]
        f2_count = self.ds.collection.find_one(
            spec_or_id=user2,
            fields=["following_count"])["following_count"]
        return f1_count * f2_count

