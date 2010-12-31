#!/usr/bin/env python

from httplib import HTTPException
import time
import json

from settings import DEBUG
from settings import ANNOTATION_TYPES, CATEGORIES, SEARCH_TYPES, ITEMS_PER_PAGE


################################################################################
## BASE RESOURCES ##############################################################
################################################################################        

class Resource():
    """Every API resource, base or dynamic, will have an associated API, a
    resource key to identify and access it, some parameters to pass via HTTP and
    its data.""" 
    def __init__(self, api):
        self.api = api
        self.resource_key = []
        self.resource_params = {}
        self.data = None

    def __str__(self):
        return "Mixcloud API Resource: ", "/".join(self.resource_key)
    
    def get_key(self):
        return self.resource_key
    
    def get_params(self):
        return self.resource_params

    def fetch_data(self):
        """Fetch the main, first-level data about the resource from the API.
        Note that this OVER-WRITES whatever is currently stored in the data
        field."""
        self.data = self.api.get_from_API(self)
    
    def get_data(self):
        """ Return the data stored for the resource, fetch it if it doesn't
        exist yet."""
        if self.data is None:
            self.fetch_data()
        return self.data

################################################################################
## DYNAMIC RESOURCES ###########################################################
################################################################################

class BaseResource(Resource):
    """Base resources have one thing in common: we want their metadata, which 
    are links to the dynamic resources. See dynamic_resource_type.py.
     
    Optionally, a Unix epoch timestamp could also be passed to the resource to
    specify the time up to which dynamic resources are returned, where this is 
    applicable."""
    def __init__(self, api, until=None):
        Resource.__init__(self, api)
        self.resource_params = {"metadata": 1}
        self.dyn_resources = {}
        # For some metaconnections, we may want to specify a time with which to
        # limit the dynamic resources returned, notably favorites and cloudcasts
        # Default to the current time.
        if not until:
            self.metaconns_until = int(time.time())
        else:
            self.metaconns_until = int(until)
        
    def set_until_time(self, until=time.time()):
        self.metaconns_until = int(until)
        self.propogate_until_time()
        
    def propogate_until_time(self):
        for conn in self.dyn_resources:
            self.dyn_resources[conn].set_until_param(self.metaconns_until)    
               
    def populate(self):
        """Run this after initialising an instance to gather all relevant 
        data."""
        self.fetch_data()
        self.populate_metaconns()

    def populate_metaconns(self):
        """Fetch the relevant dynamic resources and store them. Beware of 
        fetch_data()'s overwriting!"""
        self.propogate_until_time()
        for conn in self.api.metaconns_whitelist:
            if conn in self.dyn_resources.keys():
                conn_data = self.get_metaconn(conn)
                self.data[conn] = conn_data
        
    def get_metaconn(self, metaconn):
        """Fetch the clean (relevant) data for a particular dynamic resource 
        and return it."""
        if DEBUG:
            print "Populating", metaconn, "..."
        if metaconn in self.dyn_resources.keys():
            return self.dyn_resources[metaconn].get_clean_data()
                
    def get_field(self, fieldname):
        try:
            return self.data[fieldname]
        except KeyError as k:
            print k
            print "Could not find", fieldname, "in data. Ensure you have \
            populated the object's data field with get_data() or populate()."        
                 

class InteractiveResource(BaseResource):
    """The User and Cloudcast resources are this class's children, as they have
    the "comments" and "favorites" dynamic resources in common."""
    def __init__(self, api, user, resource=None, until=None):
        BaseResource.__init__(self, api, until)
        self.resource_key.append(user)
        if resource: 
            self.resource_key.append(resource)
        self.dyn_resources = {
                "comments": Comments(api, user, resource),
                "favorites": Favorites(api, user, resource)
            }
        
class AnnotationResource(BaseResource):
    """The Tag, Artist and Track resources are this class's children, as they 
    have the "popular" and "new" dynamic resources in common."""
    def __init__(self, api, 
                 annotation_type, resource1, resource2=None, until=None):
        BaseResource.__init__(self, api, until)
        assert annotation_type in ANNOTATION_TYPES
        self.resource_key = [annotation_type]
        self.resource_key.append(resource1)
        if resource2: 
            self.resource_key.append(resource2)
        self.dyn_resources = {
            "popular": Popular(api),
            "new": New(api)
        }
        
