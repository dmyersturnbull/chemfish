from dataclasses import dataclass
from chemfish.calc.interpolation import *
from chemfish.core.core_imports import *


@dataclass(frozen=True)
class FeatureType:
    """

    Attributes:
        valar_feature: The Features row instance in Valar
        time_dependent: Whether the feature corresponds to frames in the video (possibly differing by a constant)
        stride_in_bytes: The number of bytes (in the poorly named features.floats) per value, such as 8 for a double value
        recommended_scale: A multiplier of the values for display, such as 1000 for values on that order
        recommended_unit: An arbitrary string to label units with; should account for the recommended_scale
        is_interpolated: For time-dependent features, whether the feature is interpolated to align with the timesamps.
                         This is generally a good idea for PointGrey+ features, and a bad idea for cameras with less accurate timestamps.
        generations: Generations of video data this feature can apply to.
    """

    valar_feature: Features
    time_dependent: bool
    stride_in_bytes: int
    recommended_scale: int
    recommended_unit: str
    is_interpolated: bool
    generations: Set[DataGeneration]

    @property
    def internal_name(self):
        return self.valar_feature.name + ("-i" if self.is_interpolated else "")

    @property
    def external_name(self):
        return self.valar_feature.name + ("[⌇]" if self.is_interpolated else "")

    def calc(
        self,
        wf: WellFeatures,
        frame_timestamps: Optional[np.array],
        stim_timestamps: Optional[np.array],
        well: Union[Wells, int],
        stringent: bool = False,
    ) -> np.array:
        """


        Args:
            wf: WellFeatures:
            frame_timestamps: Required if is_interpolated
            stim_timestamps: Required if is_interpolated
            well:
            stringent:

        Returns:

        """
        if self.is_interpolated and (frame_timestamps is None or stim_timestamps is None):
            raise ValueError(
                f"frame_timestamps and stim_timestamps must be non-None for interpolated feature ${self.internal_name}"
            )
        if well is None and wf is not None:
            well = wf.well
        elif well is not None and wf is None:
            wf = (
                WellFeatures.select()
                .where(WellFeatures.well == well)
                .where(WellFeatures.type == self.valar_feature)
                .first()
            )
            if wf is None:
                raise ValarLookupError(f"No feature {self.valar_feature.name} for well {well}")
        return self.from_blob(
            wf.floats, frame_timestamps, stim_timestamps, well, stringent=stringent
        )

    @abcd.abstractmethod
    def to_blob(self, arr: np.array) -> None:
        """


        Args:
            arr: np.array:

        """
        raise NotImplementedError()

    @abcd.abstractmethod
    def from_blob(
        self,
        blob: bytes,
        frame_timestamps: np.array,
        stim_timestamps: np.array,
        well: Union[Wells, int],
        stringent: bool = False,
    ):
        """


        Args:
            blob: bytes:
            well:
            frame_timestamps:
            stim_timestamps:
            stringent:

        Returns:

        """
        raise NotImplementedError()

    def __repr__(self):
        return self.valar_feature.name + ("[⌇]" if self.is_interpolated else "")

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return isinstance(other, FeatureType) and other.internal_name == self.internal_name

    def __hash__(self):
        return hash(self.internal_name)


class _ConsecutiveFrameFeature(FeatureType, metaclass=abcd.ABCMeta):
    """"""

    def from_blob(
        self,
        blob: bytes,
        frame_timestamps: Optional[np.array],
        stim_timestamps: Optional[np.array],
        well: Union[Wells, int],
        stringent: bool = False,
    ) -> np.array:
        """


        Args:
            blob: bytes:
            well:
            frame_timestamps:
            stim_timestamps:
            stringent:

        Returns:

        """
        well = Wells.fetch(well)
        if len(blob) == 0:
            logger.warning(f"Empty {self.valar_feature.name} feature array for well {well.id}")
            return np.empty(0, dtype=np.float32)
        floats = Tools.blob_to_signed_floats(blob)
        floats.setflags(write=1)  # blob_to_floats gets read-only arrays
        # Previously, MI at t=0 was defined to be 0. Since Valar2, it's defined to be NaN.
        # This won't affect visualization but could affect analysis, so let's always set it to be NaN.
        floats[0] = 0.0
        if self.is_interpolated:
            return FeatureInterpolation(self.valar_feature).interpolate(
                floats, frame_timestamps, stim_timestamps, well, stringent=stringent
            )
        return floats


class _Mi(_ConsecutiveFrameFeature):
    """"""

    def __init__(self, interpolated: bool):
        v = Features.select().where(Features.name == "MI").first()
        super().__init__(v, True, 4, 1000, "(10³)", interpolated, DataGeneration.all_generations())

    def to_blob(self, arr: np.array) -> bytes:
        """


        Args:
            arr: np.array:

        Returns:

        """
        return Tools.signed_floats_to_blob(arr)


class _Diff(_ConsecutiveFrameFeature):
    """"""

    def __init__(
        self, name: str, tau: int, recommended_scale: int, recommended_unit: str, interpolated: bool
    ):
        v = Features.select().where(Features.name == f"{name}({tau})").first()
        generations = (
            DataGeneration.pointgrey_generations()
            if interpolated
            else DataGeneration.all_generations()
        )
        super().__init__(
            v, True, 4, recommended_scale, recommended_unit, interpolated, generations=generations
        )

    def to_blob(self, arr: np.array) -> bytes:
        """


        Args:
            arr: np.array:

        Returns:

        """
        return Tools.array_to_blob(arr, np.float32)


class FeatureTypes:
    """
    The feature types in valar.features.
    """

    MI = _Mi(False)
    cd_10 = _Diff("cd", 10, 1, "", False)
    MI_i = _Mi(True)
    cd_10_i = _Diff("cd", 10, 1, "", True)
    known = [MI, cd_10, MI_i, cd_10_i]

    @classmethod
    def of(cls, f: Union[FeatureType, str]) -> FeatureType:
        """
        Fetches a feature from its **internal** name.

        Args:
            f: A value in FeatureType.internal_name in one of the FeatureType entries in ``FeatureTypes.known``

        Returns:
            The FeatureType

        """
        if isinstance(f, Features):
            raise TypeError(
                "Can't get FeatureType by Valar Features row because it's ambiguous. Get the feature type explicitly using FeatureTypes._ ."
            )
        if not isinstance(f, (FeatureType, str)):
            raise TypeError(f"Can't get FeatureType by type {type(f)}")
        if isinstance(f, FeatureType):
            return f
        for v in FeatureTypes.known:
            if v.internal_name == f:
                return v
        raise ValarLookupError(f"No feature {f}")


__all__ = ["FeatureType", "FeatureTypes"]
