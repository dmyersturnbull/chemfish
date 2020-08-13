from __future__ import annotations

import traceback

from PIL.Image import Image

from chemfish.caches.audio_caches import *
from chemfish.caches.caching_wfs import *
from chemfish.caches.sensor_caches import *
from chemfish.caches.stim_caches import *
from chemfish.caches.video_caches import *
from chemfish.caches.wf_caches import *

# from chemfish.calc.chem import ChemSimplifer
# from chemfish.calc.chem_graphics import ChemGraphicsKit
from chemfish.core.core_imports import *
from chemfish.ml import *
from chemfish.ml.classifiers import *
from chemfish.ml.transformers import *
from chemfish.model.app_frames import *
from chemfish.model.assay_frames import *
from chemfish.model.compound_names import *
from chemfish.model.concerns import *
from chemfish.model.features import *
from chemfish.model.sensors import *
from chemfish.model.stim_frames import *
from chemfish.model.videos import *
from chemfish.model.well_names import *
from chemfish.model.wf_builders import *
from chemfish.viz._internal_viz import *
from chemfish.viz.figures import *
from chemfish.viz.heatmaps import *
from chemfish.viz.importance_plots import *
from chemfish.viz.sensor_plots import *
from chemfish.viz.stim_plots import *
from chemfish.viz.timeline_plots import *
from chemfish.viz.trace_plots import *
from chemfish.viz.well_plots import *

QLike = Union[ExpressionLike, pd.DataFrame, str, int, float, Runs, Submissions]
QsLike = Union[
    ExpressionLike,
    WellFrame,
    Union[int, Runs, Submissions, str],
    Iterable[Union[int, Runs, Submissions, str]],
]

DEFAULT_NAMER = WellNamers.elegant()

generation_feature_preferences = {
    **{g: FeatureTypes.MI for g in DataGeneration.pike_generations()},
    **{g: FeatureTypes.cd_10_i for g in DataGeneration.pointgrey_generations()},
    DataGeneration.HIGHSPEED_LEGACY: FeatureTypes.MI,
}


class AggType(SmartEnum):
    NONE = enum.auto()
    NAME = enum.auto()
    IMPORTANT = enum.auto()
    PACK = enum.auto()
    RUN = enum.auto()

    def function(self) -> Callable[[WellFrame], WellFrame]:
        return {
            "none": lambda df: df,
            "name": lambda df: df.agg_by_name(),
            "important": lambda df: df.agg_by_important(),
            "pack": lambda df: df.agg_by_pack(),
            "run": lambda df: df.agg_by_run(),
        }[self.name.lower()]

    def agg(self, df: WellFrame) -> WellFrame:
        return self.function()(df)


