import pytest
from chemfish.core.environment import *


class TestEnvironmentSetUpRequired:
    """
    Tests for KaleEnvironment.
    When running from PyCharm, set the environment variable VALARPY_CONFIG to one for the test database.
    VALARPY_CONFIG=VALARPY_TESTDB_CONFIG
    You can do that in Run...Edit Configuration.
    """

    def test_load(self):
        # TODO
        env = KaleEnvironment()
