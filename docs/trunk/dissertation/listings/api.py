#!/usr/bin/env python

from collections import deque
from time import sleep
from urllib import urlencode
from httplib import HTTPException
import httplib2
import json
import socks

from settings import (METACONNS, RESPECT_TIME, DEFAULT_API, DEBUG, PROXIES,
                      DEFAULT_METACONNS_WHITELIST, DEFAULT_METACONNS_BLACKLIST)

class MixcloudAPIException(HTTPException):
    def __init__(self, uri, status_code, *args):
        HTTPException.__init__(self, uri, status_code, args)
        self.uri = uri
        if isinstance(status_code, int):
            self.status = status_code
        else:
            self.status = -1
        self.message = str(self.status) + ": Problem accessing " + uri + "."


class MixcloudAPIRateLimitException(MixcloudAPIException):
    def __init__(self, uri, retry, status_code=403, *args):
        MixcloudAPIException.__init__(self, uri, status_code, retry, args)
        self.retry = retry
        self.message = (str(self.status) + ": Rate limit hit, retry after " 
                        + str(self.retry) + " seconds.")


class MixcloudAPI():
    """This handles connections to api.mixcloud.com, optionally via proxies.
    
This class can be an initialised with a list, containing dictionaries (or 
'None's) providing the parameters to pass on to httplib2.ProxyInfo()."""
    def __init__(self, list_of_proxies=None):

        if list_of_proxies:
            self.proxies = deque()
            for prx_values in list_of_proxies:
                if prx_values:
                    self.proxies.append(httplib2.ProxyInfo(**prx_values))
                    print "Added proxy:", prx_values
                else:
                    self.proxies.append(None)
            self.current_proxy = self.proxies[0]
        else:
            self.proxies = []
            self.current_proxy = None

        self.connection = None
        self.open_connection()
        self.metaconns_whitelist = DEFAULT_METACONNS_WHITELIST
        self.metaconns_blacklist = DEFAULT_METACONNS_BLACKLIST
        
        
            
    @classmethod        
    def get_uri(cls, resource_key, params):
        path = cls.get_path(resource_key)
        path = cls.add_params(path, params)
        return DEFAULT_API + path
    
    @classmethod        
    def get_path(cls, resource_key):
        """Return the path, relative to API's root, to the object object given
         the key."""                     
        path = "/".join(resource_key)
        path = "/" + path + "/"
        return path

    @classmethod        
    def add_params(cls, base, params):
        """Add the parameters specified in params as GET arguments to the end 
        of the URI."""
        enc_params = urlencode(params)
        return base + "?" + enc_params

    def switch_proxy(self):
        "Rotate through proxies, if there are any."
        if self.proxies:
            self.proxies.rotate()
            self.current_proxy = self.proxies[0]
            print "INFO: API blocking: switched proxy..."
            if self.current_proxy:
                print str(self.current_proxy.astuple())

    def open_connection(self):
        """Open a httplib2 connection which is persistent under HTTP/1.1."""
        self.connection = httplib2.Http(proxy_info=self.current_proxy)
        
    def reset_connection(self):
        del self.connection
        self.open_connection()

    def get_from_API(self, obj):
        """First get the base path of the object from its resource key and
        then pass to request() with parameters."""
        if getattr(obj, "paged", None):
            return self.get_from_API_paged(obj)
        uri = self.get_uri(obj.resource_key, obj.resource_params)     
        return self.request(uri)

    def get_from_API_paged(self, obj):
        uri = self.get_uri(obj.resource_key, obj.resource_params)
        # Accumulate data over pages in a book
        book = []
        page = self.request(uri)
        try:
            book.extend(page["data"])
            while ( ("paging" in page.keys()) and
                    ("next" in page["paging"].keys()) ):
                uri = page["paging"]["next"]
                page = self.request(uri)
                book.extend(page["data"])                
        except KeyError:
            print "KeyError in get_from_API_paged() on:"
            print uri
        # Return uncurated data book, with all the junk
        return book

    def request(self, uri, respect=RESPECT_TIME):
        """Request object at path from the server and return the JSON data of 
        the given resource as a Python object."""
        sleep(respect) # just out of respect for the API server
        # While loop to force retry if blank returned
        if DEBUG:
            print uri
        # initialise content before loop
        content = None
        # keep track of number of proxy switches within the function's scope
        switching_tries = 0
        while (not content):
            resp, content = self.connection.request(uri)
            # Handle unsuccessful request:
            if resp.status != 200:
                # Rate limit is hit when response status is 403
                if (resp.status == 403 and
                    (not self.proxies or switching_tries > len(self.proxies))):                    
                    raise MixcloudAPIRateLimitException(
                                                        uri=uri, 
                                                        retry=int(resp["retry-after"]))
                elif (resp.status == 403 
                      and self.proxies and switching_tries <= len(self.proxies)):
                    self.switch_proxy()
                    self.reset_connection()
                    # Reset content so while loop continues
                    content = None
                    switching_tries += 1
                    continue                                    
                raise MixcloudAPIException(uri, resp.status)
        api_output = json.loads(content)
        return api_output
    
    def set_metaconns_blacklist(self, *blist):
        self.metaconns_blacklist = []
        for i in blist:
            if i not in METACONNS:
                continue
            self.metaconns_blacklist.append(i)
    
    def set_metaconns_whitelist(self, *wlist):
        self.metaconns_whitelist = []
        for i in wlist:
            if i not in METACONNS:
                continue
            self.metaconns_whitelist.append(i)


