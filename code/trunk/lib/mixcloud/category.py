#!/usr/bin/env python

from httplib import HTTPException

from api import MetaConnection
from api import MixcloudAPIException
from resource.base_resource_type import CategoryResource
import resource.dynamic_resource_type as dyn_rsrc

class Category(CategoryResource):
    def __init__(self, cat, api):
        CategoryResource.__init__(cat)
        self.api = api
        
