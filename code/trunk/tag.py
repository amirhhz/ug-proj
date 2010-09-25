#!/usr/bin/env python

from api import getFromAPI, api_url, r_api_url

def getTag(tag):
	tagURL = r_api_url.format("tag/" + tag)
	return getFromAPI(tagURL)