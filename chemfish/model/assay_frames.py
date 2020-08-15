"""
Dataframes listing assays in batteries.
"""

from __future__ import annotations

from chemfish.core.core_imports import *


class AssayFrame(TypedDf):
    """
    A Pandas DataFrame that has one row per assay in a battery.
    Each row has the assay_positions ID, the assay name and simplified_name, and the start and end times.
    """

    @classmethod
    def of(cls, battery: Union[Batteries, int, str]) -> AssayFrame:
        return AssayFrame(AssayFrame._assay_df(battery))

    @classmethod
    def required_columns(cls) -> Sequence[str]:
        return [
            "position_id",
            "assay_id",
            "name",
            "simplified_name",
            "start_ms",
            "end_ms",
            "n_ms",
            "start",
            "end",
            "duration",
        ]

    def by_substring(
        self, superstrings: Union[str, Assays, Iterable[Union[str, Assays]]]
    ) -> AssayFrame:
        """
        Get rows by substrings (or whole strings) of the assay names
        Examples:
            - `assays.by_substring('red')`
            - `assays.by_substring(['red', Assays.fetch('VSR1')])`
        :returns A copy
        """
        if not Tools.is_true_iterable(superstrings):
            superstrings = [superstrings]
        superstrings = [a.name if isinstance(a, Assays) else a for a in superstrings]
        return AssayFrame.of(
            self[
                any([(self["assay"] == s) | (self["assay"].str.contains(s)) for s in superstrings])
            ]
        )

    @classmethod
    def _assay_df(cls, battery: Union[int, str]) -> pd.DataFrame:
        """Returns a DataFrame of the assay name, start, and end in a battery."""
        simplifier = ValarTools.assay_name_simplifier()
        battery = Batteries.fetch(battery)
        query = (
            AssayPositions.select(AssayPositions, Assays, StimulusFrames, Stimuli, Batteries)
            .join(Assays)
            .join(StimulusFrames, JOIN.LEFT_OUTER)
            .join(Stimuli, JOIN.LEFT_OUTER)
            .switch(AssayPositions)
            .join(Batteries)
            .where(Batteries.id == battery.id)
        )
        assay_positions = pd.DataFrame(
            [
                pd.Series(
                    [
                        ap.id,
                        ap.assay.id,
                        ap.assay.name,
                        simplifier(ap.assay.name),
                        ValarTools.assay_ms_per_stimframe(ap.assay) * ap.start,
                        ValarTools.assay_ms_per_stimframe(ap.assay) * (ap.start + ap.assay.length),
                    ]
                )
                for ap in query
            ]
        )
        df = (
            assay_positions.rename(
                columns={
                    0: "position_id",
                    1: "assay_id",
                    2: "name",
                    3: "simplified_name",
                    4: "start_ms",
                    5: "end_ms",
                    6: "n_ms",
                }
            )
            .drop_duplicates()
            .sort_values("start_ms")
        )
        df["start"] = df["start_ms"].map(Tools.ms_to_minsec)
        df["end"] = df["end_ms"].map(Tools.ms_to_minsec)
        df["duration"] = (df["end_ms"] - df["start_ms"]).map(Tools.ms_to_minsec)
        return df.reset_index()


__all__ = ["AssayFrame"]
