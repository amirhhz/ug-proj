#!/usr/bin/env python

from api import getFromAPI, api_url, r_api_url

class MCUser():
	def __init__(self,username):
		self.JSONdata = self.getUserData(username)
		self.name = self.JSONdata["username"]

	def getJSON(self):
		return self.JSONdata	

	def getUserData(self, username):
		userURL = r_api_url.format(username)
		return getFromAPI(userURL)
	
	def getFollowers(self):
		"""Return a list of the followers of the user given."""

		followersURL = api_url.format(self.name + "/followers") + "?offset=0&limit=100"
		followers = []

		try:		
			api_op = getFromAPI(followersURL)
			followers = [user["username"] for user in api_op["data"]]

			while ( ("paging" in api_op.keys()) and 
					("next" in api_op["paging"].keys()) ):
				api_op = getFromAPI(api_op["paging"]["next"])
				followers += [user["username"] for user in api_op["data"]]
			return followers
		
		except KeyError:
			return followers

	def mongoSave(self, mongo_coll):
		mongo_coll.save(self.getJSON())

class UserSet(set):
	pass
		
