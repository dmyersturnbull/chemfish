import soundfile

from chemfish.core.core_imports import *
from chemfish.model.cache_interfaces import ASensorCache
from chemfish.model.sensors import *

DEFAULT_CACHE_DIR = chemfish_env.cache_dir / "sensors"
bdata_names = {"sauronx-microphone-wav", "preview", "webcam"}


@abcd.auto_eq()
@abcd.auto_repr_str()
class SensorCache(ASensorCache):
    """
    A cache for sensor data from a given run
    """

    def __init__(self, cache_dir: PLike = DEFAULT_CACHE_DIR):
        self._cache_dir = Tools.prepped_dir(cache_dir)

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @abcd.overrides
    def path_of(self, tup: Tup[SensorLike, RunLike]) -> Path:
        sensor, run = tup
        sensor = Sensors.fetch(sensor)
        ext = ".flac" if "microphone-wav" in sensor.name else ".bytes"
        return self.cache_dir / str(run.id) / (sensor.name + ext)

    @abcd.overrides
    def key_from_path(self, path: PLike) -> Tup[SensorLike, RunLike]:
        path = Path(path).relative_to(self.cache_dir)
        run = int(re.compile(r"^r([0-9]+)$").fullmatch(path.parent.name).group(1))
        sensor = re.compile(r"^r([a-z0-9\-_]+)\..+$").fullmatch(path.name).group(1)
        return sensor, run

    @abcd.overrides
    def download(self, *sensors: Iterable[Tup[SensorLike, RunLike]]):
        for sensor, run in sensors:
            self._download(sensor, run)

    def bt_data(self, run: RunLike) -> BatteryTimeData:
        millis = self._download("sauronx-stimulus-ms", run)
        return BatteryTimeData(run, millis[0], millis[-1])

    @abcd.overrides
    def load(self, tup: Tup[SensorNames, RunLike]):
        sensor_name, run = tup
        sensor_name = SensorNames.of(sensor_name)
        run = ValarTools.run(run)
        if sensor_name == SensorNames.PHOTORESISTOR:
            return PhotoresistorSensor(
                run,
                self._download("sauronx-tinkerkit-photometer-ms", run),
                self._download("sauronx-tinkerkit-photometer-values", run),
                self.bt_data(run),
                None,
            )
        elif sensor_name == SensorNames.THERMISTOR:
            return ThermistorSensor(
                run,
                self._download("sauronx-tinkerkit-thermometer-ms", run),
                self._download("sauronx-tinkerkit-thermometer-values", run),
                self.bt_data(run),
                None,
            )
        elif sensor_name == SensorNames.MICROPHONE:
            self._download("sauronx-microphone-wav", run)
            millis = np.repeat(self._download("sauronx-microphone-ms", run), 1024)
            data, sampling_rate = soundfile.read(self.path_of(("sauronx-microphone-wav", run)))
            return MicrophoneRawSensor(run, millis, data, self.bt_data(run), sampling_rate)
        elif sensor_name == SensorNames.STIMULUS_TIMING:
            return StimulusTimeData(run, self._download("sauronx-stimulus-ms", run))
        elif sensor_name == SensorNames.CAMERA_TIMING:
            return CameraTimeData(run, self._download("sauronx-snapshot-ms", run))
        elif sensor_name == SensorNames.WEBCAM:
            return ImageSensor(run, self._download("webcam", run))
        elif sensor_name == SensorNames.PREVIEW:
            return ImageSensor(run, self._download("preview", run)).draw_roi_grid()
        else:
            raise UnsupportedOpError("Sensor of type {} cannot be loaded".format(sensor_name))

    def _download(self, sensor: SensorLike, run: RunLike) -> bytes:
        """
        Fetches sensor data if cache is available. Downloads if cache not present.
        :param sensor:
        :param run:
        :return: Raw/Converted Sensor Data
        """
        sensor = Sensors.fetch(sensor)
        run = ValarTools.run(run)
        path = self.path_of((sensor, run))
        if path.exists():
            if sensor.name in bdata_names:
                return path.read_bytes()
            else:
                return InternalValarTools.convert_sensor_data_from_bytes(sensor, path.read_bytes())
        Tools.prep_file(path, exist_ok=False)
        logger.minor("Downloading {} for run r{} from Valar...".format(sensor.name, run.id))
        data = (
            SensorData.select(SensorData)
            .where(SensorData.run_id == run.id)
            .where(SensorData.sensor_id == sensor.id)
            .first()
        )
        if data is None:
            raise ValarLookupError("No data for sensor {} on run {}".format(sensor.id, run.name))
        path.write_bytes(data.floats)
        if sensor.name in bdata_names:
            return data.floats
        else:
            return InternalValarTools.convert_sensor_data_from_bytes(sensor, data.floats)


__all__ = ["SensorCache"]
