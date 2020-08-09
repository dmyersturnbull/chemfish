from chemfish.core.core_imports import *
from chemfish.model.stim_frames import *
from chemfish.model.assay_frames import *
from chemfish.model.app_frames import *
from chemfish.viz.figures import *
from chemfish.viz.stim_plots import StimframesPlotter
from chemfish.viz import CakeComponent
from chemfish.viz.internal_viz import *


@abcd.auto_eq()
@abcd.auto_repr_str()
class ImportancePlotter(CakeComponent, KvrcPlotting):
    """
    Plots weight (often importance) across a time-series,
    either as a thin heatmap with no y axis (a sequence of vertical lines),
    or as a scatter plot.
    """

    def __init__(
        self,
        scatter: bool = False,
        cmap: Union[str, Colormap] = FancyCmaps.white_black(),
        vmax_quantile: Optional[float] = 0.95,
    ):
        self._scatter, self._cmap = scatter, cmap
        self._vmax_quantile = vmax_quantile

    def plot(
        self,
        weights: np.array,
        ax: Axes = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
    ) -> Figure:
        if vmin is None:
            vmin = np.quantile(weights, 1 - self._vmax_quantile)
        if vmax is None:
            vmax = np.quantile(weights, self._vmax_quantile)
        if ax is None:
            figure = plt.figure(figsize=(KVRC.trace_width, KVRC.trace_layer_height))
            ax = figure.add_subplot(111)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_yticklabels([])
        ax.set_ylabel("weight")
        if self._scatter:
            if isinstance(weights, tuple):
                ax.scatter(weights[0], weights[1], c=KVRC.weight_scatter_color, rasterized=False)
            else:
                ax.scatter(
                    np.arange(0, len(weights)),
                    weights,
                    c=KVRC.weight_scatter_color,
                    rasterized=False,
                )
            ax.set_ylim(vmin, vmax)
        else:
            ax.imshow(
                np.atleast_2d(weights),
                cmap=self._cmap,
                aspect="auto",
                vmin=vmin,
                vmax=vmax,
                rasterized=KVRC.rasterize_traces,
            )
        return ax.get_figure()


__all__ = ["ImportancePlotter"]
