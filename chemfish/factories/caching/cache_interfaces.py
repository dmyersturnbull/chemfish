from __future__ import annotations

import pydub
from moviepy.audio.io.AudioFileClip import AudioClip

from chemfish.core.core_imports import *
from chemfish.core.valar_singleton import *
from chemfish.model.waveforms import *
from chemfish.model.sensors import *
from chemfish.model.assay_frames import AssayFrame
from chemfish.model.stim_frames import BatteryStimFrame
from chemfish.model.well_frames import *

KEY = TypeVar("KEY")
VALUE = TypeVar("VALUE")


class ASauronxVideo(metaclass=ABCMeta):
    """"""


@abcd.auto_repr_str()
@abcd.auto_hash()
@abcd.auto_eq()
class AChemfishCache(Generic[KEY, VALUE], metaclass=ABCMeta):
    """ """

    @property
    def cache_dir(self) -> Path:
        """ """
        raise NotImplementedError()

    def path_of(self, key: KEY) -> Path:
        """


        Args:
            key:

        Returns:

        """
        raise NotImplementedError()

    def key_from_path(self, path: PathLike) -> KEY:
        """


        Args:
            path: PathLike:

        Returns:

        """
        raise NotImplementedError()

    def download(self, *keys: KEY) -> None:
        """


        Args:
            *keys:

        """
        raise NotImplementedError()

    def load(self, key: KEY) -> VALUE:
        """


        Args:
            key:

        Returns:

        """
        raise NotImplementedError()

    def contains(self, key: KEY) -> bool:
        """


        Args:
            key:

        Returns:

        """
        return self.path_of(key).exists()

    def contents(self) -> Sequence[KEY]:
        """

        Returns:

        """
        lst = []
        for path in self.cache_dir.iterdir():
            k = self.key_from_path(path)
            ## it might not be a relevant file (ex thumbs.db)
            if k is not None:
                lst.append(k)
        return lst

    def delete(self, key: KEY) -> None:
        """


        Args:
            key:

        Returns:

        """
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
    """"""

    def load_multiple(self, runs: RunsLike) -> WellFrame:
        """


        Args:
            runs:

        Returns:

        """
        raise NotImplementedError()

    def with_dtype(self, dtype) -> AWellCache:
        """


        Args:
            dtype:

        Returns:

        """
        raise NotImplementedError()


class ASensorCache(AChemfishCache[Tup[SensorNames, RunLike], SensorDataLike], metaclass=ABCMeta):
    """"""


class AAssayCache(AChemfishCache[BatteryLike, AssayFrame], metaclass=ABCMeta):
    """"""


class AStimCache(AChemfishCache[BatteryLike, BatteryStimFrame], metaclass=ABCMeta):
    """"""

    @property
    def is_expanded(self):
        """"""
        raise NotImplementedError()


class StimulusWaveform(Waveform):
    """"""

    pass


class AVideoCache(AChemfishCache[RunLike, ASauronxVideo], metaclass=ABCMeta):
    """"""


class AnAudioStimulusCache(AChemfishCache[StimulusLike, Path], metaclass=ABCMeta):
    """ """

    def load_moviepy(self, stimulus: StimulusLike) -> AudioClip:
        """


        Args:
            stimulus:

        Returns:

        """
        raise NotImplementedError()

    def load_pydub(self, name: str) -> pydub.AudioSegment:
        """


        Args:
            name:

        Returns:

        """
        raise NotImplementedError()

    def load_waveform(self, stimulus) -> StimulusWaveform:
        """


        Args:
            stimulus:

        Returns:

        """
        raise NotImplementedError()


__all__ = [
    "AChemfishCache",
    "ASensorCache",
    "AWellCache",
    "AAssayCache",
    "AStimCache",
    "AnAudioStimulusCache",
    "AVideoCache",
    "StimulusWaveform",
    "ASauronxVideo",
]
