#!/usr/bin/env python

### API settings ###

DEBUG = True

DEFAULT_API = "http://api.mixcloud.com"

# words used in resource keys of "metadata connections" on mixcloud
METACONNS = [
    "comments","favourites","followers","following","listens", "cloudcasts",
    "similar", "popular", "new", "users", "listeners",
    "userpick-users", "userpick-cloudcasts"
]

DEFAULT_METACONNS_WHITELIST = [
                               "cloudcasts", 
                               "followers", 
                               "following", 
                               "favorites", 
                               "listens"
                               ]
DEFAULT_METACONNS_BLACKLIST = [
                               "comments", 
                               "feed", 
                               "similar", 
                               "listeners"
                               ]

RESPECT_TIME = 0.2 #in seconds

CATEGORIES = [
    "business", "comedy", "culture", "drum-and-bass", "dubstep-bass",
    "education", "electronica", "funk-soul", "hip-hop", "indie", "jazz-ambient",
    "news", "mix-series", "politics", "reggae-dancehall", "sport", "techno",
    "technology", "world"
    ]

SEARCH_TYPES = ["cloudcast", "user", "tag", "artist", "track"]

ANNOTATION_TYPES = ["tag", "artist", "track"] 

ITEMS_PER_PAGE = 100