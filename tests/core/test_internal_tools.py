import pytest
from typing import Iterator, Sequence, Set

# noinspection PyProtectedMember
from chemfish.core._tools import *


class TestValarToolsMethodSetUpRequired:
    """
    Tests for InternalTools.
    When running from PyCharm, set the environment variable VALARPY_CONFIG to one for the test database.
    VALARPY_CONFIG=VALARPY_TESTDB_CONFIG
    You can do that in Run...Edit Configuration.
    """

    def test_all_or_none_are_none(self):
        assert not InternalTools.all_or_none_are_none([1, 1], None)
        assert InternalTools.all_or_none_are_none([None, None], None)
        assert InternalTools.all_or_none_are_none([0, None], None) is None

    def test_all_or_none_are_true(self):
        assert InternalTools.all_or_none_are_true([1, 1], None)
        assert not InternalTools.all_or_none_are_true([0, 0], None)
        assert InternalTools.all_or_none_are_true([0, 1], None) is None

if __name__ == "__main__":
    pytest.main()
