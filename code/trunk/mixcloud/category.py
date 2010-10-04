#!/usr/bin/env python

import api

def getCategory(cat):
	catURL = api.getResourceURL("category", cat)
	return api.getFromAPI(catURL)
