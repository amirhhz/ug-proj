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

    def getFromAPI(self, resource_string, as_obj=True):
        """Connects to the specified server and returns the JSON data of the given resource from the Mixcloud API, as a Python object by default."""

        sleep(0.2) # just out of respect
        try:
            self.connection.request("GET",resource_string)
            api_response = self.connection.getresponse()
            if api_response.status != 200:
                if api_response.status == 403:
                    raise HTTPException
                raise Exception
            if as_obj:
                api_output = json.load(api_response)
                return api_output
            # Otherwise just return string representing the JSON
            else:
                api_output = api_response.read()
                return api_output

        except HTTPException as e:
            retry = (int) (api_response.getheader("retry-after"))
            print api_response.status, api_response.reason
            print "Retrying after", retry ,"seconds ..."
            sleep(retry)            
            self.getFromAPI(resource_string)
                      
    def getBaseURL(self, *resource_key):
        """Return the URL of a Mixcloud API object given a tuple of strings constituting the key."""
        key = "/".join(resource_key)
        key = "/" + key + "/"
        return key

        
    def addURLParams(self, resourceURL, force_meta=True, **params):
        """Add the parameters specified in params as GET arguments to the end of the URL, forcing the metadata=1 parameter by default"""
        # If indicated, make sure "metadata" parameter is set to 1
        if force_meta: params.update(metadata=1)
        enc_params = urlencode(params)
        return resourceURL + "?" + enc_params

        
    def getResourceURL(self, *resource_key, **params):
        """First get the base URL from provided resource key tuple and then add HTTP GET parameters, returning the result."""
        base = self.getBaseURL(*resource_key)
        full = self.addURLParams(base,**params)
        return full


class MetaConnection():
    """Class to faciliate the traversal of metadata connections provided by resources, including pagination."""
    def __init__(self, baseURL, api, offset=0, limit=100, **params):
        self.api = api
        self.limit = limit
        self.curr_offset = offset
        self.baseURL = baseURL
        self.init_page = self.api.addURLParams(baseURL, False, offset=offset, limit=limit)
        # init next_page to current page so that getNextPage() can work as expected
        self.next_page = self.init_page
        # initiliase to true but change as appropriate on getFirstPage
        self.has_next = True 

    def hasNext(self):
        return self.has_next

    def getNextPage(self):
        # Fetch first page as Python object
        page = self.api.getFromAPI(self.next_page, True)
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

