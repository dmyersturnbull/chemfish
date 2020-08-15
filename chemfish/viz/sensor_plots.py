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
    def __init__(self, stimplotter: Optional[StimframesPlotter] = None, quantile: float = 0.995):
        self.stimplotter = StimframesPlotter(fps=1000) if stimplotter is None else stimplotter
        self.quantile = quantile

    def diagnostics(
        self,
        run,
        stimframes: StimFrame,
        sensors: Sequence[TimeDepChemfishSensor],
        start_ms: Optional[int] = None,
    ) -> Figure:
        run = Tools.run(run, join=True)
        t0 = time.monotonic()
        n = len(sensors)
        logger.info("Plotting {} sensors for r{}...".format(n, run.id))
        # set up the figure and gridspec
        figure = plt.figure(
            figsize=(chemfish_rc.trace_width, chemfish_rc.trace_layer_const_height + n * chemfish_rc.trace_layer_height)
        )
        gs = GridSpec(n + 1, 1, height_ratios=[1] * (n + 1), figure=figure)
        gs.update(hspace=chemfish_rc.trace_hspace)
        # plot the sensors in turn
        for i, data in enumerate(sensors):
            x_vals, y_vals = data.timing_data, data.sensor_data
            ax = figure.add_subplot(gs[i])
            if isinstance(data, MicrophoneWaveFormSensor):
                ax.scatter(
                    x_vals,
                    y_vals,
                    rasterized=chemfish_rc.sensor_rasterize,
                    s=chemfish_rc.sensor_mic_point_size,
                    c=chemfish_rc.sensor_mic_color,
                )
                ax.set_ylim(ymin=-1, ymax=1)
            else:
                ax.plot(
                    x_vals,
                    y_vals,
                    rasterized=chemfish_rc.sensor_rasterize,
                    linewidth=chemfish_rc.sensor_line_width,
                    c=chemfish_rc.sensor_line_color,
                )
                ax.set_ylim(
                    np.quantile(y_vals, 1 - self.quantile), np.quantile(y_vals, self.quantile)
                )
            ax.get_xaxis().set_ticks([])
            ax.get_yaxis().set_ticks([])
            label = data.symbol if chemfish_rc.sensor_use_symbols else data.abbrev
            ax.set_ylabel(label, rotation=(0 if chemfish_rc.sensor_use_symbols else 90))
            ax.set_xlim(data.bt_data.start_ms, data.bt_data.end_ms)
        # finally add the stimframes
        ax2 = figure.add_subplot(gs[n])
        self.stimplotter.plot(stimframes, ax=ax2, starts_at_ms=start_ms)
        ax2.set_ylabel(
            "⚑" if chemfish_rc.sensor_use_symbols else "stimuli",
            rotation=0 if chemfish_rc.sensor_use_symbols else 90,
        )
        FigureTools.stamp_runs(figure.axes[0], run)
        logger.minor("Plotted sensor data. Took {}s.".format(round(time.monotonic() - t0, 1)))
        return figure


__all__ = ["SensorPlotter"]
