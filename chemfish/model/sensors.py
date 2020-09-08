from __future__ import annotations

from PIL import Image, ImageDraw

from chemfish.core.core_imports import *
from chemfish.core.valar_singleton import *
from chemfish.model.audio import *


@enum.unique
class SensorNames(SmartEnum):
    """
    Enum of SensorNames. Put all Sensors that are involved in sensor_caches in here.
    """

    PHOTOSENSOR = enum.auto()
    THERMOSENSOR = enum.auto()
    MICROPHONE = enum.auto()
    SECONDARY_CAMERA = enum.auto()
    PREVIEW_FRAME = enum.auto()
    STIMULUS_TIMING = enum.auto()
    CAMERA_TIMING = enum.auto()
    RAW_SECONDARY_CAMERA = enum.auto()
    RAW_PREVIEW_FRAME = enum.auto()
    RAW_MICROPHONE_RECORDING = enum.auto()
    RAW_MICROPHONE_MILLIS = enum.auto()
    RAW_CAMERA_MILLIS = enum.auto()
    RAW_STIMULUS_MILLIS = enum.auto()
    RAW_STIMULUS_VALUES = enum.auto()
    RAW_STIMULUS_IDS = enum.auto()
    RAW_PHOTOSENSOR_MILLIS = enum.auto()
    RAW_PHOTOSENSOR_VALUES = enum.auto()
    RAW_THERMOSENSOR_MILLIS = enum.auto()
    RAW_THERMOSENSOR_VALUES = enum.auto()

    @property
    def extension(self) -> str:
        return ".flac" if self is SensorNames.MICROPHONE else ".bytes"


class MicrophoneWaveform(Waveform):
    """"""

    pass


@abcd.auto_repr_str()
@abcd.auto_eq()
@abcd.auto_hash()
class BatteryTimeData:
    """
    BatteryTimeData object (contains start/end timestamps, length of battery, etc.) for a given run.
    These are the empirical values, not the expected ones!

    """

    def __init__(self, run: RunLike, start_ms: int, end_ms: int):
        """

        Args:
            run:
            start_ms:
            end_ms:
        """
        self.run, self.start_ms, self.end_ms = Tools.run(run), int(start_ms), int(end_ms)

    @property
    def start_end_dts(self) -> Tup[datetime, datetime]:
        """"""
        return self.start_dt, self.end_dt

    @property
    def start_dt(self) -> datetime:
        """"""
        return self.run.datetime_run + timedelta(milliseconds=self.start_ms)

    @property
    def end_dt(self) -> datetime:
        """"""
        return self.run.datetime_run + timedelta(milliseconds=self.end_ms)

    def __len__(self) -> int:
        return len(self.data)


class ChemfishSensor:
    """"""

    def __init__(self, run: RunLike, sensor_data: Union[SensorDataLike, Image.Image]):
        """
        Sensor wrapper object that holds converted sensor_data for a given run.

        Args:
            run: Run ID, Submission ID, Submission Object, or Run Object
            sensor_data: Converted Sensor_data

        """
        self._sensor_data = sensor_data
        self._run = ValarTools.run(run)

    @property
    def run(self) -> Runs:
        """ """
        return self._run

    @property
    def data(self) -> Union[SensorDataLike, Image.Image]:
        """ """
        return self._sensor_data

    @property
    def name(self) -> str:
        """ """
        return Tools.strip_off_end(self.__class__.__name__.lower(), "sensor")

    @property
    def abbrev(self) -> str:
        """ """
        raise NotImplementedError()

    @property
    def symbol(self) -> str:
        """ """
        raise NotImplementedError()

    def __str__(self):
        return "{}(r{} ℓ={})".format(self.__class__.__name__, self.run.id, len(self._sensor_data))

    def __repr__(self):
        return "{}(r{} ℓ={} @{})".format(
            self.__class__.__name__, self.run.id, len(self._sensor_data), str(hex(id(self)))
        )