class CategoryResource(BaseResource):
    """Category resources are unique in their metadata's dynamic resources,
    so this class is only inherited by the Category resource."""
    def __init__(self, api, category, until=None):
        BaseResource.__init__(self, api, until)
        self.resource_key = ["categories"]
        self.resource_key.append(category)
        self.dyn_resources = {
            "cloudcasts": Cloudcasts(api, category),
            "users": Users(api, category),
            "userpick_cloudcasts": UserpickCloudcasts(api, category),
            "userpick_users": UserpickUsers(api, category),
        }

################################################################################
## DYNAMIC RESOURCES ###########################################################
################################################################################


class DynRsrcException(Exception):
    def __init__(self, rsrc_type):
        Exception.__init__(self)
        self.rsrc_type = rsrc_type


class DynResource(Resource):
    def __init__(self, api):
        Resource.__init__(self, api)
        self.resource_params = {"limit": ITEMS_PER_PAGE}
        self.paged = True
        
    def get_clean_data(self):
        """By "clean" we mean "relevant". This will always be a list of items,
        but the items could be simply strings (e.g. usernames), a list of pairs
        ([ username, slug] ) or full dictionaries of data (cloudcast JSONs)."""
        return self.get_data()
        
    def set_until_param(self, until):
        """Update dynamic resource with a date that will be used when fetching
        its data from the API. Note that this isn't a class variable, but an
        update of the resource_params class variable with an "until" field."""
        self.resource_params.update({"until": until})


class SocialDynResource(DynResource):
    """ This is for code shared between the Followers and Following dynamic
    resource classes."""
    def __init__(self, api):
        DynResource.__init__(self, api)
        self.resource_params.update({"offset": 0})
    
    def get_clean_data(self):
        """Returns the list of the users for the dynamic resource."""
        self.get_data()
        clean_list = []
        try:
            clean_list = [user["username"] for user in self.data]
        except KeyError:
            pass
        return clean_list
    
    def set_until_param(self, until):
        """Social resources do not take until dates as parameters so this method
        is a stub."""
        return
    
class SimpleInteractionDynResource(DynResource):
    """The Favorites, Cloudcasts and Listens dynamic resources inherit from
    this, because for these the only part of the data we are interested in is 
    the cloudcast key (i.e. a user-cloudcast pairing) so the get_clean_data() 
    method for these returns just these pairings in a dictionary."""
    def __init__(self, api):
        DynResource.__init__(self, api)

    def get_clean_data(self):
        self.get_data() 
        clean_list = []
        for item in self.data:
            clean_list.append({"user": item["user"]["username"], 
                               "cloudcast_slug": item["slug"]})
        return clean_list     

class Followers(SocialDynResource):
    def __init__(self, api, user):
        SocialDynResource.__init__(self, api)
        self.resource_key = [user, "followers"]

    
class Following(SocialDynResource):
    def __init__(self, api, user):
        SocialDynResource.__init__(self, api)
        self.resource_key = [user, "following"]


class Cloudcasts(SimpleInteractionDynResource):
    def __init__(self, api, user_or_cat):
        SimpleInteractionDynResource.__init__(self, api)
        self.resource_key = [user_or_cat, "cloudcasts"]
    
    def get_clean_data(self):
        """"Clean" data for the cloudcast resource should actually be a list of 
        each cloudcast's full JSON data, so here we fetch those. For user, slug
        pairs use get_clean_clean_data() on a Cloudcasts instance.""" 
        clean_data = []
        key_list = self.get_clean_clean_data()
        for item in key_list:
            cloudcast = Cloudcast(self.api, 
                                  item["user"], 
                                  item["cloudcast_slug"])
            clean_data.append(cloudcast.get_data())
        return clean_data
        
    def get_clean_clean_data(self):
        return SimpleInteractionDynResource.get_clean_data(self)


