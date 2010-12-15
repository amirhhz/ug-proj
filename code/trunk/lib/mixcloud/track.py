#!/usr/bin/env python

import api

def getTrack(artist, track):
	trackURL = api.getResourceURL("track", artist, track)
	return api.getFromAPI(trackURL)
