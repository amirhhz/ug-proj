#!/usr/bin/env python

import csv
import pymongo

from settings import MONGO_COLLECTION

default_coll = MONGO_COLLECTION

def fix_asymmetry(user_coll):
    cursor = user_coll.find(
                            spec={
                                  "$or": [
                                          {"following_count": {"$gt": 0}},
                                          {"follower_count": {"$gt": 0}},
                                          {"listen_count": {"$gt": 0}},
                                          {"favorite_count": {"$gt": 0}},
                                          ]
                                  },
                            fields=["_id", 
                                    "following_count", "follower_count",
                                    "following", "followers",
                                    "favorite_count", "listen_count",
                                    "favorites", "listens"],
                            timeout=False
                            )
    
    for each in cursor:
        fix_social_asymmetry(user_coll, each)
        fix_content_asymmetry(user_coll, each)
    
def save_social_asymmetry(user_coll, followers_file, following_file):

    # Initialise the CSV files to write data to
    fr = open(followers_file, "w")
    fg = open(following_file, "w")    
    fr_csv = csv.writer(fr)
    fr_csv.writerow(["user",
                     "missing_as_followee_count", 
                     "missing_as_followee_of"])
    fg_csv = csv.writer(fg)
    fg_csv.writerow(["user",
                    "missing_as_follower_count", 
                    "missing_as_follower_of"])
    
    # This MongoDB cursor limits the search to users with social connections
    cursor = user_coll.find(
                            spec={
                                  "$or": [
                                          {"following_count": {"$gt": 0}},
                                          {"follower_count": {"$gt": 0}},                                          
                                          ]
                                  },
                            fields=["_id", 
                                    "following_count", "follower_count",
                                    "following", "followers"],
                            timeout=False
                            )
    try:
        for user in cursor:        
            if user["follower_count"] > 0:
                fr_result = find_asym_followers(user_coll, user)
                if fr_result:
                    fr_csv.writerow([user["_id"], 
                                     len(fr_result), 
                                     fr_result])            
            if user["following_count"] > 0:
                fg_result = find_asym_following(user_coll, user)
                if fg_result:
                    fg_csv.writerow([user["_id"], 
                                     len(fg_result), 
                                     fg_result])            
    finally:
        fr.close()
        fg.close()

def save_content_asymmetry(user_coll, cc_file):
    cc = open(cc_file, "w")    
    cc_csv = csv.writer(cc)
    cc_csv.writerow(["user",
                     "missing_cloudcasts_count", 
                     "missing_cloudcasts"])    
    cursor = user_coll.find(
                            spec={
                                  "$or": [
                                          {"favorite_count": {"$gt": 0}},
                                          {"listen_count": {"$gt": 0}},                                          
                                          ]
                                  },
                            fields=["_id", 
                                    "favorite_count", "listen_count",
                                    "favorites", "listens"],
                            timeout=False
                            )
    try:
        for user in cursor:        
            cc_result = find_missing_cloudcasts(user_coll, user)
            if cc_result:
                cc_csv.writerow([user["_id"], 
                                 len(cc_result), 
                                 [(i["user"] + "/" + i["cloudcast_slug"]) for i in cc_result]
                                 ])            
    finally:
        cc.close()

def fix_social_asymmetry(user_coll, user):
    # if the argument is not a user's data dict, get it
    if not (isinstance(user, dict) and
            user.has_key("_id") and
            user.has_key("following") and
            user.has_key("followers")):    
        user = user_coll.find_one(
                                  spec={"username": user},
                                  fields=["_id", 
                                        "following_count", "follower_count",
                                        "following", "followers"]
                                  )    

    # Fixing the followers list:
    asym_followers = find_asym_followers(user_coll, user)
    if asym_followers:
        for dud in asym_followers:
            user["followers"].remove(dud)
        user["follower_count"] = len(user["followers"])
        
        user_coll.update(
                         spec={"_id": user["_id"]},
                         document={"$set": {"followers": user["followers"]} },
                         safe=True                                
                         )
        user_coll.update(
                         spec={"_id": user["_id"]},
                         document={"$set": {"follower_count": user["follower_count"]} },
                         safe=True
                         )
        print "Successfully fixed FOLLOWER asymmetry for", user["_id"]
    
    # Fixing the followees list:
    asym_followees = find_asym_following(user_coll, user)
    if asym_followees:
        for dud in asym_followees:
            user["following"].remove(dud)
        user["following_count"] = len(user["following"])
    
        user_coll.update(
                         spec={"_id": user["_id"]},
                         document={"$set": {"following": user["following"]} },
                         safe=True
                         )
        user_coll.update(
                         spec={"_id": user["_id"]},
                         document={"$set": {"following_count": user["following_count"]} },
                         safe=True
                         )
        print "Successfully fixed FOLLOWING asymmetry for", user["_id"]

