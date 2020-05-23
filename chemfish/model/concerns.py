"""
Concerns are specifically concerns about runs.
They include run and batch annotations, number of features, and more.
"""

from __future__ import annotations

# importing dataclass directly is necessary to fix pycharm warnings
from dataclasses import dataclass
from kale.core.core_imports import *
from traceback import FrameSummary, StackSummary
from kale.model.well_frames import *
from kale.model.features import *
from kale.model.sensors import *
from kale.model.cache_interfaces import ASensorCache

control_types = {c.name: c for c in ControlTypes.select()}
TRASH_CONTROLS = {
    c: control_types[c] for c in {"ignore", "near-WT (-)", "no drug transfer", "low drug transfer"}
}
DEFINITELY_BAD_CONTROLS = {c: control_types[c] for c in {"no drug transfer", "low drug transfer"}}


class ConcernFrame(SimpleFrame):
    pass


class TargetTimeKind(Enum):
    ACCLIMATION = 1
    WAIT = 2
    TREATMENT = 3


@enum.unique
class Severity(enum.Enum):
    """
    An enum and estimate of how bad a concern is.

    These values are analagous to the choices in Annotations.level and BatchAnnotations.level.
    And in cases where the Concern is derived from an Annotation or BatchAnnotation,
    the Concern's Severity will generally be equivalent to the annotation's level.
    The exceptions are 'fix' and 'to_fix' (described below).
    In order of best to worst:
        * GOOD       ~ '0:good'      Indicates that the data is more trustworthy than normally expected (not a concern)
        * NOTE       ~ '1:note'      Indicates something neither good nor bad (also not a concern)
        * CAUTION    ~ '2:caution'   Something concerning but will (generally) interfere in _no_ analyses (ex: wait time is 2 hours instead of 1)
        * WARNING    ~ '3:warning'   Something that will interfere in _some_ analyses (ex: treatment time is 2 hours instead of 1)
        * DANGER     ~ '4:danger'    Something that will interfere in _most_ analyses (ex: blue LED was out)
        * CRITICAL   ~ '9:deleted'   Something that will interfere with _all_ analyses; the data should be discarded (ex: video was empty)
    Because we don't delete data, even if it's garbage, adding a 9:delete annotation effectively marks the data as deleted.

    Annotations with 'to_fix' or 'fixed' annotations are generally translated as:
        * to_fix     ~ DANGER (you REALLY should fix it before analyzing)
        * fixed      ~ NOTE   (fixing an issue doesn't make the data better than expected)

    Many Concern types are not derived from Annotations or BatchAnnotations.
    For example, wells with low drug transfer, late treatment times, missing features or sensors, etc.
    `ConcernRule`s define a Severity, but you can of course make your own rules for defining these.

    For example:
    The Severity of treatment times built into `TargetTimeConcernRule.severity` has specific rules
    for how bad (or good) a late (or early) treatment, wait (pre-treatment), or acclimation duration is.
    For example, >2-fold late treatment is marked with DANGER.
    You could also define your own function:
    ```
    def lateness(concern: TargetTimeConcern) -> Severity:
        if concern.kind is not TargetTimeKind.TREATMENT:
            raise ValueError("Not defined on kind {}".format(concern.kind))
        if concern.actual > 2*60*60 or concern.actual < 0.5*60*60:  # 2 hours late or 30 min early
            return Severity.CRITICAL
        else:
        return Severity.NOTE
    ```

    A good rule of thumb:
        * DANGER or CRITCAL  -- discard or fix
        * WARNING            -- examine and decide
        * CAUTION            -- examine and confirm
        * GOOD or NOTE       -- ignore these

    """

    GOOD, NOTE, CAUTION, WARNING, DANGER, CRITICAL = 0, 1, 2, 3, 4, 9

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    def __le__(self, other):
        return self.value <= other.value

    def __ge__(self, other):
        return self.value >= other.value

    @property
    def to_enum_value(self) -> str:
        return self.value + ":" + self.name.lower()

    @property
    def log_fn(self):
        return getattr(logger, self.log_level.lower())

    @property
    def log_level(self) -> str:
        return {
            9: "ERROR",  # shouldn't be used, so don't
            4: "WARNING",
            3: "WARNING",
            2: "CAUTION",
            1: "INFO",
            0: "INFO",
        }[self.value]

    @property
    def emoji(self) -> str:
        """
        Returns a single-character symbol indicating the severity, followed by padding spaces.
        They are:
            - ⛔  for CRITICAL
            - ☢  for DANGER
            - ⚠  for WARNING
            - ·   for CAUTION
            -     for NOTE and GOOD (spaces)
        Unfortunately, not all monospace fonts handle these widths correctly.
        Therefore using ljust and rjust probably won't work as expected:
            The radiation and warning signs have Neutral East Asian width.
            The no entry symbol has Ambiguous East Asian width.
            The rest have smaller widths.
        To work around this, hair spaces are appended. But that's not enough.
        """
        return {
            9: Chars.donotenter,
            4: Chars.radiation + Chars.hairspace,
            3: Chars.warning + Chars.hairspace,
            2: Chars.middot + Chars.hairspace * 2,
            1: "\u2007" + Chars.hairspace * 2,
            0: "\u2007" + Chars.hairspace * 2,
        }[self.value]

    @classmethod
    def of(cls, level: Union[Severity, int, str]):
        """
        Returns a Severity from:
            - a Severity instance
            - the name of a Severity (case-insensitive)
            - the name of an Annotation or BatchAnnotation level (case-insensitive)
            - the numerical value of a Severity
        """
        if hasattr(level, "value"):
            # TODO not good, but can't check for isinstance with enum
            level = level.value
        if isinstance(level, str):
            for x in cls:
                if level.upper() == x.name:
                    return x
            return cls.parse(level)
        elif isinstance(level, int):
            for x in cls:
                if level == x.value:
                    return x
            raise XValueError("Bad value {}".format(level))
        raise XTypeError("Bad type {} for {}".format(type(level), level))

    @classmethod
    def parse(cls, level: str) -> Severity:
        """
        Parses a 'level' value from Annotations or BatchAnnotations.
        :raises LookupFailedError
        """
        level = level.lower()
        if level == "to_fix":
            return Severity.DANGER
        if level == "9:deleted":
            return Severity.CRITICAL
        for val in Severity:
            if val.name == level or level[0] == str(val.value):
                return val
        raise LookupFailedError("Level {} not recognized".format(level))

    @classmethod
    def bad_values(cls) -> Sequence[Severity]:
        return [Severity.CAUTION, Severity.WARNING, Severity.DANGER, Severity.CRITICAL]

    @classmethod
    def key_str(cls) -> str:
        return Chars.dangled(
            "  ".join([s.name + ":" + s.emoji.strip() for s in Severity.bad_values()])
        )


