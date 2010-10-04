#!/usr/bin/env python

import api

def getCloudcast(username, cloudcast):
	cloudcastURL = api.getResourceURL(username, cloudcast)
	return api.getFromAPI(cloudcastURL)
