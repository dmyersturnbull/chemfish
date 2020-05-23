from __future__ import annotations
from matplotlib.figure import Figure
from kale.core.core_imports import *
from kale.viz.confusion_plots import *
from dscience.ml.confusion_matrix import ConfusionMatrix as _CM


class ConfusionMatrix(_CM):
    def heatmap(
        self,
        vmin: float = 0,
        vmax: float = 1,
        runs: Optional[Sequence[int]] = None,
        renamer: Union[None, Mapping[str, str], Callable[[str], str]] = None,
        label_colors: Union[bool, Mapping[str, str]] = False,
    ) -> Figure:
        """
        Generates a heatmap.
        :param vmin: Set this as the minimum accuracy (white on the colorbar)
        :param vmax: Set this as the maximum accuracy (black on the colorbar)
        :param runs: Run stamps in the upper-left corner with these runs (not verified)
        :param renamer: A function that maps the class names to new names for plotting
        :param label_colors: Mapping from names to colors for the labels; or a string for all control colors
        :return: The figure, which was not displayed
        """
        return ConfusionPlots.plot(
            self, vmin=vmin, vmax=vmax, renamer=renamer, runs=runs, label_colors=label_colors
        )


class ConfusionMatrices:
    @classmethod
    def average(cls, matrices: Sequence[ConfusionMatrix]) -> ConfusionMatrix:
        return ConfusionMatrix.average(matrices)

    @classmethod
    def zeros(cls, classes: Sequence[str]):
        return ConfusionMatrix(
            pd.DataFrame(
                [pd.Series({"class": r, **{c: 0.0 for c in classes}}) for r in classes]
            ).set_index("class")
        )

    @classmethod
    def perfect(cls, classes: Sequence[str]):
        return ConfusionMatrix(
            pd.DataFrame(
                [
                    pd.Series({"class": r, **{c: 1.0 if r == c else 0.0 for c in classes}})
                    for r in classes
                ]
            ).set_index("class")
        )

    @classmethod
    def uniform(cls, classes: Sequence[str]):
        return ConfusionMatrix(
            pd.DataFrame(
                [
                    pd.Series({"class": r, **{c: 1.0 / len(classes) for c in classes}})
                    for r in classes
                ]
            ).set_index("class")
        )


__all__ = ["ConfusionMatrix", "ConfusionMatrices"]