@dataclass
class Concern(metaclass=abc.ABCMeta):
    """
    A result from a quality test on behavioral data on a run (or well).
    Might indicate an issue or potential issue. Refer to its `severity`.
    """

    run: Runs
    severity: Severity

    @property
    def name(self):
        return self.__class__.__name__.replace("Concern", "")

    def as_dict(self) -> Mapping[str, Any]:
        raise NotImplementedError()

    def description(self) -> str:
        raise NotImplementedError()

    def _main_dict(self) -> Mapping[str, Any]:
        return {
            "kind": self.name,
            "severity": self.severity.name,
            "run": self.run,
            "description": self.description(),
        }


@dataclass
class LoadConcern(Concern):
    """
    The data could not be loaded at all.
    """

    error: BaseException
    tb: FrameSummary

    def as_dict(self) -> Mapping[str, Any]:
        return {**self._main_dict(), "message": str(self.error)}

    def description(self) -> str:
        return "Load failed with {}".format(self.run.id, type(self.error))


@dataclass
class ImpossibleTimeConcern(Concern):
    kind: str
    value: str

    def as_dict(self) -> Mapping[str, Any]:
        return {**self._main_dict(), "kind": self.kind, "value": self.value}

    def description(self) -> str:
        return "{} time is {}".format(self.kind, self.value)


@dataclass
class MissingSensorConcern(Concern):
    generation: DataGeneration
    expected: Set[Sensors]
    actual: Set[Sensors]

    @property
    def missing(self) -> Set[Sensors]:
        return self.expected - self.actual

    def as_dict(self) -> Mapping[str, Any]:
        return {
            **self._main_dict(),
            "defined": frozenset([s.name for s in self.actual]),
            "missing": frozenset([s.name for s in self.missing]),
        }

    def description(self) -> str:
        if len(self.missing) > 1:
            return "Missing sensors: {}".format(", ".join([s.name for s in self.missing]))
        elif len(self.missing) == 1:
            return "Missing sensor: {}".format(", ".join([s.name for s in self.missing]))
        else:
            return "Has all sensors"


