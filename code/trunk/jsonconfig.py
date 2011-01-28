#!/usr/bin/env python
"""Simple wrapper to read and write configuration files."""
import json

class JSONConfig(object):
    def __init__(self, filename=None):
        if filename:
            self.read_conf(filename)
    
    def read_conf(self, filename):
        with open(filename, "r") as conf:
            self._data = json.load(conf)
    
    def write_conf(self, filename):
        with open(filename, "w") as conf:
            json.dump(self._data, conf, indent=2)


class MongoConfig(JSONConfig):
    def __init__(self, filename=None):
        JSONConfig.__init__(self, filename)
        

class RedisConfig(JSONConfig):
    def __init__(self, filename=None):
        JSONConfig.__init__(self, filename)


class ScrubberConfig(JSONConfig):
    def __init__(self, filename=None):
        JSONConfig.__init__(self, filename)
        

class RecommenderConfig(JSONConfig):
    def __init__(self, filename=None):
        JSONConfig.__init__(self, filename)
        

class StatsConfig(JSONConfig):
    def __init__(self, filename=None):
        JSONConfig.__init__(self, filename)


class CrawlerConfig(JSONConfig):
    def __init__(self, filename=None):
        JSONConfig.__init__(self, filename)
