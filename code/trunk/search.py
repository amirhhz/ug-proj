#!/usr/bin/env python

from api import getFromAPI, api_url, r_api_url
from urllib import quote_plus

def getSearch(query, type="cloudcast"):
	"""Returns the search result of query, within the type - cloudcast, user, tag, artist, track."""
	artistURL = api_url.format("search") + "?q=" + quote_plus(query) + "&type" + type
	return getFromAPI(artistURL)