"""
Can depend on all model objects.
"""
from __future__ import annotations
from chemfish.core.core_imports import *
from chemfish.model.well_frames import *
from chemfish.model.app_frames import *
from chemfish.model.assay_frames import *


@abcd.status(CodeStatus.Immature)
class AugmentedWellFrame(WellFrame):
    """
    Extra tools for WellFrames.
    """

    def with_stimulus(self, stimulus: Union[None, int, str]) -> AugmentedWellFrame:
        x = pd.Series(self._stimulus_on_frames(stimulus))
        return self[x.index(x)]

    def without_stimulus(self, stimulus: Union[None, int, str]) -> AugmentedWellFrame:
        x = ~pd.Series(self._stimulus_on_frames(stimulus))
        return self[x.index(x)]

    def _stimulus_on_frames(self, stimulus: Union[None, int, str]) -> np.array:
        battery = Batteries.fetch(self.only("battery_id"))
        stimulus = Stimuli.fetch(stimulus)
        fps = Tools.only([ValarTools.frames_per_second(r) for r in self.unique_runs()])
        app = AppFrame.of(battery).by_stimulus(stimulus)
        ons = app.ms_on(stimulus)
        offs = app.ms_off(stimulus)
        intersection = set(ons).intersection(offs)
        if len(intersection) > 0:
            raise DataIntegrityError(
                "Stimulus {} in battery {} has on/off overlapping ms values {}".format(
                    stimulus.name, battery.name, intersection
                )
            )
        onoff = list(sorted([(t, True) for t in ons] + [(t, False) for t in offs]))
        values = np.zeros(self.feature_length())
        last_t, last_v = 0, False
        for t, v in onoff:
            t = t / 1000 * fps
            values[last_t:t] = last_v
            last_t, last_v = t, v
        values[last_t : self.feature_length()] = last_v
        return values

    def assay_matching(
        self, assay: Union[None, int, str], position_id: Optional[int] = None
    ) -> AugmentedWellFrame:
        """
        Takes an assay ID, full name, or uniquely identifying substring
        If a given assay occurs multiple times in a battery, position_id must be given and other arguments are ignored
        """
        if assay is None and position_id is None:
            return self
        battery = self.only("battery_id")
        a_df = AssayFrame.of(battery)
        if position_id is None:
            firsts = a_df.loc[
                (a_df.assay_id == assay)
                | (a_df.name.str.contains(str(assay)))
                | (a_df.simplified_name == str(assay)),
                "start_ms",
            ].values
            lasts = a_df.loc[
                (a_df.assay_id == assay)
                | (a_df.name.str.contains(str(assay)))
                | (a_df.simplified_name == str(assay)),
                "end_ms",
            ].values
        else:
            firsts = a_df.loc[a_df.position_id == position_id, "start_ms"].values
            lasts = a_df.loc[a_df.position_id == position_id, "end_ms"].values
        if len(firsts) > 1 or len(lasts) > 1:
            raise UserError(
                """
                    Found multiple instances of requested assays, but no position_id was given.
                    Either the given substring does not uniquely specify an assay or a position_id must be given.
                """
            )
        else:
            return self.slice_ms(firsts[0], lasts[0])


__all__ = ["AugmentedWellFrame"]
