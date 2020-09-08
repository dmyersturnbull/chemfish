from __future__ import annotations

from chemfish.core.core_imports import *

from .treatments import Treatment, Treatments


def _w(attrs: str):
    """


    Args:
        attrs: str:

    Returns:

    """
    return lambda w, ts: Tools.look(w, attrs)


def _r(attrs: str):
    """


    Args:
        attrs: str:

    Returns:

    """
    return lambda w, ts: Tools.look(w, "run." + attrs)


class WellFrameColumns:
    """
    The functions that are used to generate the WellFrame columns.
    """

    experiment_id = "experiment_id", _w("run.experiment.id")
    experiment_name = "experiment_name", _w("run.experiment.name")
    control_type = "control_type", _w("control_type.name")
    control_type_id = "control_type_id", _w("control_type.id")
    well = "well", _w("id")
    index = "well_index", _w("well_index")
    row = "row", lambda w, ts: (w.well_index - 1) // w.run.plate.plate_type.n_columns + 1
    column = "column", lambda w, ts: (w.well_index - 1) % w.run.plate.plate_type.n_columns + 1
    well_label = (
        "well_label",
        lambda w, ts: WB1(
            w.run.plate.plate_type.n_rows, w.run.plate.plate_type.n_columns
        ).index_to_label(w.well_index),
    )
    run = "run", _r("id")
    tag = "tag", _r("tag")
    run_description = "run_description", _r("description")
    submission = "submission", _r("submission.lookup_hash")
    physical_plate = "physical_plate", _r("plate.id")
    battery_id = "battery_id", _r("experiment.battery.id")
    battery_name = "battery_name", _r("experiment.battery.name")
    template_plate_id = "template_plate_id", _r("experiment.template_plate.id")
    template_plate_name = "template_plate_name", _r("experiment.template_plate.name")
    person_run = "person_run", _r("experimentalist.username")
    person_plated = "person_plated", _r("plate.person_plated.username")
    datetime_run = "datetime_run", _r("datetime_run")
    datetime_dosed = "datetime_dosed", _r("datetime_dosed")
    datetime_plated = "datetime_plated", _r("plate.datetime_plated")
    datetime_inserted = "datetime_inserted", _r("created")
    variant_id = "variant_id", _w("variant.id")
    variant_name = "variant_name", _w("variant.name")
    n_fish = "n_fish", _w("n")
    dpf = "age", _w("age")
    sauron = "sauron", _r("sauron_config.sauron.id")
    sauron_config = "sauron_config", _r("sauron_config.id")
    well_group = "well_group", _w("well_group")
    treatment = (
        "treatments",
        lambda w, ts: Treatments(
            [Treatment.from_well_treatment(t) for t in ts if t.batch_id is not None]
        ),
    )
    project_description = "experiment_description", _r("experiment.description")
    b_ids = (
        "b_ids",
        lambda w, ts: tuple(
            {Treatment.from_well_treatment(t).bid for t in ts if t.batch_id is not None}
        ),
    )
    c_ids = (
        "c_ids",
        lambda w, ts: tuple(
            {Treatment.from_well_treatment(t).cid for t in ts if t.batch_id is not None}
        ),
    )

    # the order here dictates the order of index columns
    required_fns = [
        well,
        index,
        row,
        column,
        well_label,
        run,
        submission,
        physical_plate,
        control_type,
        control_type_id,
        variant_id,
        variant_name,
        treatment,
        b_ids,
        c_ids,
        well_group,
        n_fish,
        dpf,
        tag,
        run_description,
        experiment_id,
        experiment_name,
        battery_id,
        battery_name,
        template_plate_id,
        template_plate_name,
        sauron_config,
        sauron,
        person_run,
        person_plated,
        datetime_run,
        datetime_dosed,
        datetime_plated,
        datetime_inserted,
    ]

    reserved_fns = [*required_fns, project_description]

    required_names = ["name", "pack", *[x[0] for x in required_fns]]

    # feature is reserved but unused
    reserved_names = [
        "name",
        "pack",
        "display_name",
        "size",
        "marker",
        "color",
        *[x[0] for x in reserved_fns],
        "compound_names",
        "feature",
    ]

    essential_cols = {
        "name",
        "pack",
        "compound_names",
        "control_type",
        "control_type_id",
        "battery_id",
        "battery_name",
        "treatments",
        "c_ids",
        "b_ids",
        "n_fish",
        "age",
        "variant_id",
        "variant_name",
        "well_group",
    }

    important_cols = {*essential_cols, "sauron_config"}

    display_cols = {"display_name", "size", "color", "marker"}

    position_cols = {"well", "well_index", "well_label", "row", "column"}

    special_cols = {"name", "pack", "display_name", "size", "compound_names", "color", "marker"}

    machine_cols = {"sauron_config", "sauron"}

    battery_cols = {"battery_id", "battery_name"}

    experiment_cols = {
        "experiment_id",
        "experiment_name",
        "battery_id",
        "battery_name",
        "template_plate_id",
        "template_plate_name",
    }


class WellFrameColumnTools:
    """"""

    int32_cols = {
        "well",
        "well_index",
        "row",
        "column",
        "run",
        "physical_plate",
        "n_fish",
        "age",
        "experiment_id",
        "battery_id",
        "sauron_config",
        "sauron",
    }

    _o_int_cols = ["control_type_id", "variant_id", "n_fish", "age", "template_plate_id"]
    _o_str_cols = [
        "control_type",
        "variant_name",
        "well_group",
        "template_plate_name",
        "run_description",
        "_feature",
    ]
    _o_date_cols = ["datetime_dosed"]

    @classmethod
    def from_nan(cls, df: pd.DataFrame):
        """
        Temporarily replace NaNs and Nones to little-used values.

        Args:
            df:

        Returns:

        """
        for c in WellFrameColumnTools._o_int_cols:
            if c in df.columns:
                df[c] = df[c].fillna(-1)
        for c in WellFrameColumnTools._o_str_cols:
            if c in df.columns:
                df[c] = df[c].fillna("```")
        # Since pandas represents timestamps in nanosecond resolution, the timespan that can be represented using a 64-bit integer is limited to approximately 584 years
        for c in WellFrameColumnTools._o_date_cols:
            if c in df.columns:
                df[c] = df[c].fillna(pd.Timestamp.min)
        return df

    @classmethod
    def to_nan(cls, df: pd.DataFrame):
        """
        Undoes WellFrameColumnTools._from_nan

        Args:
            df:

        Returns:

        """
        for c in WellFrameColumnTools._o_int_cols:
            if c in df.columns:
                df[c] = df[c].replace(-1, np.nan)
        for c in WellFrameColumnTools._o_str_cols:
            if c in df.columns:
                df[c] = df[c].replace("```", None)
        for c in WellFrameColumnTools._o_date_cols:
            if c in df.columns:
                df[c] = df[c].replace(pd.Timestamp.min, None)
        return df


__all__ = ["WellFrameColumnTools", "WellFrameColumns"]