@dataclass
class WellConcern(Concern):
    trash: Mapping[ControlTypes, int]

    @property
    def name(self):
        return "WellConcern"

    def as_dict(self) -> Mapping[str, Any]:
        x = Tools.join_kv(self.trash, ",")
        return {**self._main_dict(), "counts": "-" if len(x) == 0 else x}

    def description(self) -> str:
        if len(self.trash) > 0:
            return "Hazard well(s) present: " + ", ".join(
                k.name + Chars.bracketed("n=" + str(v)) for k, v in self.trash.items()
            )
        else:
            return "No hazard wells"


@dataclass
class BatchConcern(Concern):
    batch: Batches
    annotation: BatchAnnotations

    def as_dict(self) -> Mapping[str, Any]:
        return {
            **self._main_dict(),
            "id": self.annotation.id,
            "batch": self.batch.id,
            "description": self.annotation.description,
        }

    def description(self) -> str:
        return "Suspicious batch b{}: {}".format(self.batch.id, Chars.squoted(self.annotation.name))


@dataclass
class _AnnotationConcern(Concern, metaclass=abc.ABCMeta):
    annotation: Annotations

    def as_dict(self) -> Mapping[str, Any]:
        return {
            **self._main_dict(),
            "id": self.annotation.id,
            "description": self.annotation.description,
            "datetime_annotated": self.annotation.created,
            "user_annotated": self.annotation.annotator.username,
        }


@dataclass
class _ErrorConcern(Concern, metaclass=abc.ABCMeta):
    expected: float
    actual: float

    @property
    def raw_diff(self) -> float:
        return self.actual - self.expected

    @property
    def raw_error(self) -> float:
        return abs(self.raw_diff)

    @property
    def relative_error(self) -> float:
        return abs(self.relative_diff)

    @property
    def relative_diff(self) -> float:
        if not hasattr(self, "__relative_diff"):
            if self.expected == 0 or np.isinf(self.expected):
                logger.debug(
                    "Expected value is {}. Setting relative_diff=+inf".format(self.expected)
                )
                self.__relative_diff = np.inf
            else:
                # noinspection PyAttributeOutsideInit
                self.__relative_diff = (self.actual - self.expected) / self.expected
        return self.__relative_diff

    @property
    def log2_diff(self) -> float:
        if not hasattr(self, "__log2diff"):
            if self.expected == 0 or np.isinf(self.expected):
                logger.debug("Expected value is {}. Setting log2_diff=+inf".format(self.expected))
                self.__log2diff = np.inf
            elif self.actual == 0 or np.isinf(self.actual):
                logger.debug("Actual value is {}. Setting log2_diff=+inf".format(self.actual))
                self.__log2diff = np.inf
            else:
                # noinspection PyAttributeOutsideInit
                self.__log2diff = np.log2(self.actual) - np.log2(self.expected)
        return self.__log2diff

    def as_dict(self) -> Mapping[str, Any]:
        return {
            **self._main_dict(),
            "raw_diff": self.raw_diff,
            "expected": self.expected,
            "actual": self.actual,
            "relative_error": self.relative_error,
            "log2_diff": self.log2_diff,
        }


@dataclass
class SensorLengthConcern(_ErrorConcern):
    generation: DataGeneration
    sensor: Sensors

    def as_dict(self) -> Mapping[str, Any]:
        return {**super().as_dict(), "sensor": self.sensor.id}

    def description(self) -> str:
        return "Sensor {} length: {}: {} → {}".format(
            self.sensor.name, self.severity.name.lower(), self.expected, self.actual
        )


@dataclass
class TargetTimeConcern(_ErrorConcern):
    kind: TargetTimeKind
    annotation: Optional[Annotations]

    @property
    def name(self):
        return self.kind.name.capitalize() + "Sec"

    def as_dict(self) -> Mapping[str, Any]:
        return {**super().as_dict(), "annotation_id": Tools.look(self.annotation, "id")}

    def description(self) -> str:
        diff = Tools.pretty_float(self.log2_diff, 2)
        actual = Tools.pretty_float(self.actual, None).lstrip("+")
        expected = Tools.pretty_float(self.expected, None).lstrip("+")
        return "{} is {}× (log₂) off: {} → {}".format(
            self.kind.name.capitalize().ljust(11), diff.ljust(7), expected.ljust(5), actual.ljust(5)
        )


@dataclass
class AnnotationConcern(_AnnotationConcern):
    def description(self) -> str:
        return (
            "Annotation: "
            + Chars.squoted(self.annotation.name)
            + " "
            + Chars.parened("id=" + str(self.annotation.id))
        )


