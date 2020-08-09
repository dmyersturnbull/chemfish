import matplotlib.ticker as ticker
from chemfish.core.core_imports import *
from chemfish.viz.internal_viz import *
from chemfish.core.valar_tools import *
from chemfish.model.stim_frames import *
from chemfish.model.assay_frames import *
from chemfish.viz import *


@abcd.auto_eq()
@abcd.auto_repr_str()
class StimframesPlotter(CakeLayer, KvrcPlotting):
    def __init__(
        self,
        should_label: bool = True,
        mark_every_n_ms: Optional[int] = None,
        fps: int = 1000,
        audio_waveform: bool = True,
        assay_labels: bool = False,
        legacy: bool = False,
    ):
        """

        :param should_label: Show axis labels
        :param mark_every_n_ms: Explicitly control the number of x ticks per ms; otherwise chooses nice defaults.
        :param fps: IGNORED. Legacy option.
        :param audio_waveform: Show audio stimuli as waveforms. This requires that the stimframes passed have embedded (expanded) waveforms.
        :param assay_labels: Show a label at the bottom for each assay
        :param legacy: Whether the batteries being plotted are legacy
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
        # prep / define stuff
        t0 = time.monotonic()
        if battery is not None:
            battery = Batteries.fetch(battery)
        if battery is None:
            logger.debug("Plotting battery with {} stimframes...".format(len(stimframes)))
        else:
            logger.debug(
                "Plotting battery {} with {} stimframes...".format(battery.id, len(stimframes))
            )
        if starts_at_ms is None:
            starts_at_ms = 0
        n_ms = len(stimframes) * 1000 / self._fps
        if ax is None:
            figure = plt.figure(figsize=(KVRC.trace_width, KVRC.trace_height))
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

        if KVRC.stimplot_legend_on:
            ordered_names, ordered_colors = [k[1] for k in ordered], [k[2] for k in ordered]
            FigureTools.manual_legend(
                ax,
                ordered_names,
                ordered_colors,
                bbox_to_anchor=KVRC.stimplot_legend_bbox,
                ncol=KVRC.stimplot_legend_n_cols,
                loc=KVRC.stimplot_legend_loc,
            )
        # cover up line at y=0:
        if KVRC.stimplot_cover_width > 0:
            ax.hlines(
                y=0,
                xmin=0,
                xmax=len(stimframes),
                color=KVRC.stimplot_cover_color,
                linewidth=KVRC.stimplot_cover_width,
                zorder=20,
                alpha=1,
            )
        ax.set_ybound(0, 1)
        ax.set_xbound(0, len(stimframes))
        logger.debug("Finished plotting battery. Took {}s.".format(round(time.monotonic() - t0, 1)))
        return ax

    def _plot_stim(self, stim, r, ax, kind):
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
                alpha=KVRC.stimplot_audio_line_alpha,
                label=c,
                s=KVRC.stimplot_audio_line_width,
                clip_on=KVRC.stimplot_clip,
                rasterized=KVRC.rasterize_traces,
                marker=".",
                facecolors=KVRC.stimplot_audio_linecolor,
                edgecolors="none",
            )
            return ax, ValarTools.stimulus_display_name(c), KVRC.stimplot_audio_linecolor
        if KVRC.stimplot_line_alpha > 0:
            ax.plot(
                r,
                color=KVRC.get_stimulus_colors()[stim.name],
                alpha=KVRC.stimplot_line_alpha,
                label=c,
                linewidth=KVRC.stimplot_line_width,
                clip_on=KVRC.stimplot_clip,
                rasterized=KVRC.rasterize_traces,
            )
        if KVRC.stimplot_fill_alpha > 0:
            ax.fill_between(
                range(0, n_stimframes),
                r,
                0,
                alpha=KVRC.stimplot_fill_alpha,
                facecolor=KVRC.get_stimulus_colors()[c],
                edgecolor="none",
                linewidth=0,
                clip_on=KVRC.stimplot_clip,
                rasterized=KVRC.rasterize_traces,
            )
        return ax, ValarTools.stimulus_display_name(c), KVRC.get_stimulus_colors()[stim.name]

    def _plot_assays(self, assays, starts_at_ms, n_ms, ax):
        if not self._assay_labels and not KVRC.assay_lines_without_text:
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
            width = KVRC.assay_line_width
            color = KVRC.assay_line_color
            alpha = KVRC.assay_line_alpha
            height = (
                KVRC.assay_line_with_text_height
                if self._assay_labels
                else KVRC.assay_line_without_text_height
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
                    if KVRC.assay_start_times
                    else a.simplified_name
                )
                ax.annotate(
                    text,
                    (0.5 * start + 0.5 * end, -0.5),
                    horizontalalignment="center",
                    rotation=90,
                    color=KVRC.assay_text_color,
                    annotation_clip=False,
                    alpha=KVRC.assay_text_alpha,
                )

    def _axis_labels(self, stimframes, ax, starts_at_ms, total_ms):
        if self._should_label:
            self._label_x(stimframes, ax, starts_at_ms, total_ms)
            ax.grid(False)
            ax.set_ylabel(KVRC.stimplot_y_label)
        else:
            ax.set_xticks([])
        ax.get_yaxis().set_ticks([])

    def _label_x(self, stimframes, ax2, starts_at_ms, total_ms):
        assert starts_at_ms is not None
        assert self._fps is not None
        mark_every = self._best_marks(stimframes)
        units, units_per_sec = InternalVizTools.preferred_units_per_sec(mark_every, total_ms)
        mark_freq = mark_every / 1000 * self._fps
        # TODO  + 5*mark_freq ??
        ax2.set_xticks(np.arange(0, np.ceil(len(stimframes)) + mark_freq, mark_freq))
        ax2.set_xlabel("time ({})".format(units))
        ax2.xaxis.set_major_formatter(
            ticker.FuncFormatter(
                lambda frame, pos: "{0:g}".format(
                    round((frame / self._fps + starts_at_ms / 1000) * units_per_sec),
                    KVRC.trace_time_n_decimals,
                )
            )
        )

    def _best_marks(self, stimframes):
        if self._mark_every_n_ms is None:
            return InternalVizTools.preferred_tick_ms_interval(len(stimframes) / self._fps * 1000)
        else:
            return self._mark_every_n_ms


__all__ = ["StimframesPlotter"]
