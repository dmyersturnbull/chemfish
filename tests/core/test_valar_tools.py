from datetime import datetime

import pytest

from chemfish.core.valar_singleton import *
from chemfish.core.valar_tools import *


class TestValarTools:
    """Tests for ValarTools."""

    def test_run_wrong_param(self):
        """Tests that run method responds properly when nonexistent ID/name/tag/sub_hash is given."""
        with pytest.raises(ValarLookupError):
            ValarTools.run(599999)
        with pytest.raises(ValarLookupError):
            ValarTools.run(-1)
        with pytest.raises(ValarLookupError):
            ValarTools.run("000000000000")
        with pytest.raises(ValarLookupError):
            ValarTools.run("non_existent_run")
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            ValarTools.run({1: 4})

    def test_sensors_on(self):
        """Tests if sensors_on returns all sensors for a valid run."""
        fake_set = {str(s) for s in ValarTools.sensors_on(self.fake_run)}
        empty_set = {str(s) for s in ValarTools.sensors_on(3)}
        valid_set = {str(s) for s in ValarTools.sensors_on(1)}
        expected_valid = {i.sensor.name for i in SensorData.select().where(SensorData.run == 1)}
        assert not fake_set
        assert not empty_set
        assert expected_valid == valid_set

    def test_features_on(self):
        """Tests if features_on returns all features for a valid run."""
        fake_set = ValarTools.features_on(self.fake_run)
        empty_set = ValarTools.features_on(3)
        valid_set = ValarTools.features_on(1)
        expected_valid = {WellFeatures.select().where(WellFeatures.well_id == 1).first().type.name}
        assert not empty_set
        assert not fake_set
        assert expected_valid == valid_set


