#!/usr/bin/env python

from time import sleep
from urllib import urlencode
from httplib import HTTPConnection, HTTPException, BadStatusLine
import json

default_api = "api.mixcloud.com"

class MixcloudAPI():

    def __init__(self):
        self.connection = None
        self.connectToAPI()

        # words used in resource keys of "metadata connections" on mixcloud
        self.metaconn_keys = [
            "comments","favourites","followers","following","listens", "cloudcasts",
            "similar", "popular", "new", "users", 
            "userpick-users", "userpick-cloudcasts"
        ]

    def connectToAPI(self, api_address=default_api):
        """Makes connection to the API server."""
        self.connection = HTTPConnection(api_address)

    def getFromAPI(self, resource_string, as_obj=True, respect=0.25):
        """Connects to the specified server and returns the JSON data of the given resource from the Mixcloud API, as a Python object by default."""

        sleep(respect) # just out of respect
#        try:
        self.connection.request("GET",resource_string)
        api_response = self.connection.getresponse()
        if api_response.status != 200:
            if api_response.status == 403:
                raise MixcloudAPIException((int)(api_response.getheader("retry-after")))
            raise HTTPException(api_response.status)
        if as_obj:
            api_output = json.load(api_response)
            return api_output
        # Otherwise just return string representing the JSON
        else:
            api_output = api_response.read()
            return api_output

    def getBaseURL(self, *resource_key):
        """Return the suffix part of the URL of a Mixcloud API object given a
tuple of strings constituting the key."""
        key = "/".join(resource_key)
        key = "/" + key + "/"
        return key

        
    def addURLParams(self, resourceURL, force_meta=True, **params):
        """Add the parameters specified in params as GET arguments to the end 
of the URL, forcing the metadata=1 parameter by default."""
        # If indicated, make sure "metadata" parameter is set to 1
        if force_meta: params.update(metadata=1)
        enc_params = urlencode(params)
        return resourceURL + "?" + enc_params

        
    def getResourceURL(self, *resource_key, **params):
        """First get the base suffix part of URL from provided resource key 
tuple and then add HTTP GET parameters, returning the result."""
        base = self.getBaseURL(*resource_key)
        full = self.addURLParams(base,**params)
        return full


class MetaConnection():
    """Class to faciliate the traversal of metadata connections provided by 
resources, including pagination."""
    def __init__(self, api, baseURL, **params):
        self.api = api
        try:
            self.limit = params["limit"]
        except KeyError:
            self.limit = 100
        try:
            self.curr_offset = params["offset"]
        except KeyError:
            self.curr_offset = 0
        self.baseURL = baseURL
        self.init_page = self.api.addURLParams(baseURL, False, **params)
        # init next_page to current page so that getNextPage() can work as expected
        self.next_page = self.init_page
        # initiliase to true but change as appropriate on getNextPage()
        self.has_next = True 

    def hasNext(self):
        return self.has_next

    def getNextPage(self):
        # Fetch first page as Python object
        page = None
        try:
            page = self.api.getFromAPI(self.next_page)
        except MixcloudAPIException as apie:
            print "Error during pagination: Mixcloud is blocking requests."
            self.api.connection.close()
            retry = apie.getRetry()
            print "Retrying after", retry ,"seconds ..."
            sleep(retry+1)
            self.api.connectToAPI()            
            page = self.api.getFromAPI(self.next_page)
        except HTTPException as he:
            print "Unknown HTTPException occurred."
            print he.args
            exit()       
        # if next page exists, update fields as appropriate
        if ( ("paging" in page.keys()) and 
             ("next" in page["paging"].keys()) ):
            self.has_next = True
            self.curr_offset += self.limit
            self.next_page = self.api.addURLParams(
                self.baseURL, False, offset=self.curr_offset, limit=self.limit
            )
        # If last page, nullify fields
        else:
            self.has_next = False
            self.next_page = None
        return page
             
    def resetPage(self):
        self.next_page = self.init_page
        self.has_next = True
        
class MixcloudAPIException(HTTPException):
    def __init__(self, retry):
        self.retry = retry
    def getRetry(self):
        return self.retry

