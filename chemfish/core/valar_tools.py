from chemfish.core._imports import *
import ast, shutil
import subprocess
from natsort import natsorted
import tomlkit
from pocketutils.support.toml_data import TomlData
from chemfish.core._tools import *
from chemfish.core.tools import *
from chemfish.core.valar_singleton import *
from chemfish.core.data_generations import DataGeneration


def _build_stim_colors():
    dct = {
        s.name: "#" + s.default_color if s.audio_file is None else "black" for s in Stimuli.select()
    }
    dct.update(InternalTools.load_resource("core", "stim_colors.json"))
    return dct


_stimulus_display_colors = _build_stim_colors()


def _build_stim_names():
    dct = {s.name: s.name for s in Stimuli.select()}
    resource = InternalTools.load_resource("core", "stim_names.json")[0]
    dct.update(resource)
    for k, v in copy(dct).items():
        v = v.replace("_", " ")
        if v.endswith("Sq"):
            v = v[:-2] + " square"
        if v.lower().endswith("hzS"):
            v = v[:-3] + "Hz sine"
        v = v.replace("hz", "Hz")
        dct[k] = v
    return dct


_stimulus_replace = _build_stim_names()

_control_replace = {"killed (+)": "lethal (+)"}

_pointgrey_sensors = set(Sensors.list_where((Sensors.id > 2) & (Sensors.id != 7)))
_sauronx_sensors = set(Sensors.list_where((Sensors.id > 2) & (Sensors.id != 7)))
_required_sauronx_sensors = set(Sensors.list_where((Sensors.id > 2) & (Sensors.id < 7)))
_legacy_sensors = set(Sensors.list_where(Sensors.id < 3))
_required_legacy_sensors = set(Sensors.list_where(Sensors.id == 2))


class StimulusType(SmartEnum):
    LED = 1
    AUDIO = 2
    SOLENOID = 3
    NONE = 4
    IR = 5


class DataLocation(SmartEnum):
    SHIRE = 1
    UPLOADS = 2
    NEITHER = 3


_saurons = list(Saurons.select())
# use for mapping after converting to a lowercase str
_sauron_str_name_map: Mapping[str, str] = {
    **{str(s.id): "S" + s.name for s in _saurons if len(s.name) == 1},
    **{str(s.id): s.name for s in _saurons if len(s.name) > 1},
    **{s.name.lower(): "S" + s.name for s in _saurons if len(s.name) == 1},
    **{s.name.lower(): s.name for s in _saurons if len(s.name) > 1},
    **{"s" + str(s.id): "S" + s.name for s in _saurons if len(s.name) == 1},
    **{"s" + str(s.id): s.name for s in _saurons if len(s.name) > 1},
}


