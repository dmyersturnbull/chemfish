from matplotlib import dates as mdates

from chemfish.core.core_imports import *
from chemfish.model.metrics import *
from chemfish.viz._internal_viz import *
from chemfish.viz.figures import *


class TimelineLabelType(SmartEnum):
    NONE = enum.auto()
    TIMES = enum.auto()
    RUNS = enum.auto()
    PLATES = enum.auto()
    TAGS = enum.auto()
    DESCRIPTIONS = enum.auto()

    def process(self, runs: RunsLike) -> Optional[Sequence[str]]:
        runs = Tools.runs(runs)
        if self is TimelineLabelType.NONE:
            return ["" for _ in runs]
        elif self is TimelineLabelType.TIMES:
            return None
        elif self is TimelineLabelType.RUNS:
            return ["r" + str(r.id) for r in runs]
        elif self is TimelineLabelType.PLATES:
            return ["p" + str(r.plate_id) for r in runs]
        elif self is TimelineLabelType.TAGS:
            return [str(r.tag) for r in runs]
        elif self is TimelineLabelType.DESCRIPTIONS:
            return [str(r.description) for r in runs]
        else:
            raise XTypeError(str(self))


class DurationType(SmartEnum):
    WAIT = enum.auto()
    TREATMENT = enum.auto()
    ACCLIMATION = enum.auto()
    TREATMENT_TO_START = enum.auto()
    PLATING_TO_START = enum.auto()

    @property
    def description(self) -> str:
        if self is DurationType.TREATMENT_TO_START:
            return "time since treatment (min)"
        elif self is DurationType.PLATING_TO_START:
            return "time since plating (min)"
        else:
            return self.name.lower() + " duration"

    def get_minutes(self, run: RunLike) -> float:
        run = Tools.run(run, join=True)
        if self is DurationType.WAIT:
            return ValarTools.wait_sec(run) / 60
        elif self is DurationType.TREATMENT:
            return ValarTools.treatment_sec(run) / 60
        elif self is DurationType.ACCLIMATION:
            return run.acclimation_sec / 60
        elif self is DurationType.TREATMENT_TO_START:
            return (ValarTools.treatment_sec(run) + run.acclimation_sec) / 60
        elif self is DurationType.PLATING_TO_START:
            return (
                ValarTools.treatment_sec(run) + ValarTools.wait_sec(run) + run.acclimation_sec
            ) / 60
        else:
            raise XTypeError(str(self))


@abcd.auto_eq()
@abcd.auto_repr_str()
class TimelinePlotter(KvrcPlotting):
    """
    Plots timelines, mostly for when plates were run.
    Colors are assigned per experiment, with a legend label each.
    """

    def __init__(
        self,
        use_times: bool = False,
        date_format: str = "%Y-%m-%d",
        x_locator=mdates.DayLocator(),
        n_y_positions: int = 10,
    ):
        """
        :param use_times: Sets the y-values to the actual times; great for precision but tends to require a large height
        """
        self.use_times, self.date_format, self.x_locator = use_times, date_format, x_locator
        self.n_y_positions = n_y_positions

    def plot(
        self,
        dates: Sequence[datetime],
        experiments: Optional[Sequence[str]] = None,
        labels: Optional[Sequence[str]] = None,
    ):
        # fill in default values
        if experiments is None:
            experiments = ["" for _ in dates]
        if labels is None:
            labels = [
                str(idate.hour).zfill(2) + ":" + str(idate.minute).zfill(2) for idate in dates
            ]
        # sort
        data = sorted(list(Tools.zip_strict(dates, experiments)), key=lambda t: t[0])
        dates, experiments = [t[0] for t in data], [t[1] for t in data]
        # get colors
        if len(set(experiments)) > 1:
            colors = InternalVizTools.assign_colors_x(experiments, [None for _ in experiments])
        else:
            colors = ["black" for _ in experiments]
        # get min and max datetimes
        mn, mx = min(dates), max(dates)
        mn = datetime(mn.year, mn.month, mn.day, 0, 0, 0)
        mx = datetime(mx.year, mx.month, mx.day + 1, 0, 0, 0)
        halfway = mn + (mx - mn) / 2
        figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)
        ###############
        # plot
        ###############
        # the y_index will get reset to 0 each day
        y_index, last_date = 0, dates[0]
        for idate, iexp, icolor, ipretty in Tools.zip_list(dates, experiments, colors, labels):
            # reset so that the level always starts at 0 for each day
            if (
                idate.year != last_date.year
                or idate.month != last_date.month
                or idate.day != last_date.day
            ):
                y_index = 0
            # get the actual y-value in coordinates
            if self.use_times:
                y_val = idate.hour + idate.minute / 60
            else:
                y_val = (y_index % self.n_y_positions) - self.n_y_positions // 2
            # plot the markers
            ax.scatter(
                idate,
                y_val,
                marker=chemfish_rc.timeline_marker_shape,
                s=chemfish_rc.timeline_marker_size,
                c=icolor,
                alpha=1,
            )
            # weirdly, excluding this breaks everything
            ax.plot((idate, idate), (0, y_val), alpha=0)
            # show text
            horizontalalignment = "left" if idate < halfway else "right"
            xpos_offset = int(chemfish_rc.timeline_marker_size / 10)  # about right emperically
            xpos = idate + timedelta(
                hours=(xpos_offset if horizontalalignment == "left" else -xpos_offset)
            )
            ax.text(
                xpos,
                y_val,
                ipretty,
                horizontalalignment=horizontalalignment,
                verticalalignment="center",
            )
            y_index += 1
            last_date = idate
        # fix x ticks / locations / labels
        ax.xaxis.set_major_locator(self.x_locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter(self.date_format))
        ax.set_xlim(mn, mx)
        # remove y tick labels if they're just ordered
        if not self.use_times:
            ax.get_yaxis().set_ticks([])
        # fix x tick labels
        for x in ax.get_xticklabels():
            x.set_rotation(90)
            x.set_ha("center")
        # legend for experiments
        if any((e != "" for e in experiments)):
            FigureTools.manual_legend(ax, experiments, colors)
        return figure


