from __future__ import annotations
from binascii import hexlify
from chemfish.core.core_imports import *
from chemfish.calc.audio_expansion import *
from chemfish.model.audio import Waveform


class StimFrame(OrganizingFrame, metaclass=abc.ABCMeta):
    """
    A DataFrame where the rows are milliseconds (or 'stimulus frames') and the columns are stimuli.
    A couple of properties:
        - The values are normally 0-255, but for some legacy assays are 0-1.
        - The rows are normally in milliseconds, but for legacy assays are currently every 40ms (25fps).
        - For SauronX assays, values for audio stimuli will have either:
            a)  A single nonzero value followed by zeros to indicate that playback of the native audio file length begins there.
            b)  More than one nonzero value in a row, indicating that the playback will start at the first nonzero position and end at the last.
                This means that the audio will be repeated and truncated as necessary to fill that number of milliseconds.
            c)  A waveform embedded centered around 127.5 with maximum of 255 and minimum of 0.
                This will be used if expand_audio_inplace is called, or Kale is set to store waveforms.
            In the first two cases, the first nonzero value dictates the volume, where 255 is the max volume allowed by SauronX,
            which is in turn determined by the audio card, the amplifier setting, and the settings configured in the Toml
    """

    def expand_audio_inplace(
        self, waveform_loader: Callable[[StimulusLike], Waveform], is_legacy: bool
    ) -> None:
        """
        Replaces position in the stimframes for audio stimuli with values from a waveform.
        Also sets all solenoids and soft solenoids to have intensity 255.
        :param waveform_loader: A function mapping stimulus names to Waveform objects; The waveforms will be 'standardized' to range from 0 to 255.
        :param is_legacy:
        """
        for stim in self.columns:
            stim = Stimuli.fetch(stim)
            orig_stim_name = copy(stim.name)
            kind = ValarTools.stimulus_type(stim).name
            if kind == StimulusType.SOLENOID.name:
                self[stim.name] = 255 * (self[stim.name] > 0)
            if stim.audio_file is not None:
                try:
                    self[orig_stim_name] = AudioExpansion.expand(
                        self[orig_stim_name], stim, waveform_loader(stim.name), is_legacy=is_legacy
                    )
                except Exception as e:
                    raise AlgorithmError("Failed to expand audio {}".format(orig_stim_name)) from e

    def with_nonzero(self, stim_or_type: Union[str, Stimuli, StimulusType]):
        return self.with_at_least(stim_or_type, 0)

    def with_at_least(self, stim_or_type: Union[str, Stimuli, StimulusType], byteval: int):
        if byteval < 0 or byteval > 255:
            raise OutOfRangeError("{} is not a byte".format(byteval), value=byteval)
        real_stim = Stimuli.fetch_or_none(stim_or_type)
        real_type = None if real_stim is not None else StimulusType.of(stim_or_type)
        sel = None
        for stim in self.columns:
            if (
                real_stim is not None
                and Stimuli.fetch(stim) == real_stim
                or real_type is not None
                and (ValarTools.stimulus_type(stim) is StimulusType.of(stim_or_type))
            ):
                if sel is None:
                    sel = self[stim] > 0
                else:
                    sel |= self[stim] > 0
        return self[sel]

    @classmethod
    def _frame_df(cls, battery: Union[Batteries, int, str]) -> pd.DataFrame:
        battery = Batteries.fetch(battery)
        battery = Batteries.fetch(battery)
        stimuli_in_batteries = (
            Stimuli.select(StimulusFrames, Stimuli, Assays, AssayPositions, Batteries)
            .join(StimulusFrames, join_type=JOIN.LEFT_OUTER)
            .join(Assays)
            .join(AssayPositions)
            .join(Batteries)
            .where(Batteries.id == battery.id)
        )
        df = pd.DataFrame(
            [
                [
                    f.name,
                    f.default_color,
                    f.stimulusframes.assay.name,
                    f.stimulusframes.assay.assaypositions.start,
                    f.stimulusframes.assay.length,
                    f.stimulusframes.assay.assaypositions.start + f.stimulusframes.assay.length,
                    hexlify(f.stimulusframes.frames_sha1).decode("utf8"),
                    Tools.jvm_sbytes_to_ubytes(f.stimulusframes.frames),
                ]
                for f in stimuli_in_batteries
            ],
            columns=[
                "stimulus",
                "color",
                "assay",
                "start",
                "length",
                "end",
                "frames_sha1",
                "frames",
            ],
        )
        logger.info("Downloaded battery {}".format(battery.name))
        if len(df) == 0:
            logger.warning(
                "Battery {} / {} has no stimulus frames".format(battery.id, battery.name)
            )
        return df.sort_values("start")

    @classmethod
    def _slice_stim(
        cls, stimframes, name: str, start_ms: Optional[int] = None, end_ms: Optional[int] = None
    ):
        stimframes_per_ms = 25 / 1000 if ValarTools.battery_is_legacy(name) else 1
        start_ms = 0 if start_ms is None else start_ms
        end_ms = len(stimframes) / stimframes_per_ms if end_ms is None else end_ms
        # return stimframes[int(np.floor(stimframes_per_ms * start_ms)) : int(np.ceil(stimframes_per_ms * end_ms))]
        return stimframes[int(stimframes_per_ms * start_ms) : int(stimframes_per_ms * end_ms)]

    @classmethod
    def _generate_stimframes(
        cls, battery: Batteries, fps_for_sampling: Optional[int] = None
    ) -> pd.DataFrame:
        """Construct a dataframe suitable for plotting stimframes alongside MIs.
        :param battery: A name or ID of a battery
        :param fps_for_sampling: Sample every x frames, starting at 0. This option should mostly be avoided.
        """
        fdf = StimFrame._frame_df(battery)
        if len(fdf) == 0:
            dct = {
                k: v
                for k, v in zip(
                    fdf.columns,
                    [
                        "none",
                        "#ffffff",
                        "",
                        0,
                        battery.length,
                        battery.length,
                        "",
                        np.zeros((battery.length,)),
                    ],
                )
            }
            fdf = fdf.append(pd.Series(dct), ignore_index=True)
        the_range = np.arange(fdf.tail(1).end.values) if len(fdf) > 0 else []
        empty_df = pd.DataFrame(index=the_range, columns=set(fdf.stimulus))
        for idx in fdf.index:
            start_index = fdf.start.loc[idx]
            assay_frames = fdf.frames.loc[idx]
            stim_name = fdf.stimulus.loc[idx]
            empty_df.loc[
                start_index : start_index + len(assay_frames) - 1, stim_name
            ] = assay_frames
        stimframes = empty_df.fillna(0)
        if fps_for_sampling is not None:
            return stimframes[:: int(1000 / fps_for_sampling)]
        else:
            return stimframes


