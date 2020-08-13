from __future__ import annotations

import warnings

from pocketutils.support.df_mem_cache import *

from chemfish.core.core_imports import *
from chemfish.model.cache_interfaces import AWellCache
from chemfish.model.features import FeatureType, FeatureTypes
from chemfish.model.well_names import WellNamers
from chemfish.model.wf_builders import *

FeatureTypeLike = Union[None, int, str, Features, FeatureType]

DEFAULT_CACHE_DIR = chemfish_env.cache_dir / "wells"


@abcd.auto_eq()
@abcd.auto_repr_str()
class WellCache(AWellCache):
    """
    A cache for WellFrames with a particular feature.
    """

    def __init__(self, feature: FeatureTypeLike, cache_dir: PLike = DEFAULT_CACHE_DIR, dtype=None):
        self.feature = FeatureTypes.of(feature) if feature is not None else None
        cache_dir = Path(cache_dir) / ("-" if self.feature is None else self.feature.internal_name)
        self._cache_dir = Tools.prepped_dir(cache_dir)
        self._dtype = dtype

    @abcd.overrides
    def with_dtype(self, dtype) -> WellCache:
        """
        Returns a copy with dtype set.
        Features will be converted when loaded using `pd.as_type(dtype)`.
        """
        return WellCache(self.feature, self._cache_dir, dtype)

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @abcd.overrides
    def path_of(self, run: RunLike) -> Path:
        run = Tools.run(run)
        return self.cache_dir / (str(run.id) + ".h5")

    @abcd.overrides
    def key_from_path(self, path: PLike) -> RunLike:
        path = Path(path).relative_to(self.cache_dir)
        return int(re.compile(r"^([0-9]+)\.h5$").fullmatch(path.name).group(1))

    @abcd.overrides
    def load_multiple(self, runs: RunsLike) -> WellFrame:
        runs = Tools.runs(runs)
        self.download(*runs)
        return WellFrame.concat(*[self.load(r) for r in runs])

    @abcd.overrides
    def load(self, run: RunLike) -> WellFrame:
        run = Tools.run(run)
        self.download(run)
        return self._load(run)

    @abcd.overrides
    def download(self, *runs: RunsLike) -> None:
        # TODO this is broken!!!
        runs = {r for r in Tools.runs(runs) if r not in self}
        if len(runs) > 10:
            for r in runs:
                self.download(r)
        elif len(runs) > 0:
            wf = (
                WellFrameBuilder.runs(runs)
                .with_feature(self.feature, self._dtype)
                .with_names(WellNamers.well())
                .build()
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with Tools.silenced(no_stderr=True, no_stdout=False):
                    self._save(wf)

    def _load(self, runs: RunsLike) -> WellFrame:
        runs = ValarTools.runs(runs)

        def read(r):
            with Tools.silenced(no_stderr=True, no_stdout=True):
                try:
                    df = pd.read_hdf(self.path_of(r), "df")
                except Exception:
                    raise CacheSaveError(
                        "Failed to load run [] from cache at {}".format(str(r), self.path_of(r))
                    )
                df = WellFrame(df)
            df = df.reset_index()
            df["name"] = df["well"]
            df = WellFrame.of(df)
            if self._dtype is not None:
                df = df.astype(self._dtype)
            return df

        if len(runs) == 0:
            return WellFrame.new_empty(1)  # best attempt?
        return WellFrame(pd.concat([read(r) for r in runs], sort=False))

    def _save(self, df: WellFrame) -> None:
        """Saves a well-by-well dataframe as HDF5.
        :param df: Use large_dfs.fetch_wells
        """
        for run in df["run"].unique():
            dfc = WellFrame.vanilla(df[df["run"] == run].copy())
            saved_to = self.path_of(run)
            logger.minor("Saving run {} to {}".format(run, saved_to))
            with Tools.silenced(no_stderr=True, no_stdout=True):
                try:
                    dfc.to_hdf(str(saved_to), "df")
                except Exception:
                    raise CacheSaveError(
                        "Failed to save run [] to cache at {}".format(str(run), saved_to)
                    )


__all__ = ["WellCache"]
