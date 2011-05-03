# Intended for testing with "nosetests"

import unittest
import json
from mongomix import MixcloudDataset, MixcloudUser
from subprocess import Popen


test_data = """
"""
with open("team.json", "r") as team_data:
    test_data = json.load(team_data)


def setup_module():
    pass

def teardown_module():
    pass


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
