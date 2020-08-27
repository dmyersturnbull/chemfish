import os
from datetime import timedelta

import pytest
from pocketutils.core.exceptions import *

from chemfish.core.tools import *
from chemfish.core.valar_singleton import *
from chemfish.model.compound_names import *
from chemfish.model.treatment_names import *
from chemfish.model.well_names import *
from chemfish.model.wf_builders import *


class TestWellFrameBuilder:
    """Tests for WellFrameBuilder."""

    def __init__(self):
        self.fake_run = None
        self.fake_well = None

    @pytest.fixture(scope="class")
    def setup(self) -> None:
        """Set-up method that initializes a fake_run and fake_well for the following two tests cases."""
        self.fake_run = Runs()
        run_attributes = [
            "id",
            "experiment_id",
            "plate_id",
            "description",
            "experimentalist_id",
            "datetime_run",
            "sauron_config_id",
        ]
        run_values = [
            10000,
            3,
            5,
            10,
            "description_one",
            4,
            datetime.strptime("2019-05-26 11:12:17", "%Y-%m-%d %H:%M:%S"),
            3,
        ]
        for attr, val in zip(run_attributes, run_values):
            setattr(self.fake_run, attr, val)
        self.fake_well = Wells()
        fw_att = [
            "id",
            "run_id",
            "well_index",
            "control_type_id",
            "variant_id",
            "well_group",
            "n",
            "age",
        ]
        well_values = [10000, 100, 2, 1, 9, "fake_group", 1, 13]
        for attr, val in zip(fw_att, well_values):
            setattr(self.fake_well, attr, val)

    def test_wells(self):
        """Tests wells constructor method for WellFrameBuilder."""
        with pytest.raises(ValarLookupError):
            WellFrameBuilder.wells(10000000)  # fake id provided
        with pytest.raises(XTypeError):
            WellFrameBuilder.wells(self.fake_run)  # fake run provided
        with pytest.raises(ValarTableTypeError):
            WellFrameBuilder.wells([self.fake_run, self.fake_run])  # list of fake runs
        with pytest.raises(ValarLookupError):
            WellFrameBuilder.wells(self.fake_well).build()  # Nonexistent Well provided
        use_wells_list = [
            Wells.select().where(Wells.id == 1).first(),
            4,
        ]  # WellFrame with Well id : 1 , 4
        one_well_wf_ids = set(
            WellFrameBuilder.wells(1).build()["well"]
        )  # Well IDs of WellFrame with just one well
        assert one_well_wf_ids == {1}
        wells_wf_ids = set(
            WellFrameBuilder.wells(use_wells_list).build()["well"]
        )  # Well IDs of WellFrame with list of wells
        assert wells_wf_ids == {1, 4}

    def test_runs(self):
        """Tests runs constructor method method for WellFrameBuilder."""
        with pytest.raises(ValarLookupError):
            WellFrameBuilder.runs(100000)  # Nonexistent Run ID
        with pytest.raises(XTypeError):
            WellFrameBuilder.runs(self.fake_well)  # Well instance that is not in chemfishtest db
        with pytest.raises(ValarTableTypeError):
            WellFrameBuilder.runs([self.fake_well, self.fake_well])  # List of well Instances
        with pytest.raises(ValarLookupError):
            WellFrameBuilder.runs(
                self.fake_run
            ).build()  # Run instance that is not in chemfishtest db
        rl = [Runs.select().where(Runs.id == 1).first(), 3]
        one_run_wells = {
            w.id for w in Wells.select().where(Wells.run == 1)
        }  # All well IDs associated with Run 1
        runs_list_wells = {
            w.id for w in Wells.select().where((Wells.run == rl[0].id) | (Wells.run == rl[1]))
        }  # All Well IDs associated with Run 1
        one_run_wf_ids = set(
            WellFrameBuilder.runs(1).build()["well"]
        )  # Well IDs of WellFrame that contains Wells associated with Run 1 (Uses .runs)
        runs_list_wf_ids = set(
            WellFrameBuilder.runs(rl).build()["well"]
        )  # Well IDs of WellFrame that contains Wells associated with Runs in rl
        wells_wf_ids = set(
            WellFrameBuilder.wells(one_run_wells).build()["well"]
        )  # Well IDs of WellFrame that contains Wells associated with Run 1 (Uses .wells)
        assert one_run_wf_ids == one_run_wells
        assert runs_list_wf_ids == runs_list_wells
        assert wells_wf_ids == one_run_wf_ids