@dataclass
class ToFixConcern(_AnnotationConcern):
    fixed_with: Optional[Annotations]

    def description(self) -> str:
        return "{} to_fix {} ({}; id={}): {}".format(
            "Unfixed" if self.fixed_with is None else "Fixed",
            Chars.squoted(self.annotation.name),
            self.annotation.created,
            self.annotation.id,
            self.annotation.description,
        )


@dataclass
class NFeaturesConcern(_ErrorConcern):
    def as_dict(self) -> Mapping[str, Any]:
        return super().as_dict()

    def description(self) -> str:
        return "Feature length: {} → {}".format(self.expected, self.actual)


@dataclass
class GenerationConcern(Concern):
    expected_generations: Set[DataGeneration]
    actual_generation: DataGeneration

    def as_dict(self) -> Mapping[str, Any]:
        return {
            **self._main_dict(),
            "expected_generations": tuple(self.expected_generations),
            "actual_generation": self.actual_generation.name,
        }

    def description(self) -> str:
        return "Generation(s) {} (expected) → {}".format(
            Tools.join(self.expected_generations, ",", attr="name"), self.actual_generation.name
        )


class ConcernRule:
    @property
    def clazz(self) -> Type[Concern]:
        raise NotImplementedError()

    def of(self, df: WellFrame):
        raise NotImplementedError()

    def severity(self, concern) -> Severity:
        raise NotImplementedError()

    def _new(self, run: Runs, *args):
        concern = self.clazz(run, Severity.CRITICAL, *args)
        concern.severity = self.severity(concern)
        return concern


class MissingSensorConcernRule(ConcernRule):
    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        return MissingSensorConcern

    def severity(self, concern: MissingSensorConcern) -> Severity:
        # 16, 17 are snapshots, so missing them isn't serious
        missing = {s for s in concern.missing}
        bad = {s for s in concern.missing if s.id not in [16, 17]}
        verybad = {s for s in concern.missing if s.id not in [16, 17]}
        generation = concern.generation
        version = (
            ValarTools.run_tag(concern.run, "sauronx_version") if generation.is_sauronx() else None
        )
        if concern.generation.is_pointgrey():
            pass
            # if it was SauronX with pymata-aio, then missing light sensors is critical
        if len(verybad) > 0 and concern.generation.is_pointgrey():
            return Severity.CRITICAL
        elif len(verybad) > 0:
            return Severity.DANGER
        elif len(bad) > 0 and concern.generation.is_pointgrey():
            return Severity.WARNING
        elif len(bad) > 0:
            return Severity.CAUTION  # just missing snapshots
        else:
            return Severity.GOOD

    def of(self, df: WellFrame) -> Generator[MissingSensorConcern, None, None]:
        for run in df.unique_runs():
            run = Runs.fetch(run)
            # TODO check registry
            generation = ValarTools.generation_of(run)
            if generation is DataGeneration.POINTGREY:
                expected = ValarTools.pointgrey_required_sensors()
            elif generation.is_sauronx():
                expected = ValarTools.sauronx_required_sensors()
            else:
                expected = ValarTools.legacy_required_sensors()
            actual = ValarTools.sensors_on(run)
            yield self._new(run, generation, expected, actual)


class SensorLengthConcernRule(ConcernRule):
    def __init__(self, as_of: datetime, sensor_cache):
        self.as_of = as_of
        self.sensor_cache = sensor_cache
        self._photosensor = Sensors.fetch("sauronx-tinkerkit-photometer-ms")

    @property
    def clazz(self) -> Type[Concern]:
        return SensorLengthConcern

    def severity(self, concern: SensorLengthConcern) -> Severity:
        for thresh, level in zip(
            [2, 2 / 4, 2 / 16, 2 / 16, 2 / 256],
            [Severity.CRITICAL, Severity.DANGER, Severity.WARNING, Severity.CAUTION, Severity.NOTE],
        ):
            if np.abs(concern.log2_diff) > thresh:
                return level
        return Severity.GOOD

    def of(self, df: WellFrame) -> Generator[SensorLengthConcern, None, None]:
        for run in df.unique_runs():
            generation = ValarTools.generation_of(run)
            if generation is not DataGeneration.POINTGREY:
                continue  # not supported -- yet
            run = Runs.fetch(run)
            sampling = float(
                ValarTools.toml_item(run, "sauron.hardware.sensors.sampling_interval_milliseconds")
            )
            expected = np.float(run.experiment.battery.length / sampling)
            photo_data = None
            try:
                photo_data = self.sensor_cache.load((SensorNames.PHOTORESISTOR, run))
            except ValarLookupError:
                pass  # hit debug below
            if photo_data is None:
                logger.debug("Missing photosensor data on r{}".format(run.id))
            else:
                actual = np.float(len(photo_data.data))
                yield self._new(run, expected, actual, generation, self._photosensor)
                # we won't bother for thermo


