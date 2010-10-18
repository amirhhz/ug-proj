#!/usr/bin/env python

from time import sleep
from urllib import urlencode
from urllib2 import urlopen, HTTPError, URLError
import json

# base Mixcloud API URL, with a parameter to be filled in with a resource key
api_url = "http://api.mixcloud.com/{0}/"

connection_keys = [
    "comments","favourites","followers","following","listens", "cloudcasts",
    "similar", "popular", "new", "users", 
    "userpick-users", "userpick-cloudcasts"
]


def getFromAPI(resourceURL, as_obj=True):
    """Returns the JSON data of the given resource from the Mixcloud API, as a Python object by default."""

    sleep(0.2) # just out of respect

    try:
        api_handle = urlopen(resourceURL)
        # requested, return the JSON response as a python object
        if as_obj:
            api_output = json.load(api_handle)
            api_handle.close()
            return api_output
        # Otherwise just return string representing the JSON
        else:
            api_output = api_handle.read()
            return api_output

    except HTTPError as e:
        print e
        error_op = json.load(e)
        retry = error_op["error"]["retry_after"]
        print "Retry after", retry
        print "Waiting ..."
        sleep(retry+2)
        print "Back up :)"
        return getFromAPI(resourceURL)
                
    except URLError as e:
        print "URL Error: ", e.reason
        print "Cannot open URL %s for reading" % resourceURL
        exit()
        
def getBaseURL(*resource_key):
    """Return the URL of a Mixcloud API object given a tuple of strings constituting the key, corresponding to the {0} parameter in the api_url field."""
    key = "/".join(resource_key)
    return api_url.format(key)

    
def addURLParams(resourceURL, force_meta=True, **params):
    """Add the parameters specified in params as GET arguments to the end of the URL, forcing the metadata=1 parameter by default"""
    # If indicated, make sure "metadata" parameter is set to 1
    if force_meta: params.update(metadata=1)
    enc_params = urlencode(params)
    return resourceURL + "?" + enc_params

    
def getResourceURL(*resource_key, **params):
    """First get the base URL from provided resource key tuple and then add HTTP GET parameters, returning the result."""
    base = getBaseURL(*resource_key)
    full = addURLParams(base,**params)
    return full


class MetaConnection():
    """Class to faciliate the traversal of metadata connections provided by resources, including pagination."""
    def __init__(self, baseURL, offset=0, limit=100, **params):
        self.init_page = addURLParams(baseURL, False, offset=offset, limit=limit)
        # init next_page to current page so that getNextPage() can work as expected
        self.next_page = self.init_page
        # initiliase to true but change as appropriate on getFirstPage
        self.has_next = True 

    def HasNext(self):
        return self.has_next

    def getNextPage(self):
        # Fetch first page as Python object
        page = getFromAPI(self.next_page, True)
        # if next page exists, update fields as appropriate
        if ( ("paging" in page.keys()) and 
             ("next" in page["paging"].keys()) ):
            self.has_next = True
            self.next_page = page["paging"]["next"]
        # If last page, nullify fields
        else:
            self.has_next = False
            self.next_page = None
        return page
             
    def resetPage(self):
        self.next_page = self.init_page
        self.has_next = True

