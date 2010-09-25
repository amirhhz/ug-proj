#!/usr/bin/env python

from api import getFromAPI, api_url, r_api_url

def getTrack(artist, track):
	trackURL = r_api_url.format("track/" + artist + "/" + track)
	return getFromAPI(trackURL)
