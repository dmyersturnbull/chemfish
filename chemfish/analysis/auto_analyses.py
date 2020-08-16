import argparse
import traceback

from chemfish.core.core_imports import *
from chemfish.model.concerns import *
from chemfish.model.concern_rules import *
from chemfish.model.sensors import *
from chemfish.model.well_frames import *
from chemfish.model.well_names import *
from chemfish.quick import *
from chemfish.viz.figures import *


@abcd.auto_repr_str()
class AutoScreenTracer:
    def __init__(
        self,
        quick: Quick,
        path: PathLike = ".",
        redo: bool = False,
        traces: bool = False,
        plot_sensors: Optional[Union[SensorNames, str]] = None,
        metric: Optional[Callable[[WellFrame], pd.Series]] = None,
        path_fn: Callable[[Runs], str] = None,
        saver: Optional[FigureSaver] = None,
        redownload: bool = False,
    ):
        self.path = Tools.prepped_dir(path)
        self.redo = redo
        self.traces = traces
        self.plot_sensors = [SensorNames.PHOTORESISTOR] if plot_sensors is None else plot_sensors
        self.metric = metric
        self.saver = FigureSaver(clear=True) if saver is None else copy(saver)
        self.saver._save_under = None
        self.quick = copy(quick)
        self.redownload = redownload
        if path_fn is None:
            path_fn = lambda run: Path(
                run.experiment.name.replace(" :: ", "_").replace(":", "_"), run.name
            )
        self.path_fn = path_fn
        deltat = datetime.now() - self.quick.as_of
        if deltat > timedelta(hours=24):
            logger.caution(f"Quick is {deltat} earlier than now")
        if self.quick.enable_checks:
            logger.caution(
                "Quick had enable_checks=True. Disabling here because AutoScreenTracer handles this itself."
            )
            self.quick.enable_checks = False
        if self.quick.auto_fix:
            logger.caution(
                "Quick had auto_fix=True. Disabling here because AutoScreenTracer handles this itself."
            )
            self.quick.auto_fix = False
        w = lambda b: "with" if b else "without"
        logger.info(
            f"Plotting {w(traces)} traces and with sensors {', '.join([str(s) for s in self.plot_sensors])}"
        )

    def plot_project(
        self,
        project: Union[Projects, int, str],
        control: Union[ControlTypes, str, int] = "solvent (-)",
    ):
        project = Projects.fetch(project)
        self.plot_where(Projects.id == project.id, control)

    def plot_experiment(
        self,
        experiment: Union[Experiments, int, str],
        control: Union[ControlTypes, str, int] = "solvent (-)",
    ):
        experiment = Experiments.fetch(experiment)
        self.plot_where(Experiments.id == experiment.id, control)

    def plot_where(
        self, where, control: Union[None, ControlTypes, str, int] = "solvent (-)"
    ) -> None:
        control = None if control is None else ControlTypes.fetch(control)
        runs = self.quick.query_runs(where)
        logger.notice(f"Plotting {runs} runs...")
        for run in Tools.loop(runs, logger.info):
            try:
                self.plot_run(run, control)
            except:
                logger.exception(f"Failed to process run {run.id}")
        logger.notice(f"Plotted {len(runs)} runs.")

    def plot_run(
        self, run: Runs, control: Union[None, ControlTypes, str, int] = "solvent (-)"
    ) -> None:
        q0 = self.quick
        run = Runs.fetch(run)
        FigureTools.clear()
        logger.info(100 * Chars.hline)
        control = None if control is None else ControlTypes.fetch(control)
        path = self.run_path(run)
        path.mkdir(parents=True, exist_ok=True)
        done_path = path / ".done"
        if done_path.exists() and not self.redo:
            logger.info(f"Handling r{run.id}... No need.")
            return
        logger.info(f"Handling r{run.id}...")
        try:
            if self.redownload:
                q0.delete(run)
            df = q0.df(run)
            # log and save concerns
            concerns = Concerns.of(
                df,
                self.quick.feature,
                self.quick.sensor_cache,
                as_of=None,
                min_severity=Severity.CAUTION,
            )
            if len(concerns) > 0:
                Concerns.log_warnings(concerns)
            else:
                logger.minor(f"No concerns for r{run.id}")
            concerns = Concerns.to_df(concerns)
            concerns.to_csv(path / "concerns.csv")
            # now fix issues
            # DO NOT AUTO-FIX! We'll do it here, after we emit concerns
            df = q0.fix(df)
            # misc stuff
            tags = Tools.query(RunTags.select().where(RunTags.run == run))
            tags.to_csv(path / "tags.csv")
            self._write_scores(df, control, path)
            ########################################
            # and now come the plots
            ########################################
            with FigureTools.hiding():
                self._plot(df, control, path)
            ########################
            # we're done with plots
            self._write_properties(done_path)
            logger.info(f"Done with r{run.id}.")
        except:
            tb = traceback.format_exc()
            (path / ".failed").write_text(datetime.now().isoformat() + "\n\n" + tb, encoding="utf8")
            raise
        FigureTools.clear()

    def _write_scores(self, df: WellFrame, control: ControlTypes, path: Path):
        if self.metric is None:
            scores = (
                pd.DataFrame(np.square(df.z_score(control)).mean(axis=1))
                .rename(columns={0: "dist"})
                .reset_index()[["name", "control_type", "dist"]]
            )
        else:
            scores = self.metric(df)
            # keep columns
        scores.to_csv(path / "scores.csv")

    def _plot(self, df: WellFrame, control: ControlTypes, path: Path):

        q0 = self.quick
        # save traces and heatmaps
        def trace_it():
            yield from q0.traces(df, control_types=control, always_plot_control=False)

        if self.traces and control is not None:
            logger.debug("Plotting traces...")
            self.saver.save_all(trace_it(), path / "traces")
        logger.debug("Plotting heatmaps...")
        self.saver.save(q0.rheat(df, show_name_lines=False), path / "rheat")
        if control is not None:
            self.saver.save(
                q0.zheat(df, control_type=control, show_name_lines=False, show_control_lines=True),
                path / "zheat",
            )
        # diagnostics
        logger.debug("Plotting diagnostics...")
        try:
            figure = q0.diagnostics(run, sensors=self.plot_sensors)
            self.saver.save(figure, path / "diagnostics")
        except:  # need base exception for RuntimeError: Internal psf_fseek() failed from soundfile
            logger.error("Failed to get main sensor data", exc_info=True)
        # sensor data info
        logger.debug("Saving additional sensor data...")
        try:
            img = q0.sensor_cache.load(SensorNames.PREVIEW, run).sensor_data  # type Image
            img.save(path / "preview.png", "png")
        except:
            logger.minor("No ROI preview")
        try:
            img = q0.sensor_cache.load(SensorNames.WEBCAM, run).sensor_data  # type Image
            img.save(path / "snap.png", "png")
        except:
            logger.minor("No webcam snapshot")
        # additional info
        # logger.debug("Saving structures...")
        # try:
        #    img = q0.structures_on_plate(run)
        #    img.save(path / "structures.png", "png")
        # except Exception:
        #    logger.error("Failed to plot structures", exc_info=True)

    def _write_properties(self, done_path: Path):
        Tools.write_properties_file(
            {
                "chemfish_version": chemfish_version,
                "chemfish_startup_time": chemfish_start_time.isoformat(),
                "current_time": datetime.now().isoformat(),
            },
            done_path,
        )

    def run_path(self, run: Runs) -> Path:
        return self.path / self.path_fn(run)


