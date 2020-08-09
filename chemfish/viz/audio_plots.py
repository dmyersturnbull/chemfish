import matplotlib.ticker as ticker
import librosa
import librosa.display as ldisplay
from chemfish.core.core_imports import *
from chemfish.model.audio import Waveform
from chemfish.viz.internal_viz import *
from chemfish.viz.figures import *


class WaveformPlotter(KvrcPlotting):
    def __init__(self, minimum: float = -1, maximum: float = 1):
        self.minimum, self.maximum = minimum, maximum

    def scatter(
        self,
        data: np.array,
        sampling_rate: float,
        n_ms: float,
        start_ms: Optional[float] = None,
        subtitle: Optional[str] = None,
        suptitle: Optional[str] = None,
        ax: Optional[Axes] = None,
    ) -> Figure:
        """
        Plots a scatterplot of the waveform.
        Also see `plot_waveform`, which is similar but uses librosa for display.
        :param start_ms:
        :param n_ms:
        :param sampling_rate:
        :param data:
        :param suptitle: Figure title
        :param subtitle: Axis title
        :param ax: The axes to plot on
        :return: The Matplotlib Figure
        """
        if ax is None:
            figure = plt.figure()
            ax = figure.add_subplot(1, 1, 1)
        figure = ax.get_figure()
        ax.scatter(
            np.arange(0, len(data)),
            data,
            c=KVRC.audio_waveform_color,
            s=KVRC.audio_waveform_point_size,
            clip_on=False,
            rasterized=KVRC.rasterize_waveforms,
        )
        if suptitle is not None:
            figure.suptitle(suptitle, y=KVRC.suptitle_y)
        if subtitle is not None:
            ax.set_title(subtitle)
        ax.set_xlim(0, len(data))
        ax.set_ylim(self.minimum, self.maximum)
        self._label_x(ax, sampling_rate, n_ms, start_ms)
        ax.set_yticks([])
        return figure

    def line(
        self,
        data: np.array,
        sampling_rate: float,
        n_ms: float,
        start_ms: Optional[float] = None,
        subtitle: Optional[str] = None,
        suptitle: Optional[str] = None,
        ax: Optional[Axes] = None,
    ) -> Figure:
        """
        Plots a line plot of the waveform using librosa waveplot.
        Also see `scatter`, which plots a simple scatterplot
        :param suptitle:
        :param subtitle:
        :param start_ms:
        :param n_ms:
        :param sampling_rate:
        :param data:
        :param ax: The axes to plot on; if set will ignore figsize
        :return: The Matplotlib Figure
        """
        if ax is None:
            figure = plt.figure(figsize=(KVRC.trace_width, KVRC.trace_height))
            ax = figure.add_subplot(1, 1, 1)
        else:
            figure = ax.get_figure()
        # TODO ignores max_sr=10?
        ldisplay.waveplot(
            data.astype(np.float32),
            ax=ax,
            sr=sampling_rate,
            color=KVRC.audio_waveform_color,
            linewidth=KVRC.audio_waveform_line_width,
        )
        if suptitle is not None:
            figure.suptitle(suptitle, y=KVRC.suptitle_y)
        if subtitle is not None:
            ax.set_title(subtitle)
        ax.set_xlabel("time (s)")
        # TODO set the x axis like the other plots
        # TODO also use start_ms
        ax.set_ylim(self.minimum, self.maximum)
        ax.set_xlim(0, n_ms / 1000)
        ax.set_yticks([])
        return figure

    def spectrogram(
        self,
        data: np.array,
        sampling_rate: float,
        n_ms: float,
        start_ms: Optional[float] = None,
        subtitle: Optional[str] = None,
        suptitle: Optional[str] = None,
        ax: Optional[Axes] = None,
    ) -> Figure:
        """
        Plots a spectrogram with ax.imshow. First calls librosa.amplitude_to_db on the data.
        Note that this does NOT use librosa for the plot.
        :param subtitle:
        :param suptitle:
        :param start_ms:
        :param n_ms:
        :param sampling_rate:
        :param data:
        :param ax: The axes to plot on; if set will ignore figsize
        :return: The Matplotlib Figure
        """
        # TODO why are some options ignored?
        if ax is None:
            figure = plt.figure()
            ax = figure.add_subplot(1, 1, 1)
        figure = ax.get_figure()
        d = librosa.amplitude_to_db(np.abs(librosa.stft(data.astype(np.float32))), ref=np.max)
        img = ax.imshow(
            d,
            cmap=FancyCmaps.white_blue()
            if KVRC.audio_spectrogram_cmap is None
            else KVRC.audio_spectrogram_cmap,
            aspect="auto",
        )
        cbar = FigureTools.add_aligned_colorbar(ax, img, number_format="%+2.0f dB")
        ax.set_ylabel("frequency (Hz)")
        ax.set_xlabel("time (s)")
        # TODO set the x axis like the other plots
        # TODO also use start_ms
        for i, tick in enumerate(cbar.ax.get_yticklabels()):
            tick.set_text(tick.get_text().replace("-", "−"))
            if i % 2 == 1:
                tick.set_visible(False)
        if suptitle is not None:
            figure.suptitle(suptitle, y=KVRC.suptitle_y)
        if subtitle is not None:
            ax.set_title(subtitle)
        return figure

    def _label_x(self, ax, sampling_rate: float, n_ms: float, start_ms: Optional[float]):
        starts_at_ms = 0 if start_ms is None else start_ms
        mark_every = InternalVizTools.preferred_tick_ms_interval(n_ms)
        units, units_per_sec = InternalVizTools.preferred_units_per_sec(mark_every, n_ms)
        mark_freq = mark_every / 1000 * sampling_rate
        total_x = sampling_rate * n_ms / 1000
        ax.set_xticks(np.arange(0, total_x, mark_freq))
        ax.set_xlabel("time ({})".format(units))
        ax.xaxis.set_major_formatter(
            ticker.FuncFormatter(
                lambda frame, pos: "{0:g}".format(
                    round((frame / sampling_rate + starts_at_ms / 1000) * units_per_sec), 1
                )
            )
        )