class TestWellFrameBuilderNoSetUp:
    """ """

    def test_constructor(self):
        """Tests datetime constructor for WellFrameBuilder."""
        past_time = datetime.now() - timedelta(minutes=1)
        dt_wf_well_ids = set(WellFrameBuilder(past_time).build()["well"])
        dt_wells_ids = {w.id for w in Wells.select().where(Wells.created < past_time)}
        assert (
            dt_wf_well_ids == dt_wells_ids
        )  # Datetime wellframe should return all objects before given time.
        assert (
            WellFrameBuilder(None) is not None
        )  # Even with no datetime wellframe object should be returned.
        # TODO warn
        # with pytest.raises(RefusingRequestError):
        #     WellFrameBuilder(datetime.now())

    def test_where(self):
        """Tests where method for WellFrameBuilder."""
        wf_runs_where = (
            WellFrameBuilder.runs(1).where(Wells.id == 1).build()
        )  # WF retrieved by runs conditioned on where
        wf_wells = WellFrameBuilder.wells(1).build()  # WF retrieved by wells with ID 1
        wf_sup_where = (
            WellFrameBuilder.runs(1).where(Suppliers.description == "good supplier").build()
        )
        wf_sup_ex_where = (
            WellFrameBuilder.runs(1).where(Suppliers.description == "good supplier").build()
        )
        wf_two_wheres = (
            WellFrameBuilder.runs(1)
            .where(Wells.well_group == "well group one")
            .where(ControlTypes.id == 2)
            .build()
        )  # Multiple wheres should work.
        assert wf_runs_where == wf_wells
        assert list(wf_two_wheres["well_group"]) == ["well group one", "well group one"]
        assert list(wf_two_wheres["control_type_id"]) == [2, 2]
        with pytest.raises(ValarLookupError):
            WellFrameBuilder.runs(1).where(Wells.id == -10).build()
        assert wf_sup_ex_where.equals(wf_sup_where)

    def test_with_feature(self):
        """Tests with_feature method for WellFrameBuilder."""
        wf_runs_none = WellFrameBuilder.runs(1).with_feature(None).build()
        wf_runs = WellFrameBuilder.runs(1).build()
        act_well_one = (
            WellFrameBuilder.wells(1).with_feature("MI").build().values[0][1:]
        )  # exclude first element because default sets it to zero.
        exp_well_one = Tools.blob_to_signed_floats(
            WellFeatures.select().where(WellFeatures.id == 1).first().floats
        )[
            1:
        ]  # exclude first element because default sets it to zero.
        assert exp_well_one == act_well_one
        assert wf_runs.equals(wf_runs_none)
        with pytest.raises(ValarLookupError):
            WellFrameBuilder.runs(1).with_feature("Nonexistent Feature").build()
        with pytest.raises(ContradictoryRequestError):
            WellFrameBuilder.runs(1).with_feature("MI").with_feature(
                "cd(10)"
            )  # Can only have one feature at a time

    def test_with_column(self):
        """Tests with_column method for WellFrameBuilder."""
        expected_tup = ("good supplier", "good supplier", "good supplier", "good supplier")
        ex_wf = (
            WellFrameBuilder.wells(1)
            .with_column(
                "supplier_description",
                lambda w, ts: tuple(t.batch.supplier.description for t in ts),
            )
            .build()
        )
        reg_wf = (
            WellFrameBuilder.wells(1)
            .with_column(
                "supplier_description",
                lambda w, ts: tuple(t.batch.supplier.description for t in ts),
            )
            .build()
        )
        assert ex_wf["supplier_description"][0] == expected_tup
        assert None in reg_wf["supplier_description"][0]
        with pytest.raises(ReservedError):
            WellFrameBuilder.wells(1).with_column(
                "name", lambda w, ts: tuple(t.batch.supplier.description for t in ts)
            ).build()
        with pytest.raises(ReservedError):
            WellFrameBuilder.wells(1).with_column(
                "well", lambda w, ts: tuple(t.batch.supplier.description for t in ts)
            ).build()
        with pytest.raises(XTypeError):
            # noinspection PyTypeChecker
            WellFrameBuilder.wells(1).with_column(
                123513515145, lambda w, ts: tuple(t.batch.supplier.description for t in ts)
            ).build()

    def test_with_names(self):
        """Tests with_names method for WellFrameBuilder. Very simple. Just checks that the name column has expected name values."""
        with pytest.raises(XTypeError):
            # noinspection PyTypeChecker
            WellFrameBuilder.runs(1).with_names("hello").build()
        reg_df = WellFrameBuilder.wells(1).build()
        namer = (
            WellNamerBuilder()
            .text("be warned! ", if_missing_col="control_type")
            .column("control_type", suffix="; ")
            .treatments(displayer=StringTreatmentNamer("c${cid} (${um}µM)"))
            .build()
        )
        named_wf = WellFrameBuilder.wells(1).with_names(namer).build()
        assert list(namer(reg_df)) == list(named_wf["name"])

    def test_with_empty_display_names(self):
        """Tests that the display_names are just the names if no display_namer is set."""
        reg_df = WellFrameBuilder.wells(1).build()
        namer = (
            WellNamerBuilder()
            .text("be warned! ", if_missing_col="control_type")
            .column("control_type", suffix="; ")
            .treatments(displayer=StringTreatmentNamer("c${cid} (${um}µM)"))
            .build()
        )
        named_wf = WellFrameBuilder.wells(1).with_names(namer).build()
        assert list(namer(reg_df)) == list(named_wf["display_name"])

    def test_with_display_names(self):
        """Tests with_display_names method for WellFrameBuilder. Very simple. Just checks that the name column has expected values."""
        with pytest.raises(XTypeError):
            # noinspection PyTypeChecker
            WellFrameBuilder.runs(1).with_display_names("hello").build()
        reg_df = WellFrameBuilder.wells(1).build()
        namer = (
            WellNamerBuilder()
            .text("be warned! ", if_missing_col="control_type")
            .column("control_type", suffix="; ")
            .treatments(displayer=StringTreatmentNamer("c${cid} (${um}µM)"))
            .build()
        )
        named_wf = WellFrameBuilder.wells(1).with_display_names(namer).build()
        assert namer(reg_df) == list(named_wf["display_name"])

    def test_with_packs(self):
        """Tests with_packs method for WellFrameBuilder. Very simple. Just checks that the pack column has expected pack values."""
        with pytest.raises(XTypeError):
            # noinspection PyTypeChecker
            WellFrameBuilder.runs(1).with_packs("hello").build()

        def pack_func(df):
            """


            Args:
              df:

            Returns:

            """
            return "pack" + df["row"].astype(str)

        reg_df = WellFrameBuilder.wells(1).build()
        pack_wf = WellFrameBuilder.wells(1).with_packs(pack_func).build()
        assert list(pack_wf["pack"]) == list(pack_func(reg_df))

    def test_with_compound_names(self):
        """Tests with_compound_names for WellFrameBuilder. Very simple. Just checks that the compound_name column has expected compound_name values."""
        with pytest.raises(XTypeError):
            # noinspection PyTypeChecker
            WellFrameBuilder.runs(1).with_compound_names("hello").build()
        # TODO chris, did I break this? --Douglas
        comp_df = WellFrameBuilder.wells(1).with_compound_names(CompoundNamers.tiered()).build()
        assert comp_df["compound_names"][0] == ("compound_one",)

    def test_build(self):
        """Tests build method for WellFrameBuilder. Makes sure no NaN values are returned."""
        no_nan_wfs = WellFrameBuilder.runs(
            1
        ).build()  # Should not contain any NaNs as all fields are populated correctly in chemfishtest for Run 1.
        nan_val = float("nan")
        for i in no_nan_wfs.index.names:
            assert nan_val not in no_nan_wfs[i]
        assert isinstance(no_nan_wfs, WellFrame)


if __name__ == "__main__":
    pytest.main()