class TargetTimeConcernRule(ConcernRule):
    """
        Processes deviations from expected treatment, wait, and acclimation durations.
        Looks for rows in the `Annotations` tables with names:
            - expected :: seconds :: acclimation
            - expected :: seconds :: wait
            - expected :: seconds :: treatment
        When it can't find an annotation, falls back to the value in `Concerns.expected_times`.
        Otherwise, yields a concern for each run, each of the 3 kinds, and each corresponding annotations.
    """

    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        return TargetTimeConcern

    def severity(self, concern: TargetTimeConcern) -> Severity:
        """
        Gets a severity based on various lab experience.
        Subject to change. Current rules:
            Tries the levels from highest to lowest, each with a progressively more liberal bound on relative error.
            Each level's bound is its higher level's bound divided by a power of 2.
            These powers are: 1, 2, 4, 16
            For treatment time:
                - rel error > 2.0    ⇒ DANGER
                - rel error > 1.25   ⇒ WARNING
                - rel error > 1.0625 ⇒ CAUTION
                - rel error > 1.125  ⇒ NOTE
                - rel error ≤ 1.125  ⇒ GOOD
                So for a 1-hour treatment time, DANGER is <30min or >2hr,
                WARNING is <45min or >90min,
                CAUTION or higher is applied for being 7.5 minutes late,
                and GOOD is applied for being ≤3.75 minutes late.
            For (pre-treatment) wait time:
                The logic is similar, following halving thresholds.
                But the bounds are asymmetric: For DANGER, < 4-fold or > 8-fold (usually <15min or >8hr)
            For (dark) acclimation time:
                Same idea, with values < 4-fold or > 8-fold (usually <2.5min or >80min)
        """
        if hasattr(self, "__severity") and self.__severity is not None:
            return self.__severity

        def fail(low, high) -> bool:
            return concern.log2_diff < low or concern.log2_diff >= high

        def halving(low, high):
            for i, then in zip(
                [1, 2, 4, 16], [Severity.DANGER, Severity.WARNING, Severity.CAUTION, Severity.NOTE]
            ):
                if fail(low / i, high / i):
                    return then
            return Severity.GOOD

        if concern.kind is TargetTimeKind.TREATMENT:
            return halving(-2, 2)
        elif concern.kind is TargetTimeKind.WAIT:
            return halving(-4, 8)
        elif concern.kind is TargetTimeKind.ACCLIMATION:
            return halving(-4, 8)
        else:
            assert False, concern.kind

    def of(self, df: WellFrame) -> Generator[TargetTimeConcern, None, None]:
        for run in df.unique_runs():
            run = Runs.fetch(run)  # type: Runs
            yield from self._time_concerns(run, TargetTimeKind.ACCLIMATION)
            yield from self._time_concerns(run, TargetTimeKind.WAIT)
            if run.datetime_dosed is not None:
                yield from self._time_concerns(run, TargetTimeKind.TREATMENT)

    def _time_concerns(
        self, run: Runs, kind: TargetTimeKind
    ) -> Generator[TargetTimeConcern, None, None]:
        actual = self._fetch_actual_time(run, kind)
        if actual is None:
            actual = np.inf
        for expected, tag in self._fetch_expected_times(run, kind):
            yield self._new(run, expected, actual, kind, tag)

    def _fetch_actual_time(self, run: Runs, kind: TargetTimeKind) -> float:
        if kind is TargetTimeKind.WAIT:
            return ValarTools.wait_sec(run)
        elif kind is TargetTimeKind.TREATMENT:
            return ValarTools.treatment_sec(run)
        else:
            return ValarTools.acclimation_sec(run)

    def _fetch_expected_times(
        self, run: Runs, kind: TargetTimeKind
    ) -> Generator[Tup[float, Optional[Annotations]], None, None]:
        # get from experiment notes; otherwise fall back
        # but always override if there are Annotations for that run
        annotation_name = "expected :: seconds :: " + kind.name.lower()
        pattern = re.compile(annotation_name + " *= *" + "(\\d+)")
        if run.experiment.notes:
            match = list(pattern.finditer(run.experiment.notes))
            if len(match) > 2:
                logger.error(
                    "Multiple tags matching {} in notes for experiment {}".format(
                        annotation_name, run.experiment.name
                    )
                )
                expected = self.default_expected_time(kind)
            elif len(match) == 1:
                expected = float(match[0].group(1))
            else:
                expected = self.default_expected_time(kind)
            annots = self._find_annotations(run, kind)
            if len(annots) > 0:
                for tag in annots:
                    try:
                        yield float(tag.value)
                        yield (float(tag.value), tag)
                    except (AttributeError, ArithmeticError):
                        raise XValueError(
                            "Annotation {} does not have a valid float value (is {})".format(
                                tag.id, tag.value
                            )
                        )
            else:
                yield (expected, None)

    def default_expected_time(self, kind: TargetTimeKind) -> float:
        return {
            TargetTimeKind.ACCLIMATION: 10 * 60,
            TargetTimeKind.WAIT: 60 * 60,
            TargetTimeKind.TREATMENT: 60 * 60,
        }[kind]

    def _find_annotations(self, run: Runs, kind: TargetTimeKind) -> Sequence[Annotations]:
        annotation_name = "expected :: seconds :: " + kind.name.lower()
        return list(
            Annotations.select()
            .where(Annotations.run == run)
            .where(Annotations.name == annotation_name)
        )


