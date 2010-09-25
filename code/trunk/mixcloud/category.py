#!/usr/bin/env python

from api import getFromAPI, api_url, r_api_url

def getCategory(cat):
	artistURL = r_api_url.format("category/" + cat)
	return getFromAPI(artistURL)