import pydub
from moviepy.audio.io.AudioFileClip import AudioFileClip, AudioClip

from chemfish.core.core_imports import *
from chemfish.core.environment import chemfish_env
from chemfish.model.audio import *
from chemfish.model.cache_interfaces import AnAudioStimulusCache, StimulusWaveform

DEFAULT_CACHE_DIR = chemfish_env.cache_dir / "stimuli"


@abcd.auto_eq()
@abcd.auto_repr_str()
class AudioStimulusCache(AnAudioStimulusCache):
    """
    A cache for audio files for stimuli.
    """

    def __init__(self, cache_dir: PLike = DEFAULT_CACHE_DIR):
        self._cache_dir = Tools.prepped_dir(cache_dir)

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @abcd.overrides
    def path_of(self, stimulus: StimulusLike) -> Path:
        return self.cache_dir / (stimulus.name + ".wav")

    @abcd.overrides
    def key_from_path(self, path: PLike) -> StimulusLike:
        pass

    @abcd.overrides
    def load(self, stimulus: StimulusLike) -> Path:
        """Returns the local path, downloading if necessary."""
        stimulus = Stimuli.fetch(stimulus)
        self.download(stimulus)
        return self.path_of(stimulus)

    @abcd.overrides
    def download(self, *keys: StimulusLike) -> None:
        for stimulus in keys:
            stimulus = Stimuli.fetch(stimulus)
            tmpfile = self.path_of(stimulus)
            if tmpfile.exists():
                return
            if stimulus.audio_file_id is None:
                raise ValarLookupError("No audio file for {}".format(stimulus.name))
            audio_file = AudioFiles.fetch(stimulus.audio_file_id)
            if audio_file.data is None:
                raise DataIntegrityError(
                    "Audio file for stimulus {} has no data".format(stimulus.name)
                )
            if audio_file.filename.endswith("mp3"):
                fmt_str = "mp3"
            else:
                fmt_str = "wav"
            try:
                song = pydub.AudioSegment(
                    data=audio_file.data, sample_width=2, frame_rate=44100, channels=1
                )
            except Exception:
                raise DataIntegrityError(
                    "Audio file for stimulus {} is invalid".format(stimulus.name)
                )
            song.export(tmpfile, format=fmt_str)

    @abcd.overrides
    def load_moviepy(self, stimulus: StimulusLike) -> AudioClip:
        fetched = self.load(stimulus)
        try:
            return AudioFileClip(fetched)
        except Exception:
            raise DataIntegrityError("Failed load stimulus {} as an AudioFileClip".format(stimulus))

    @abcd.overrides
    def load_pydub(self, stimulus: StimulusLike) -> pydub.AudioSegment:
        path = self.load(stimulus)
        try:
            return pydub.AudioSegment.from_file(path)
        except Exception:
            raise DataIntegrityError("Failed to read file {}".format(path))

    @abcd.overrides
    def load_waveform(self, stimulus: StimulusLike) -> StimulusWaveform:
        stimulus = Stimuli.fetch(stimulus)
        path = self.load(stimulus)
        try:
            data, sampling_rate = librosa.load(str(path))
        except Exception:
            raise LoadError("Failed to read file {}".format(path))
        return StimulusWaveform(
            stimulus.name, str(path), data, sampling_rate, -1, 1, stimulus.description
        )


__all__ = ["StimulusWaveform", "AudioStimulusCache"]
