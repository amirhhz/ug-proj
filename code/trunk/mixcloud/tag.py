#!/usr/bin/env python

import api

def getTag(tag):
	tagURL = api.getResourceURL("tag", tag)
	return api.getFromAPI(tagURL)
