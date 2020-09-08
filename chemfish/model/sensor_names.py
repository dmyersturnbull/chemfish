from __future__ import annotations

from chemfish.core.core_imports import *


@enum.unique
class SensorNames(SmartEnum):
    """
    Enum of SensorNames. Put all Sensors that are involved in sensor_caches in here.
    """

    PHOTOSENSOR = enum.auto()
    THERMOSENSOR = enum.auto()
    MICROPHONE = enum.auto()
    MICROPHONE_WAVEFORM = enum.auto()
    SECONDARY_CAMERA = enum.auto()
    PREVIEW_FRAME = enum.auto()
    STIMULUS_MILLIS = enum.auto()
    CAMERA_MILLIS = enum.auto()
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
    def is_raw(self) -> bool:
        return self.name.startswith("RAW_")

    @property
    def is_composite(self) -> bool:
        return not self.name.startswith("RAW_")

    @property
    def components(self) -> Sequence[SensorNames]:
        if self.is_audio_composite:
            return [SensorNames.RAW_MICROPHONE_MILLIS, SensorNames.RAW_MICROPHONE_RECORDING]
        elif self == SensorNames.PHOTOSENSOR:
            return [SensorNames.RAW_PHOTOSENSOR_MILLIS, SensorNames.RAW_PHOTOSENSOR_VALUES]
        elif self == SensorNames.THERMOSENSOR:
            return [SensorNames.RAW_THERMOSENSOR_MILLIS, SensorNames.RAW_THERMOSENSOR_VALUES]
        elif self == SensorNames.STIMULUS_MILLIS:
            return [
                SensorNames.RAW_STIMULUS_IDS,
                SensorNames.RAW_STIMULUS_MILLIS,
                SensorNames.RAW_STIMULUS_VALUES,
            ]
        elif self == SensorNames.CAMERA_MILLIS:
            return [SensorNames.RAW_CAMERA_MILLIS]
        elif self == SensorNames.PREVIEW_FRAME:
            return [SensorNames.RAW_PREVIEW_FRAME]
        elif self == SensorNames.SECONDARY_CAMERA:
            return [SensorNames.RAW_SECONDARY_CAMERA]
        else:
            return []

    @property
    def millis_component(self) -> Optional[SensorNames]:
        return {
            SensorNames.MICROPHONE: SensorNames.RAW_MICROPHONE_MILLIS,
            SensorNames.PHOTOSENSOR: SensorNames.RAW_PHOTOSENSOR_MILLIS,
            SensorNames.THERMOSENSOR: SensorNames.RAW_THERMOSENSOR_MILLIS,
            SensorNames.STIMULUS_MILLIS: SensorNames.RAW_STIMULUS_MILLIS,
            SensorNames.CAMERA_MILLIS: SensorNames.RAW_CAMERA_MILLIS,
        }.get(self)

    @property
    def values_component(self) -> Optional[SensorNames]:
        return {
            SensorNames.MICROPHONE: SensorNames.RAW_MICROPHONE_RECORDING,
            SensorNames.PHOTOSENSOR: SensorNames.RAW_PHOTOSENSOR_VALUES,
            SensorNames.THERMOSENSOR: SensorNames.RAW_THERMOSENSOR_VALUES,
            SensorNames.STIMULUS_MILLIS: SensorNames.RAW_STIMULUS_VALUES,
        }.get(self)

    @property
    def raw_bytes_component(self) -> Optional[SensorNames]:
        return {
            SensorNames.PREVIEW_FRAME: SensorNames.RAW_PREVIEW_FRAME,
            SensorNames.SECONDARY_CAMERA: SensorNames.RAW_SECONDARY_CAMERA,
        }.get(self)

    @property
    def is_timing(self) -> bool:
        return self == SensorNames.CAMERA_MILLIS or self == SensorNames.STIMULUS_MILLIS

    @property
    def is_audio_composite(self) -> bool:
        return self == SensorNames.MICROPHONE

    @property
    def is_audio_waveform(self) -> bool:
        return self == SensorNames.MICROPHONE_WAVEFORM

    @property
    def is_image(self) -> bool:
        return self in [
            SensorNames.PREVIEW_FRAME,
            SensorNames.RAW_PREVIEW_FRAME,
            SensorNames.SECONDARY_CAMERA,
            SensorNames.RAW_SECONDARY_CAMERA,
        ]

    @property
    def is_time_dependent(self) -> bool:
        """
        Returns True if this is a composite sensor that has matching vectors of values and milliseconds.
        (It might also have other accompanying sensors.)
        Always returns False for raw sensors.

        Returns:
            Obvious
        """
        return (
            self == SensorNames.PHOTOSENSOR
            or self == SensorNames.THERMOSENSOR
            or self == SensorNames.MICROPHONE
        )

    @property
    def extension(self) -> str:
        if self.is_audio_composite or self is SensorNames.RAW_MICROPHONE_RECORDING:
            return ".flac"
        elif self.is_image:
            return ".jpg"
        else:
            return ".npy"

    @property
    def json_name(self) -> Optional[str]:
        if self.is_raw:
            return self.name.lower().replace("raw_", "")
        return None

    @property
    def py_class_name(self) -> str:
        if self.is_raw:
            return "RawData"
        else:
            return self.name.capitalize() + "Sensor"


__all__ = ["SensorNames"]
