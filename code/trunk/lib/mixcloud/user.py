#!/usr/bin/env python

from httplib import HTTPException
from time import sleep

from api import MetaConnection
from api import MixcloudAPIException
from resource.base_resource_type import InteractiveResource
import resource.dynamic_resource_type as dyn_rsrc
from cloudcast import Cloudcast

class User(InteractiveResource):
    def __init__(self, username, api):
        InteractiveResource.__init__(self, username)
        self.api = api
        self.dyn_resources.update({
            "feed": dyn_rsrc.Feed(username),
            "followers": dyn_rsrc.Followers(username),
            "following": dyn_rsrc.Following(username),
            "cloudcasts": dyn_rsrc.Cloudcasts(username),
            "listens": dyn_rsrc.Listens(username)
        })
        try:
            self.user_data = self.api.getFromAPI(self.api.getResourceURL(username))
        except MixcloudAPIException as apie:
            print "Error during User() init: Mixcloud is blocking requests."
            self.api.connection.close()
            retry = apie.getRetry()
            print "Retrying after", retry ,"seconds ..."
            sleep(retry+1)
            self.api.connectToAPI()
            self.user_data = self.api.getFromAPI(self.api.getResourceURL(username))
        except HTTPException as he:
            print "Unknown HTTPException occurred during User() init."
            print he.args
            print "Retrying again in 5 seconds..."
            self.api.connection.close()
            sleep(5)
            print "Ping!"
            self.api.connectToAPI()            
            self.user_data = self.api.getFromAPI(self.api.getResourceURL(username))

        self.id = self.user_data["username"]
        # for MongoDB's benefit, set _id field to username, which is unique
        self.user_data["_id"] = self.id
        
        # initialise custom fields to avoid errors later
        self.user_data["feed"] = []
        self.user_data["followers"] = []
        self.user_data["following"] = []
        self.user_data["cloudcasts"] = []
        self.user_data["comments"] = []
        self.user_data["listens"] = []
        self.user_data["favorites"] = []

        self.meta_conns = dict()
        # for all dynamic resources, produce a MetaConnection object
        for resource in self.dyn_resources.keys():
            self.meta_conns[resource] = MetaConnection(
                api, 
                api.getBaseURL(*self.dyn_resources[resource].resource_key), 
                **self.dyn_resources[resource].resource_params
            )

    def saveAllConnections(self):
        if self.user_data["cloudcasts"] == []: self.saveCloudcasts()
        if self.user_data["followers"] == []: self.saveFollowers()
        if self.user_data["following"] == []: self.saveFollowing()
        if self.user_data["favorites"] == []: self.saveFavorites()
        if self.user_data["listens"] == []: self.saveListens()
        
        
    def getAllSocialConnections(self):
        self.saveAllConnections()
        sc = set()
        sc.update(
            self.user_data["followers"],
            self.user_data["following"],
            [item["user"] for item in self.user_data["favorites"]],
            [item["user"] for item in self.user_data["listens"]],
        )
        return sc

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

    def saveFollowers(self):
        followers = self.getFollowers()
        self.user_data["followers"] = followers

    def getFollowing(self):
        """Return a list of the users being followed the user given."""
        following = self._getSocialList("following")
        return following

    def saveFollowing(self):
        following = self.getFollowing()
        self.user_data["following"] = following

    def getListens(self):
        """Return the users and cloudcasts user has listened to."""
        listens = self._getInteractionList("listens")
        return listens
    
    def saveListens(self):
        listens = self.getListens()
        self.user_data["listens"] = listens
        
    def getFavorites(self):
        """Return a list of users whose cloudcasts the user has favourited."""
        faves = self._getInteractionList("favorites")
        return faves

    def saveFavorites(self):
        faves = self.getFavorites()
        self.user_data["favorites"] = faves
    
    def getCloudcasts(self):
        conn = self.getConnection("cloudcasts")
        cloudcasts = []
        try:
            while (conn.hasNext()):
                api_op = conn.getNextPage()
                for cc in api_op["data"]:
                    curr_cc = Cloudcast(self.id, cc["slug"], self.api)
#saving cloudcast data turned out to slow things down way too much
#                    curr_cc.saveAllConnections()
                    cloudcasts.append(curr_cc.getCloudcastData())
            return cloudcasts
        except KeyError:
            return cloudcasts

    def saveCloudcasts(self):
        cloudcasts = self.getCloudcasts()
        self.user_data["cloudcasts"] = cloudcasts

    def _getSocialList(self, conn_type):
        """Private method to get the follower/following usernames connected to the user"""
        conn = self.getConnection(conn_type)
        soc_list = []
        try:        
            while (conn.hasNext()):
                api_op = conn.getNextPage()
                soc_list += [user["username"] for user in api_op["data"]]
            return soc_list
        except KeyError:
            return soc_list
            
    def _getInteractionList(self, conn_type):
        """Private method to get the listens/favorites of the user"""
        conn = self.getConnection(conn_type)
        interact_list = []
        try:
            while (conn.hasNext()):
                api_op = conn.getNextPage()
                for item in api_op["data"]:
                    interact_list.append({
                        "user": item["user"]["username"],
                        "cloudcast_slug": item["slug"]
                        })
            return interact_list
        except KeyError:
            return interact_list

#class UserSet(set):
#    pass

