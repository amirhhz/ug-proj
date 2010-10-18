#!/usr/bin/env python

from httplib import HTTPException
from time import sleep

from api import MetaConnection
from api import MixcloudAPIException
from resource.base_resource_type import InteractiveResource
import resource.dynamic_resource_type as dyn_rsrc

class Cloudcast(InteractiveResource):
    def __init__(self, username, cloudcast, api):
        InteractiveResource.__init__(self, username, cloudcast)
        self.api = api
        self.dyn_resources.update({
            "similar": dyn_rsrc.Similar(username, cloudcast),
            "listeners": dyn_rsrc.Listeners(username, cloudcast)
        })
        try:
            print username, " ", cloudcast
            self.cloudcast_data = self.api.getFromAPI(self.api.getResourceURL(username, cloudcast))
        except MixcloudAPIException as apie:
            print "Error during Cloudcast() init: Mixcloud is blocking requests."
            self.api.connection.close()
            retry = apie.getRetry()
            print "Retrying after", retry ,"seconds ..."
            sleep(retry+1)
            self.api.connectToAPI()
            self.cloudcast_data = self.api.getFromAPI(self.api.getResourceURL(username, cloudcast))
        except HTTPException as he:
            print "Unknown HTTPException occurred during Cloudcast() init."
            print he.args
            exit()       
        
        self.meta_conns = dict()
        # for all dynamic resources, produce a MetaConnection object
        for resource in self.dyn_resources.keys():
            self.meta_conns[resource] = MetaConnection(
                api, 
                api.getBaseURL(resource.resource_keys), 
                resource.resource_params
            )

    def saveAllConnections(self):
        self.saveFavorites()
        self.saveListeners()
        self.saveComments()

    def getCloudcastData(self):
        return self.cloudcast_data
    
    def getConnection(self, conn_type):
        try:
            return self.meta_conns[conn_type]
        except KeyError:
            return

    def getListeners(self):
        """Return the users who have listened to the cloudcast."""
        listeners = self._getInteractionList("listeners")
        return listeners
    
    def saveListeners(self):
        listeners = self.getListens()
        self.cloudcast_data["listeners"] = listeners
        
    def getFavorites(self):
        """Return a list of users who have favorited the cloudcast."""
        faves = self._getInteractionList("favorites")
        return faves

    def saveFavorites(self):
        faves = self.getFavorites()
        self.cloudcast_data["favorites"] = faves

    def getComments(self):
        conn = self.getConnection("comments")
        comments_list = []
        try:
            while (conn.hasNext()):
                api_op = conn.getNextPage()
                for item in api_op["data"]:
                    comments_list.append({
                        "user": item["user"]["username"],
                        "comment": item["comment"],
                        "submit_date": item["submit_date"],
                        "key": item["key"]
                    })
            return comments_list
        except KeyError:
            return comments_list        

    def saveComments(self):
        comments = self.getComments()
        self.cloudcast_data["comments"] = comments

    def _getInteractionList(self, conn_type):
        """Private method to get the listeners/favoriters of the cloudcast"""
        conn = self.getConnection(conn_type)
        interact_list = []
        try:
            while (conn.hasNext()):
                api_op = conn.getNextPage()
                interact_list += [item["username"] for item in api_op["data"]]
            return interact_list
        except KeyError:
            return interact_list


