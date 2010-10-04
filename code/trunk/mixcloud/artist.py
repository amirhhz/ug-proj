#!/usr/bin/env python

import api

def getArtist(artist):
	artistURL = api.getResourceURL("artist", artist)
	return api.getFromAPI(artistURL)
	
