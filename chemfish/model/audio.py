from __future__ import annotations

import librosa
import librosa.display as ldisplay
import pydub

from chemfish.core.core_imports import *


class AudioTools:
    """ """

    @classmethod
    def listen(cls, path: Union[str, PurePath, bytes]):
        """
        Returns an audio container that Jupyter notebook will display.
        Must be run from a Jupyter notebook.
        Will raise an ImportError if IPython cannot be imported.

        Args:
            path: The local path to the audio file

        Returns:
            A jupyter notebook ipd.Audio object

        """
        # noinspection PyPackageRequirements
        import IPython.display as ipd

        if isinstance(path, (str, PurePath)):
            path = str(Path(path))
            return ipd.Audio(filename=path)
        else:
            return ipd.Audio(data=path)

    @classmethod
    def to_wav(cls, path: PathLike):
        """


        Args:
            path: PathLike:

        Returns:

        """
        path = Tools.prepped_file(path)
        with path.open("rb") as rf:
            song = pydub.AudioSegment(data=rf.read(), sample_width=2, frame_rate=44100, channels=1)
        song.export(path.with_suffix("wav"), format="wav")
        return path.with_suffix("wav")

    @classmethod
    def load_pydub(cls, path: PathLike) -> pydub.AudioSegment:
        """


        Args:
            path: PathLike:

        Returns:

        """
        path = str(Path(path))
        return pydub.AudioSegment.from_file(path)


class Waveform:
    """
    Contains an array representing an audio waveform.
    Aso has a sampling rate, a name, an optional description, and optional file path.

    """

    def __init__(
        self,
        name: str,
        path: Optional[str],
        data: np.array,
        sampling_rate: float,
        minimum: float,
        maximum: float,
        description: Optional[str] = None,
        start_ms: Optional[float] = None,
        end_ms: Optional[float] = None,
    ):
        self.name = name
        self.description = description
        self.path = path
        self.data = data
        self.start_ms = start_ms
        self.end_ms = end_ms
        self.sampling_rate = sampling_rate
        self.minimum = minimum
        self.maximum = maximum
        self.n_ms = len(self.data) / self.sampling_rate * 1000

    def standardize_sauronx(self, minimum: float = 0, maximum: float = 255) -> Waveform:
        """
        Downsamples to **1000 Hz** and normalizes to between 0 and 255.
        This is useful for various purposes in Chemfish, such as embedding into plots.

        Args:
          minimum: Normally 0
          maximum: Normally 255
          ms_freq: Normally 1000, though possibly 25 or 50 for legacy data

        Returns:
            The same Waveform as a copy

        """
        return self._standardize(minimum, maximum)

    def standardize_legacy(self, minimum: float = 0, maximum: float = 255) -> Waveform:
        """
        Downsamples to **25 Hz** and normalizes to between 0 and 255.
        This is useful for various purposes in Chemfish, such as embedding into plots.

        Args:
            minimum: Normally 0
            maximum: Normally 255
            ms_freq: Normally 1000, though possibly 25 or 50 for legacy data

        Returns:
            The same Waveform as a copy

        """
        return self._standardize(minimum, maximum, ms_freq=25)

    def _standardize(
        self, minimum: float = 0, maximum: float = 255, ms_freq: int = 1000
    ) -> Waveform:
        """


        Args:
             minimum:
             maximum:
            ms_freq:

        Returns:

        """
        if minimum < 0 or maximum > 255:
            raise OutOfRangeError("Must be between 0 and 255")
        y = self.downsample(ms_freq).data
        y = (y - y.min()) * (maximum - minimum) / (y.max() - y.min()) + minimum
        y = y.round().astype(np.int32)
        s = Waveform(self.name, self.path, y, 1000, minimum, maximum, self.description)
        s.n_ms = int(s.n_ms)
        return s

    def normalize(self, minimum: float = -1, maximum: float = 1) -> Waveform:
        """
        Constraints values between -1 and 1.

        Args:
            minimum: Normally -1
            maximum: Normally 1

        Returns:
            The same Waveform as a copy

        """
        y = (self.data - self.data.min()) * (maximum - minimum) / (
            self.data.max() - self.data.min()
        ) + minimum
        return Waveform(
            self.name, self.path, y, self.sampling_rate, minimum, maximum, self.description
        )

    def ds_chunk_mean(self, new_sampling_hertz: float) -> Waveform:
        """
        Alternative to downsampling. Splits data into discrete chunks and then calculates mean for those chunks.

        Args:
            new_sampling_hertz: rate of sampling

        Returns:
            numpy array of orr

        """
        if new_sampling_hertz > self.sampling_rate:
            raise OutOfRangeError(
                f"New sampling rate is higher than current of {self.sampling_rate}"
            )
        chunk_size = int(self.sampling_rate / new_sampling_hertz)
        groups = [self.data[x : x + chunk_size] for x in range(0, len(self.data), chunk_size)]
        means = np.array([sum(group) / len(group) for group in groups])
        return Waveform(
            self.name,
            self.path,
            means,
            new_sampling_hertz,
            self.minimum,
            self.maximum,
            self.description,
        )

    def downsample(self, new_sampling_hertz: float) -> Waveform:
        """
        Downsamples to a new rate using librosa.resample.

        Args:
            new_sampling_hertz: A float such as 44100

        Returns:
            The same Waveform as a copy

        """
        if new_sampling_hertz > self.sampling_rate:
            raise OutOfRangeError(
                f"New sampling rate is higher than current of {self.sampling_rate}"
            )
        # setting res_type='scipy' seems to allow downsampling to smaller values without DivideByZero errors
        y = librosa.resample(self.data, self.sampling_rate, new_sampling_hertz, res_type="scipy")
        return Waveform(
            self.name,
            self.path,
            y,
            new_sampling_hertz,
            self.minimum,
            self.maximum,
            self.description,
        )

    def smooth(
        self, window_size: int, function=lambda s: s.mean(), window_type: Optional[str] = "triang"
    ) -> Waveform:
        """
        Smooths with a sliding window over time.

        Args:
            window_size: The number of elements in the window
            function:
            window_type: See Pandas pd.Series.rolling win_type

        Returns:
            The same Waveform as a copy

        """
        data = function(
            pd.Series(self.data).rolling(window_size, min_periods=1, win_type=window_type)
        ).values
        return Waveform(
            self.name,
            self.path,
            data,
            self.sampling_rate,
            self.minimum,
            self.maximum,
            self.description,
        )

    def slice_ms(self, start_ms: int, end_ms: int) -> Waveform:
        """
        Gets a section of the waveform.

        Args:
            start_ms: The start milliseconds
            end_ms: The end milliseconds

        Returns:
          The same Waveform as a copy

        """
        a = int(round(self.sampling_rate * start_ms / 1000))
        b = int(round(self.sampling_rate * end_ms / 1000))
        return Waveform(
            self.name,
            self.path,
            self.data[a:b],
            self.sampling_rate,
            self.minimum,
            self.maximum,
            self.description,
            a,
            b,
        )

    def __repr__(self):
        return "Waveform(name={} @ {}, n={}, {}s, range={}-{})".format(
            self.name,
            self.sampling_rate,
            len(self.data),
            round(self.n_ms / 1000, 1),
            self.minimum,
            self.maximum,
        )

    def __str__(self):
        return repr(self)


__all__ = ["AudioTools", "Waveform", "librosa", "ldisplay"]
