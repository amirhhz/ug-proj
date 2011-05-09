# Intended for testing with "nosetests"

import unittest
import json
from mongomix import MixcloudDataset, MixcloudUser, MixcloudUserDiff
from subprocess import Popen


test_data = {}
datasets = {}

def setup_module():
    test_data = {
        1: json.load(open("team.1.json", "r")),
        2: json.load(open("team.2.json", "r"))
    }

    datasets = {
        1: MixcloudDataset(db="test", collection="ds1"),
        2: MixcloudDataset(db="test", collection="ds2")
    }

    for x in (1, 2):
        datasets[x].collection.drop()
        datasets[x].collection.insert(test_data[x].values())


def teardown_module():
    for x in (1, 2):
        datasets[x].collection.drop()


class TestMixcloudUserDiff(unittest.TestCase):
    def setUp(self):
        rez1 = datasets[1].get_user("rez")
        rez2 = datasets[2].get_user("rez")
        rez_diff = MixcloudUserDiff(rez1, rez2)

    def test_follower_diff(self):
        pass

    def test_following_diff(self):
        pass

    def test_favorites_diff(self):
        pass

    def test_listens_diff(self):
        pass

    def tearDown(self):
        return


class TestMixcloudDataset(unittest.TestCase):
    def setUp(self):
        return

    def test_get_user(self):
        pass

    def test_save_user(self):
        pass

    def test_add_follow(self):
        pass

    def test_remove_follow(self):
        pass

    def test_soc_net(self):
        pass

    def tearDown(self):
        return


class TestMixcloudUser(unittest.TestCase):
    pass


class TestSimilarity(unittest.TestCase):
    pass


if __name__ == "__main__":
    pass
