#!/usr/bin/env python

from api import getFromAPI, api_url, r_api_url

def getArtist(artist):
	artistURL = r_api_url.format("artist/" + artist)
	return getFromAPI(artistURL)
	