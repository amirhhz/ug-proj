#!/usr/bin/env python

CATEGORIES = [
    "business", "comedy", "culture", "drum-and-bass", "dubstep-bass",
    "education", "electronica", "funk-soul", "hip-hop", "indie", "jazz-ambient",
    "news", "mix-series", "politics", "reggae-dancehall", "sport", "techno",
    "technology", "world"
    ]

SEARCH_TYPES = [
    "cloudcast", "user", "tag", "artist", "track"
]

class DynRsrcException(Exception):
    def __init__(self, rsrc_type):
        self.rsrc_type = rsrc_type

class BaseDynResource():
    def __init__(self):
        self.resource_key = None
        self.resource_params = {"offset": 0, "limit": 100}
    

class Categories(BaseDynResource):
    def __init__(self, cat):
        BaseDynResource.__init__(self)
        if cat not in CATEGORIES:
            raise DynRsrcException("Categories")
        self.cat = cat        
        self.resource_key = ("categories", cat)

class Popular(BaseDynResource):
    def __init__(self):
        BaseDynResource.__init__(self)
        self.resource_key = ("popular")

class Hot(BaseDynResource):
    def __init__(self):
        BaseDynResource.__init__(self)
        self.resource_key = ("popular", "hot")

class New(BaseDynResource):
    def __init__(self):
        BaseDynResource.__init__(self)
        self.resource_key = ("new")    

class Search(BaseDynResource):
    def __init__(self, search_str, search_type):
        BaseDynResource.__init__(self)
        if search_type not in SEARCH_TYPES:
            raise DynRsrcException("Search")
        self.resource_key = ("search")
        self.resource_params.update({"q": search_str, "type": search_type})

class Feed(BaseDynResource):
    def __init__(self, user):
        BaseDynResource.__init__(self)
        self.resource_key = (user, "feed")

class Followers(BaseDynResource):
    def __init__(self, user):
        BaseDynResource.__init__(self)
        self.resource_key = (user, "followers")
    
class Following(BaseDynResource):
    def __init__(self, user):
        BaseDynResource.__init__(self)
        self.resource_key = (user, "following")

class Comments(BaseDynResource):
    def __init__(self, user, resource=None):
        BaseDynResource.__init__(self)
        if resource is None:
            self.resource_key = (user, "comments")
        else:
            self.resource_key = (user, resource, "comments")

class Favorites(BaseDynResource):
    def __init__(self, user, resource=None):
        BaseDynResource.__init__(self)
        if resource is None:
            self.resource_key = (user, "favorites")
        else:
            self.resource_key = (user, resource, "favorites")

class Cloudcasts(BaseDynResource):
    def __init__(self, user_or_cat):
        BaseDynResource.__init__(self)
        self.resource_key = (user_or_cat, "cloudcasts")

class Listens(BaseDynResource):
    def __init__(self, user):
        BaseDynResource.__init__(self)
        self.resource_key = (user, "listens")

class Listeners(BaseDynResource):
    def __init__(self, user, cloudcast):
        BaseDynResource.__init__(self)
        self.resource_key = (user, cloudcast, "listeners")

class Similar(BaseDynResource):
    def __init__(self, user, cloudcast):
        BaseDynResource.__init__(self)
        self.resource_key = (user, cloudcast, "similar")

class Users(BaseDynResource):
    def __init__(self, cat):
        BaseDynResource.__init__(self)
        self.resource_key = (cat, "users")

class Userpick_users(BaseDynResource):
    def __init__(self, cat):
        BaseDynResource.__init__(self)
        self.resource_key = (cat, "userpick_users")

class Userpick_cloudcasts(BaseDynResource):
    def __init__(self, cat):
        BaseDynResource.__init__(self)
        self.resource_key = (cat, "userpick_cloudcasts")