@abcd.external
@abcd.auto_info()
@abcd.auto_eq()
class Quick:
    """
    ..rst
    A collection of ways to get data and plot data with nice defaults.

    Each instance can (and generally should) hold every kind of on-disk cache in the caches package.
    Quick has enough arguments that they're best called using :class:`Quicks`.

    ### Methods

    Fetching methods:
    * `Quick.df`:                  Returns a WellFrame for one or more runs
    * `Quick.stim`:                Returns a StimFrame from a battery
    * `Quick.df_and_stims`:        Returns a WellFrame and a StimFrame
    * `Quick.video`:               Returns a SauronX video for a run
    * `Quick.microphone_waveform`: Returns the waveform from the microphone for a run
    * `Quick.stim_waveform`:       Returns the waveform from an audio stimulus
    * Some methods delegating to `Quick.sensor_cache`

    ### Plotting

    There are also plotting methods of a few types:

    * streaming, which return iterators of (name, Figure) tuples. These include:
        * `Quick.traces`:        Simple time-traces of motion averaged for each name
        * `Quick.smears`:        Time-traces of 'confidence' intervals (80th by default)
        * `Quick.zmears`:        Time-traces of 'confidence' intervals after taking a Z-score with respect to the controls.
    * heatmaps:
        * `Quick.rheat`:         White-to-black heatmaps of the raw features.
        * `Quick.zheat`:         Blue-to-white-to-red heatmaps of the Z-scores with respect to controls.
    * misc:
        * *diagonstics*:         Data from the time-dependent sensors alongside the stimframes
        * *bar*:                 Barplot of mean (or other aggregation) of the features per name
    * images:
        * `Quick.webcam_snap`:         Pillow image from the webcam
        * `Quick.roi_snap`:            Pillow image from the main camera's initial snapshot, with the well grid ROI overlaid
        * `Quick.structures_on_plate`: A grid of the chemical structures on the plate

    The streaming plotters each have two variants:

        * *singular* (ex `Quick.trace`), which call plt.show and return None.
        * *plural* (ex `Quick.traces`), which return the iterators and don't display them
    """

    def __init__(
        self,
        feature: Union[str, FeatureType],
        generation: Union[str, DataGeneration],
        as_of: datetime,
        cache: WellCache,
        facade: Optional[WellMemoryCache],
        stim_cache: StimframeCache,
        audio_stimulus_cache: AudioStimulusCache,
        sensor_cache: SensorCache,
        video_cache: VideoCache,
        enable_checks: bool = True,
        auto_fix: bool = True,
        discard_trash: Union[bool, Set[ControlLike]] = False,
        compound_namer: CompoundNamer = CompoundNamers.tiered(),
        default_namer: Optional[WellNamer] = DEFAULT_NAMER,
        quantile: Optional[float] = 0.95,
        trace_ymax: Optional[float] = None,
        zscore_min_max: Optional[float] = None,
        smoothing_factor: float = 0.1,
    ):
        """
        Builds a new Quick.
        WARNING: The details of the arguments auto_fix and enable_checks are subject to change.
        In particular, more auto-fixes could be added in the future. If this is unacceptable for your use, disable this option.
        :param feature: Generate WellFrames and plots using this feature.
        :param generation: Generation permitted
        :param as_of: Enables additional methods by setting max datetime for those queries. This includes querying by flexible Peewee Expressions
        :param cache: A FrameCache for saving WellFrames on disk
        :param facade: An optional FrameFacade for saving WellFrames into memory
        :param stim_cache: A StimCache for saving StimFrames objects on disk
        :param default_namer: By default, draw WellFrames with this Namer
        :param enable_checks: Warn about missing frames, 'concern' rows in the annotations table, suspicious batches, and more; see Concerns.warn_common_checks for full info
        :param auto_fix: Applies fixes to WellFrames
        :param sensor_cache: A SensorCache.
        :param video_cache: A VideoCache.
        :param compound_namer: Fill in 'compound_names' column in WellFrame using this function. May also be used in other places.
                                NOTE: A copy will be made with `compound_namer.as_of` set to `as_of`.
        :param audio_stimulus_cache: An AudioStimulusCache for caching audio files, etc.
        :param quantile: A quantile for setting min and max on various plot types, including sensor plots and z-score plots (also see zscore_min_max)
        :param trace_ymax: If set, limit the y axis on traces to this; great for features like cd(10) but less so for MI
        :param zscore_min_max: If set, limit zmear bounds to +/- this value; otherwise a percentile will be chosen
        :param discard_trash: Automatically discard wells with control type in Concerns.trash_controls if True, or a passed set
        :param smoothing_factor: This times the frames per second = default smoothing window size
        """
        if as_of > datetime.now():
            logger.warning(
                "as_of is set {} in the future".format(
                    Tools.delta_time_to_str((as_of - datetime.now()).total_seconds())
                )
            )
        if cache is not None and facade is not None:
            raise ContradictoryRequestError(
                "Must specify either cache or facade, or none. This is because a facade is already backed by its own cache."
            )
        self.feature = FeatureTypes.of(feature)
        self.generation = DataGeneration.of(generation)
        self.as_of = as_of
        self.default_namer = default_namer
        self.compound_namer = copy(compound_namer)
        self.compound_namer.as_of = as_of
        self.facade = facade
        self.well_cache = facade.cache if facade is not None else cache
        self.stim_cache = stim_cache
        # TODO this ignores the cache dir
        self.expanded_stim_cache = StimframeCache(
            waveform_loader=audio_stimulus_cache.load_waveform
        )
        self.sensor_cache = sensor_cache
        self.video_cache = video_cache
        self.audio_stimulus_cache = audio_stimulus_cache
        self.enable_checks = enable_checks
        self.auto_fix = auto_fix
        self.quantile = quantile
        self.trace_ymax = trace_ymax
        self.zscore_min_max = zscore_min_max
        if discard_trash is False:
            self.discard_trash = set()
        elif discard_trash is True:
            control_types = {c.name: c for c in ControlTypes.select()}
            self.discard_trash = {
                c: control_types[c]
                for c in {"ignore", "near-WT (-)", "no drug transfer", "low drug transfer"}
            }
        else:
            self.discard_trash = discard_trash
        self.smoothing_factor = smoothing_factor
        self.min_log_severity = Severity.CAUTION

    def trace(
        self,
        run: QsLike,
        smoothing: Optional[int] = None,
        namer: Optional[WellNamer] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        control_names=None,
        control_types=None,
        weights: Optional[np.array] = None,
        label_assays: bool = False,
        always_plot_control: bool = False,
        agg_type: Union[AggType, str] = AggType.NAME,
    ) -> None:
        for name, figure in self.traces(
            run,
            smoothing=smoothing,
            namer=namer,
            start_ms=start_ms,
            end_ms=end_ms,
            control_names=control_names,
            control_types=control_types,
            weights=weights,
            label_assays=label_assays,
            always_plot_control=always_plot_control,
            agg_type=agg_type,
        ):
            plt.show(figure)

    def traces(
        self,
        run: QsLike,
        smoothing: Optional[int] = None,
        namer: Optional[WellNamer] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        control_names=None,
        control_types=None,
        weights: Optional[np.array] = None,
        label_assays: bool = False,
        always_plot_control: bool = False,
        agg_type: Union[AggType, str] = AggType.NAME,
    ) -> Iterator[Tup[str, Figure]]:
        (
            df,
            stimframes,
            assays,
            control_names,
            fps,
            stimplotter,
            extra_gs,
            extra_fn,
        ) = self._everything(
            run, namer, start_ms, end_ms, control_names, control_types, weights, label_assays
        )
        battery = df.only("battery_id")
        if smoothing is None:
            smoothing = int(round(self.smoothing_factor * fps))
        tracer = TracePlotter(
            feature=self.feature,
            stimframes_plotter=stimplotter,
            extra_gridspec_slots=extra_gs,
            always_plot_control=always_plot_control,
            y_bounds=(0, self.trace_ymax) if self.trace_ymax else None,
        )
        run_dict = {
            n: df.with_name(n).unique_runs() for n in df.unique_names()
        }  # prior to agg_samples
        agged = AggType.of(agg_type).agg(df)
        return tracer.plot(
            agged.smooth(window_size=smoothing),
            stimframes,
            control_names=control_names,
            starts_at_ms=start_ms,
            extra=extra_fn,
            run_dict=run_dict,
            assays=assays,
            battery=battery,
        )

    '''
    def structures(self, *compounds, **kwargs) -> Image:
        return ChemGraphicsKit().draw_grid(compounds, **kwargs)

    def structures_on_plate(
        self, run: RunLike, simplify: bool = False, aggressive: bool = False
    ) -> Image:
        """
        Plots a grid of the compound structures on the plate.
        :param run: A run ID, instance, name, or tag, or submission hash or instance
        :param simplify: Desalts and deduplicates structures
        :param aggressive: Simplify 'aggressively', removing all but the largest connected component of each structure
        :return: A Pillow Image
        """
        run = ValarTools.run(run)
        kit = ChemGraphicsKit(ChemSimplifer(aggressive).simplify if simplify else lambda s: s)

        def nameit(wt: WellTreatments) -> str:
            if wt.batch.compound is None:
                return "b" + str(wt.batch.id)
            vals = self.compound_namer.fetch(wt.batch.compound)
            return "; ".join(["b" + str(k) if v is None else v for k, v in vals.items()])

        return kit.draw_plate(run, labels=nameit)
    '''

    def smear(
        self,
        run: QsLike,
        smoothing: Optional[int] = None,
        namer: Optional[WellNamer] = None,
        ci: float = 0.8,
        show_means: bool = False,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        control_names=None,
        control_types=None,
        weights: Optional[np.array] = None,
        label_assays: bool = False,
    ) -> None:
        for name, figure in self.smears(
            run,
            smoothing=smoothing,
            namer=namer,
            ci=ci,
            show_means=show_means,
            start_ms=start_ms,
            end_ms=end_ms,
            control_names=control_names,
            control_types=control_types,
            weights=weights,
            label_assays=label_assays,
        ):
            plt.show(figure)

    def smears(
        self,
        run: QsLike,
        smoothing: Optional[int] = None,
        namer: Optional[WellNamer] = None,
        ci: float = 0.8,
        show_means: bool = False,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        control_names=None,
        control_types=None,
        weights: Optional[np.array] = None,
        label_assays: bool = False,
        always_plot_control: bool = False,
    ) -> Iterator[Tup[str, Figure]]:
        (
            df,
            stimframes,
            assays,
            control_names,
            fps,
            stimplotter,
            extra_gs,
            extra_fn,
        ) = self._everything(
            run, namer, start_ms, end_ms, control_names, control_types, weights, label_assays
        )
        battery = df.only("battery_id")
        if smoothing is None:
            smoothing = int(round(self.smoothing_factor * fps))
        top_bander, bottom_bander, mean_bander = self._banders(ci, smoothing, show_means)
        run_dict = {
            n: df.with_name(n).unique_runs() for n in df.unique_names()
        }  # prior to agg_samples
        tracer = TracePlotter(
            feature=self.feature,
            stimframes_plotter=stimplotter,
            always_plot_control=always_plot_control,
            bottom_bander=bottom_bander,
            top_bander=top_bander,
            mean_bander=mean_bander,
            extra_gridspec_slots=extra_gs,
            y_bounds=(0, self.trace_ymax),
        )
        return tracer.plot(
            df,
            stimframes,
            control_names=control_names,
            starts_at_ms=start_ms,
            extra=extra_fn,
            run_dict=run_dict,
            battery=battery,
        )

    def zmear(
        self,
        run: QsLike,
        control_type: Union[None, str, int, ControlTypes] = None,
        control_name: Optional[str] = None,
        smoothing: Optional[int] = None,
        namer: Optional[WellNamer] = None,
        ci: float = 0.8,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        weights: Optional[np.array] = None,
        subtraction=None,
    ) -> None:
        for name, figure in self.zmears(
            run,
            control_type=control_type,
            control_name=control_name,
            smoothing=smoothing,
            namer=namer,
            ci=ci,
            start_ms=start_ms,
            end_ms=end_ms,
            weights=weights,
            subtraction=subtraction,
        ):
            plt.show(figure)

    def zmears(
        self,
        run: QsLike,
        control_type: Union[None, str, int, ControlTypes] = None,
        control_name: Optional[str] = None,
        smoothing: Optional[int] = None,
        namer: Optional[WellNamer] = None,
        ci: float = 0.8,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        weights: Optional[np.array] = None,
        subtraction=None,
        label_assays: bool = False,
    ) -> Iterator[Tup[str, Figure]]:
        (
            df,
            stimframes,
            assays,
            control_name,
            fps,
            stimplotter,
            extra_gs,
            extra_fn,
        ) = self._everything(
            run, namer, start_ms, end_ms, control_name, control_type, weights, label_assays
        )
        battery = df.only("battery_id")
        if smoothing is None:
            smoothing = int(round(self.smoothing_factor * fps))
        if control_name is None:
            control_name = df.with_controls().unique_names()
        control_name = Tools.only(control_name, name="control types")
        zscores = self._control_subtract(
            df, control_type, control_name, subtraction=subtraction
        ).agg_by_name()
        if self.zscore_min_max is None:
            y_min = zscores.quantile(0.001, axis=1).min()
            y_max = zscores.quantile(0.999, axis=1).max()
        else:
            y_min, y_max = -self.zscore_min_max, self.zscore_min_max
        top_bander, bottom_bander, mean_bander = self._banders(
            ci, smoothing, True
        )  # TODO True, right?
        run_dict = {
            n: df.with_name(n).unique_runs() for n in df.unique_names()
        }  # prior to agg_samples
        tracer = TracePlotter(
            feature=self.feature,
            stimframes_plotter=stimplotter,
            bottom_bander=bottom_bander,
            top_bander=top_bander,
            mean_bander=mean_bander,
            mean_band_color="black",
            with_bar=True,
            extra_gridspec_slots=extra_gs,
            y_bounds=(y_min, y_max),
        )
        traces = tracer.plot(
            zscores,
            stimframes,
            starts_at_ms=start_ms,
            extra=extra_fn,
            control_names=control_name,
            run_dict=run_dict,
            battery=battery,
        )
        for name, figure in traces:
            figure.axes[0].set_ylabel(
                "Z-score [{}]".format(KVRC.feature_names[self.feature.internal_name])
            )
            yield name, figure

    def _banders(self, ci, smoothing, show_means):
        top_bander = lambda group: group.agg_by_name(lambda s: s.quantile(ci)).smooth(
            window_size=smoothing
        )
        bottom_bander = lambda group: group.agg_by_name(lambda s: s.quantile(1 - ci)).smooth(
            window_size=smoothing
        )
        mean_bander = (
            (lambda group: group.agg_by_name().smooth(window_size=smoothing))
            if show_means
            else None
        )
        return top_bander, bottom_bander, mean_bander

    def zheat(
        self,
        run: QsLike,
        control_type: Union[None, str, int, ControlTypes] = None,
        control_name: Optional[str] = None,
        threshold: float = 1.0,
        namer: Optional[WellNamer] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        show_control_lines: bool = True,
        show_name_lines: bool = True,
        ignore_controls: bool = False,
    ) -> Figure:
        """
        Makes a heatmap of z-scores with respect to controls.
        If neither control_type nor control_name are set, looks for a single negative control and uses that.
        If either is set, uses that one. Will raise a UserContradictionError if both are set.
        :param show_name_lines: Show horizontal lines between different names
        :param show_control_lines: Show horizontal lines between different control types
        :param run: A run ID, name, or object
        :param control_type: The name, ID, or object of a ControlTypes; or None
        :param control_name: The name of an item in WellFrame.names(); or None
        :param threshold: Show anything with a value +/- this as pure white
        :param namer: A namer for WellFrameBuilder
        :param start_ms: Cuts the dataframes, calculating milliseconds from the known framerate
        :param end_ms: Cuts the dataframes, calculating milliseconds from the known framerate
        :param ignore_controls: Don't plot any control wells
        :return: The matplotlib Figure
        """
        df, stimframes = self.df_and_stims(run, namer, start_ms, end_ms, audio_waveform=None)
        fps = self._stimframes_per_second(df)
        battery = df.only("battery_id")
        stimplotter = StimframesPlotter(fps=fps)
        zscores = self._control_subtract(df, control_type, control_name).threshold_zeros(threshold)
        if ignore_controls:
            zscores = zscores.without_controls_matching()
        heater = HeatPlotter(
            symmetric=True,
            stimframes_plotter=stimplotter,
            vmax_quantile=self.quantile,
            name_sep_line=show_name_lines,
            control_sep_line=show_control_lines,
        )
        figure = heater.plot(zscores, stimframes, starts_at_ms=start_ms, battery=battery)
        return figure

    def rheat(
        self,
        run: QsLike,
        namer: Optional[WellNamer] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        show_name_lines: bool = True,
    ) -> Figure:
        df, stimframes = self.df_and_stims(run, namer, start_ms, end_ms, audio_waveform=None)
        battery = df.only("battery_id")
        stimplotter = StimframesPlotter(fps=self._stimframes_per_second(df))
        heater = HeatPlotter(stimframes_plotter=stimplotter, name_sep_line=show_name_lines)
        return heater.plot(df, stimframes, starts_at_ms=start_ms, battery=battery)

    def tsne(
        self,
        run: QsLike,
        namer: Optional[WellNamer] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        outlier_stds: Optional[float] = 5,
        path_stub: Optional[PLike] = None,
        **kwargs,
    ) -> Tup[WellFrame, Figure]:
        all_params = {"outlier_stds": outlier_stds, **kwargs}
        # noinspection PyTypeChecker
        transform = SklearnTransform(TSNE(**kwargs))
        if outlier_stds is not None:
            transform = WellTransforms.compose(transform, OutlierStdTransform(outlier_stds))
        return self.transform(
            run,
            transform,
            all_params,
            namer=namer,
            start_ms=start_ms,
            end_ms=end_ms,
            path_stub=path_stub,
        )

    def transform(
        self,
        run: QsLike,
        transform: WellTransform,
        all_params: Mapping[str, Any],
        recolor: bool = True,
        namer: Optional[WellNamer] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        path_stub: Optional[PLike] = None,
    ) -> Tup[WellFrame, Figure]:
        df = self.df(run, namer=namer, start_ms=start_ms, end_ms=end_ms)
        trans = transform.fit(df)
        if path_stub is not None:
            path_stub = Path(path_stub)
            trans.to_hdf(path_stub.with_suffix(".transform.h5"))
            Tools.save_json(all_params, path_stub.with_suffix(".transform.json"))
            logger.info(
                "Saved {} and {}".format(
                    path_stub.with_suffix(".transform.h5"), path_stub.with_suffix(".transform.json")
                )
            )
        figure = WellPlotters.basic(trans, recolor=recolor)
        if path_stub is not None:
            FigureSaver().save(figure, path_stub.with_suffix(".transform.pdf"))
        return trans, figure

    def classify(
        self,
        run: QsLike,
        save_dir: Optional[PLike] = None,
        namer: Optional[WellNamer] = None,
        model_fn: SklearnWfClassifierWithOob = WellForestClassifier,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        color: bool = False,
        sort: bool = True,
        load_only: bool = False,
        **kwargs,
    ) -> WellForestClassifier:
        save_dir = Tools.prepped_dir(save_dir, exist_ok=False)
        save_dir = ClassifierPath(save_dir)
        df = self.df(run, namer=namer, start_ms=start_ms, end_ms=end_ms)
        model = model_fn.build(**kwargs)
        if save_dir.exists():
            logger.info("Loading existing model at {}".format(save_dir))
            model.load(save_dir)
        elif load_only:
            raise OpStateError("Model at {} trained".format(save_dir))
        else:
            model.train(df)
        if color:
            controls = df.with_controls().sort_values("control_type")
            label_colors = InternalVizTools.assign_color_dict_x(
                controls.names(), controls["control_type"]
            )
        else:
            label_colors = None
        model.save_to_dir(save_dir, figures=True, sort=sort, label_colors=label_colors)
        # now let's color a confusion matrix
        FigureTools.clear()
        return model

    def diagnostics(
        self,
        run: RunLike,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        sensors: Optional[Sequence[Union[SensorNames, str]]] = None,
    ) -> Figure:
        run = Tools.run(run, join=True)
        if sensors is None:
            sensors = ["thermistor", "photoresistor", "microphone"]
        stimframes = self.stim(run.experiment.battery, start_ms, end_ms, audio_waveform=True)
        stimplotter = StimframesPlotter(
            audio_waveform=True,
            fps=ValarTools.battery_stimframes_per_second(run.experiment.battery),
        )
        sensor_data = []
        for sensor in sensors:
            sensor = SensorNames.of(sensor)
            if sensor == SensorNames.MICROPHONE:
                sensor_data.append(
                    self.sensor_cache.load((SensorNames.MICROPHONE, run)).waveform(1000)
                )
            else:
                self.sensor_cache.load((sensor, run)).slice_ms(start_ms, end_ms)
        return SensorPlotter(stimplotter=stimplotter, quantile=self.quantile).diagnostics(
            run, stimframes, sensor_data, start_ms=start_ms
        )

    def durations(self, runs: RunsLike, kind: DurationType) -> Figure:
        return RunDurationPlots.of(runs, kind)

    def timeline(
        self,
        runs: QsLike,
        label_with: Union[str, TimelineLabelType] = TimelineLabelType.TIMES,
        use_experiments: bool = True,
        **kwargs,
    ) -> Figure:
        return TimelinePlots.of(runs, label_with, use_experiments=use_experiments, **kwargs)

    def stim_plot(
        self,
        battery: Union[StimFrame, Batteries, int, str],
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        audio_waveform: bool = True,
        label_assays: bool = False,
        stimframes: Optional[BatteryStimFrame] = None,
    ) -> Figure:
        """
        :param battery:
        :param start_ms:
        :param end_ms:
        :param audio_waveform:
        :param label_assays:
        :param stimframes: If supplied:
                - `audio_waveform` is ignored
                - `start_ms` and `end_ms` will be attempted, BUT!
                    If `stimframes` was already sliced, the result will be wrong
        :return:
        """
        battery = Batteries.fetch(battery)
        assays = AssayFrame.of(battery)
        sfps = ValarTools.battery_stimframes_per_second(battery)
        if stimframes is None:
            stimframes = self.stim(battery, start_ms, end_ms, audio_waveform)
        else:
            stimframes = stimframes.slice_ms(battery, start_ms, end_ms)
            audio_waveform = False
        plotter = StimframesPlotter(
            fps=sfps, audio_waveform=audio_waveform, assay_labels=label_assays
        )
        ax = plotter.plot(stimframes, assays=assays, starts_at_ms=start_ms, battery=battery)
        return ax.get_figure()

    def df_and_stims(
        self,
        run: QsLike,
        namer: Optional[WellNamer] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        audio_waveform: Optional[bool] = None,
    ) -> Tup[WellFrame, BatteryStimFrame]:
        """
        Fetches both a WellFrame and a BatteryStimFrame for it.
        See `Quick.df` and `Quick.stim` for more info.
        WARNING:
            If the battery is not unique for the passed WellFrame, will emit a warning and use the battery with the lowest ID.
        :param run: Anything accepted by `Quick.df`
        :param namer: A Namer to set `WellFrame['name']`, or None to use `self.default_namer`.
        :param start_ms: The milliseconds after the first frame to slice starting at, or None to mean 0; uses the ideal framerate
        :param end_ms: The milliseconds after the first frame to slice until, or None to mean the feature end; uses the ideal framerate
        :param audio_waveform: Replace the audio stimuli with the values of a standardized waveform; great for plotting.
                Generally only useful for plotting.
                If None then set True iff the battery is SauronX.
        :return: The WellFrame
        :raises MultipleMatchesError: If multiple batteries were found
        """
        df = self.df(run, namer, start_ms, end_ms)
        battery = df.only("battery_name")
        stimframes = self.stim(battery, start_ms, end_ms, audio_waveform=audio_waveform)
        return df, stimframes

    def assays(self, battery: Union[Batteries, int, str]) -> AssayFrame:
        return AssayFrame.of(battery)

    def apps(self, battery: Union[Batteries, int, str]) -> AppFrame:
        return AppFrame.of(battery)

    def stim(
        self,
        battery: BatteryLike,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        audio_waveform: Optional[bool] = False,
    ) -> BatteryStimFrame:
        """
        Get a BatteryStimFrame for a battery
        :param battery: A battery name, ID, or instance
        :param start_ms: The milliseconds after the first frame to slice starting at, or None to mean 0; uses the ideal framerate
        :param end_ms: The milliseconds after the first frame to slice until, or None to mean the feature end; uses the ideal framerate
        :param audio_waveform: Replace the audio stimuli with the values of a standardized waveform; great for plotting.
                Generally only useful for plotting.
                If None then set True iff the battery is SauronX.
        :return: BatteryStimFrame
        """
        battery = Batteries.fetch(battery)
        if audio_waveform is None:
            audio_waveform = ValarTools.battery_is_legacy(battery)
        if audio_waveform:
            stimframes = self.expanded_stim_cache.load(battery)
        else:
            stimframes = self.stim_cache.load(battery)
        return stimframes.slice_ms(battery, start_ms, end_ms)

    def video(self, run: RunLike) -> SauronxVideo:
        run = ValarTools.run(run)
        return self.video_cache.load(run)

    def microphone_waveform(
        self, run: RunLike, start_ms: Optional[int] = None, end_ms: Optional[int] = None
    ) -> MicrophoneWaveform:
        run = ValarTools.run(run)
        x: MicrophoneWaveform = self.sensor_cache.load(SensorNames.MICROPHONE, run)
        return x.slice_ms(start_ms, end_ms)

    def stim_waveform(self, stimulus: StimulusLike) -> StimulusWaveform:
        return self.audio_stimulus_cache.load_waveform(stimulus)

    def webcam_snap(self, run: RunLike) -> Image:
        return self.sensor_cache.load(SensorNames.WEBCAM, run).sensor_data

    def roi_snap(self, run: RunLike) -> Image:
        return self.sensor_cache.load(SensorNames.PREVIEW, run).sensor_data

    def battery_time_data(self, run: RunLike) -> BatteryTimeData:
        return self.sensor_cache.bt_data(run)

    def df(
        self,
        run: QsLike,
        namer: Optional[WellNamer] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> WellFrame:
        """
        Gets a WellFrame from any of:
            - A run ID, name, tag, or instance, or submission hash or instance
            - An iterable of any of the above
            - A WellFrame or DataFrame to be converted to a WellFrame
        If a WellFrame is passed, will return it immediately if no options are passed.
        For example, will only autofix if the DataFrame is fetched from a cache or Valar.
        More details are below.
        Rules for setting the WellFrame names:
            - In every case, will set the name column if `namer` is passed.
            - If `namer` is not set and `run` is a WellFrame or DataFrame, will keep the names of the passed WellFrame
            - If `namer` is not set and `run` is neither of those, will set the names with `self.default_namer`.
        Rules about sorting:
            - If `run` is a WellFrame or DataFrame, will keep its sorting
            - Otherwise will call `WellFrame.sort_std`.
        Applying fixes and checks:
            1) If `self.enable_checks` is True, will output warnings about the data to stdout.
            2) If `self.auto_fix` is True, will apply data standardization and fixes. These will happen after slicing (if applicable).
            2) If `self.discard_trash_controls` is not False, will discard those wells (if fresh).
        :param run: Any of the above
        :param namer: A Namer to set `WellFrame['name']`, or None to use `self.default_namer` unless passing a WellFrame (in which case the existing names are used).
        :param start_ms: The milliseconds after the first frame to slice starting at, or None to mean 0; uses the ideal framerate
        :param end_ms: The milliseconds after the first frame to slice until, or None to mean the feature end; uses the ideal framerate
        :return: The WellFrame
        """
        return self._df(run, namer, start_ms, end_ms)

    def errors(self, df: WellFrame) -> None:
        """
        Raises errors for issues with this WellFrame.
        Called internally by `Quick.df`, but may also be useful outside.
        :raises MultipleGenerationsError
        :raises IncompatibleGenerationError
        """
        used_generations = {ValarTools.generation_of(run) for run in df.unique_runs()}
        if len(used_generations) > 1:
            raise MultipleGenerationsError(
                "Got multiple generations in quick.df {}".format(used_generations)
            )
        used_generation = next(iter(used_generations))
        if used_generation is not self.generation:
            raise IncompatibleGenerationError(
                "Wrong generation {}; expected {}".format(used_generation, self.generation)
            )

    def spit_concerns(
        self,
        wheres: ExpressionsLike,
        min_severity: Severity = Severity.GOOD,
        as_of: Optional[datetime] = None,
        path: Optional[PLike] = None,
    ) -> Sequence[Concern]:
        """
        Finds `Concern`s on runs matching the conditions `wheres` (which are processed by `Quick.query_runs`).
        Saves the information as a CSV spreadsheet periodically (every 10 runs) while processing.
        """
        q0 = copy(self)
        q0.enable_checks = False
        q0.auto_fix = False
        q0.as_of = datetime.now()
        runs = q0.query_runs(wheres)
        logger.notice("Spitting issues for {} runs".format(len(runs)))
        coll = SimpleConcernRuleCollection(q0.feature, q0.sensor_cache, as_of, min_severity)
        concerns = []
        for i, run in enumerate(Tools.loop(runs, log=logger.info, every_i=10)):
            try:
                df = q0.df(run)
                concerns.extend(list(coll.of(df)))
            except Exception as e:
                concerns.append(
                    LoadConcern(run, Severity.CRITICAL, e, traceback.extract_tb(e.__traceback__))
                )
            if i % 10 == 0 and path is not None:
                Concerns.to_df(concerns).to_csv(path)
        if path is not None:
            Concerns.to_df(concerns).to_csv(path)
        return concerns

    def query_runs(self, wheres: Union[RunsLike, ExpressionsLike]) -> List[Runs]:
        """
        Return a list of `Run`s matching all of the expressions given.
        The following tables are joined on.
            Runs, Experiments, Projects, ProjectTypes, Batteries, Submissions, SauronConfigs, Saurons, Users, Plates
        Ex: `query_runs([Batteries.id == 99, Saurons.id == 4)]`
        """
        wheres = InternalTools.listify(wheres)
        try:
            # select while joining on the tables below
            wheres = Runs.id << {r.id for r in Tools.runs(wheres)}
        except:
            pass
        query = (
            Runs.select(
                Runs,
                Experiments,
                Projects,
                ProjectTypes,
                Batteries,
                Submissions,
                SauronConfigs,
                Saurons,
                Users,
                Plates,
            )
            .join(Experiments)
            .join(Projects)
            .join(ProjectTypes, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Batteries)
            .switch(Runs)
            .join(Submissions, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(SauronConfigs)
            .join(Saurons)
            .switch(Runs)
            .join(Users)
            .switch(Runs)
            .join(Plates)
        )
        for where in wheres:
            query = query.where(where)
        return list(query)

    def log_concerns(self, df: WellFrame, min_severity: Severity = Severity.CAUTION) -> None:
        """
        Emit logger messages for concerns in this WellFrame, only for level >= `min_severity`.
        Also see `Quick.concerns`.
        """
        c = Concerns.of(df, self.feature, self.sensor_cache, as_of=None, min_severity=min_severity)
        Concerns.log_warnings(c)

    def fix(self, df):
        """
        Applies fixes.
        These are performed automatically when auto_fix=True.
        These fixes are:
            - 0s between assays for legacy run
            - NaN "unification": If any well has a NaN in a position, sets all wells to have NaN there
            - Discarding "trash" wells, IF discard_trash is set
        """
        if (
            self.auto_fix
            and self.feature is not None
            and self.feature.time_dependent
            and self.generation in [DataGeneration.PIKE_LEGACY_MATT, DataGeneration.PIKE_MGH]
        ):
            # This block deals with a weird problem in legacy data:
            # Because there were hidden gaps of time between assays, the value at the start of each assay
            # was set to 0. This is weird for analysis and plotting.
            # To fix it, we'll use WellFrame.completion to fill in these gaps.
            # _BUT_: WellFrame.completion needs to fill 0s AND NaNs.
            # If there are missing frames at the end represented as NaNs, we want to leave them alone.
            # So, replace the NaNs with -1.0, then call WellFrame.completion, then fill the NaNs again.
            # For simplicity, we'll do all three steps even if there are no assay gaps.
            n_unified = df.unify_last_nans_inplace(fill_value=-1.0)
            if self.feature.internal_name == FeatureTypes.MI.internal_name:
                n_zeros = (df.values == 0).astype(int).sum()
                if n_zeros.any() > 0:
                    logger.warning("MI trace contains 0s and might have breaks between assays.")
                    df = WellFrame.retype(df.completion().replace(-1.0, np.NaN))
            if n_unified > 0:
                logger.warning("Unified {} NaNs at the end".format(n_unified))
            df = WellFrame.retype(df.fillna(0))
        elif self.auto_fix:
            # if the feature is not interpolated, n_unified_start will always be 0
            n_unified_start = df.unify_first_nans_inplace(0)
            n_unified_end = df.unify_last_nans_inplace(0)
            if n_unified_start > 1 or n_unified_end > 1:
                logger.warning(
                    "Unified {} {} at the start and {} at the end".format(
                        n_unified_start, "NaNs" if n_unified_start > 1 else "NaN", n_unified_end
                    )
                )
        n = len(df)
        if len(self.discard_trash) > 0:
            df = df.without_controls_matching(names=self.discard_trash)
            if len(df) != n:
                logger.caution("Discarded {} trash controls".format(len(df) - n))
        return df

    def _df(
        self,
        run: QsLike,
        namer: Optional[WellNamer] = None,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> WellFrame:
        try:
            df, is_fresh = self._fetch_df(run)
            if is_fresh:
                # note that adding compound_names only when is_fresh can lead to unexpected results
                # I don't see a better alternative though
                if self.compound_namer is not None:
                    df = df.with_new_compound_names(self.compound_namer)
                # MAKE SURE to check for errors and warnings BEFORE slicing or fixing
                self.errors(df)
                if self.enable_checks:
                    self.log_concerns(df, min_severity=self.min_log_severity)
                df = df.slice_ms(start_ms, end_ms)
                if self.auto_fix:
                    df = self.fix(df)
            else:
                # we still need to slice it if it's not fresh
                df = df.slice_ms(start_ms, end_ms)
            if namer is not None:
                df = df.with_new_names(namer)
                df = df.with_new_display_names(namer)
        except NoFeaturesError as err:
            # we can't raise in an except block or we'll get a "During handling of the above exception"
            if isinstance(err, NoFeaturesError):
                msg = self._no_such_features_message(run)
                raise NoFeaturesError(msg) from None
            else:
                raise err
        return df

    def _no_such_features_message(self, run):
        if isinstance(run, (str, int, float, Runs, Submissions)):
            return "The feature {} is not defined on run r{}. These are: {}".format(
                self.feature, run, ", ".join(ValarTools.features_on(run))
            )
        elif isinstance(run, ExpressionLike):
            with Tools.silenced(no_stdout=True, no_stderr=False):
                x = WellFrameBuilder(self.as_of).where(run).build().unique_runs()
            feats_map = {r: ValarTools.features_on(r) for r in x}
            missing = [
                "r" + str(k)
                for k, v in feats_map.items()
                if self.feature.valar_feature.name not in v
            ]
            return "The feature {} is not defined on runs {}.".format(
                self.feature, ",".join(missing)
            )
        else:
            feats_defined = (
                "["
                + "; ".join(
                    [
                        "r" + str(ValarTools.run(r)) + ": " + ", ".join(ValarTools.features_on(r))
                        for r in run
                    ]
                )
                + "]"
            )
            return "The feature {} is not defined on runs {}. These are: {}".format(
                self.feature,
                ",".join(["r" + str(r.id) for r in ValarTools.runs(run)]),
                feats_defined,
            )

    def _fetch_df(self, run) -> Tup[WellFrame, bool]:
        # ignore limit and generation if fresh
        if isinstance(run, WellFrame) or isinstance(run, pd.DataFrame):
            return WellFrame.of(run), False
        # If namer= was passed, it will be used in df()
        # For now, use default_namer if a WellFrame (or WellFrame in disguise) wasn't passed
        # Otherwise, use what was already there
        # If it's a WellFrame or dataframe, leave it alone
        # Ok, great. Now build from the appropriate place
        if isinstance(run, ExpressionLike):
            run = [run]
        is_expression = Tools.is_true_iterable(run) and all(
            (isinstance(r, ExpressionLike) for r in run)
        )
        if is_expression and self.as_of is None:
            raise RefusingRequestError(
                "Will not fetch from flexible queries unless Quick.as_of is set."
            )
        elif is_expression:
            df = CachingWellFrameBuilder(self.well_cache, self.as_of).where(run).build()
        elif self.facade is not None:
            df = self.facade(run)
        elif self.well_cache is not None:
            df = self.well_cache.load(run)
        else:
            df = WellFrameBuilder.runs(run).with_feature(self.feature).build()
        # instead, we'll build the names in Quick.df()
        df = df.with_new_names(self.default_namer)
        df = df.with_new_display_names(self.default_namer)
        return df.sort_std(), True

    def _everything(
        self, run, namer, start_ms, end_ms, control_names, control_types, weights, label_assays
    ):
        """Only for plotting."""
        df, stimframes = self.df_and_stims(run, namer, start_ms, end_ms, audio_waveform=True)
        control_names = self._control_names(df, control_names, control_types)
        fps = self._stimframes_per_second(df)
        weights = self._slice_weight_ms(df, weights, start_ms, end_ms)
        extra_gs, extra_fn = self._weighter(weights)
        stimplotter = StimframesPlotter(fps=fps, assay_labels=label_assays, audio_waveform=True)
        assays = AssayFrame.of(df.only("battery_name"))
        return df, stimframes, assays, control_names, fps, stimplotter, extra_gs, extra_fn

    def _control_names(self, df, control_names, control_types):
        if control_names is not None and control_types is not None:
            raise ContradictoryRequestError("Can't supply both control_names and control_types")
        if control_types is not None:
            control_names = df.with_controls_matching(names=control_types).unique_names()
        if control_names is None:
            control_names = df.with_controls().unique_names()
        return control_names

    def _control_subtract(
        self,
        df: WellFrame,
        control_type: Optional[str],
        control_name: Optional[str],
        subtraction=None,
    ) -> WellFrame:
        # use z-score by default
        if subtraction is None:
            subtraction = lambda case, control: (case - control.mean()) / case.std()
        # handle main cases: both, name, type, or neither
        if control_name is not None and control_type is not None:
            raise ContradictoryRequestError(
                "Can only specify a control_type or a control_name; got {} and {}".format(
                    control_type, control_name
                )
            )
        elif control_name is not None:
            return df.name_subtract(subtraction, control_name)
        elif control_type is not None:
            return df.control_subtract(subtraction, control_type)
        else:
            control_type = df.only_control_matching(positive=False)
            return df.control_subtract(subtraction, control_type)

    def _stimframes_per_second(self, df: WellFrame) -> int:
        if all((Tools.is_empty(z) for z in df["submission"].unique())):
            return 25
        elif all((not Tools.is_empty(z) for z in df["submission"].unique())):
            return 1000
        else:
            raise MultipleFrameratesError("Can't combine legacy and SauronX data")

    def _weighter(self, weights: Optional[np.array]):
        if weights is None:
            return None, None
        else:
            importer = ImportancePlotter()
            return (
                [1],
                lambda f, gs, name: importer.plot(weights, f.add_subplot(gs[1], sharex=f.axes[0])),
            )

    def _slice_weight_ms(
        self,
        df: WellFrame,
        weights: Optional[np.array],
        start_ms: Optional[int],
        end_ms: Optional[int],
    ):
        if weights is None:
            return None
        fpses = {ValarTools.frames_per_second(r) for r in df["run"].unique()}
        assert len(fpses) == 1, str(len(fpses))
        fps = next(iter(fpses))
        return weights[
            None
            if start_ms is None
            else int(np.floor(start_ms * fps / 1000)) : None
            if end_ms is None
            else int(np.ceil(end_ms * fps / 1000))
        ]

    def delete(self, runs: Union[RunsLike, peewee.Query, ExpressionLike]) -> None:
        return self.__delitem__(runs)

    def __delitem__(self, runs: Union[RunsLike, peewee.Query, ExpressionLike]) -> None:
        """
        Deletes one or more runs from self.facade (if it exists) or self.cache (if it exists).
        Does nothing if neither is defined.
        """
        if isinstance(runs, peewee.Query):
            runs = list(runs)
        elif isinstance(runs, ExpressionLike):
            runs = self.query_runs(runs)
        else:
            runs = Tools.runs(runs)
        if not all([isinstance(r, Runs) for r in runs]):
            raise XTypeError("Bad query type")
        for run in runs:
            if self.facade is not None:
                # TODO does this work?
                self.facade.delete(run)
            if self.well_cache is not None:
                self.well_cache.delete(run)
        logger.notice("Deleted {} run(s) from the cache(s)".format(len(runs)))

    def __repr__(self):
        if self.as_of is None:
            return "Quick({})".format(self.feature)
        else:
            return "Quick({} @ {})".format(self.feature, str(self.as_of)[:-3])

    def __str__(self):
        return repr(self)


@abcd.external
class Quicks:
    @classmethod
    def pointgrey(cls, as_of: Optional[datetime], **kwargs):
        return cls.choose(DataGeneration.POINTGREY, as_of=as_of, **kwargs)

    @classmethod
    def pike_sauronx(cls, as_of: Optional[datetime], **kwargs):
        return cls.choose(DataGeneration.PIKE_SAURONX, as_of=as_of, **kwargs)

    @classmethod
    def pike_legacy(cls, as_of: Optional[datetime], **kwargs):
        return cls.choose(DataGeneration.PIKE_LEGACY, as_of=as_of, **kwargs)

    @classmethod
    def pike_legacy_matt(cls, as_of: Optional[datetime], **kwargs):
        return cls.choose(DataGeneration.PIKE_LEGACY_MATT, as_of=as_of, **kwargs)

    @classmethod
    def pike_mgh(cls, as_of: Optional[datetime], **kwargs):
        return cls.choose(DataGeneration.PIKE_MGH, as_of=as_of, **kwargs)

    @classmethod
    def choose(cls, generation: Union[str, DataGeneration], as_of: Optional[datetime], **kwargs):
        generation = DataGeneration.of(generation)
        feature, kwargs = InternalTools.from_kwargs(
            kwargs, "feature", generation_feature_preferences[generation]
        )
        if "namer" in kwargs and "default_namer" not in kwargs:
            kwargs["default_namer"] = kwargs["namer"]
            del kwargs["namer"]  # it's ok -- this is already a copy
        audio_stimulus_cache = AudioStimulusCache()
        return Quick(
            feature,
            generation,
            as_of,
            cache=WellCache(feature),
            facade=None,
            stim_cache=StimframeCache(),
            sensor_cache=SensorCache(),
            video_cache=VideoCache(),
            audio_stimulus_cache=audio_stimulus_cache,
            **kwargs,
        )


__all__ = ["Quick", "Quicks", "AggType"]
