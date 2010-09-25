#!/usr/bin/env python

from api import getFromAPI, api_url, r_api_url

def getUser(username):
	userURL = r_api_url.format(username)
	return getFromAPI(userURL)
	
def getUserFollowers(username):
	"""Return a list of the followers of the user given."""

	followersURL = api_url.format(username + "/followers") + "?offset=0&limit=50"
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