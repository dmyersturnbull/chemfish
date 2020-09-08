import soundfile
from PIL import Image
import pydub

from chemfish.core.core_imports import *
from chemfish.model.cache_interfaces import ASensorCache
from chemfish.model.sensors import *

DEFAULT_CACHE_DIR = chemfish_env.cache_dir / "sensors"

name_to_sensor: Mapping[SensorNames, Type[ChemfishSensor]] = {
    SensorNames.THERMOSENSOR: ThermosensorSensor,
    SensorNames.PHOTOSENSOR: PhotosensorSensor,
    SensorNames.MICROPHONE: MicrophoneSensor,
    SensorNames.STIMULUS_MILLIS: StimulusTimeData,
    SensorNames.CAMERA_MILLIS: CameraTimeData,
    SensorNames.PREVIEW_FRAME: PreviewFrameSensor,
    SensorNames.SECONDARY_CAMERA: SecondaryCameraSensor,
    **{name: RawDataSensor for name in list(SensorNames) if name.is_raw},
}


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
            # doing this is SO much simpler
            # otherwise we'd have to duplicate the switch logic
            # to handle raw and composite sensors separately
            self.load((sensor, run))

    def bt_data(self, run: RunLike) -> EmpiricalBatteryTimeData:
        """


        Args:
          run: RunLike:

        Returns:

        """
        millis = self._download_raw(SensorNames.RAW_STIMULUS_MILLIS, run)
        return EmpiricalBatteryTimeData(run, millis[0], millis[-1])

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
    def load_microphone(self, run: RunLike) -> MicrophoneSensor:
        """


        Args:
            run:

        Returns:

        """
        # noinspection PyTypeChecker
        return self.load((SensorNames.MICROPHONE, run))

    @abcd.overrides
    def load_waveform(self, run: RunLike) -> MicrophoneWaveformSensor:
        """


        Args:
            run:

        Returns:

        """
        # noinspection PyTypeChecker
        return self.load((SensorNames.MICROPHONE_WAVEFORM, run))

    @abcd.overrides
    def load_preview_frame(self, run: RunLike) -> ImageSensor:
        """


        Args:
            run:

        Returns:

        """
        # noinspection PyTypeChecker
        return self.load((SensorNames.PREVIEW_FRAME, run))

    @abcd.overrides
    def load_secondary_camera(self, run: RunLike) -> ImageSensor:
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
        for component in sensor_name.components:
            logger.debug(f"Finding {component} for {sensor_name}")
            self._download_raw(component, run)
        # okay, now fetch the real one
        if sensor_name.is_audio_waveform:
            return self._load_audio_waveform(run)
        if sensor_name.is_audio_composite:
            return self._load_audio(run)
        elif sensor_name.is_time_dependent:
            return self._load_time_dep(sensor_name, run)
        elif sensor_name.is_timing:
            # noinspection PyTypeChecker
            z: Type[TimeDataSensor] = name_to_sensor[sensor_name]
            return z(run, self._download_raw(sensor_name.millis_component, run))
        elif sensor_name.is_image:
            # noinspection PyTypeChecker
            z: Type[ImageSensor] = name_to_sensor[sensor_name]
            return z(run, self._download_raw(sensor_name.raw_bytes_component, run))
        elif sensor_name.is_raw:
            return RawDataSensor(run, self._download_raw(sensor_name, run))
        else:
            raise UnsupportedOpError(f"Sensor of type {sensor_name} cannot be loaded")

    def _load_audio_waveform(self, run: Runs) -> MicrophoneWaveformSensor:
        path = self.path_of((SensorNames.MICROPHONE_WAVEFORM, run))
        mic = self._load_audio(run).slice_ms(None, None)
        if path.exists():
            logger.debug(f"Loading waveform from {path}")
            vec = np.load(str(path))
            waveform = MicrophoneWaveform(
                name=run.name,
                path=None,
                data=vec,
                sampling_rate=mic.samples_per_sec,
                minimum=-1,
                maximum=-1,
                description=run.name,
                start_ms=None,
                end_ms=None,
            )
            return MicrophoneWaveformSensor(
                run=run,
                waveform=waveform,
                timing_data=mic.timing_data,
                battery_data=mic.bt_data,
                samples_per_sec=1000,
            )
        else:
            logger.debug(f"Making waveform fresh")
            waveform_sensor = mic.waveform(1000)
            np.save(str(path), waveform_sensor.waveform.data)
            return waveform_sensor

    def _load_audio(self, run: Runs) -> MicrophoneSensor:
        self._download_raw(SensorNames.RAW_MICROPHONE_RECORDING, run)
        # why 1024?
        millis = np.repeat(self._download_raw(SensorNames.RAW_MICROPHONE_MILLIS, run), 1024)
        data, sampling_rate = soundfile.read(
            self.path_of((SensorNames.RAW_MICROPHONE_RECORDING, run))
        )
        return MicrophoneSensor(run, millis, data, self.bt_data(run), sampling_rate)

    def _load_time_dep(self, sensor_name: SensorNames, run: Runs) -> TimeDepChemfishSensor:
        # noinspection PyTypeChecker
        z: Type[TimeDepChemfishSensor] = name_to_sensor[sensor_name]
        return z(
            run,
            self._download_raw(sensor_name.millis_component, run),
            self._download_raw(sensor_name.values_component, run),
            self.bt_data(run),
            None,
        )

    def _download_raw(
        self, sensor_name: SensorNames, run: RunLike
    ) -> Union[None, np.array, bytes, str, Image.Image]:
        """
        Fetches sensor data if cache is available. Downloads if cache not present.

        Args:
            sensor_name:
            run: RunLike:

        Returns:
            Raw/Converted Sensor Data

        """
        run = ValarTools.run(run)
        generation = ValarTools.generation_of(run)
        sensor = Sensors.fetch(ValarTools.standard_sensor(sensor_name, generation))
        path = self.path_of((sensor_name, run))
        if path.exists():
            logger.debug(f"Loading {sensor.name} from {path}")
            if sensor_name.is_image:
                return Image.open(path)
            elif sensor_name == SensorNames.RAW_MICROPHONE_RECORDING:
                return path.read_bytes()
            else:
                return np.load(str(path))
                # return ValarTools.convert_sensor_data_from_bytes(sensor, path.read_bytes())
        Tools.prep_file(path, exist_ok=False)
        logger.debug(f"Downloading {sensor.name} for run r{run.id} from Valar...")
        data = (
            SensorData.select(SensorData)
            .where(SensorData.run_id == run.id)
            .where(SensorData.sensor_id == sensor.id)
            .first()
        )
        if data is None:
            raise ValarLookupError(f"No data for sensor {sensor.id} on run r{run.name}")
        converted = ValarTools.convert_sensor_data_from_bytes(sensor, data.floats)
        if sensor_name.is_image or sensor_name == SensorNames.RAW_MICROPHONE_RECORDING:
            path.write_bytes(converted)
        else:
            # noinspection PyTypeChecker
            np.save(str(path), converted)
        return converted


__all__ = ["SensorCache"]
