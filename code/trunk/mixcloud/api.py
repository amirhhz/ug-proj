#!/usr/bin/env python

from urllib2 import urlopen, HTTPError, URLError
import json

api_url = "http://api.mixcloud.com/{}/"
# Rich API URL template, i.e. with all metadata
r_api_url = "http://api.mixcloud.com/{}/?metadata=1"

def getFromAPI(resourceURL):
	"""Returns the JSON data of the given resource from the Mixcloud API, as a Python object."""
	try:
		print resourceURL
		api_handle = urlopen(resourceURL)
		api_output = json.load(api_handle)
		api_handle.close()
		return api_output
	except HTTPError as e:
		print e
	except URLError as e:
		print "URL Error: ", e.reason
		print "Cannot open URL %s for reading" % resourceURL
		return