class BatchConcernRule(ConcernRule):
    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        return BatchConcern

    def severity(self, concern: BatchConcern) -> Severity:
        return Severity.parse(concern.annotation.level)

    def of(self, df: WellFrame) -> Generator[BatchConcern, None, None]:
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        batches = {batch.id: batch for batch in Batches.fetch_all(df.unique_batch_ids())}
        query = BatchAnnotations.select().where(BatchAnnotations.batch << set(batches.keys()))
        if self.as_of:
            query = query.where(BatchAnnotations.created < self.as_of)
        anns = Tools.multidict(query, "batch_id")
        for run in df.unique_runs():
            for batch_id in df.with_run(run).unique_batch_ids():
                for concern in anns[batch_id]:
                    yield self._new(runs[run], batches[batch_id], concern)


class AnnotationConcernRule(ConcernRule):
    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        return AnnotationConcern

    def severity(self, concern: AnnotationConcern) -> Severity:
        return Severity.parse(concern.annotation.level)

    def of(self, df: WellFrame) -> Generator[AnnotationConcern, None, None]:
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        query = (
            Annotations.select(Annotations, Users, Runs, Submissions)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(Annotations)
            .join(Runs)
            .switch(Annotations)
            .join(Submissions, JOIN.LEFT_OUTER)
            .where(Annotations.run_id << set(runs))
        )
        if self.as_of:
            query = query.where(Annotations.created < self.as_of)
        anns = Tools.multidict(query, "run_id")
        for run in df.unique_runs():
            for concern in anns[run]:
                yield self._new(runs[run], concern)


class ToFixConcernRule(ConcernRule):
    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        return ToFixConcern

    def severity(self, concern: ToFixConcern) -> Severity:
        if concern.fixed_with is None:
            return Severity.NOTE
        else:
            return Severity.parse(concern.annotation.level)

    def of(self, df: WellFrame) -> Generator[ToFixConcern, None, None]:
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        to_fixes = Tools.multidict(self._query("to_fix", runs), "run_id")
        fixed = Tools.multidict(self._query("fixed", runs), "run_id")
        for run in df.unique_runs():
            to_fixes_r = sorted(to_fixes[run], key=lambda a: a.created)
            fixed_values = Tools.multidict(fixed[run], "value")
            for to_fix in to_fixes_r:
                yield self._new(runs[run], to_fix, fixed_values.get(str(to_fix.id)))

    def _query(self, level: str, runs):
        q = (
            Annotations.select(Annotations, Users, Runs, Submissions)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(Annotations)
            .join(Runs)
            .switch(Annotations)
            .join(Submissions, JOIN.LEFT_OUTER)
            .where(Annotations.run_id << set(runs))
            .where(Annotations.level == level)
        )
        return q.where(Annotations.created < self.as_of)


class GenerationConcernRule(ConcernRule):
    def __init__(self, as_of: datetime, feature: Union[FeatureType, str]):
        self.as_of = as_of
        self.feature = FeatureTypes.of(feature)

    @property
    def clazz(self) -> Type[Concern]:
        return GenerationConcern

    def severity(self, concern: GenerationConcern) -> Severity:
        return Severity.DANGER

    def of(self, df: WellFrame) -> Generator[GenerationConcern, None, None]:
        if self.feature is None:
            return
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        for run in df.unique_runs():
            generation = ValarTools.generation_of(run)
            if generation not in self.feature.data_generations:
                yield self._new(runs[run], self.feature.data_generations, generation)