class TimeData(ChemfishSensor, metaclass=abc.ABCMeta):
    """
    BatteryTimeData object (contains start/end timestamps, length of battery, etc.) for a given run.
    These are the empirical values, not the expected ones!

    """

    def __init__(self, run: RunLike, battery_data: np.array):
        super().__init__(run, battery_data)
        self.planned_battery_n_ms = run.experiment.battery.length

    def timestamps(self) -> Sequence[datetime]:
        """ """
        return [self.run.datetime_run + timedelta(milliseconds=int(ms)) for ms in self.data]

    def timestamp_at(self, ind: int) -> datetime:
        """


        Args:
            ind: int:

        Returns:

        """
        return self.run.datetime_run + timedelta(milliseconds=int(self.data[ind]))

    @property
    def start_ms(self) -> int:
        """ """
        return self._sensor_data[0]

    @property
    def end_ms(self) -> int:
        """ """
        return self._sensor_data[-1]

    @property
    def n_ms(self) -> float:
        """ """
        # noinspection PyUnresolvedReferences
        return (self._sensor_data[1] - self._sensor_data[0]).total_seconds() * 1000

    @property
    def start_end_dts(self) -> Tup[datetime, datetime]:
        """ """
        return self.timestamp_at(0), self.timestamp_at(-1)

    def __len__(self) -> int:
        return len(self.data)


class StimulusTimeData(TimeData):
    """ """

    @property
    def abbrev(self) -> str:
        """ """
        return "stim"

    @property
    def symbol(self) -> str:
        """ """
        return "⚑"


class CameraTimeData(TimeData):
    """"""

    @property
    def abbrev(self) -> str:
        """ """
        return "frame"

    @property
    def symbol(self) -> str:
        """ """
        return "🎥"


class RawData(ChemfishSensor):
    """"""

    @property
    def abbrev(self) -> str:
        """ """
        return "raw"

    @property
    def symbol(self) -> str:
        """ """
        return "⚒"


class ImageSensor(ChemfishSensor):
    def __init__(self, run: RunLike, sensor_data: SensorDataLike):
        """
        Sensor that holds Image sensor data (Webcam and Preview). Applies grid if it holds preview data.

        Args:
            run: Run ID, Submission ID, Submission Object, or Run Object
            sensor_data: Converted image sensor data (Webcam/Preview)

        Returns:

        """
        super().__init__(run, sensor_data)

    @property
    def data(self) -> Image.Image:
        """ """
        return self._sensor_data

    def draw_roi_grid(
        self, color: str = "black", roi_ref: Union[int, str, Refs] = 63
    ) -> ChemfishSensor:
        """
        Draws a grid, returning a new ImageSensor.

        Args:
            color: A color code recognized by PIL (Python Imaging Library), such as a hex code starting with #
            roi_ref: The reference from which to obtain the ROIs; the default is the sauronx ROI set from the TOML,
                     which may or may not exist

        Returns:
            A copy of this ImageSensor

        """
        new = deepcopy(self)
        draw = ImageDraw.Draw(new.data)
        roi_ref = Refs.fetch(roi_ref).id
        rois = list(
            Rois.select(Rois, Wells)
            .join(Wells)
            .where(Wells.run_id == self.run.id)
            .where(Rois.ref == roi_ref)
        )
        wb1 = Tools.wb1_from_run(self.run)
        if len(rois) != wb1.n_wells:
            raise LengthMismatchError(f"{len(rois)} rois but {wb1.n_wells} wells")
        for w in rois:
            draw.rectangle((w.x0, w.y0, w.x1, w.y1), outline=color)
        return new

    @property
    def abbrev(self) -> str:
        return "roi"

    @property
    def symbol(self) -> str:
        return "📷"


