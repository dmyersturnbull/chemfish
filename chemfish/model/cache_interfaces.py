from __future__ import annotations

from abc import ABCMeta

import pydub
from moviepy.audio.io.AudioFileClip import AudioClip, AudioFileClip

from chemfish.core.core_imports import *
from chemfish.core.valar_singleton import *
from chemfish.model.audio import *
from chemfish.model.sensors import *
from chemfish.model.stim_frames import BatteryStimFrame
from chemfish.model.videos import *
from chemfish.model.well_frames import *

KEY = TypeVar("KEY")
VALUE = TypeVar("VALUE")


@abcd.auto_repr_str()
@abcd.auto_hash()
@abcd.auto_eq()
class AChemfishCache(Generic[KEY, VALUE], metaclass=ABCMeta):
    @property
    def cache_dir(self) -> Path:
        raise NotImplementedError()

    def path_of(self, key: KEY) -> Path:
        raise NotImplementedError()

    def key_from_path(self, path: PathLike) -> KEY:
        raise NotImplementedError()

    def download(self, *keys: KEY) -> None:
        raise NotImplementedError()

    def load(self, key: KEY) -> VALUE:
        raise NotImplementedError()

    def contains(self, key: KEY) -> bool:
        return self.path_of(key).exists()

    def contents(self) -> Sequence[KEY]:
        lst = []
        for path in self.cache_dir.iterdir():
            k = self.key_from_path(path)
            ## it might not be a relevant file (ex thumbs.db)
            if k is not None:
                lst.append(k)
        return lst

    def delete(self, key: KEY) -> None:
        # TOD delete directories
        path = self.path_of(key).relative_to(self.cache_dir).parts
        if self.contains(key):
            self.path_of(key).unlink()

    def __contains__(self, key: KEY) -> bool:
        return self.contains(key)

    def __delitem__(self, key: KEY) -> None:
        self.delete(key)

    def __getitem__(self, key: KEY) -> VALUE:
        return self.load(key)


class AWellCache(AChemfishCache[RunLike, WellFrame], metaclass=ABCMeta):
    def __init__(self, feature, cache_dir: PathLike, dtype):
        raise NotImplementedError()

    def load_multiple(self, runs: RunsLike) -> WellFrame:
        raise NotImplementedError()

    def with_dtype(self, dtype) -> AWellCache:
        raise NotImplementedError()


class ASensorCache(AChemfishCache[Tup[SensorNames, RunLike], SensorDataLike], metaclass=ABCMeta):
    def __init__(self, cache_dir: PathLike):
        raise NotImplementedError()


class AStimCache(AChemfishCache[BatteryLike, BatteryStimFrame], metaclass=ABCMeta):
    def __init__(self, cache_dir: PathLike, dtype, loader):
        raise NotImplementedError()

    @property
    def is_expanded(self):
        raise NotImplementedError()


class StimulusWaveform(Waveform):
    pass


class AVideoCache(AChemfishCache[RunLike, SauronxVideo], metaclass=ABCMeta):
    def __init__(self, cache_dir: PathLike, shire_store: PathLike):
        raise NotImplementedError()


class AnAudioStimulusCache(AChemfishCache[StimulusLike, Path], metaclass=ABCMeta):
    def __init__(self, cache_dir: PathLike):
        raise NotImplementedError()

    def load_moviepy(self, stimulus: StimulusLike) -> AudioClip:
        raise NotImplementedError()

    def load_pydub(self, name) -> pydub.AudioSegment:
        raise NotImplementedError()

    def load_waveform(self, stimulus) -> StimulusWaveform:
        raise NotImplementedError()


__all__ = [
    "AChemfishCache",
    "ASensorCache",
    "AWellCache",
    "AStimCache",
    "AnAudioStimulusCache",
    "AVideoCache",
    "StimulusWaveform",
]