class ImpossibleTimeConcernRule(ConcernRule):
    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        return ImpossibleTimeConcern

    def severity(self, concern: ImpossibleTimeConcern) -> Severity:
        generation = ValarTools.generation_of(concern.run)
        # some legacy data was missing these values (especially datetime plated)
        if generation.is_sauronx() or str(concern.value) != "None":
            return Severity.DANGER
        else:
            return Severity.CAUTION

    def of(self, df: WellFrame) -> Generator[ImpossibleTimeConcern, None, None]:
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        for run in df.unique_runs():
            run = runs[run]
            dfx = df.with_run(run)
            batches = dfx["b_ids"].unique()
            plate = Plates.fetch(run.plate)  # type: Plates
            if run.plate.datetime_plated is None:
                yield self._new(run, "datetime_plated", "None")
            if len(batches) > 0 and run.datetime_dosed is None:
                yield self._new(
                    run,
                    "datetime_dosed",
                    "None [batches {}]".format(",".join([str(b) for b in batches])),
                )
            if len(batches) == 0 and run.datetime_dosed is not None:
                yield self._new(
                    run, "datetime_dosed", run.datetime_dosed.isoformat() + " [no batches]"
                )
            if run.datetime_dosed is not None and run.datetime_run < run.datetime_dosed:
                yield self._new(
                    run,
                    "datetime_dosed" + Chars.right + "datetime_run",
                    run.datetime_dosed.isoformat() + Chars.right + run.datetime_run.isoformat(),
                )
            if plate.datetime_plated is not None and run.datetime_run < plate.datetime_plated:
                yield self._new(
                    run,
                    "datetime_plated" + Chars.right + "datetime_run",
                    plate.datetime_plated.isoformat() + Chars.right + run.datetime_run.isoformat(),
                )


class NFeaturesConcernRule(ConcernRule):
    def __init__(self, as_of: datetime, feature: Union[None, FeatureType, str]):
        self.as_of = as_of
        self.feature = None if feature is None else FeatureTypes.of(feature)

    @property
    def clazz(self) -> Type[Concern]:
        return NFeaturesConcern

    def severity(self, concern: NFeaturesConcern) -> Severity:
        # multiples of 4
        if concern.raw_error > 192:
            return Severity.CRITICAL
        elif concern.raw_error > 48:
            return Severity.DANGER
        elif concern.raw_error > 12:
            return Severity.WARNING
        elif concern.raw_error > 3:
            # losing up to 2 is expected due to trimming
            # in practice, 3 are often lost
            # gaining frames is much weirder, but we'll keep the same thresholds
            return Severity.CAUTION
        elif concern.raw_error > 0:
            return Severity.NOTE
        else:
            return Severity.GOOD

    def of(self, df: WellFrame) -> Generator[GenerationConcern, None, None]:
        if self.feature is None or not self.feature.time_dependent:
            return
        runs = {run.id: run for run in Runs.fetch_all(df.unique_runs())}
        for run in df.unique_runs():
            dfx = WellFrame.of(df.with_run(run))
            n_expected = int(ValarTools.expected_n_frames(run))
            n_actual = int(dfx.feature_length())
            n_nan = dfx.count_nans_at_end() + dfx.count_nans_at_start()
            yield self._new(runs[run], n_expected, n_actual - n_nan)


class WellConcernRule(ConcernRule):
    def __init__(self, as_of: datetime):
        self.as_of = as_of

    @property
    def clazz(self) -> Type[Concern]:
        return WellConcern

    def severity(self, concern: WellConcern) -> Severity:
        very_bad = {
            t.name: n for t, n in concern.trash.items() if t.name in DEFINITELY_BAD_CONTROLS
        }
        if len(very_bad) == 24:
            return Severity.CRITICAL
        if len(very_bad) > 12:
            return Severity.DANGER
        elif len(very_bad) > 6:
            return Severity.WARNING
        elif len(concern.trash) > 0:
            return Severity.CAUTION
        else:
            return Severity.GOOD

    def of(self, df: WellFrame) -> Generator[WellConcern, None, None]:
        def counts(dfx):
            x = {v: len(dfx.with_controls_matching(c)) for c, v in TRASH_CONTROLS.items()}
            return {a: b for a, b in x.items() if b > 0}

        for run in df.unique_runs():
            cs = counts(df.with_run(run))
            yield self._new(Runs.fetch(run), cs)


