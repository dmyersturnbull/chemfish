from __future__ import annotations

from matplotlib.figure import Figure

from chemfish.core.core_imports import *
from chemfish.model.metrics import *
from chemfish.model.responses import *
from chemfish.viz.accuracy_plots import *


class SummarizedSpindleFrame(BaseScoreFrame):
    """"""

    def to_dose_response(
        self, axis: int, splitter: Callable[[str], Tup[str, str]] = Tools.split_drug_dose
    ) -> DoseResponseFrame1D:
        """


        Args:
            axis:
            splitter:

        Returns:

        """
        summary = self.copy()
        all_controls = {s.name: s.name for s in ControlTypes.select()}
        all_controls.update({s: s.name for s in ControlTypes.select()})
        split = [splitter(name) for name in summary["label"]]
        summary["label"] = [i[0] for i in split]
        summary["x_raw"] = [
            np.nan if Tools.is_probable_null(s) else s for s in [k[1] for k in split]
        ]
        if all(summary["x_raw"].isnull()):
            logger.caution("All response x values are null")
        del split  # we're going to sort, so don't use this!!
        summary = summary.sort_values(["label", "x_raw"])
        summary["control"] = summary["label"].map(all_controls.get)
        summary["x_text"] = summary["x_raw"].map(
            lambda s: np.nan if Tools.is_probable_null(s) else Tools.round_to_sigfigs(s, 3)
        )
        summary["x_value"] = summary.groupby("label").cumcount()
        summary["upper_" + str(axis)] = summary["upper"]
        summary["lower_" + str(axis)] = summary["lower"]
        summary["score_" + str(axis)] = summary["score"]
        return DoseResponseFrame1D(
            summary[
                [
                    "label",
                    "control",
                    "x_raw",
                    "x_text",
                    "x_value",
                    "upper_" + str(axis),
                    "lower_" + str(axis),
                    "score_" + str(axis),
                ]
            ]
        )

