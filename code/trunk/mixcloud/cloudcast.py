#!/usr/bin/env python

from api import getFromAPI, api_url, r_api_url

def getCloudcast(username, cloudcast):
	cloudcastURL = r_api_url.format(username + "/" + cloudcast)
	return getFromAPI(cloudcastURL)