def fix_content_asymmetry(user_coll, user):
    # if the argument is not a user's data dict, get it
    if not (isinstance(user, dict) and
            user.has_key("_id") and
            user.has_key("listens") and
            user.has_key("favorites")):
        user = user_coll.find_one(
                                  spec={"username": user},
                                  fields=["_id", 
                                        "favorite_count", "listen_count",
                                        "favorites", "listens"]
                                  )

    missing_cc = find_missing_cloudcasts(user_coll, user)
    if missing_cc:
        for dud in missing_cc:
            if dud in user["listens"]:
                user["listens"].remove(dud)
            if dud in user["favorites"]:
                user["favorites"].remove(dud)
        user["listen_count"] = len(user["listens"])
        user["favorite_count"] = len(user["favorites"])
    
    if missing_cc: 
        user_coll.update(
                         spec={"_id": user["_id"]},
                         document={"$set": {"listens": user["listens"]} },
                         safe=True                                  
                         )
        user_coll.update(
                         spec={"_id": user["_id"]},
                         document={"$set": {"listen_count": user["listen_count"]} },
                         safe=True
                         )
        user_coll.update(
                         spec={"_id": user["_id"]},
                         document={"$set": {"favorites": user["favorites"]} },
                         safe=True                                 
                         )
        user_coll.update(
                         spec={"_id": user["_id"]},
                         document={"$set": {"favorite_count": user["favorite_count"]} },
                         safe=True
                         )
        print "Successfully fixed CLOUDCAST asymmetry for", user["_id"]
    
def find_asym_followers(user_coll, user):
    """Find  asymmetry in the list of the user's followers: there is asymmetry
    if for the list of followers, the corresponding entry in the followers' 
    following list is missing.""" 

    if not user["followers"]:
        # if user has an empty followers list, just return
        return
    
    
    # A dictionary with users as keys and the values being the list of their 
    # followers who don't have the key user in their following list 
    result = []
    
    followers = user["followers"]
    for person in followers:
        follower = user_coll.find(
                                  spec={"_id": person, "following": user["_id"]},
                                  fields=[]
                                  )
        if not (follower.count() == 1):
            result.append(person)
    return result

def find_asym_following(user_coll, user):
    """Find asymmetry in the list of the user's followees: there is asymmetry
    if for the list of followees, the corresponding entry in the followees' 
    follower list is missing.""" 

    if not user["following"]:
        # if user has an empty following list, just return
        return

    # A dictionary with users as keys and the values being the list of their 
    # followers who don't have the key user in their following list 
    result = []
    
    followees = user["following"]
    for person in followees:
        followee = user_coll.find(
                                  spec={"_id": person, "followers": user["_id"]},
                                  fields=[]
                                  )
        if not (followee.count() == 1):
            result.append(person)
    return result

def find_missing_cloudcasts(user_coll, user):
    """Takes a user data dict as input, return list of user-slug pairs of 
    missing cloudcasts."""

    if not (user["listens"] and user["favorites"]):
        # if user has empty interaction lists, just return
        return    
    result = []

    cc_list = user["listens"]
    #Only add favorites if they weren't in the listens list
    for f in user["favorites"]:
        if f not in cc_list:
            cc_list.append(f)
    
    for cc in cc_list:
        match = user_coll.find(
                               spec={"_id": cc["user"], 
                                     "cloudcasts.slug": cc["cloudcast_slug"]}
                               )
        if not (match.count() == 1):
            result.append(cc)
    return result


if __name__ == "__main__":
    save_social_asymmetry(default_coll, 
                          "followersa-post-fix.csv", "followinga-post-fix.csv")
    save_content_asymmetry(default_coll, "contenta-post-fix.csv")   
#    fix_asymmetry()          
        
        