import matplotlib.ticker as ticker

from chemfish.core.core_imports import *
from chemfish.core.valar_tools import *
from chemfish.model.assay_frames import *
from chemfish.model.stim_frames import *
from chemfish.viz import *
from chemfish.viz._internal_viz import *


@abcd.auto_eq()
@abcd.auto_repr_str()
class StimframesPlotter(CakeLayer, KvrcPlotting):
    def __init__(
        self,
        should_label: bool = True,
        mark_every_n_ms: Optional[int] = None,
        audio_waveform: bool = True,
        assay_labels: bool = False,
        legacy: bool = False,
    ):
        """
        Constructor.

        Args:
            should_label: Show axis labels
            mark_every_n_ms: Explicitly control the number of x ticks per ms; otherwise chooses nice defaults.
            fps: IGNORED. Legacy option.
            audio_waveform: Show audio stimuli as waveforms. This requires that the stimframes passed have embedded (expanded) waveforms.
            assay_labels: Show a label at the bottom for each assay
            legacy: Whether the batteries being plotted are legacy
        """
        self._should_label = should_label
        self._mark_every_n_ms = mark_every_n_ms
        self._audio_waveform = audio_waveform
        self._assay_labels = assay_labels
        self._legacy = legacy
        self._fps = 25 if legacy else 1000

    def plot(
        self,
        stimframes: StimFrame,
        ax: Optional[Axes] = None,
        assays: AssayFrame = None,
        starts_at_ms: int = 0,
        battery: Union[None, Batteries, str, int] = None,
    ) -> Axes:
        """


        Args:
          stimframes: StimFrame:
          ax:
          assays:
          starts_at_ms: int:  (Default value = 0)
          battery:

        Returns:

        """
        # prep / define stuff
        t0 = time.monotonic()
        if battery is not None:
            battery = Batteries.fetch(battery)
        if battery is None:
            logger.debug(f"Plotting battery with {len(stimframes)} stimframes...")
        else:
            logger.debug(f"Plotting battery {battery.id} with {len(stimframes)} stimframes...")
        if starts_at_ms is None:
            starts_at_ms = 0
        n_ms = len(stimframes) * 1000 / self._fps
        if ax is None:
            figure = plt.figure(figsize=(chemfish_rc.trace_width, chemfish_rc.trace_height))
            ax = figure.add_subplot(111)
        # the figure should always have a white background
        ax.set_facecolor("white")
        # Matt's historical pre-sauronx sauron used a definition of 0 to 1 instead of 255
        # This corrects for that.
        # Unfortunately, if the stimframes are always 0 or 1 in a range of 0-255, this will be wrong
        if stimframes.max().max() > 1:
            # noinspection PyTypeChecker
            stimframes /= 255.0
        all_stims = {s.name: s for s in Stimuli.select()}
        # plot all the stimuli
        ordered = []
        # sort by type first; this affects which appears on top; also skip 'none'
        stimulus_list = sorted(
            [(ValarTools.stimulus_type(s).value, s) for s in stimframes.columns if s != "none"]
        )
        for kind, c in stimulus_list:
            stim = all_stims[c]
            kind = ValarTools.stimulus_type(stim)
            _ax, _name, _color = self._plot_stim(stim, stimframes[c].values, ax, kind)
            if _name is not None and stim.audio_file_id is None:  # TODO permit
                ordered.append((kind.value, _name, _color))  # kind first for sort order later
        ordered = sorted(ordered)
        # plot the assay bounds / labels as needed
        if assays is not None:
            self._plot_assays(assays, starts_at_ms, n_ms, ax)
        # set the axis labels and legend
        self._axis_labels(stimframes, ax, starts_at_ms=starts_at_ms, total_ms=n_ms)
        from chemfish.viz.figures import FigureTools

        if chemfish_rc.stimplot_legend_on:
            ordered_names, ordered_colors = [k[1] for k in ordered], [k[2] for k in ordered]
            FigureTools.manual_legend(
                ax,
                ordered_names,
                ordered_colors,
                bbox_to_anchor=chemfish_rc.stimplot_legend_bbox,
                ncol=chemfish_rc.stimplot_legend_n_cols,
                loc=chemfish_rc.stimplot_legend_loc,
            )
        # cover up line at y=0:
        if chemfish_rc.stimplot_cover_width > 0:
            ax.hlines(
                y=0,
                xmin=0,
                xmax=len(stimframes),
                color=chemfish_rc.stimplot_cover_color,
                linewidth=chemfish_rc.stimplot_cover_width,
                zorder=20,
                alpha=1,
            )
        ax.set_ybound(0, 1)
        ax.set_xbound(0, len(stimframes))
        logger.debug(f"Finished plotting battery. Took {round(time.monotonic() - t0, 1)}s.")
        return ax

    def _plot_stim(self, stim, r, ax, kind):
        """


        Args:
          stim:
          r:
          ax:
          kind:

        Returns:

        """
        c = stim.name
        n_stimframes = len(r)
        x = np.argwhere(r > 0)
        y = r[r > 0]
        if not np.any(r > 0):
            return ax, None, None
        if stim.audio_file is not None and self._audio_waveform:
            ax.scatter(
                x,
                y,
                alpha=chemfish_rc.stimplot_audio_line_alpha,
                label=c,
                s=chemfish_rc.stimplot_audio_line_width,
                clip_on=chemfish_rc.stimplot_clip,
                rasterized=chemfish_rc.rasterize_traces,
                marker=".",
                facecolors=chemfish_rc.stimplot_audio_linecolor,
                edgecolors="none",
            )
            return ax, ValarTools.stimulus_display_name(c), chemfish_rc.stimplot_audio_linecolor
        if chemfish_rc.stimplot_line_alpha > 0:
            ax.plot(
                r,
                color=chemfish_rc.get_stimulus_colors()[stim.name],
                alpha=chemfish_rc.stimplot_line_alpha,
                label=c,
                linewidth=chemfish_rc.stimplot_line_width,
                clip_on=chemfish_rc.stimplot_clip,
                rasterized=chemfish_rc.rasterize_traces,
            )
        if chemfish_rc.stimplot_fill_alpha > 0:
            ax.fill_between(
                range(0, n_stimframes),
                r,
                0,
                alpha=chemfish_rc.stimplot_fill_alpha,
                facecolor=chemfish_rc.get_stimulus_colors()[c],
                edgecolor="none",
                linewidth=0,
                clip_on=chemfish_rc.stimplot_clip,
                rasterized=chemfish_rc.rasterize_traces,
            )
        return ax, ValarTools.stimulus_display_name(c), chemfish_rc.get_stimulus_colors()[stim.name]

    def _plot_assays(self, assays, starts_at_ms, n_ms, ax):
        """


        Args:
          assays:
          starts_at_ms:
          n_ms:
          ax:

        Returns:

        """
        if not self._assay_labels and not chemfish_rc.assay_lines_without_text:
            return
        for a in assays.itertuples():
            start = (a.start_ms - starts_at_ms) * self._fps / 1000
            end = (a.end_ms - starts_at_ms) * self._fps / 1000
            if start < 0 or end < 0:
                continue
            if a.end_ms > n_ms + starts_at_ms:
                continue
            if ValarTools.assay_is_background(a.assay_id):
                continue
            # STIMPLOT_ASSAY_LINE_HEIGHT should depend on the height and the font size
            # for some reason, setting alpha= here doesn't work
            width = chemfish_rc.assay_line_width
            color = chemfish_rc.assay_line_color
            alpha = chemfish_rc.assay_line_alpha
            height = (
                chemfish_rc.assay_line_with_text_height
                if self._assay_labels
                else chemfish_rc.assay_line_without_text_height
            )
            lines = ax.vlines(
                start, -height, 0, lw=width, colors=color, clip_on=False, alpha=0.0, zorder=1
            )
            lines.set_alpha(alpha)
            lines = ax.vlines(
                end, -height, 0, lw=width, colors=color, clip_on=False, alpha=0.0, zorder=1
            )
            lines.set_alpha(alpha)
            lines = ax.hlines(
                -height, start, end, lw=width, colors=color, clip_on=False, alpha=0.0, zorder=1
            )
            lines.set_alpha(alpha)
            if self._assay_labels and not ValarTools.assay_is_background(a.assay_id):
                minsec = a.start
                text = (
                    a.simplified_name + " (" + minsec + ")"
                    if chemfish_rc.assay_start_times
                    else a.simplified_name
                )
                ax.annotate(
                    text,
                    (0.5 * start + 0.5 * end, -0.5),
                    horizontalalignment="center",
                    rotation=90,
                    color=chemfish_rc.assay_text_color,
                    annotation_clip=False,
                    alpha=chemfish_rc.assay_text_alpha,
                )

    def _axis_labels(self, stimframes, ax, starts_at_ms, total_ms):
        """


        Args:
          stimframes:
          ax:
          starts_at_ms:
          total_ms:

        Returns:

        """
        if self._should_label:
            self._label_x(stimframes, ax, starts_at_ms, total_ms)
            ax.grid(False)
            ax.set_ylabel(chemfish_rc.stimplot_y_label)
        else:
            ax.set_xticks([])
        ax.get_yaxis().set_ticks([])

    def _label_x(self, stimframes, ax2, starts_at_ms, total_ms):
        """


        Args:
          stimframes:
          ax2:
          starts_at_ms:
          total_ms:

        Returns:

        """
        assert starts_at_ms is not None
        assert self._fps is not None
        mark_every = self._best_marks(stimframes)
        units, units_per_sec = InternalVizTools.preferred_units_per_sec(mark_every, total_ms)
        mark_freq = mark_every / 1000 * self._fps
        # TODO  + 5*mark_freq ??
        ax2.set_xticks(np.arange(0, np.ceil(len(stimframes)) + mark_freq, mark_freq))
        ax2.set_xlabel(f"time ({units})")
        ax2.xaxis.set_major_formatter(
            ticker.FuncFormatter(
                lambda frame, pos: "{0:g}".format(
                    round((frame / self._fps + starts_at_ms / 1000) * units_per_sec),
                    chemfish_rc.trace_time_n_decimals,
                )
            )
        )

    def _best_marks(self, stimframes):
        """


        Args:
          stimframes:

        Returns:

        """
        if self._mark_every_n_ms is None:
            return InternalVizTools.preferred_tick_ms_interval(len(stimframes) / self._fps * 1000)
        else:
            return self._mark_every_n_ms


__all__ = ["StimframesPlotter"]
