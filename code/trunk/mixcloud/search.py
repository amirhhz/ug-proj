#!/usr/bin/env python

import api
from urllib import quote_plus

def getSearch(query, stype="cloudcast"):
	"""Returns the search result of query, within the type - cloudcast, user, tag, artist, track."""
	
	params = dict({"query":quote_plus(query),"type":stype})
	searchURL = api.getResourceURL("search", params)	
	return api.getFromAPI(searchURL)
