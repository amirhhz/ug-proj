#!/usr/bin/env python
from mixcloud import User, MixcloudAPI, MixcloudAPIException
from resurrect_settings import MONGO_DB, UNTIL_TIME

class Resurrection:
    """This class handles the problem of missing users in the dataset. It is 
    initialised with an "until" time which specifies the date that the said 
    dataset was obtained so that only information about the users up to that 
    point in time are obtained."""
    def __init__(self, until=UNTIL_TIME):
        self.until = until 
        self.api = MixcloudAPI()
        # set a new whitelist without social connections which I am rebuilding
        # from the rest of the dataset
        self.api.set_metaconns_whitelist("cloudcasts", "favorites", "listens")

        self.collection = MONGO_DB.user
        self.dead_users = []
        self.resurrected = []
        
    def resurrect(self):
        self.dead_users = self.find_dead_users()
        while self.dead_users:
            name = self.dead_users.pop()
            print ":::" + name ###
            try:
                current_user = User(self.api, name, self.until)
                current_user.populate()                
                # Need to repopulate the social links so that they are 
                # consistent with the rest of dataset
                current_user.data["followers"] = []
                current_user.data["following"] = []
                self.fix_connections(current_user)
                print "Social connections fixed ..."
                
                self.collection.save(current_user.get_data(), safe=True)
                self.resurrected.append(current_user.get_user_id())
            except Exception, e:
                print e
                raise e
            finally:
                self.flush()
            print ":::Resurrected " + name + "!"        
    
    def find_dead_users(self):
        cursor = self.collection.find({"username": {"$exists": False}})
        dead_users = [each["_id"] for each in cursor]
        return dead_users
    
    def fix_connections(self, user):
        name = user.get_user_id()
        followers_cursor = self.collection.find(spec={"following": name},
                                                fields=["_id"])
        user.data["followers"] = [each["_id"] for each in followers_cursor]

        following_cursor = self.collection.find(spec={"followers": name},
                                                fields=["_id"])
        user.data["following"] = [each["_id"] for each in following_cursor]
        
        # Correct all the counts for the truncated time period
        user.data["following_count"] = len(user.data["following"])
        user.data["follower_count"] = len(user.data["followers"])
        user.data["favorite_count"] = len(user.data["favorites"])
        user.data["cloudcast_count"] = len(user.data["cloudcasts"])
        
    def flush(self):
        from resurrect_settings import MONGO_CONNECTION
        admindb = MONGO_CONNECTION.admin
        admindb.command("fsync")


if __name__ == "__main__":
    import sys
    graveyard = Resurrection()
    try:
        graveyard.resurrect()
    except KeyboardInterrupt:
        sys.exit()
    except Exception, e:
        print e
    finally:
        graveyard.flush()
    
    
        