class ConcernRuleCollection:
    def __init__(
        self,
        feature: Union[FeatureType, str],
        sensor_cache,
        as_of: Optional[datetime],
        min_severity: Union[int, str, Severity] = Severity.GOOD,
    ):
        self.feature = FeatureTypes.of(feature)
        self.sensor_cache = sensor_cache
        self.as_of = as_of
        self.min_severity = Severity.of(min_severity)

    @property
    def rules(self) -> Sequence[ConcernRule]:
        raise NotImplementedError()

    def of(self, df: WellFrame) -> Generator[Concern, None, None]:
        runs = list(df.unique_runs())
        key = Severity.key_str()
        if len(runs) > 1:
            logger.info("Checking {} on {} runs.".format(self.__class__.__name__, len(runs)))
        elif len(runs) == 1:
            logger.info("Checking {} on run r{}.".format(self.__class__.__name__, runs[0]))
        for rule in self.rules:
            logger.debug("Checking rule {}".format(rule.__class__.__name__))
            concerns = list(rule.of(df))
            if len(concerns) > 0 and len(runs) == 1:
                logger.debug("Found {} concerns on r{}.".format(len(concerns), runs[0]))
            elif len(concerns) > 0:
                logger.debug("Found {} concerns on {} runs.".format(len(concerns), len(runs)))
            for concern in concerns:
                if concern.severity >= self.min_severity:
                    logger.debug(
                        "Found concern {} on r{}: {}".format(
                            concern.__class__.name, concern.run.id, concern.description()
                        )
                    )
                    yield concern


class SimpleConcernRuleCollection(ConcernRuleCollection):
    @property
    def rules(self) -> Sequence[ConcernRule]:
        return [
            GenerationConcernRule(self.as_of, self.feature),
            ImpossibleTimeConcernRule(self.as_of),
            MissingSensorConcernRule(self.as_of),
            SensorLengthConcernRule(self.as_of, self.sensor_cache),
            NFeaturesConcernRule(self.as_of, self.feature),
            TargetTimeConcernRule(self.as_of),
            AnnotationConcernRule(self.as_of),
            ToFixConcernRule(self.as_of),
            WellConcernRule(self.as_of),
            BatchConcernRule(self.as_of),
        ]


class SensorConcernRuleCollection(ConcernRuleCollection):
    @property
    def rules(self) -> Sequence[ConcernRule]:
        # TODO add sensor-processing rules
        return []


class Concerns:
    @classmethod
    def default_collection(
        cls,
        feature: Union[FeatureType, str],
        sensor_cache,
        as_of: Optional[datetime],
        min_severity: Union[int, str, Severity] = Severity.GOOD,
    ) -> ConcernRuleCollection:
        return SimpleConcernRuleCollection(feature, sensor_cache, as_of, min_severity)

    @classmethod
    def of(
        cls,
        df: WellFrame,
        feature: Union[FeatureType, str],
        sensor_cache,
        as_of: Optional[datetime],
        min_severity: Union[int, str, Severity] = Severity.GOOD,
    ) -> Sequence[Concern]:
        return list(cls.default_collection(feature, sensor_cache, as_of, min_severity).of(df))

    @classmethod
    def log_warnings(cls, concerns: Sequence[Concern]):
        concerns = list(concerns)  # might be a generator, even though that's the wron gtype
        if len(concerns) == 0:
            return  # will break the max fn otherwise
        widest_severity = max([len(c.severity.name.lower()) for c in concerns])
        widest_name = max([len(c.name) for c in concerns])
        widest_run = max([1 + len(str(c.run.id)) for c in concerns])
        for concern in concerns:
            concern.severity.log_fn(
                concern.severity.emoji
                + " "
                + ("r" + str(concern.run.id)).ljust(widest_run + 1)
                + " "
                + concern.name.ljust(widest_name + 1)
                + " "
                + Chars.shelled(concern.severity.name.lower()).rjust(widest_severity + 1)
                + " "
                + concern.description()
            )

    @classmethod
    def to_df(cls, concerns: Sequence[Concern]) -> ConcernFrame:
        return ConcernFrame([pd.Series(concern.as_dict()) for concern in concerns])


__all__ = [
    "Concerns",
    "Concern",
    "Severity",
    "LoadConcern",
    "SimpleConcernRuleCollection",
    "ConcernRuleCollection",
    "SensorConcernRuleCollection",
]
