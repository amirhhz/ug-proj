#!/usr/bin/env python

from time import sleep
from urllib import urlencode
from httplib import HTTPException
import httplib2
import json

from base_resources import InteractiveResource, AnnotationResource, CategoryResource
import dynamic_resources as dyn_rsrc

from settings import METACONNS, RESPECT_TIME, DEFAULT_METACONN_WHITELIST, DEFAULT_METACONN_BLACKLIST, default_api


class MixcloudAPI():
    def __init__(self):
        self.open_connection()
        self.metaconns_whitelist = DEFAULT_METACONNS_WHITELIST
        self.metaconns_blacklist = DEFAULT_METACONNS_BLACKLIST

    def open_connection(self):
        """Open a httplib2 connection which is persistent under HTTP/1.1."""
        self.connection = httplib2.Http()
        
    def reset_connection(self, uri):
        del self.connection
        self.open_connection()

    def get_from_API(self, obj):
        """First get the base path of the object from its resource key and
        then pass to request() with parameters."""
        if obj.paged:
            return self.get_from_API_paged(obj)
        uri = self.get_uri(obj.resource_key, obj.resource_params)     
        return self.request(uri)

    def get_from_API_paged(self, obj):
        uri = self.get_uri(obj.resource_key, obj.resource_params)
        # Accumulate data over pages in a book
        book = []
        page = self.request(uri)
        try:
            book.append(page["data"])
            while ( ("paging" in page.keys()) and
                    ("next" in page["paging"].keys()) ):
                uri = page["paging"]["next"]
                page = self.request(uri)
                book.append(page["data"])                
        except KeyError:
            print "KeyError in get_from_API_paged() on:"
            print uri
        # Return uncurated data book, with all the junk
        return book

            
    def get_uri(self, resource_key, params):
        path = self.get_path(*resource_key)
        path = self.add_params(path, **params)
        return default_api + path

    def get_path(self, *resource_key):
        """Return the path, relative to API's root, to the object object given
         the key."""
        path = "/".join(resource_key)
        path = "/" + path + "/"
        return path

    def add_params(self, base, **params):
        """Add the parameters specified in params as GET arguments to the end 
        of the URI."""
        # If indicated, make sure "metadata" parameter is set to 1
        enc_params = urlencode(params)
        return base + "?" + enc_params

    def request(self, uri, respect=RESPECT_TIME):
        """Request object at path from the server and return the JSON data of 
        the given resource as a Python object."""
        content = None
        sleep(respect) # just out of respect for the API server
        # While loop to force retry if blank returned
        while (not content):
            resp, content = self.connection.request(uri)
            if resp.status != 200:
                if resp.status == 403:
                    raise MixcloudAPIException((int)(resp["Retry-After"]))
                raise HTTPException(resp.status)
        api_output = json.loads(content)
        return api_output
    
    def set_metaconns_blacklist(self, *list):
        self.metaconns_blacklist = []
        for i in list:
            if i not in METACONNS:
                continue
            self.metaconns_blacklist.append(i)
    
    def set_metaconns_whitelist(self, *list):
        self.metaconns_whitelist = []
        for i in list:
            if i not in METACONNS:
                continue
            self.metaconns_whitelist.append(i)


class User(InteractiveResource):
    def __init__(self, api, username):
        InteractiveResource.__init__(self, api, username)
        # Augment the User resource with dynamic resources further to those
        # inherited from InteractiveResource
        self.dyn_resources.update({
            "feed": dyn_rsrc.Feed(username),
            "followers": dyn_rsrc.Followers(username),
            "following": dyn_rsrc.Following(username),
            "cloudcasts": dyn_rsrc.Cloudcasts(username),
            "listens": dyn_rsrc.Listens(username)
        })

    def populate(self):
        """Run this after initialising an instance to gather all relevant data."""
        try:
            self.fetch_data()
            self.populate_metaconns()
        except MixcloudAPIException:
            pass
        except HTTPException:
            pass
        # for MongoDB's benefit, set _id field to username, which is unique
        self.data["_id"] = username
        
    def get_user_id(self):
        return self.data["_id"]
    
    def get_followers(self):
        return self.data["followers"]
    
    def get_following(self):
        return self.data["following"]
    
    def get_favorites(self):
        pass
    
    def get_cloudcasts(self):
       pass
    
    def get_listens(self):
        pass
    
    def get_favorited_users(self):
        pass
    
    def get_listened_to_users(self):
        pass
    
    def get_social_connections(self):
        return self.get_followers() + self.get_following()
    
    
class Cloudcast(InteractiveResource):
    def __init__(self, api, username, cloudcast):
        InteractiveResource.__init__(self, api, username, cloudcast)
        self.dyn_resources.update({
            "similar": dyn_rsrc.Similar(username, cloudcast),
            "listeners": dyn_rsrc.Listeners(username, cloudcast)
        })
        try:
            self.fetch_data()
        except MixcloudAPIException as apie:
            pass
        except HTTPException as he:
            pass

class Tag(AnnotationResource):
    def __init__(self, api, tag):
        AnnotationResource.__init__(self, api, tag)
        
class Artist(AnnotationResource):
    def __init__(self, api, artist):
        AnnotationResource.__init__(self, api, artist)

class Track(AnnotationResource):
    def __init__(self, api, artist, track):
        AnnotationResource.__init__(self, api, artist, track)

class Category(CategoryResource):
    def __init__(self, api, cat):
        CategoryResource.__init__(self, api, cat)
        
class MixcloudAPIException(HTTPException):
    def __init__(self, retry):
        self.retry = retry
    def get_retry(self):
        return self.retry