class AutoScreenTraces:
    @classmethod
    def run(cls, args):
        parser = argparse.ArgumentParser("Auto-generate screening plots")
        parser.add_argument("path", type=str)
        parser.add_argument("experiment", type=str)
        parser.add_argument("--control", required=False, type=str, default="solvent (-)")
        parser.add_argument("--generation", required=False, type=str, default="pointgrey")
        parser.add_argument("--feature", required=False, type=str)
        parser.add_argument("--ignore-batches", required=False, type=int, nargs="*")
        parser.add_argument("--traces", required=False, action="store_true")
        parser.add_argument("--plot-sensors", required=False, type=str, nargs="*")
        parser.add_argument("--stderr", required=False, action="store_true")
        parser.add_argument("--stdout", required=False, action="store_true")
        parser.add_argument("--redo", required=False, action="store_true")
        args = parser.parse_args(args)
        ignore_bids = args.ignore_bids
        q = Quicks.choose(
            args.generation,
            datetime.now(),
            feature=args.feature,
            namer=WellNamers.screening_plate_with_labels(ignore_bids),
        )
        tracer = AutoScreenTracer(
            q, args.path, redo=args.redo, traces=args.traces, plot_sensors=args.plot_sensors
        )
        tracer.plot_experiment(args.experiment, args.control)


if __name__ == "__main__":
    AutoScreenTraces().run(sys.argv[1:])

__all__ = ["AutoScreenTracer"]