class WaveformPlots:
    @classmethod
    def scatter(cls, waveform: Waveform, ax: Optional[Axes] = None) -> Figure:
        """
        Plots a scatterplot of the waveform.
        Also see `plot_waveform`, which is similar but uses librosa for display.
        :param waveform Waveform to plot
        :param ax: The axes to plot on; if set will ignore figsize
        """
        return WaveformPlots._plot(waveform, "scatter", ax)

    @classmethod
    def plot_waveform(cls, waveform: Waveform, ax: Optional[Axes] = None) -> Figure:
        """
        Plots a line plot of the waveform using librosa waveplot.
        Also see `scatter`, which plots a simple scatterplot
        :param waveform Waveform to plot
        :param ax: The axes to plot on; if set will ignore figsize
        """
        return WaveformPlots._plot(waveform, "line", ax)

    @classmethod
    def plot_spectrogram(cls, waveform: Waveform, ax: Optional[Axes] = None) -> Figure:
        """
        Plots a spectrogram with ax.imshow. First calls librosa.amplitude_to_db on the data.
        Note that this does NOT use librosa for the plot.
        :param waveform Waveform to plot
        :param ax: The axes to plot on; if set will ignore figsize
        """
        return WaveformPlots._plot(waveform, "spectrogram", ax)

    @classmethod
    def _plot(cls, waveform: Waveform, plot_function: str, ax: Optional[Axes] = None) -> Figure:
        plotter = WaveformPlotter(waveform.minimum, waveform.maximum)
        return getattr(plotter, plot_function)(
            waveform.data.astype(np.float32),
            waveform.sampling_rate,
            waveform.n_ms,
            waveform.start_ms,
            waveform.name,
            waveform.description,
            ax=ax,
        )


__all__ = ["WaveformPlotter", "WaveformPlots"]
