from matplotlib import gridspec

from chemfish.core.core_imports import *
from chemfish.model.stim_frames import StimFrame
from chemfish.model.well_frames import WellFrame
from chemfish.viz import CakeComponent
from chemfish.viz._internal_viz import *
from chemfish.viz.figures import *
from chemfish.viz.figures import FigureTools
from chemfish.viz.stim_plots import *


@abcd.auto_eq()
@abcd.auto_repr_str()
class HeatPlotter(CakeComponent, KvrcPlotting):
    """
    Plots heatmaps with wells on the y-axis, time on the x-axis, and MI or another time-dependent feature as color.
    Can be either symmetric (blue→white→red) or "raw" (white→black).
    See ?HeatPlotter for more info.
    """

    def __init__(
        self,
        stimframes_plotter: Optional[StimframesPlotter] = None,
        should_label: bool = True,
        cmap: Optional[str] = None,
        vmax_quantile: float = 0.95,
        symmetric: bool = False,
        name_sep_line: bool = False,
        control_sep_line: bool = False,
    ):
        """
        Creates a new plotter to be applied to any data.
        By default `cmap` is set intelligently. If you override it, use a diverging colormap if `symmetric=True` and linear otherwise.
        :param stimframes_plotter:
        :param should_label: Show x and y labels and tick labels
        :param cmap:
        :param vmax_quantile:
        :param symmetric: If True, calculates z=abs(max(MI)) and sets vmin=-z and vmax=z.
        :param name_sep_line:
        :param control_sep_line:
        """
        self._stimframes_plotter = (
            stimframes_plotter if stimframes_plotter is not None else StimframesPlotter()
        )
        self._should_label = should_label
        self._cmap = (
            cmap
            if cmap is not None
            else (FancyCmaps.blue_white_red() if symmetric else FancyCmaps.white_black())
        )
        self._symmetric = symmetric
        self._vmax_quantile = vmax_quantile
        self._name_sep_line = name_sep_line
        self._control_sep_line = control_sep_line

    def plot(
        self,
        df: WellFrame,
        stimframes: Optional[StimFrame],
        starts_at_ms: int = 0,
        battery: Union[None, Batteries, int, str] = None,
    ) -> Figure:
        t0 = time.monotonic()
        battery = Batteries.fetch(battery)
        n_plots = len(df)
        logger.info("Plotting heatmap with {} rows...".format(n_plots))
        vmin, vmax = self._vmin_max(df)
        figure, ax1, ax2 = self._figure(len(df), stimframes is not None)
        if KVRC.rasterize_heatmaps:
            ax1.imshow(df, aspect="auto", vmin=vmin, vmax=vmax, cmap=self._cmap)
        else:
            ax1.pcolormesh(df, vmin=vmin, vmax=vmax, cmap=self._cmap)
        self._adjust(df, ax1)
        if stimframes is not None:
            self._stimframes_plotter.plot(
                stimframes, ax2, starts_at_ms=starts_at_ms, battery=battery
            )
        logger.minor(
            "Plotted heatmap with {} rows. Took {}s.".format(
                n_plots, round(time.monotonic() - t0, 1)
            )
        )
        FigureTools.stamp_runs(ax1, df.unique_runs())
        return figure

    def _figure(self, n_rows: int, with_stimframes: bool):
        figure = plt.figure(figsize=(KVRC.heatmap_width, KVRC.heatmap_row_height * n_rows))
        if with_stimframes:
            gs = gridspec.GridSpec(
                2,
                1,
                height_ratios=[n_rows * KVRC.heatmap_row_height, KVRC.heatmap_stimplot_height],
                figure=figure,
            )
        else:
            gs = gridspec.GridSpec(1, 1, height_ratios=[1], figure=figure)
        gs.update(hspace=KVRC.heatmap_hspace)
        ax1 = figure.add_subplot(gs[0])
        if with_stimframes:
            ax2 = figure.add_subplot(gs[1])
            ax2.margins(0, 0)
        else:
            ax2 = None
        return figure, ax1, ax2

    def _adjust(self, df, ax1):
        ax1.xaxis.set_ticklabels([])
        ax1.xaxis.set_ticks([])
        ax1.margins(0, 0)
        offset = 0.5 if KVRC.rasterize_heatmaps else 0.0
        ax1.set_yticks([x - offset for x in range(0, len(df), 1)])
        if self._should_label:
            ax1.set_ylabel("well")
            label_names = self._get_label_names(df)
            ax1.set_yticklabels(label_names, va="top")
        if self._name_sep_line:
            params = {
                "linestyle": KVRC.heatmap_name_sep_style,
                "lw": KVRC.heatmap_name_sep_width,
                "alpha": KVRC.heatmap_name_sep_alpha,
                "color": KVRC.heatmap_name_sep_color_symmetric
                if self._symmetric
                else KVRC.heatmap_name_sep_color_asymmetric,
            }
            self._add_lines(df.names(), ax1, params)
        if self._control_sep_line:
            params = {
                "linestyle": KVRC.heatmap_control_sep_style,
                "lw": KVRC.heatmap_control_sep_width,
                "alpha": KVRC.heatmap_control_sep_alpha,
                "color": KVRC.heatmap_control_sep_color_symmetric
                if self._symmetric
                else KVRC.heatmap_control_sep_color_asymmetric,
            }
            self._add_lines(df["control_type"], ax1, params)

    def _get_label_names(self, df):
        label_names = []
        last_label_name = ""
        for ell in df.names():
            if ell != last_label_name:
                label_names.append(FigureTools.fix_labels(ell))
                last_label_name = ell
            else:
                label_names.append("")
        return label_names

    def _vmin_max(self, df):
        if self._symmetric:
            highest = df.abs().quantile(self._vmax_quantile, axis=1).quantile(self._vmax_quantile)
            return -highest, highest
        else:
            vmin = df.quantile(self._vmax_quantile, axis=1).quantile(1 - self._vmax_quantile)
            vmax = df.quantile(self._vmax_quantile, axis=1).quantile(self._vmax_quantile)
            return vmin, vmax

    def _add_lines(self, vals, ax1, sep_line):
        if sep_line is None:
            return
        prev_name = -1
        offset = 0.5 if KVRC.rasterize_heatmaps else 0.0
        for i, name in enumerate(vals):
            # TODO WHAT???
            if str(name) == "nan":
                continue
            if i > 0 and name != prev_name:
                ax1.axhline(y=i - offset, **sep_line)
            prev_name = name


__all__ = ["HeatPlotter"]
