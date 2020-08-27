from chemfish.calc.interpolation import *
from chemfish.core.core_imports import *


class FeatureType:
    """ """

    def __init__(
        self,
        valar_feature: Features,
        time_dependent: bool,
        stride_in_bytes: int,
        recommended_scale: int,
        recommended_unit: str,
        is_interpolated: bool,
        generations: Set[DataGeneration],
    ):
        """

        :param valar_feature: The Features row instance in Valar
        :param time_dependent: Whether the feature corresponds to frames in the video (possibly differing by a constant)
        :param stride_in_bytes: The number of bytes (in the poorly named features.floats) per value, such as 8 for a double value
        :param recommended_scale: A multiplier of the values for display, such as 1000 for values on that order
        :param recommended_unit: An arbitrary string to label units with; should account for the recommended_scale
        :param is_interpolated: For time-dependent features, whether the feature is interpolated to align with the timesamps.
                This is generally a good idea for PointGrey+ features, and a bad idea for cameras with less accurate timestamps.
        :param generations: Generations of video data this feature can apply to.
        """
        self.valar_feature = valar_feature
        self.id = valar_feature.id
        self.time_dependent = time_dependent
        self.feature_name = valar_feature.name
        self.external_name = self.feature_name + ("[⌇]" if is_interpolated else "")
        self.stride_in_bytes = stride_in_bytes
        self.recommended_scale = recommended_scale
        self.recommended_unit = recommended_unit
        self.is_interpolated = is_interpolated
        self.internal_name = self.valar_feature.name + ("-i" if self.is_interpolated else "")
        self.data_generations = generations

    def calc(self, wf: WellFeatures, well: Union[Wells, int], stringent: bool = False) -> np.array:
        """


        Args:
          wf: WellFeatures:
          well:
          stringent:

        Returns:

        """
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
        return self.from_blob(wf.floats, well, stringent=stringent)

    @abcd.abstractmethod
    def to_blob(self, arr: np.array):
        """


        Args:
          arr: np.array:

        Returns:

        """
        raise NotImplementedError()

    @abcd.abstractmethod
    def from_blob(self, blob: bytes, well: Union[Wells, int], stringent: bool = False):
        """


        Args:
          blob: bytes:
          well: Union[Wells:
          int]:
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
    """ """

    def from_blob(self, blob: bytes, well: Union[Wells, int], stringent: bool = False):
        """


        Args:
          blob: bytes:
          well: Union[Wells:
          int]:
          stringent:

        Returns:

        """
        well = Wells.fetch(well)
        if len(blob) == 0:
            logger.warning(f"Empty {self.feature_name} feature array for well {well.id}")
            return np.empty(0, dtype=np.float32)
        floats = Tools.blob_to_signed_floats(blob)
        floats.setflags(write=1)  # blob_to_floats gets read-only arrays
        # Previously, MI at t=0 was defined to be 0. Since Valar2, it's defined to be NaN.
        # This won't affect visualization but could affect analysis, so let's always set it to be NaN.
        floats[0] = 0.0
        if self.is_interpolated:
            return FeatureInterpolation(self.valar_feature).interpolate(
                floats, well, stringent=stringent
            )
        return floats


class _Mi(_ConsecutiveFrameFeature):
    """ """

    def __init__(self, interpolated: bool):
        v = Features.select().where(Features.name == "MI").first()
        super().__init__(v, True, 4, 1000, "(10³)", interpolated, DataGeneration.all_generations())

    def to_blob(self, arr: np.array):
        """


        Args:
          arr: np.array:

        Returns:

        """
        return Tools.signed_floats_to_blob(arr)


class _Diff(_ConsecutiveFrameFeature):
    """ """

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

    def to_blob(self, arr: np.array):
        """


        Args:
          arr: np.array:

        Returns:

        """
        return Tools.array_to_blob(arr, np.float32)


class FeatureTypes:
    """The feature types in valar.features."""

    MI = _Mi(False)
    cd_10 = _Diff("cd", 10, 1, "", False)
    MI_i = _Mi(True)
    cd_10_i = _Diff("cd", 10, 1, "", True)
    known = [MI, cd_10, MI_i, cd_10_i]

    @classmethod
    def of(cls, f: Union[FeatureType, str]) -> FeatureType:
        """
        Fetches a feature from its INTERNAL name.

        Args:
            f: A value in FeatureType.internal_name in one of the FeatureType entries in FeatureTypes.known
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