class ValarTools:
    """
    Miscellaneous user-facing tools specific to the data we have in Valar.
    For example, uses our definition of a library plate ID.
    Some of these functions simply call their equivalent Tools or InternalTools functions.
    """

    @classmethod
    def stimulus_wavelength_colors(cls) -> Mapping[str, str]:
        """
        Get a mapping from stimulus names to a good approximation as a single color.
        *Only covers LED stimuli, plus the IR.*
        """
        return dict(InternalTools.load_resource("core", "wavelength_colors.json")[0])

    @classmethod
    def stimulus_display_colors(cls) -> Mapping[str, str]:
        return copy(_stimulus_display_colors)

    @classmethod
    def stimulus_display_color(cls, stim: Union[int, str, Stimuli]) -> str:
        stim_name = stim if isinstance(stim, str) else Stimuli.fetch(stim).name
        return copy(_stimulus_display_colors[stim_name])

    @classmethod
    def sort_controls_first(
        cls, df: pd.DataFrame, column: str, more_controls: Optional[Set[str]] = None
    ) -> pd.DataFrame:
        first = ValarTools.controls_first(df[column], more_controls=more_controls)
        return ValarTools.sort_first(df, column, first)

    @classmethod
    def sort_first(
        cls, df: pd.DataFrame, column: Union[str, int, pd.Series], first: Sequence[str]
    ) -> pd.DataFrame:
        if isinstance(column, str) or isinstance(column, int):
            column = df[column]
        df = df.copy()
        first = [*first, *[k for k in column if k not in first]]
        df["__sort"] = column.map(lambda s: first.index(s))
        df = df.sort_values("__sort")
        df = df.drop("__sort", axis=1)
        return df

    @classmethod
    def controls_first(
        cls, names: Iterable[str], sorting=natsorted, more_controls: Optional[Set[str]] = None
    ) -> Sequence[str]:
        """
        Sorts a set of names, putting control types first.
        Controls are sorted by: positve/negative (+ first), then name.
        Both controls and their display values are included.
        After the controls, sorts the remainder by name.
        This can be very useful for plotting.
        """
        names = set(names)
        query = list(
            sorted(
                list(ControlTypes.select().order_by(ControlTypes.positive, ControlTypes.name)),
                key=lambda c: -c.positive,
            )
        )
        controls = list(
            Tools.unique(
                InternalTools.flatten([(c.name, ValarTools.control_display_name(c)) for c in query])
            )
        )
        if more_controls is not None:
            controls.extend(more_controls)
        new_names = [c for c in controls if c in names]
        new_names.extend(sorting([s for s in names if s not in controls]))
        return new_names

    @classmethod
    def stimulus_type(cls, stimulus: Union[str, int, Stimuli]) -> StimulusType:
        stimulus = Stimuli.fetch(stimulus)
        if stimulus.audio_file_id is not None:
            return StimulusType.AUDIO
        elif "solenoid" in stimulus.name:
            return StimulusType.SOLENOID
        elif "LED" in stimulus.name:
            return StimulusType.LED
        elif stimulus.name == "none":
            return StimulusType.NONE
        elif stimulus.name in ["IR", "IR array"]:
            return StimulusType.IR
        assert False, "No type for stimulus {} found!".format(stimulus.name)

    @classmethod
    def toml_file(cls, run: RunLike) -> TomlData:
        """
        Get the SauronX TOML config file for a run. Is guaranteed to exist for SauronX data, but won't for legacy.
        :param run: A run ID, name, tag, instance, or submission instance or hash
        :return: The wrapped text of the config file
        :raises: SauronxOnlyError
        """
        run = Tools.run(run)
        if run.submission is None:
            raise SauronxOnlyError(
                "No config files are stored for legacy data (run r{})".format(run.id)
            )
        t = ConfigFiles.fetch(run.config_file)
        return TomlData(t.toml_text)

    @classmethod
    def log_file(cls, run: RunLike) -> str:
        """
        Get the SauronX log file for a run. Is guaranteed to exist for SauronX data, but won't for legacy.
        :param run: A run ID, name, tag, instance, or submission instance or hash
        :return: The text of the log file, with proper (unescaped) newlines and tabs
        :raises: SauronxOnlyError
        """
        run = ValarTools.run(run)
        if run.submission is None:
            raise SauronxOnlyError(
                "No log files are stored for legacy data (run r{})".format(run.id)
            )
        f = LogFiles.select().where(LogFiles.run == run).first()
        if f is None:
            raise ValarLookupError("No log file for SauronX run r{}".format(run.id))
        return f.text

    @classmethod
    def pointgrey_required_sensors(cls) -> Set[Sensors]:
        return copy(_pointgrey_sensors)

    @classmethod
    def sauronx_sensors(cls) -> Set[Sensors]:
        return copy(_sauronx_sensors)

    @classmethod
    def sauronx_required_sensors(cls) -> Set[Sensors]:
        return copy(_required_sauronx_sensors)

    @classmethod
    def legacy_sensors(cls) -> Set[Sensors]:
        return copy(_legacy_sensors)

    @classmethod
    def legacy_required_sensors(cls) -> Set[Sensors]:
        return copy(_required_legacy_sensors)

    @classmethod
    def treatment_sec(cls, run: RunLike) -> float:
        """
        Returns np.inf is something is missing.
        """
        run = cls.run(run)
        if run.datetime_dosed is None or run.datetime_run is None:
            return np.inf
        return (run.datetime_run - run.datetime_dosed).total_seconds()

    @classmethod
    def acclimation_sec(cls, run: RunLike) -> float:
        """
        Returns np.inf is something is missing.
        """
        # here just for consistency
        run = Tools.run(run)
        if run.acclimation_sec is None:
            return np.inf
        return run.acclimation_sec

    @classmethod
    def wait_sec(cls, run: RunLike) -> float:
        """
        Time between plating and either running or plating.
        - If dose time < plate time: wait_sec is negative
        - If not dosed: wait_sec = run time - plate time
        Returns np.inf is something is missing.
        """
        run = Tools.run(run)
        plate = Plates.fetch(run.plate)  # type: Plates
        if run.plate.datetime_plated is None:
            # logger.error("Plate {} (run {}) has no datetime_plated".format(run.plate.id, run.id))
            return np.inf
        if run.datetime_dosed is None:
            return (run.datetime_run - plate.datetime_plated).total_seconds()
        else:
            return (run.datetime_dosed - plate.datetime_plated).total_seconds()

    @classmethod
    def download_file(cls, remote_path: PLike, local_path: str, overwrite: bool = False) -> None:
        remote_path = str(remote_path)
        try:
            return ValarTools._download(remote_path, local_path, False, overwrite)
        except Exception:
            raise DownloadError(
                "Failed to download file {} to {} with{} overwrite".format(
                    remote_path, local_path, "" if overwrite else "out"
                )
            )

    @classmethod
    def download_dir(cls, remote_path: PLike, local_path: str, overwrite: bool = False) -> None:
        try:
            remote_path = str(remote_path)
            return ValarTools._download(remote_path, local_path, True, overwrite)
        except Exception:
            raise DownloadError(
                "Failed to download dir {} to {} with{} overwrite".format(
                    remote_path, local_path, "" if overwrite else "out"
                )
            )

    @classmethod
    def _download(cls, remote_path: str, path: PLike, is_dir: bool, overwrite: bool) -> None:
        path = str(path)
        if "10.36.0.20" in path or path.startswith("Z:") or "shire" in path or "ind" in path:
            raise RefusingRequestError(
                "For safety will not copy data to a path containing '10.36.0.20' or starting with 'Z:' or containing 'shire' or 'ind'"
            )
        # TODO check overwrite and prep
        logger.debug("Downloading {} -> {}".format(remote_path, path))
        Tools.prep_file(path, exist_ok=overwrite)
        # TODO check regex for drive letters
        if os.name == "nt" and (remote_path.startswith(r"\\") or remote_path.startswith("Z:\\")):
            shutil.copyfile(remote_path, path)
        elif os.name == "nt":
            subprocess.check_output(["scp", remote_path, path])
        elif is_dir:
            subprocess.check_output(["rsync", "--ignore-existing", "-avz", remote_path, path])
        else:
            subprocess.check_output(
                [
                    "rsync",
                    "-t",
                    "--ignore-existing",
                    "--no-links",
                    '--exclude=".*"',
                    remote_path,
                    path,
                ]
            )

    @classmethod
    def determine_solvent_names_slow(cls) -> Mapping[int, Optional[str]]:
        """
        Queries valar to determine names of solvents used in batches and map them to their names with ref manual:high.
        This is very slow and should be used only to update the known list.
        See `known_solvent_names` instead.
        :returns A mapping from compound IDs to names
        """

        def get_label(solvent):
            row = (
                CompoundLabels.select()
                .where(CompoundLabels.compound == solvent)
                .where(CompoundLabels.ref == 86)
            ).first()
            return None if row is None else row.name

        return {b: get_label(b.solvent) for b in Batches.select()}

    @classmethod
    def known_solvent_names(cls) -> Mapping[int, str]:
        """
        Note that this map is manually defined and is not guaranteed to reflect newly-used solvents.
        Currently covers DMSO, water, ethanol, methanol, M-Propyl, DMA, and plutonium (used for testing).
        :returns A mapping from compound IDs to names
        """
        return {
            int(k): v for k, v in InternalTools.load_resource("core", "solvents.json")[0].items()
        }

    @classmethod
    def controls_matching_all(
        cls,
        names: Union[None, ControlTypes, str, int, Iterable[Union[ControlTypes, int, str]]] = None,
        **attributes,
    ) -> Set[ControlTypes]:
        """
        Return the control types matching ALL of the specified criteria.
        :param names: The set of allowed control_types
        :param attributes: Any key-value pairs mapping an attribute of ControlTypes to a required value
        """
        if names is not None and not Tools.is_true_iterable(names):
            names = [names]
        InternalTools.verify_class_has_attrs(ControlTypes, attributes)
        allowed_controls = (
            list(ControlTypes.select())
            if names is None
            else ControlTypes.fetch_all(InternalTools.listify(names))
        )
        return {
            c for c in allowed_controls if all([getattr(c, k) == v for k, v in attributes.items()])
        }

    @classmethod
    def controls_matching_any(
        cls,
        names: Union[None, ControlTypes, str, int, Iterable[Union[ControlTypes, int, str]]] = None,
        **attributes,
    ) -> Set[ControlTypes]:
        """
        Return the control types matching ANY of the specified criteria.
        :param names: A set of control_types
        :param attributes: Any key-value pairs mapping an attribute of ControlTypes to a required value
        """
        if not Tools.is_true_iterable(names):
            names = [names]
        InternalTools.verify_class_has_attrs(ControlTypes, attributes)
        if names is None:
            by_name = list(ControlTypes.select())
        elif Tools.is_true_iterable(names):
            by_name = ControlTypes.fetch_all(names)
        else:
            by_name = [ControlTypes.fetch(names)]
        by_other = {
            c
            for c in ControlTypes.select()
            if any([getattr(c, k) == v for k, v in attributes.items()])
        }
        return {*by_name, *by_other}

    @classmethod
    def generate_batch_hash(cls) -> str:
        """
        Generates a batch lookup_hash as an 8-digit lowercase alphanumeric string.
        """
        s = None
        # 41.36 bits with 1 million compounds has a 20% chance of a collision
        # that's ok because the chance for a single compound is very low, and we can always generate a new one
        while (
            s is None
            or Batches.select(Batches.lookup_hash).where(Batches.lookup_hash == s).first()
            is not None
        ):
            s = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        return s

    @classmethod
    def generate_submission_hash(cls) -> str:
        return "%012x" % (random.randrange(16 ** 12))

    @classmethod
    def generate_batch_hash_legacy(cls, batch_id: int) -> str:
        """
        Generates a batch lookup_hash as 'oc_' plus the first 11 characters the sha1 of its ID.
        This is the previous way to generate hashes, but it has problems:
            1) If there's a hash collision, we're stuck.
            2) If we need to reset the IDs, there will be overlap between new and old
            3) We waste 3 characters at the beginning and need 11 random characters
        """
        assert batch_id is not None, "Batch ID cannot be None"
        if isinstance(batch_id, Batches):
            batch_id = batch_id.id
        return "oc_" + Tools.hash_hex(batch_id, "sha1")[:11]

    @classmethod
    def generation_of(cls, run: RunLike) -> DataGeneration:
        """
        Determines the "data generation" of the run, specific to Kokel Lab data. See `DataGeneration` for more details.
        :param run: A runs instance, ID, name, tag, or submission hash or instance
        :return: A DataGeneration instance
        """
        run = ValarTools.run(run)
        sauron = run.sauron_config.sauron  # SauronConfigs.fetch(run.sauron_config).sauron
        # sauronx_version = RunTags.select().where(RunTags.run_id == run.id).where(RunTags.name == 'sauronx_version').first()
        return ValarTools.__generation(sauron.id, sauron.name, run.submission_id is not None)

    @classmethod
    def __generation(cls, sauron_id, sauron_name, has_sub):
        # The Sauron IDs are:
        #     1–9   ⇒ Pike
        #     10–19 ⇒ PointGrey
        #     20–29 ⇒ specialized
        if sauron_name == "MGH":
            return DataGeneration.PIKE_MGH
        elif sauron_name in {"2"} and not has_sub:
            return DataGeneration.PIKE_LEGACY_MATT
        elif sauron_name in {"1", "3"} and not has_sub:
            return DataGeneration.PIKE_LEGACY
        elif sauron_name in {"1", "2", "3"} and has_sub:
            return DataGeneration.PIKE_SAURONX
        elif sauron_name in {"4"}:
            return DataGeneration.POINTGREY_ALPHA
        elif 10 <= sauron_id <= 19:
            # Thor(ondor), Smaug, Drake
            return DataGeneration.POINTGREY
        elif sauron_name == "Puff" and has_sub:
            return DataGeneration.HIGHSPEED_SAURONX
        elif sauron_name == "Puff":
            return DataGeneration.HIGHSPEED_LEGACY
        elif sauron_name.startswith("EC") and sauron_name.endswith("1"):
            return DataGeneration.POINTGREY_ALPHA
        elif sauron_name.startswith("EC"):
            return DataGeneration.POINTGREY
        else:
            raise ValueError("Did not detect a generation for Sauron {}".format(sauron_name))

    @classmethod
    def features_on(cls, run: RunLike) -> Set[str]:
        """
        Finds all unique features involved in all the wells for a given run.
        :param run: A run ID, name, tag, instance, or submission hash or instance
        :return: The set of features involved in a given run.
        """
        run = ValarTools.run(run)
        pt = run.plate.plate_type
        n_wells = pt.n_rows * pt.n_columns
        features = set()
        for feature in Features.select():
            got = len(
                WellFeatures.select(
                    WellFeatures.id, WellFeatures.type_id, WellFeatures.well, Wells.id, Wells.run_id
                )
                .join(Wells)
                .where(Wells.run_id == run)
                .where(WellFeatures.type_id == feature.id)
            )
            if got == n_wells:
                features.add(feature.name)
            assert got == 0 or got == n_wells, "{} != {}".format(got, n_wells)
        return features

    @classmethod
    def sensors_on(cls, run: RunLike) -> Set[Sensors]:
        """
        Finds all unique sensor names that have sensor data for a given run.
        :param run: A run ID, name, tag, instance, or submission hash or instance
        :return: The set of sensor names that have sensor data for a given run.
        """
        run = ValarTools.run(run)
        return {
            sd.sensor
            for sd in SensorData.select(SensorData.sensor, SensorData.run, SensorData.id, Runs.id)
            .join(Runs)
            .switch(SensorData)
            .join(Sensors)
            .where(Runs.id == run.id)
        }

    @classmethod
    def looks_like_submission_hash(cls, submission_hash: str) -> bool:
        """
        :param submission_hash: Any string
        :return: Whether the string could be a submission hash (is formatted correctly)
        """
        return InternalTools.looks_like_submission_hash(submission_hash)

    @classmethod
    def battery_is_legacy(cls, battery: Union[Batteries, str, int]) -> bool:
        """
        :param battery: The battery ID, name, or instance
        :return: Whether the battery is a _true_ legacy battery; i.e. can't be run with SauronX
        """
        battery = Batteries.fetch(battery)
        return battery.name.startswith("legacy-")

    @classmethod
    def assay_is_legacy(cls, assay: Union[Assays, str, int]) -> bool:
        """
        :param assay: The assay ID, name, or instance
        :return: Whether the assay is a _true_ legacy battery; i.e. can't be run with SauronX
        """
        assay = Assays.fetch(assay)
        return assay.name.startswith("legacy-")

    @classmethod
    def assay_is_background(cls, assay: Union[Assays, str, int]) -> bool:
        """
        :param assay: The assay ID, name, or instance
        :return: Whether the assay contains real stimuli; the query is relatively fast
        """
        assay = Assays.fetch(assay)
        stimuli_id = {
            s.stimulus for s in StimulusFrames.select().where(StimulusFrames.assay_id == assay.id)
        }
        stimuli_names = {Stimuli.fetch(s_id).name for s_id in stimuli_id}
        return len(stimuli_names) == 0 or stimuli_names == {"none"}  # stimulus 'none'

    @classmethod
    def sauron_name(cls, sauron: Union[Saurons, int, str]) -> str:
        """
        Returns a display name for a Sauron. Currently this just means prepending a 'S' when necessary.
        Does not perform a fetch. Instead, uses a prefetched map of names.
        :param sauron: A Sauron instance, ID, or name
        """
        if isinstance(sauron, Saurons):
            sauron = sauron.name
        sauron = str(sauron).lower()
        if sauron not in _sauron_str_name_map:
            raise ValarLookupError("No sauron {}".format(sauron))
        return _sauron_str_name_map[sauron]

    @classmethod
    def sauron_config_name(cls, sc) -> str:
        sc = SauronConfigs.fetch(sc)
        return str(sc.id) + ":" + sc.created.strftime("%Y%m%d")

    @classmethod
    def sauron_config(cls, config: SauronConfigLike) -> SauronConfigs:
        """
        Fetches a sauron_configs row from a sauron_config or its ID, or a tuple of (sauron ID/instance/name, datetime modified).
        :raises ValarLookupError if it's not found
        """
        if isinstance(config, (int, SauronConfigs)):
            return SauronConfigs.fetch(config)
        if (
            isinstance(config, tuple)
            and len(config) == 2
            and isinstance(config[0], SauronLike)
            and isinstance(config[1], datetime)
        ):
            sauron = Saurons.fetch(config[0])
            c = (
                SauronConfigs.select()
                .where(SauronConfigs.sauron == sauron)
                .where(SauronConfigs.datetime_changed == config[1])
            )
            if c is None:
                raise ValarLookupError(
                    "No sauron_config for sauron {} at {}".format(sauron.name, config[1])
                )
            else:
                return c

    @classmethod
    def hardware_setting(cls, config: SauronConfigLike, key: str) -> Union[str]:
        config = ValarTools.sauron_config(config)
        setting = (
            SauronSettings.select(SauronSettings, SauronConfigs)
            .join(SauronConfigs)
            .where(SauronConfigs.id == config.id)
            .where(SauronSettings.name == key)
            .first()
        )
        return None if setting is None else setting.value

    @classmethod
    def hardware_settings(cls, config: SauronConfigLike) -> Mapping[str, str]:
        config = ValarTools.sauron_config(config)
        return {
            s.name: s.value
            for s in SauronSettings.select(SauronSettings, SauronConfigs)
            .join(SauronConfigs)
            .where(SauronConfigs.id == config.id)
        }

    @classmethod
    def run_tag(cls, run: RunLike, tag_name: str) -> str:
        """
        Returns a tag value from run_tags or raises a ValarLookupError.
        :param run: A run ID, name, tag, submission hash, submission instance or run instance
        :param tag_name: The value in run_tags.name
        :return: The value as an str
        """
        run = ValarTools.run(run)
        t = RunTags.select().where(RunTags.run_id == run.id).where(RunTags.name == tag_name).first()
        if t is None:
            raise ValarLookupError(
                "No run_tags row for name {} on run {}".format(tag_name, run.name)
            )
        return t.value

    @classmethod
    def run_tag_optional(cls, run: RunLike, tag_name: str) -> Optional[str]:
        """
        Returns a tag value from run_tags.
        :param run: A run ID, name, tag, submission hash, submission instance or run instance
        :param tag_name: The value in run_tags.name
        :return: The value as an str, or None if it doesn't exist
        """
        run = ValarTools.run(run)
        t = RunTags.select().where(RunTags.run_id == run.id).where(RunTags.name == tag_name).first()
        return None if t is None else t.value

    @classmethod
    def stimulus_display_name(cls, stimulus: Union[int, str, Stimuli]) -> str:
        """
        Gets a publication-ready name for a stimulus.
        For example:
            - 'violet (400nm)' instead of 'purple LED'
            - 'alarm' instead of 'MP3'
            - '4-peak 50Hz sine' instead of '4-peak_50hz_s'
            - 'whoosh' instead of 'fs_12'
        :param stimulus: A stimulus ID, name, or instance
        :return: The name as a string
        """
        stimulus = stimulus if isinstance(stimulus, str) else Stimuli.fetch(stimulus)
        return _stimulus_replace[stimulus]

    @classmethod
    def display_name(cls, name: str) -> str:
        """
        Gets a publication-ready name for label.
        Replaces control names with display names (substrings of `name`).
        """
        for k, v in _control_replace.items():
            name = name.replace(k, v)
        return name

    @classmethod
    def control_display_name(cls, control: Union[int, str, ControlTypes]) -> str:
        """
        Gets a publication-ready name for a control type.
        """
        control = ControlTypes.fetch(control)
        for k, v in _control_replace.items():
            if control.name == k:
                return v
        return control.name

    @classmethod
    def datetime_capture_finished(cls, run) -> datetime:
        """Only works for SauronX runs."""
        run = Tools.run(run)
        if run.submission is not None:
            raise SauronxOnlyError(
                "Can't get datetime_capture_finished for a legacy run: It wasn't recorded."
            )
        return datetime.strptime(
            ValarTools.run_tag(run, "datetime_capture_finished"), "%Y-%m-%dT%H:%M:%S.%f"
        )

    @classmethod
    def frames_of_ms(cls, ms: np.array, fps: int) -> np.array:
        """
        Obscure.
        :param ms: The array of millisecond values
        :param fps: The frames per second
        :return: The unique frame seconds, unique, in order
        """
        return np.unique([int(np.round(x * fps / 1000)) for x in ms])

    @classmethod
    def fetch_toml(cls, run: Union[int, str, Runs, Submissions]) -> TomlData:
        """
        Parse TomlData from config_files.
        """
        run = ValarTools.run(run)
        sxt = ConfigFiles.fetch(run.config_file_id)
        return TomlData(tomlkit.loads(sxt.toml_text))

    @classmethod
    def parse_toml(cls, sxt: Union[ConfigFiles, Runs]) -> TomlData:
        """
        Parse TomlData from config_files.
        """
        if isinstance(sxt, Runs):
            sxt = ConfigFiles.fetch(sxt.config_file_id)
        return TomlData(tomlkit.loads(sxt.toml_text))

    @classmethod
    def initials(cls, user: Union[Users, int, str]) -> str:
        """
        Returns the initials of a user.
        For example, 'matt' will be 'MMC', and 'douglas' will be 'DMT'.
        :param user: The name, ID, or instance in the users table
        :return: The initials as a string, in caps
        """
        if isinstance(user, int):
            user = Users.select().where(Users.id == user).first()
        if isinstance(user, str):
            user = Users.select().where(Users.username == user).first()
        s = ""
        if user.first_name.islower():
            user.first_name = user.first_name.capitalize()
        if user.last_name.islower():
            user.last_name = user.last_name.capitalize()
        for i, c in enumerate(user.first_name + " " + user.last_name):
            if c == c.upper() and c != c.lower():
                s += c
        return s

    @classmethod
    def users_to_initials(cls) -> Mapping[Users, str]:
        """
        Returns the initials of all Users in database.
        :return: Dictionary of all Users with keys corresponding to User Instances and values corresponding to
        initials as strings in caps
        """
        return {user: ValarTools.initials(user) for user in Users.select()}

    @classmethod
    def storage_path(cls, run: Union[int, str, Runs, Submissions], shire_path: str) -> PurePath:
        run = Tools.run(run)
        year = str(run.datetime_run.year).zfill(4)
        month = str(run.datetime_run.month).zfill(2)
        path = PurePath(shire_path, "store", year, month, str(run.tag))
        # TODO .replace('\\\\', '\\') ?
        # if path.startswith('\\'): path = '\\' + path
        return path

    @classmethod
    def expected_n_frames(cls, run: Union[int, str, Runs, Submissions]) -> int:
        """
        Calculate the number of frames expected for the ideal (configured) framerate of the run.
        Calls
        :param run: A run ID, name, tag, instance, or submission hash or instance
        :return: ValarTools.frames_per_second.
        """
        run = ValarTools.run(run)
        run = (
            Runs.select(
                Runs, Experiments.id, Experiments.battery_id, Batteries.id, Batteries.length
            )
            .join(Experiments)
            .join(Batteries)
            .where(Runs.id == run)
            .first()
        )
        battery = run.experiment.battery
        return (
            ValarTools.frames_per_second(run)
            * battery.length
            / (25 if run.submission is None else 1000)
        )

    @classmethod
    def fps_of_sauron_config(cls, sauron_config: Union[SauronConfigs, int]) -> Optional[int]:
        fps = (
            SauronSettings.select()
            .where(SauronSettings.sauron_config == sauron_config)
            .where(SauronSettings.name == "fps")
            .first()
        )
        return None if fps is None else Tools.only(fps, name="framerates").value

    @classmethod
    def sauron_configs_with_fps(
        cls, sauron: Union[Saurons, int, str], fps: int
    ) -> Sequence[SauronConfigs]:
        return ValarTools.sauron_configs_with_setting(sauron, "fps", fps)

    @classmethod
    def sauron_configs_with_setting(
        cls, sauron: Union[Saurons, int, str], name: str, value: Any
    ) -> Sequence[SauronConfigs]:
        query = (
            SauronSettings.select(SauronSettings, SauronConfigs)
            .join(SauronConfigs)
            .where(SauronSettings.name == name)
            .where(SauronSettings.value == str(value))
        )
        if sauron is not None:
            query = query.where(SauronConfigs.sauron == sauron)
        query = query.order_by(SauronConfigs.created)
        return Tools.unique([setting.sauron_config for setting in query])

    @classmethod
    def toml_data(cls, run: RunLike) -> TomlData:
        run = ValarTools.run(run)
        t = ConfigFiles.fetch(run.config_file_id)
        return TomlData(tomlkit.loads(t.toml_text))

    @classmethod
    def toml_item(cls, run: RunLike, item: str) -> Any:
        return cls.toml_items(run)[item]

    @classmethod
    def toml_items(cls, run: RunLike) -> Mapping[str, Any]:
        run = ValarTools.run(run)
        t = ConfigFiles.fetch(run.config_file_id)
        data = TomlData(tomlkit.loads(t.toml_text))
        lst = {}

        def settings(value, key):
            if isinstance(value, (dict, TomlData)):
                for k, v in value.items():
                    settings(v, str(key) + "." + str(k))
            else:
                lst[key.lstrip(".")] = value

        settings(data, "")
        return lst

    @classmethod
    def frames_per_second(cls, run: RunLike) -> int:
        """
        Determines the main camera framerate used in a run.
        NOTE:
            This is the IDEAL framerate: The one that was configured.
            To get the emperical framerate for PointGrey data, download the timestamps. (The emperical framerate is unknown for pre-PointGrey data.)
        For legacy data, always returns 25. Note that for some MGH data it might actually be a little slower or faster.
        For SauronX data, fetches the TOML data from Valar and looks up sauron.hardware.camera.frames_per_second .
        :param run: A run ID, name, tag, instance, or submission hash or instance
        :return: A Python int
        """
        run = Tools.run(run)
        if run.submission is None:
            return 25
        t = ConfigFiles.fetch(run.config_file_id)
        # noinspection PyTypeChecker
        return int(TomlData(tomlkit.loads(t.toml_text))["sauron.hardware.camera.frames_per_second"])

    @classmethod
    def battery_stimframes_per_second(cls, battery: Union[int, str, Batteries]) -> int:
        return 25 if ValarTools.battery_is_legacy(battery) else 1000

    @classmethod
    def assay_ms_per_stimframe(cls, assay: Union[int, str, Assays]) -> int:
        return 1000 / 25 if ValarTools.assay_is_legacy(assay) else 1

    @classmethod
    def frames_per_stimframe(cls, run: Union[int, str, Runs, Submissions]) -> float:
        """
        Returns the number of frames
        :param run: A run ID, name, tag, instance, or submission hash or instance
        :return:
        """
        run = ValarTools.run(run)
        if run.submission is None:
            return 1
        else:
            t = ConfigFiles.fetch(run.config_file_id)
            fps = TomlData(tomlkit.loads(t.toml_text)).get_int(
                "sauron.hardware.camera.frames_per_second"
            )
            return fps / 1000

    @classmethod
    def parse_param_value(
        cls, submission: Union[Submissions, int, str], param_name: str
    ) -> Union[
        Sequence[np.int64],
        Sequence[np.float64],
        Sequence[Batches],
        Sequence[GeneticVariants],
        np.int64,
        np.float64,
        Batches,
        GeneticVariants,
        str,
        Sequence[str],
    ]:
        """
        Parses a submission value into strings, lists, ints, floats, batches, or genetic_variants.
        :param submission: Submission Identifier
        :return: Submission Paramater value
        :param param_name: Ex '$...drug'
        """
        submission = Submissions.fetch(submission)
        params = Tools.query(
            SubmissionParams.select().where(SubmissionParams.submission == submission)
        )
        if param_name not in params["name"].tolist():
            raise ValarLookupError(
                "No submission param with name {} for submission {}".format(
                    param_name, submission.lookup_hash
                )
            )
        # handle special case of library syntax
        row = params[params["name"] == param_name].iloc[0]
        if row.value.startswith("[/") and row.value.endswith("/]"):
            return row.value
        # otherwise convert by eval
        literal = ast.literal_eval(row.value)

        # util functions
        def oc_it(oc: str):
            return Batches.fetch(oc)

        def var_it(var: str):
            return GeneticVariants.fetch(var)

        # convert
        if row.param_type == "group" and isinstance(literal, str):
            return literal
        elif row.param_type == "replicate" and isinstance(literal, int):
            return np.int64(literal)
        elif row.param_type == "group" and isinstance(literal, list):
            return literal
        elif row.param_type == "compound" and isinstance(literal, str):
            return oc_it(literal)
        elif row.param_type == "compound" and isinstance(literal, list):
            return [oc_it(oc) for oc in literal]
        elif row.param_type == "variant" and isinstance(literal, str):
            return var_it(literal)
        elif row.param_type == "variant" and isinstance(literal, list):
            return [var_it(v) for v in literal]
        elif row.param_type == "dose" and isinstance(literal, list):
            return [np.float64(dose) for dose in literal]
        elif (row.param_type == "n_fish" or row.param_type == "dose") or (
            row.param_type == "dpf" and isinstance(literal, str)
        ):
            return np.float64(literal)
        elif (row.param_type == "n_fish" or row.param_type == "dpf") and isinstance(literal, list):
            return [np.int64(l) for l in literal]
        else:
            raise TypeError(
                "This shouldn't happen: type {} of param value {} not understood".format(
                    type(literal), literal
                )
            )

    @classmethod
    def all_plates_ids_of_library(cls, ref: Union[Refs, int, str]) -> Set[str]:
        """
        Returns the batches.legacy_interal_id values, truncated to exclude the last two digits, of the batches under a library.
        For these batches, the legacy_internal_id values are the library name, followed by the plate number, followed by the well index (last 2 digits).
        This simply strips off the last two digits of legacy IDs that match the pattern described above. All legacy ids not following the pattern
        are excluded from the returned set.
        :param ref: The library Refs table ID, name, or instance
        :return: The unique library plate IDs, from the legacy_internal fields
        """
        ref = Refs.fetch(ref)
        s = set([])
        for o in Batches.select(Batches.legacy_internal, Batches.ref_id).where(
            Batches.ref_id == ref.id
        ):
            pat = re.compile("""([A-Z]{2}[0-9]{5})[0-9]{2}""")
            match = pat.fullmatch(o.legacy_internal)
            if match is not None:
                s.add(match.group(1))
        return s

    @classmethod
    def library_plate_id_of_submission(
        cls, submission: Union[Submissions, int, str], var_name: Optional[str] = None
    ) -> str:
        """
        Determines the library plate name from a submission.
        Uses a fair bit of logic to figure this out; peruse the code for more info.
        :param submission: The submission ID, hash, or instance
        :param var_name: The submission_params variable name, often something like '$...drug'
        :return: library plate id for new style submissions and truncated legacy_internal_id values for old style submissions.
        """
        submission = Submissions.fetch(submission)
        if var_name is None:
            var_name = Tools.only(
                {
                    p.name
                    for p in SubmissionParams.select().where(
                        SubmissionParams.submission == submission
                    )
                    if p.name.startswith("$...")
                },
                name="possible submission param names",
            )
        oc = ValarTools.parse_param_value(submission, var_name)
        if isinstance(oc, str) and oc.startswith("[/") and oc.endswith("/]"):
            # new style where we keep the [/CB333/] format
            # and valar.params converts it
            return oc[2:-2]
        if isinstance(oc, list):
            # old style where the website converted the library into a list
            oc = oc[0]
            # ex: CB6158101
            pat = re.compile("""([A-Z]{2}[0-9]{5})[0-9]{2}""")
            match = pat.fullmatch(oc.legacy_internal)
            if match is None:
                raise ValarLookupError(
                    "Batch {} on submission {} has the wrong legacy_internal_id form {}".format(
                        oc.lookup_hash, submission.lookup_hash, oc.legacy_internal
                    )
                )
            return match.group(1)
        else:
            assert False, "Type {} of param {} not understood".format(type(oc), oc)

    @classmethod
    def runs(
        cls, runs: Union[int, str, Runs, Submissions, Iterable[Union[int, str, Runs, Submissions]]]
    ) -> Sequence[Runs]:
        """Fetches an iterable of runs from an iterable of ID(s), tag(s), name(s),
        or submission hash(es).
        :param runs: An iterable consisting of run ID(s), name(s), tag(s), instance(s), or submission hash(es) or instance(s)
        :return: An iterable consisting of runs associated with given run identifiers."""
        return Tools.runs(runs)

    @classmethod
    def run(cls, run: Union[int, str, Runs, Submissions]) -> Runs:
        """Fetches a run from an ID, tag, name, or submission hash.
        :param run: A run ID, name, tag, instance, or submission hash or instance
        :return: A run associated with the given ID, name, tag, instance, or submission hash or instance"""
        return Tools.run(run)

    @classmethod
    def assay_name_simplifier(cls) -> Callable[[str], str]:
        """
        Return a function that strips out substrings of assay names that are undesirable for reading or figure labels.
        Strips out the legacy assay qualifiers like `(variant:...)` and the user/experiment info.
        Also removes text like '#legacy' and 'sauronx-', and 'sys :: light ::'.
        :return: A function mapping assay names to new names
        """
        _usernames = {u.username for u in Users.select(Users.username)}
        _qualifier = re.compile("-\\(variant:.*\\)")
        _end = re.compile(
            "-(?:" + "|".join(_usernames) + ")" + """-[0-9]{4}-[0-9]{2}-[0-9]{2}-0x[0-9a-h]{4}$"""
        )

        def _simplify_name(name: str) -> str:
            prefixes = dict(InternalTools.load_resource("core", "assay_prefixes.json")[0])
            s = _qualifier.sub("", _end.sub("", name))
            for k, v in prefixes.items():
                s = s.replace(k, v)
            if s.endswith(", 30s"):
                s = s[:-5]
            if s.endswith(" 255"):
                s = s[:-4]
            s = s.replace("uv", "UV")
            return s

        return _simplify_name

    @classmethod
    def simplify_assay_name(cls, assay: Union[Assays, int, str]) -> str:
        """
        See `ValarTools.assay_name_simplifier`, which is faster for many assay names.
        """
        name = assay if isinstance(assay, str) else Assays.fetch(assay).name
        return ValarTools.assay_name_simplifier()(name)

    @classmethod
    def fetch_feature_slice(
        cls, well, feature: Features, start_frame: int, end_frame: int
    ) -> Optional[np.array]:
        """
        Quickly gets only a fraction of a time-dependent feature.
        :param well: The well ID
        :param feature: The FeatureType to select
        :param start_frame: Starts at 0 as per our convention (note that MySQL itself starts at 1)
        :param end_frame: Starts at 0 as per our convention (note that MySQL itself starts at 1)
        """
        well = Wells.fetch(well)
        feature = Features.fetch(feature)
        sliced = fn.SUBSTR(
            WellFeatures.floats,
            start_frame + 1,
            feature.stride_in_bytes * (end_frame - start_frame),
        )
        blob = (
            WellFeatures.select(sliced.alias("sliced"))
            .where(WellFeatures.well_id == well.id)
            .first()
        )
        return None if blob is None else feature.from_blob(blob.sliced, well.id)


__all__ = ["ValarTools", "StimulusType"]