class TimeDepChemfishSensor(ChemfishSensor, metaclass=abc.ABCMeta):
    """ """

    def __init__(
        self,
        run: RunLike,
        timing_data: np.array,
        sensor_data: np.array,
        battery_data: BatteryTimeData,
        samples_per_sec: Optional[int],
    ):
        """
        Sensor data for sensors that have a time component

        Args:
            run: Run ID, Submission ID, Submission Object, or Run Object
            timing_data: Converted Timing Data
            sensor_data: Converted Sensor Data
            battery_data: BatteryTimeData object
            samples_per_sec: For example, audio files typically use 44100 Hz; keep None if the sampling is not even
        """
        super().__init__(run, sensor_data)
        self._bt_data = battery_data
        self._timing_data = timing_data
        self._samples_per_sec = samples_per_sec

    @property
    def samples_per_sec(self) -> int:
        """ """
        return self._samples_per_sec

    @property
    def values_per_ms(self) -> int:
        """ """
        raise NotImplementedError()

    @property
    def timing_data(self) -> SensorDataLike:
        """ """
        return self._timing_data

    @property
    def bt_data(self) -> BatteryTimeData:
        """ """
        return self._bt_data

    def slice_ms(self, start_ms: Optional[int], end_ms: Optional[int]) -> TimeDepChemfishSensor:
        """
        Slices Sensor data

        Args:
            start_ms:
            end_ms:

        Returns:
            A copy of this class

        """
        started = (
            self.bt_data.start_ms + start_ms if start_ms is not None else self.bt_data.start_ms
        )
        finished = self.bt_data.end_ms + end_ms if end_ms is not None else self.bt_data.end_ms
        i0 = 0
        i1 = len(self.timing_data)
        for i, m in enumerate(self.timing_data):
            # Change started to first timepoint in data greater than started
            if m > started and i0 == 0:
                i0 = i
            # change finished to first timepoint in data that is greater than finished
            if m > finished and i1 == len(self.timing_data):
                i1 = i
                break
        sliced_time = [started, *self.timing_data[i0:i1], finished]
        sliced_vals = [0, *self.data[i0:i1], 0]
        millis, values = (
            np.array(
                sliced_time[
                    None
                    if start_ms is None
                    else int(start_ms * self.values_per_ms) : None
                    if end_ms is None
                    else int(end_ms * self.values_per_ms)
                ]
            ),
            np.array(
                sliced_vals[
                    None
                    if start_ms is None
                    else int(start_ms * self.values_per_ms) : None
                    if end_ms is None
                    else int(end_ms * self.values_per_ms)
                ]
            ),
        )
        # TODO document that it's always the original bt data
        return self.__class__(self.run, millis, values, copy(self.bt_data), self.samples_per_sec)

    def __len__(self) -> int:
        return len(self.data)


class PhotosensorSensor(TimeDepChemfishSensor):
    """ """

    @property
    def abbrev(self) -> str:
        return "photo"

    @property
    def symbol(self) -> str:
        return "🌣"

    @property
    def values_per_ms(self) -> int:
        """ """
        return 1


class ThermosensorSensor(TimeDepChemfishSensor):
    """"""

    @property
    def abbrev(self) -> str:
        return "therm"

    @property
    def symbol(self) -> str:
        return "🌡"

    @property
    def values_per_ms(self) -> int:
        """ """
        return 1


class MicrophoneWaveformSensor(TimeDepChemfishSensor):
    """ """

    # TODO: Not sure if this is right... Don't know what it's supposed to be doing either...
    def __init__(
        self,
        run: Runs,
        timing_data: np.array,
        sensor_data: np.array,
        battery_data: BatteryTimeData,
        samples_per_sec: Optional[int],
        ds_rate: int,
    ):
        mwf = (
            MicrophoneWaveform(
                run.name, None, sensor_data, samples_per_sec, -1, -1, run.description
            )
            .ds_chunk_mean(ds_rate)
            .normalize()
        )
        td = np.linspace(timing_data[0], timing_data[-1], mwf.n_ms)
        super().__init__(run, td, mwf.data, battery_data, ds_rate)

    @property
    def abbrev(self) -> str:
        return "wav"

    @property
    def symbol(self) -> str:
        return "🔊"

    @property
    def values_per_ms(self) -> float:
        """ """
        return self.samples_per_sec / 1000


class MicrophoneSensor(TimeDepChemfishSensor):
    """ """

    @property
    def abbrev(self) -> str:
        return "mic"

    @property
    def symbol(self) -> str:
        return "🎤"

    @property
    def values_per_ms(self) -> float:
        """ """
        return 44.1  # TODO 44100 kHz

    def waveform(
        self, ds_rate: int, start_ms: Optional[int] = None, end_ms: Optional[int] = None
    ) -> MicrophoneWaveformSensor:
        """


        Args:
            ds_rate: int:
            start_ms: Optional[int]:  (Default value = None)
            end_ms: Optional[int]:  (Default value = None)

        Returns:

        """
        sliced_sensor = self.slice_ms(start_ms, end_ms)
        return MicrophoneWaveformSensor(
            self.run,
            sliced_sensor.timing_data,
            sliced_sensor.data,
            self.bt_data,
            int(self.values_per_ms * 1000),
            ds_rate,
        )


__all__ = [
    "SensorNames",
    "ChemfishSensor",
    "TimeDepChemfishSensor",
    "PhotosensorSensor",
    "MicrophoneSensor",
    "MicrophoneWaveformSensor",
    "ThermosensorSensor",
    "StimulusTimeData",
    "BatteryTimeData",
    "ImageSensor",
    "SensorNames",
    "MicrophoneWaveform",
    "CameraTimeData",
    "SensorNames",
]
