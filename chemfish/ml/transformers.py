from scipy import ndimage
from sklearn.base import TransformerMixin
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from chemfish.core.core_imports import *
from chemfish.model.well_frames import WellFrame


class WellTransform(abcd.ABC):
    """
    A WellTransformation is anything that transforms a `WellFrame` to another `WellFrame` with its `build` function.
    Examples include PCA and filtering outliers.
    The method `//` is a shorthand for `fit`, useful for composing multiple transformations. Ex:
    ```
    df = df // transform1 // transform2 // transform3
    ```
    """

    def fit(self, df: WellFrame) -> WellFrame:
        raise NotImplementedError()

    def __floordiv__(self, df: WellFrame) -> WellFrame:
        return self.fit(df)


class TrimmingWellTransform(WellTransform, metaclass=abc.ABCMeta):
    pass


class TwoDWellTransform(WellTransform, metaclass=abc.ABCMeta):
    def validate(self, df: WellFrame) -> None:
        if df.feature_length() != 2:
            raise LengthMismatchError(
                "{} only applies to WellFrames with precisely 2 features".format(
                    self.__class__.__name__
                )
            )


class OutlierStdTransform(TrimmingWellTransform):
    def __init__(self, n_stds: float = 2):
        self.n_stds = n_stds
        self.trimmed_wells = None

    def fit(self, df: WellFrame) -> WellFrame:
        original = set(df["well"])
        for col in df.columns:
            df = self._trim(df, col)
        self.trimmed_wells = original - set(df["well"])
        logger.minor("Trimmed {} wells with > {} stds".format(len(self.trimmed_wells), self.n_stds))
        return df

    def _trim(self, df, col):
        return df[(df[col] - df[col].mean()).abs() <= self.n_stds * np.std(df[col])]


class OutlierDistanceTransform(TrimmingWellTransform):
    def __init__(self, distance_fn, max_distance: float):
        self.distance_fn, self.max_distance = distance_fn, max_distance
        self.trimmed_wells = None

    def fit(self, df: WellFrame) -> WellFrame:
        original = set(df["well"])
        df = self._trim(df)
        self.trimmed_wells = set(df["well"]) - original
        logger.minor(
            "Trimmed {} wells with distance > {}".format(len(self.trimmed_wells), self.max_distance)
        )
        return df

    def _trim(self, df):
        distances = df.apply(self.distance_fn)
        return df[distances <= self.max_distance]


class RotationTransform(TwoDWellTransform):
    def __init__(self, degrees: float):
        self.degrees = degrees

    def fit(self, df: WellFrame) -> WellFrame:
        self.validate(df)
        rotated = ndimage.rotate(df.values)
        df[0] = rotated[0]
        df[1] = rotated[1]
        return df


class SklearnTransform(WellTransform, metaclass=abc.ABCMeta):
    def __init__(self, model: TransformerMixin):
        self.model = model

    def fit(self, df: WellFrame) -> WellFrame:
        logger.info(
            "Fitting {} wells and {} features with {}".format(
                len(df), df.n_columns(), self.model.__class__.__name__
            )
        )
        fitted = self.model.fit_transform(df.values)
        fitted = pd.DataFrame(fitted)
        return WellFrame.assemble(df.meta(), fitted)


class CompositeTransform(WellTransform):
    def __init__(self, *transformations: WellTransform):
        self.transformations = transformations

    def fit(self, df: WellFrame) -> WellFrame:
        for t in self.transformations:
            df = t.fit(df)
        return df


class WellTransforms:
    """
    A suite of functions that apply common `WellTransformation`s to single WellFrames.
    """

    @classmethod
    def tsne(cls, df: WellFrame, **kwargs) -> WellFrame:
        # noinspection PyTypeChecker
        return SklearnTransform(TSNE(**kwargs)).fit(df)

    @classmethod
    def pca(cls, df: WellFrame, **kwargs) -> WellFrame:
        # noinspection PyTypeChecker
        return SklearnTransform(PCA(**kwargs)).fit(df)

    @classmethod
    def compose(cls, *transformations: WellTransform):
        return CompositeTransform(*transformations)

    @classmethod
    def outlier_std(cls, df: WellFrame, n_stds: float) -> WellFrame:
        return OutlierStdTransform(n_stds).fit(df)

    @classmethod
    def outlier_dist(cls, df: WellFrame, distance_fn, max_distance) -> WellFrame:
        return OutlierDistanceTransform(distance_fn, max_distance).fit(df)

    @classmethod
    def rotate(cls, df: WellFrame, degrees: float) -> WellFrame:
        return RotationTransform(degrees).fit(df)


__all__ = [
    "TSNE",
    "WellTransform",
    "SklearnTransform",
    "CompositeTransform",
    "OutlierStdTransform",
    "OutlierDistanceTransform",
    "RotationTransform",
    "WellTransforms",
]
