from typing import Iterator, Sequence, Set

import pytest

# noinspection PyProtectedMember
from chemfish.core._tools import *


class TestValarTools:
    """ """
    def test_all_or_none_are_none(self):
        """ """
        assert not InternalTools.all_or_none_are_none([1, 1], None)
        assert InternalTools.all_or_none_are_none([None, None], None)
        assert InternalTools.all_or_none_are_none([0, None], None) is None

    def test_all_or_none_are_true(self):
        """ """
        assert InternalTools.all_or_none_are_true([1, 1], None)
        assert not InternalTools.all_or_none_are_true([0, 0], None)
        assert InternalTools.all_or_none_are_true([0, 1], None) is None


if __name__ == "__main__":
    pytest.main()
