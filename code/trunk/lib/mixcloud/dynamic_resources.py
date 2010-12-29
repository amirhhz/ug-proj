#!/usr/bin/env python

from base_resources import _Resource
from settings import CATEGORIES, SEARCH_TYPES

class DynResource(_Resource):
    def __init__(self, api):
        _Resource.__init__(self, api)
        self.resource_params = {"limit": 100}
        self.paged = True
        
    def get_clean_data(self):
        self.get_data()

class SocialDynResource(DynResource):
    """ This is for code shared between the Followers and Following dynamic
    resource classes."""
    def __init__(self, api):
        DynResource.__init__(self, api)
    
    def get_clean_data(self):
        self.get_data()
        clean_list = []
        try:
            clean_list = [user["username"] for user in self.data]
        except KeyError:
            pass
        return clean_list

class Followers(SocialDynResource):
    def __init__(self, api, user):
        DynResource.__init__(self, api)
        self.resource_key = [user, "followers"]
        self.resource_params.update({"offset": 0})
    
class Following(SocialDynResource):
    def __init__(self, api, user):
        DynResource.__init__(self, api)
        self.resource_key = [user, "following"]
        self.resource_params.update({"offset": 0})

class Favorites(DynResource):
    def __init__(self, api, user, resource=None):
        DynResource.__init__(self, api)
        if resource is None:
            self.resource_key = [user, "favorites"]
        else:
            self.resource_key = [user, resource, "favorites"]

class Cloudcasts(DynResource):
    def __init__(self, api, user_or_cat):
        DynResource.__init__(self, api)
        self.resource_key = [user_or_cat, "cloudcasts"]
    

class Categories(DynResource):
    def __init__(self, api, cat):
        DynResource.__init__(self, api)
        if cat not in CATEGORIES:
            raise DynRsrcException("Categories")
        self.cat = cat        
        self.resource_key = ["categories", cat]

class Popular(DynResource):
    def __init__(self, api):
        DynResource.__init__(self, api)
        self.resource_key = ["popular"]

class Hot(DynResource):
    def __init__(self, api):
        DynResource.__init__(self, api)
        self.resource_key = ["popular", "hot"]

class New(DynResource):
    def __init__(self, api):
        DynResource.__init__(self, api)
        self.resource_key = ["new"]    

class Search(DynResource):
    def __init__(self, api, search_str, search_type):
        DynResource.__init__(self, api)
        if search_type not in SEARCH_TYPES:
            raise DynRsrcException("Search")
        self.resource_key = ["search"]
        self.resource_params.update({"q": search_str, "type": search_type})

class Feed(DynResource):
    def __init__(self, api, user):
        DynResource.__init__(self, api)
        self.resource_key = [user, "feed"]

class Comments(DynResource):
    def __init__(self, api, user, resource=None):
        DynResource.__init__(self, api)
        if resource is None:
            self.resource_key = [user, "comments"]
        else:
            self.resource_key = [user, resource, "comments"]

class Listens(DynResource):
    def __init__(self, api, user):
        DynResource.__init__(self, api)
        self.resource_key = [user, "listens"]

class Listeners(DynResource):
    def __init__(self, api, user, cloudcast):
        DynResource.__init__(self, api)
        self.resource_key = [user, cloudcast, "listeners"]

class Similar(DynResource):
    def __init__(self, api, user, cloudcast):
        DynResource.__init__(self, api)
        self.resource_key = [user, cloudcast, "similar"]

class Users(DynResource):
    def __init__(self, api, cat):
        DynResource.__init__(self, api)
        self.resource_key = [cat, "users"]

class Userpick_users(DynResource):
    def __init__(self, api, cat):
        DynResource.__init__(self, api)
        self.resource_key = [cat, "userpick_users"]

class Userpick_cloudcasts(DynResource):
    def __init__(self, api, cat):
        DynResource.__init__(self, api)
        self.resource_key = [cat, "userpick_cloudcasts"]

class DynRsrcException(Exception):
    def __init__(self, rsrc_type):
        self.rsrc_type = rsrc_type

