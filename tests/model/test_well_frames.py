import os
from pathlib import Path

import hypothesis.strategies as strategies
import numpy as np
import pandas as pd
import pytest
from hypothesis import given
from hypothesis.extra.numpy import arrays

from chemfish.model.wf_builders import *


def float_or_string(draw):
    """
    Helper function that either returns an integer of string strategy. Used to create 'mixed' index column values.
    """
    fs = draw(strategies.booleans())
    if fs:
        return strategies.integers(min_value=0, max_value=100)
    else:
        return strategies.from_regex(r"^[a-zA-Z]+$")


@strategies.composite
def wf_strategy(draw):
    """
    Creates a list of parameters that can be used to create a WellFrame filled with dummy data.
    """
    rows = draw(strategies.integers(min_value=1, max_value=20))
    cols = draw(strategies.integers(min_value=1, max_value=20))
    num_names = draw(strategies.integers(min_value=1, max_value=10))
    names = draw(
        strategies.lists(
            strategies.from_regex(r"^[a-zA-Z]+$"),
            min_size=num_names - 1,
            max_size=num_names - 1,
            unique=True,
        )
    )
    index_arrays = draw(
        strategies.lists(
            strategies.lists(float_or_string(draw), min_size=rows, max_size=rows),
            min_size=num_names,
            max_size=num_names,
        )
    )
    data = draw(
        arrays(dtype=np.dtype("float"), shape=(rows, cols), elements=strategies.floats(0, 256))
    )
    return [index_arrays, names, data]


class TestWellFrames:
    def __init__(self):
        self.reg_wf = None

    def setUp(self) -> None:
        """
        Sets up WellFrame to use in tests.
        """
        self.reg_wf = WellFrameBuilder.wells([1, 2, 3, 4]).with_feature("MI").build()

    def test_well_frames_basic(self):
        """
        Tests WellFrame constructor and get_item method.
        """
        empty_wf = WellFrame()
        wf_two = self.reg_wf[self.reg_wf["name"] == "2"]
        feat_five = self.reg_wf[list(range(0, 5))]
        assert isinstance(empty_wf, WellFrame)
        assert set(self.reg_wf["name"]) == {"1", "2", "3", "4"}
        assert isinstance(wf_two, WellFrame)
        assert set(wf_two["name"]) == {"2"}
        assert isinstance(feat_five, WellFrame)
        assert set(feat_five.columns) == {0, 1, 2, 3, 4}

    def test_astype(self):
        """
        Tests as_type method. Makes sure it creates a new view and that only the feature columns are affected.
        """
        self.reg_wf = WellFrameBuilder.wells([1, 2, 3, 4]).with_feature("MI").build()
        copy_reg_wf = self.reg_wf.copy(deep=True)
        int_wf = self.reg_wf.astype(np.dtype(np.int32))
        assert set(self.reg_wf.dtypes) == {np.dtype(np.float64)}
        assert set(int_wf.dtypes) == {np.dtype(np.int32)}
        assert self.reg_wf.equals(
            copy_reg_wf
        ), "The astype method should not modify the wellframe in place."
        assert self.reg_wf.index.equals(
            int_wf.index
        ), "The meta index columns of the original WellFrame must be identical to the meta index columns of the wellframe returned by astype."
        assert np.array_equal(self.reg_wf.values, int_wf.values)
        assert self.reg_wf.columns.equals(
            int_wf.columns
        ), "The Feature Column names should be untouched in the returned WellFrame."
        with pytest.raises(ValueError):
            WellFrame().astype()

    def test_features_only(self):
        """
        Tests features_only method.
        """
        feats_wf = self.reg_wf
        feats_two_meta_wf = self.reg_wf.features_only(["well", "name"])
        copy_reg_wf = self.reg_wf.copy(deep=True)
        assert (
            copy_reg_wf.shape == feats_wf.shape
        ), "The shape of the WellFrame returned should be identical to the original WellFrame. Expected: {} Actual: {} ".format(
            copy_reg_wf.shape, feats_wf.shape
        )
        assert (
            feats_wf.index.name == "name"
        ), "The returned WellFrame should only have one name and not be a multi-index."
        assert set(feats_two_meta_wf.index.names) == {
            "name",
            "well",
        }, "Incorrect meta_columns returned. Expected: {} Actual: {} ".format(
            {"name", "well"}, set(feats_two_meta_wf.index.names)
        )
        assert np.array_equal(
            feats_wf.values, copy_reg_wf.values
        ), "The returned WellFrame should have all the feature columns of the original WellFrame."
        assert self.reg_wf.equals(
            copy_reg_wf
        ), "The original WellFrame should not be modified in place."
        assert isinstance(feats_wf, WellFrame), "Features_only should return a WellFrame instance."
        with pytest.raises(ValueError):
            WellFrame()


class TestWellFramesHDF:
    def __init__(self):
        self.hdf_path = None

    def setUp(self) -> None:
        """
        Setup to create hdf path file. This is used so that the tearDown method can be used.
        """
        self.hdf_path = Path("wf.h5")

    @given(wf_strategy())
    def test_to_hdf_and_read_hdf(self, data):
        """
        Tests invariant involving to_hdf and read_hdf methods. Converting a WellFrame with to_hdf and then reading that
        hdf should return the WellFrame you started with.
        """
        if (
            len(data[0]) > 1
        ):  # MultiIndex should only be created when there are multiple index columnds generated.
            wf_index = pd.MultiIndex.from_arrays(data[0], names=(["name"] + data[1]))
        else:
            wf_index = pd.Index(data[0][0], name="name")
        wf = WellFrame(index=wf_index, columns=range(data[2].shape[1]), data=data[2])
        wf.to_hdf(path=self.hdf_path, key="s")
        assert WellFrame.read_hdf(self.hdf_path, key="s").equals(wf)
        with pytest.raises(ValueError):
            # noinspection PyTypeChecker
            WellFrame().to_hdf(path=None)
        with pytest.raises(ValueError):
            # noinspection PyTypeChecker
            WellFrame().read_hdf(path=None)

    def tearDown(self) -> None:
        """
        This method is called after the test is run even if it fails. This can only be called if setUp succeeds.
        """
        if self.hdf_path.exists():
            self.hdf_path.unlink()
        os.remove(self.hdf_path)


if __name__ == "__main__":
    pytest.main()