class Favorites(SimpleInteractionDynResource, SocialDynResource):
    """Slightly complicated dynamic resource due to the fact that when it is 
    associated with a User it is an interaction resource, enlisting items the 
    user has interacted with (favorited, in this case); whereas when it is 
    associated with a Cloudcast, it is a social resource, enlisting the users 
    connected to the cloudcast (those who have favorited, in this case). So this
    class inherits from both respective parent classes and based on the 
    arguments it is given on instantiation, uses the appropriate parent's 
    methods. That is, if it is only given the API object and a username, then it
    *behaves* as an interaction resource, otherwise as a social resource.
    
    (Shot myself in the foot, maybe...?!)"""
    def __init__(self, api, user, resource=None):
        if resource is None:
            # i.e. associated with a user
            SimpleInteractionDynResource.__init__(self, api)
            self.resource_key = [user, "favorites"]
        else:
            # i.e. associated with a cloudcast
            self.resource_key = [user, resource, "favorites"]
            SocialDynResource.__init__(self, api)
    
    def get_clean_data(self):
        if len(self.resource_key) == 2:
            # i.e. The case when the dyn resource is associated with a user and 
            # is therefore an interaction resource
            return SimpleInteractionDynResource.get_clean_data(self)
        else:
            # Otherwise, this dyn resource is associated with a cloudcast
            return SocialDynResource.get_clean_data(self)
            
        
class Listens(SimpleInteractionDynResource):
    def __init__(self, api, user):
        SimpleInteractionDynResource.__init__(self, api)
        self.resource_key = [user, "listens"]
    

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


class UserpickUsers(DynResource):
    def __init__(self, api, cat):
        DynResource.__init__(self, api)
        self.resource_key = [cat, "userpick-users"]


class UserpickCloudcasts(DynResource):
    def __init__(self, api, cat):
        DynResource.__init__(self, api)
        self.resource_key = [cat, "userpick-cloudcasts"]


################################################################################
## USABLE RESOURCES ############################################################
################################################################################

class User(InteractiveResource):
    def __init__(self, api, username, until=None):
        InteractiveResource.__init__(self, api, username, until)
        # Augment the User resource with dynamic resources further to those
        # inherited from InteractiveResource
        self.dyn_resources.update({
            "feed": Feed(api, username),
            "followers": Followers(api, username),
            "following": Following(api, username),
            "cloudcasts": Cloudcasts(api, username),
            "listens": Listens(api, username)
        })
        # for MongoDB's benefit, set _id field to username, which is unique
        self.data = {}
        self.data["_id"] = self.resource_key[0]
            
    def get_user_id(self):
        return self.get_field("_id")
    
    def get_followers(self):
        return self.get_field("followers")
    
    def get_following(self):
        return self.get_field("following")
    
    def get_favorites(self):
        return self.get_field("favorites")
    
    def get_cloudcasts(self):
        return self.get_field("cloudcasts")
    
    def get_cloudcast_slugs(self):
        return [item[""]]
    
    def get_listens(self):
        return self.get_field("listens")
    
    def get_favorited_users(self):
        return [item["user"] for item in self.get_field("favorites")]
    
    def get_listened_to_users(self):
        return [item["user"] for item in self.get_field("favorites")]
    
    def get_social_connections(self):
        return (self.get_followers() + self.get_following() +
                self.get_favorited_users() + self.get_listened_to_users())    

    
class Cloudcast(InteractiveResource):
    def __init__(self, api, username, cloudcast, until=None):
        InteractiveResource.__init__(self, api, username, cloudcast, until)
        self.dyn_resources.update({
            "similar": Similar(api, username, cloudcast),
            "listeners": Listeners(api, username, cloudcast)
        })


class Tag(AnnotationResource):
    def __init__(self, api, tag, until=None):
        AnnotationResource.__init__(self, api, "tag", tag, until)

       
class Artist(AnnotationResource):
    def __init__(self, api, artist, until=None):
        AnnotationResource.__init__(self, api, "artist", artist, until)


class Track(AnnotationResource):
    def __init__(self, api, artist, track, until=None):
        AnnotationResource.__init__(self, api, "track", artist, track, until)


class Category(CategoryResource):
    def __init__(self, api, cat, until=None):
        CategoryResource.__init__(self, api, cat, until)

        
