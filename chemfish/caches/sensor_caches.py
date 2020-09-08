import soundfile
from PIL import Image

from chemfish.core.core_imports import *
from chemfish.model.cache_interfaces import ASensorCache
from chemfish.model.sensors import *

DEFAULT_CACHE_DIR = chemfish_env.cache_dir / "sensors"


@abcd.auto_eq()
@abcd.auto_repr_str()
class SensorCache(ASensorCache):
    """
    A cache for sensor data from a given run.
    """

    def __init__(self, cache_dir: PathLike = DEFAULT_CACHE_DIR):
        self._cache_dir = Tools.prepped_dir(cache_dir)

    @property
    def cache_dir(self) -> Path:
        """ """
        return self._cache_dir

    @abcd.overrides
    def path_of(self, tup: Tup[SensorNames, RunLike]) -> Path:
        """


        Args:
            tup:

        Returns:

        """
        sensor, run = tup
        return self.cache_dir / str(run.id) / (sensor.name.lower() + sensor.extension)

    @abcd.overrides
    def key_from_path(self, path: PathLike) -> Tup[SensorNames, RunLike]:
        """


        Args:
            path: PathLike:

        Returns:

        """
        path = Path(path).relative_to(self.cache_dir)
        run = int(re.compile(r"^r([0-9]+)$").fullmatch(path.parent.name).group(1))
        sensor = re.compile(r"^r([a-z0-9\-_]+)\..+$").fullmatch(path.name).group(1)
        return SensorNames[sensor.upper()], run

    @abcd.overrides
    def download(self, *sensors: Iterable[Tup[SensorNames, RunLike]]) -> None:
        """


        Args:
            *sensors:

        """
        for sensor, run in sensors:
            self._download(sensor, run)

    def bt_data(self, run: RunLike) -> BatteryTimeData:
        """


        Args:
          run: RunLike:

        Returns:

        """
        millis = self._download("stimulus_millis", run)
        return BatteryTimeData(run, millis[0], millis[-1])

    @abcd.overrides
    def load_photosensor(self, run: RunLike) -> PhotosensorSensor:
        """


        Args:
            run:

        Returns:

        """
        # noinspection PyTypeChecker
        return self.load((SensorNames.PHOTOSENSOR, run))

    @abcd.overrides
    def load_thermosensor(self, run: RunLike) -> ThermosensorSensor:
        """


        Args:
            run:

        Returns:

        """
        # noinspection PyTypeChecker
        return self.load((SensorNames.THERMOSENSOR, run))

    @abcd.overrides
    def load_wav(self, run: RunLike) -> MicrophoneSensor:
        """


        Args:
            run:

        Returns:

        """
        # noinspection PyTypeChecker
        return self.load((SensorNames.MICROPHONE, run))

    @abcd.overrides
    def load_preview(self, run: RunLike) -> ImageSensor:
        """


        Args:
            run:

        Returns:

        """
        # noinspection PyTypeChecker
        return self.load((SensorNames.PREVIEW_FRAME, run))

    @abcd.overrides
    def load_webcam(self, run: RunLike) -> ImageSensor:
        """


        Args:
            run:

        Returns:

        """
        # noinspection PyTypeChecker
        return self.load((SensorNames.SECONDARY_CAMERA, run))

    @abcd.overrides
    def load(self, tup: Tup[SensorNames, RunLike]) -> ChemfishSensor:
        """


        Args:
            tup:

        Returns:

        """
        sensor_name, run = tup
        run = ValarTools.run(run)
        if sensor_name == SensorNames.PHOTOSENSOR:
            return PhotosensorSensor(
                run,
                self._download("photosensor_millis", run),
                self._download("photosensor_values", run),
                self.bt_data(run),
                None,
            )
        elif sensor_name == SensorNames.THERMOSENSOR:
            return ThermosensorSensor(
                run,
                self._download("thermosensor_millis", run),
                self._download("thermosensor_values", run),
                self.bt_data(run),
                None,
            )
        elif sensor_name == SensorNames.MICROPHONE:
            self._download("microphone_recording", run)
            millis = np.repeat(self._download("microphone_millis", run), 1024)
            self._download("microphone_recording", run)
            data, sampling_rate = soundfile.read(
                self.path_of((SensorNames.RAW_MICROPHONE_RECORDING, run))
            )
            return MicrophoneSensor(run, millis, data, self.bt_data(run), sampling_rate)
        elif sensor_name == SensorNames.STIMULUS_TIMING:
            return StimulusTimeData(run, self._download("stimulus_millis", run))
        elif sensor_name == SensorNames.CAMERA_TIMING:
            return CameraTimeData(run, self._download("camera_millis", run))
        elif sensor_name == SensorNames.SECONDARY_CAMERA:
            return ImageSensor(run, self._download("secondary_camera", run))
        elif sensor_name == SensorNames.PREVIEW_FRAME:
            return ImageSensor(run, self._download("preview_frame", run))
        else:
            raise UnsupportedOpError(f"Sensor of type {sensor_name} cannot be loaded")

    def _download(
        self, std_sensor: str, run: RunLike
    ) -> Union[None, np.array, bytes, str, Image.Image]:
        """
        Fetches sensor data if cache is available. Downloads if cache not present.

        Args:
            sensor:
            run: RunLike:

        Returns:
            Raw/Converted Sensor Data

        """
        run = ValarTools.run(run)
        generation = ValarTools.generation_of(run)
        sensor = Sensors.fetch(ValarTools.standard_sensor(std_sensor, generation))
        sname = SensorNames["RAW_" + std_sensor.upper()]
        path = self.path_of((sname, run))
        if path.exists():
            return ValarTools.convert_sensor_data_from_bytes(sensor, path.read_bytes())
        Tools.prep_file(path, exist_ok=False)
        logger.minor(f"Downloading {sensor.name} for run r{run.id} from Valar...")
        data = (
            SensorData.select(SensorData)
            .where(SensorData.run_id == run.id)
            .where(SensorData.sensor_id == sensor.id)
            .first()
        )
        if data is None:
            raise ValarLookupError(f"No data for sensor {sensor.id} on run r{run.name}")
        path.write_bytes(data.floats)
        return ValarTools.convert_sensor_data_from_bytes(sensor, data.floats)


__all__ = ["SensorCache"]