class TestValarToolsMethodNoSetUp:
    """ """

    def test_looks_like_submission_hash(self):
        """Tests that only 12 digit hex strings return true for looks_like_submission_hash method"""
        f = ValarTools.looks_like_submission_hash
        assert not f("aef1234")
        assert not f("12334560402249")
        assert f("abc123def456")
        assert f("abcabcabcabc")
        assert f("012345678912")
        assert not f("123zxc134cvp")
        assert not f("zxv345604022492")
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            f(123456789120)

    def test_run_tag(self):
        """Tests that run_tag method returns tag value for given run id and tag name or raises ValarLookupError."""
        run_id_value = ValarTools.run_tag(1, "first run tag")
        actual_value = "0123456789"
        assert run_id_value == actual_value
        with pytest.raises(ValarLookupError):
            ValarTools.run_tag(1, "tag no exist")
        with pytest.raises(ValarLookupError):
            ValarTools.run_tag(100, "first run tag")

    def test_stimulus_display_name(self):
        """Tests stimulus_display_name."""
        f = ValarTools.stimulus_display_name
        with pytest.raises(ValarLookupError):
            f("badjfbdkf")
        assert f("black LED") == "black (0nm)"
        assert f(1) == "black (0nm)"

    def test_run(self):
        """
        Tests that the runs fetched by a run's id, the same run's unique tag, the same run's name,
        and the same run's submission hash are identical.
        """
        id_run = ValarTools.run(2)
        tag_run = ValarTools.run("unique tag")
        name_run = ValarTools.run("run_number_two")
        hash_run = ValarTools.run("dbc6e959a22e")
        assert id_run == tag_run
        assert name_run == tag_run
        assert hash_run == tag_run
        assert hash_run == name_run
        assert id_run == hash_run
        assert id_run == name_run

    def test_runs(self):
        """
        Tests that an iterable of the correct runs are fetched
        in correct order.
        """
        r1_id = 1
        r2_name = "run_number_three"
        r3_tag = "unique tag"
        r4_hash = "5abbff3cdae1"
        runs_list = ValarTools.runs(iter([r1_id, r2_name, r3_tag, r4_hash]))
        assert len(runs_list) == 4
        assert ValarTools.run(r1_id) == runs_list[0]
        assert ValarTools.run(r2_name) == runs_list[1]
        assert ValarTools.run(r3_tag) == runs_list[2]
        assert ValarTools.run(r4_hash) == runs_list[3]

    def test_assay_name_simplifier(self):
        """Tests that assay_name_simplifier returns the simplified strings."""
        ays = ValarTools.assay_name_simplifier()
        test_strings = [
            "assay",
            "legacy-run1",
            "run1-legacy-run1",
            "sys :: light :: assay3",
            "sys :: sound :: assay4",
            "sauronx-legacy-assay",
            "#legacy: -(variant:testuser)assay1",
            "legacy-sys :: light :: sys :: light+sound :: ",
            "sys :: taps :: flame :: sys :: new :: assay1",
            "assay2-test_user-2019-04-30-0xabcd",
            "assay_background:$length=500",
        ]
        actual_results = [
            "assay",
            "run1",
            "run1-run1",
            "assay3",
            "assay4",
            "assay",
            "assay1",
            "",
            "assay1",
            "assay2",
            "assay_background=500",
        ]
        assert actual_results == [ays(assay_name) for assay_name in test_strings]

    def test_parse_param_value(self):
        """Tests that the parse_param_value method responds appropriately to different user inputs."""
        with pytest.raises(ValarLookupError):
            # Existent submission hash and nonexistent param name
            ValarTools.parse_param_value("5abbff3cdae1", "hello")
        with pytest.raises(ValarLookupError):
            # Nonexistent submission hash and nonexistent param name
            ValarTools.parse_param_value("5abbff31234", "hello")
        with pytest.raises(ValarLookupError):
            # Variant in submissions param does not exist in genetic variants table.
            ValarTools.parse_param_value("dbc6e959a22e", "submission_param_2_5")
        param_nfish = ValarTools.parse_param_value("5abbff3cdae1", "submission_param_1_1")
        param_group = ValarTools.parse_param_value("5abbff3cdae1", "submission_param_1_7")
        param_group_list = ValarTools.parse_param_value("dbc6e959a22e", "submission_param_2_4")
        param_variant = ValarTools.parse_param_value("1a53c81bcde9", "submission_param_3_1")
        param_variant_list = ValarTools.parse_param_value("5abbff3cdae1", "submission_param_1_5")
        param_dose_int = ValarTools.parse_param_value("1a53c81bcde9", "dose_sp_3_1")
        param_dose = ValarTools.parse_param_value("edd9618f104a", "dose_sp_25_1")
        param_batch = ValarTools.parse_param_value("1a53c81bcde9", "submission_param_3_2")
        check_variant = GeneticVariants.fetch("genetic variant four")
        check_variant_list = [
            GeneticVariants.fetch("genetic variant two"),
            GeneticVariants.fetch("genetic variant three"),
        ]
        assert param_nfish == 14
        assert param_group == "group_one"
        assert param_group_list == ["group_one", "group_two"]
        assert check_variant == param_variant
        assert check_variant_list == param_variant_list
        assert param_dose_int == 100.0
        assert param_dose == 100.0
        assert Batches.fetch("5abbff3cdae1ab") == param_batch

    def test_library_plate_id(self):
        """Tests that library plate ids are properly returned for both the new and old style submissions."""
        f = ValarTools.library_plate_id_of_submission
        with pytest.raises(ValarLookupError):
            f("abcabcabcabccd", "$...AB123")
        with pytest.raises(ValarLookupError):
            f("1a53c81bcde9", "$...BB123")
        with pytest.raises(ValarLookupError):
            f("edd9618f104a", None)
        with pytest.raises(ValarLookupError):
            # Legacy internal id is in wrong format.
            f("dbc6e959a22e", "$...BC123")
        with pytest.raises(AssertionError):
            # submission param value corresponds to number
            f("5abbff3cdae1", "submission_param_1_1")
        corr_no_name = f("1a53c81bcde9", None)
        corr_new_lib = f("1a53c81bcde9", "$...AB123")
        corr_old_lib = f("dbc6e959a22e", "$...BC1234")
        assert "PR00010" == corr_new_lib == corr_no_name
        assert "AB01244" == corr_old_lib

    def test_all_plates_ids_of_library(self):
        """Tests that all_plates_ids_of_library returns all the batches of a library."""
        f = ValarTools.all_plates_ids_of_library
        with pytest.raises(ValarLookupError):
            f(6)  # nonexistent ref
        all_plates = f(1)
        expected_set = {"AB01244", "BC00004"}
        assert all_plates == expected_set
        # ref exists but no batches refer to it
        assert not f(2)

    def test_assay_is_background(self):
        """Tests assay_is_background."""
        f = ValarTools.assay_is_background
        with pytest.raises(ValarLookupError):
            f(1000)
        assert not f(1)  # Assay has stimulus frames but not background stimulus.
        assert f(3)  # Assay has no stimulus frames associated with it (only background present)
        assert f(4)  # Assay has stimulus frame with stimulus 'none'.
        assert not f(5)  # Assay has stimulus frame with stimulus 'none' and some other stimulus.


if __name__ == "__main__":
    pytest.main()