class TimelinePlots:
    @classmethod
    def of(
        cls,
        runs: RunsLike,
        label_with: Union[str, TimelineLabelType],
        use_experiments=True,
        **kwargs,
    ) -> Figure:
        """
        :param runs:
        :param label_with: How to label individual runs; common choices are 'runs', 'plates', and 'times'.
        :param use_experiments: If True, chooses a different color (and legend item) per exeriment
        :param kwargs: These are passed to the `TimelinePlotter` constructor
        """
        runs = Tools.runs(runs)
        labels = TimelineLabelType.of(label_with).process(runs)
        experiments = [r.experiment.name for r in runs] if use_experiments else ["" for r in runs]
        dates = [r.datetime_run for r in runs]
        # Good example: BioMol plate BM-2811, master. Drugs: adrenergic
        figure = TimelinePlotter(**kwargs).plot(dates, experiments, labels=labels)
        return figure


class RunDurationPlotter:
    """
    Plotters for durations between events like treatment and running (a plate).
    """

    def __init__(self, attribute: str):
        self._attribute = attribute

    def plot(self, kde_in_minutes: KdeData) -> Figure:
        figure = plt.figure()
        ax = figure.add_subplot(1, 1, 1)
        minute_durations, support, density = (
            kde_in_minutes.samples,
            kde_in_minutes.support,
            kde_in_minutes.density,
        )
        ax.plot(support, density, color="black", alpha=0.9)
        ax.plot(minute_durations, np.zeros(len(minute_durations)), "|", color="#0000aa")
        ax.set_ylabel("N runs")
        ax.set_yticks([])
        ax.set_yticklabels([])
        ax.set_xlabel(self._attribute)
        if len({m for m in minute_durations if m < 0}) > 0:
            logger.error("Some {} durations are negative".format(self._attribute))
        ax.set_xlim(0, None)
        return ax.get_figure()


class RunDurationPlots:
    @classmethod
    def of(
        cls,
        runs: RunsLike,
        kind: Union[DurationType, str],
        kde_params: Optional[Mapping[str, Any]] = None,
    ) -> Figure:
        t = DurationType.of(kind)
        minutes = [t.get_minutes(r) for r in Tools.runs(runs)]
        kde = KdeData.from_samples(minutes, **({} if kde_params is None else kde_params))
        return RunDurationPlotter(t.description).plot(kde)


__all__ = [
    "TimelinePlotter",
    "RunDurationPlotter",
    "TimelineLabelType",
    "TimelinePlots",
    "DurationType",
    "RunDurationPlots",
]
