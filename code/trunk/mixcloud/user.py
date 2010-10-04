#!/usr/bin/env python

import api

class MCUser():
    def __init__(self,username):
        self.user_data = api.getFromAPI(api.getResourceURL(username))
        self.id = self.user_data["username"]
        # for MongoDB's benefit, set _id field to username, which is unique
        self.user_data["_id"] = self.id        
        self.meta_conns = dict()
        # for all metadata connections in API data, turn the url into a MetaConnection object
        for conn in self.user_data["metadata"]["connections"].keys():
            self.meta_conns[conn] = api.MetaConnection(self.user_data["metadata"]["connections"][conn])

    def getUserID(self):
        return self.id

    def getUserData(self):
        return self.user_data
    
    def getConnection(self, conn_type):
        try:
            return self.meta_conns[conn_type]
        except KeyError:
            return

    def getFollowers(self):
        """Return a list of the followers of the user given."""
        followers = self._getSocialList("followers")
        return followers

    def getFollowing(self):
        """Return a list of the users being followed the user given."""
        following = self._getSocialList("following")
        return following

    def getCommentors(self):
        """Return a list of users who have commented on the user's profile."""
        commentors = self._getInteractionList("comments")
        return commentors

    def getListenedTo(self):
        """Return a list of users whose cloudcasts the user has listened to."""
        listened_to = self._getInteractionList("listens")
        return listened_to

    def getFavUsers(self):
        """Return a list of users whose cloudcasts the user has favourited."""
        fav_users = self._getInteractionList("favorites")
        return fav_users

    def _getSocialList(self, conn_type):
        """Private method to get the follower/following usernames connected to the user"""
        conn = self.getConnection(conn_type)
        soc_list = []
        try:        
            while (conn.HasNext()):
                api_op = conn.getNextPage()
                soc_list += [user["username"] for user in api_op["data"]]
            return soc_list
        except KeyError:
            return soc_list
            
    def _getInteractionList(self, conn_type):
        """Private method to get the commentor/listened to/favorites usernames connected to the user"""
        conn = self.getConnection(conn_type)
        interact_list = []
        try:
            while (conn.HasNext()):
                api_op = conn.getNextPage()
                for item in api_op["data"]:
                    interact_list.append(item["user"]["username"])
            return interact_list
        except KeyError:
            return interact_list                 

    def mongoSave(self, mongo_coll):
        mongo_coll.save(self.getUserData())

class UserSet(set):
    pass
        