class AssayStimFrame(StimFrame):
    @classmethod
    def of(
        cls,
        assay: Union[Assays, int, str],
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> AssayStimFrame:
        raise NotImplementedError()
        # assay = Assays.fetch(assay)  # type: Assays
        # stimframes = _generate_stimframes(assay)
        # stimframes = _slice(stimframes, assay.name, start_ms, end_ms)
        # return AssayStimFrame(stimframes)


class BatteryStimFrame(StimFrame):
    def slice_ms(
        self,
        battery: Union[Batteries, int, str],
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> BatteryStimFrame:
        battery = battery if isinstance(battery, str) else Batteries.fetch(battery).name
        rdf = StimFrame._slice_stim(self, battery, start_ms, end_ms)
        rdf.__class__ = BatteryStimFrame
        return rdf

    def deltas(self) -> BatteryStimFrame:
        """
        Returns a new stimframe with value 1 at the time the stimulus changed and 0 elsewhere.
        Calculates independently per stimulus.
        """
        # noinspection PyTypeChecker,PyUnresolvedReferences
        df = (self.diff() > 0).astype(np.float32).fillna(0)
        return BatteryStimFrame(df)

    def triangles(self, win_size: int = 1000) -> BatteryStimFrame:
        """
        Computes a left triangle sliding window of the deltas (see `BatteryStimFrame.deltas()`).
        Each triangle starts at value 255 at the start of a change in value at ms t
        and slopes linearally down to 0 by time `t + win_size`.
        Note that it's 0 until the exact moment when the stimulus occurred.
        Useful for weighting distance metrics, etc.
        :param win_size: The number of stimulus values for the sliding window (ms for new sauronx batteries)
        :return: A BatteryStimFrame of triangled deltas as a copy
        """

        def fix(r):
            values = np.zeros((len(r),))
            for epicenter in r[r > 0].index:
                for i in range(epicenter, min(len(r), epicenter + win_size)):
                    values[i] = win_size - i + epicenter
            return 255 * values / values.max()

        rolled = self.deltas().apply(fix, axis=0)
        return BatteryStimFrame(rolled)

    @classmethod
    def of(
        cls,
        battery: Union[Batteries, int, str, StimFrame],
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
    ) -> BatteryStimFrame:
        if isinstance(battery, BatteryStimFrame):
            return battery
        if isinstance(battery, pd.DataFrame):
            battery.__class__ = BatteryStimFrame
            # noinspection PyTypeChecker
            return battery
        battery = Batteries.fetch(battery)  # type: Batteries
        stimframes = StimFrame._generate_stimframes(battery, None)
        stimframes = StimFrame._slice_stim(stimframes, battery.name, start_ms, end_ms)
        return BatteryStimFrame(stimframes)


__all__ = ["StimFrame", "AssayStimFrame", "BatteryStimFrame"]
