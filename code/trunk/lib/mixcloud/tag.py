#!/usr/bin/env python

from httplib import HTTPException

from api import MetaConnection
from api import MixcloudAPIException
from resource.base_resource_type import AnnotationResource
import resource.dynamic_resource_type as dyn_rsrc

class Tag(AnnotationResource):
    def __init__(self, tag, api):
        AnnotationResource.__init__(tag)
        self.api = api
