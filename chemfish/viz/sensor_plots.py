from chemfish.core.core_imports import *
from chemfish.model.sensors import *
from chemfish.model.stim_frames import *
from chemfish.viz import CakeComponent
from chemfish.viz._internal_viz import *
from chemfish.viz.figures import *
from chemfish.viz.stim_plots import StimframesPlotter


@abcd.auto_eq()
@abcd.auto_repr_str()
class SensorPlotter(CakeComponent, KvrcPlotting):
    """"""

    def __init__(self, stimplotter: Optional[StimframesPlotter] = None, quantile: float = 1):
        self.stimplotter = StimframesPlotter() if stimplotter is None else stimplotter
        self.quantile = quantile

    def diagnostics(
        self,
        run,
        stimframes: StimFrame,
        battery: BatteryLike,
        sensors: Sequence[TimeDepChemfishSensor],
        start_ms: Optional[int] = None,
    ) -> Figure:
        """


        Args:
            run:
            stimframes:
            battery:
            sensors:
            start_ms:

        Returns:

        """
        run = Tools.run(run, join=True)
        t0 = time.monotonic()
        n = len(sensors)
        logger.info(f"Plotting {n} sensors for r{run.id}...")
        # set up the figure and gridspec
        figure = plt.figure(
            figsize=(
                chemfish_rc.trace_width,
                chemfish_rc.trace_layer_const_height + n * chemfish_rc.trace_layer_height,
            )
        )
        gs = GridSpec(n + 1, 1, height_ratios=[1] * (n + 1), figure=figure)
        gs.update(hspace=chemfish_rc.trace_hspace)
        # plot the sensors in turn
        for i, data in enumerate(sensors):
            ax = figure.add_subplot(gs[i])
            try:
                self._plot_one(data, ax)
            except Exception:
                logger.error(
                    f"Failed to plot {data.name} (xl: {data.timing_data.shape}, yl: {data.data.shape}"
                )
                raise
        # finally add the stimframes
        ax = figure.add_subplot(gs[n])
        self._plot_stimframes(stimframes, battery, start_ms, ax)
        FigureTools.stamp_runs(figure.axes[0], run)
        logger.minor(
            f"Plotted data for sensors {[s.name for s in sensors]}. Took {round(time.monotonic() - t0, 1)}s."
        )
        return figure

    def _plot_stimframes(
        self, stimframes: StimFrame, battery: Batteries, start_ms: Optional[int], ax
    ):
        self.stimplotter.plot(stimframes, battery, ax=ax, starts_at_ms=start_ms)
        ax.set_ylabel(
            "⚑" if chemfish_rc.sensor_use_symbols else "stimuli",
            rotation=0 if chemfish_rc.sensor_use_symbols else 90,
        )

    def _plot_one(self, data: TimeDepChemfishSensor, ax: Axes) -> None:
        if not isinstance(data, TimeDepChemfishSensor):
            raise TypeError(f"Type {type(data)} is not a TimeDepChemfishSensor")
        x_vals, y_vals = data.timing_data, data.data
        if isinstance(data, MicrophoneWaveformSensor):
            x_vals, y_vals = data.timing_data, data.waveform.data
            ax.scatter(
                x_vals,
                y_vals,
                rasterized=chemfish_rc.sensor_rasterize,
                s=chemfish_rc.sensor_mic_point_size,
                c=chemfish_rc.sensor_mic_color,
                marker=".",
                edgecolors="none",
            )
            ax.set_ylim(ymin=-1, ymax=1)
        else:
            ax.plot(
                x_vals,
                y_vals,
                rasterized=chemfish_rc.sensor_rasterize,
                linewidth=chemfish_rc.sensor_line_width,
                c=chemfish_rc.sensor_line_color,
                drawstyle="steps-pre",
            )
            ax.set_ylim(np.quantile(y_vals, 1 - self.quantile), np.quantile(y_vals, self.quantile))
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])
        label = data.symbol if chemfish_rc.sensor_use_symbols else data.abbrev
        ax.set_ylabel(label, rotation=(0 if chemfish_rc.sensor_use_symbols else 90))
        # ax.set_xlim(data.bt_data.start_ms, data.bt_data.end_ms)


__all__ = ["SensorPlotter"]
