#!/usr/bin/env python

import dynamic_resources as dyn_rsrc

class _Resource():
    """Every API resource, base or dynamic, will have an associated API, a
    resource key to identify and access it, some parameters to pass via HTTP and
    its data.""" 
    def __init__(self, api):
        self.api = api
        self.resource_key = []
        self.resource_params = {}
        self.data = None
    
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

class BaseResource(_Resource):
    """Base resources have one thing in common: we want their metadata, which 
    are links to the dynamic resources. See dynamic_resource_type.py."""
    def __init__(self, api):
        _Resource.__init__(self, api)
        self.resource_params = {"metadata": 1}
        self.dyn_resources = {}
        
    def populate(self):
        """FOR CHILDREN TO IMPLEMENT:Run this after initialising an instance to
         gather all relevant data."""

        pass
#        self.fetch_data()
#        self.populate_metaconns()

    def populate_metaconns(self):
        """Fetch the relevant dynamic resources and store them. Beware of 
        fetch_data()'s overwriting!"""
        for conn in self.api.metaconns_whitelist:
            if conn in self.dyn_resources.keys():
                conn_data = self.get_metaconn(conn)
                self.data[conn] = conn_data
        
    def get_metaconn(self, metaconn):
        """Fetch the clean (relevant) data for a particular dynamic resource 
        and return it."""
        if metaconn in self.dyn_resources.keys():
            return self.dyn_resources[metaconn].get_clean_data()
                 

class InteractiveResource(BaseResource):
    """The User and Cloudcast resources are this class's children, as they have
    the "comments" and "favorites" dynamic resources in common."""
    def __init__(self, api, user, resource=None):
        BaseResource.__init__(self, api)
        self.resource_key.append(user)
        if resource: 
            self.resource_key.append(resource)
        self.dyn_resources = {
                "comments": dyn_rsrc.Comments(user, resource),
                "favorites": dyn_rsrc.Favorites(user, resource)
            }
        
class AnnotationResource(BaseResource):
    """The Tag, Artist and Track resources are this class's children, as they have
    the "popular" and "new" dynamic resources in common."""
    def __init__(self, api, resource1, resource2=None):
        BaseResource.__init__(self, api)
        self.resource_key.append(resource1)
        if resource2: 
            self.resource_key.append(resource2)
        self.dyn_resources = {
            "popular": dyn_rsrc.Popular(resource),
            "new": dyn_rsrc.New(resource)
        }
        
class CategoryResource(BaseResource):
    """Category resources are unique in their metadata's dynamic resources,
    so this class is only inherited by the Category resource."""
    def __init__(self, api, resource):
        BaseResource.__init__(self, api)
        self.resource_key.append(resource)
        self.dyn_resources = {
            "cloudcasts": dyn_rsrc.Cloudcasts(resource),
            "users": dyn_rsrc.Users(resource),
            "userpick_cloudcasts": dyn_rsrc.Userpick_cloudcasts(resource),
            "userpick_users": dyn_rsrc.Userpick_users(resource),
        }

