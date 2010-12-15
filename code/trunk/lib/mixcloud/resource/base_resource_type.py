#!/usr/bin/env python

import dynamic_resource_type as dyn_rsrc

class InteractiveResource():
    def __init__(self, user, resource=None):
        self.dyn_resources = {
                "comments": dyn_rsrc.Comments(user, resource),
                "favorites": dyn_rsrc.Favorites(user, resource)
            }
           
        
class AnnotationResource():
    def __init__(self, resource):
        self.dyn_resources = {
            "popular": dyn_rsrc.Popular(resource),
            "new": dyn_rsrc.New(resource)
        }
        
class CategoryResource():
    def __init__(self, resource):
        self.dyn_resources = {
            "cloudcasts": dyn_rsrc.Cloudcasts(resource),
            "users": dyn_rsrc.Users(resource),
            "userpick_cloudcasts": dyn_rsrc.Userpick_cloudcasts(resource),
            "userpick_users": dyn_rsrc.Userpick_users(resource),
        }

