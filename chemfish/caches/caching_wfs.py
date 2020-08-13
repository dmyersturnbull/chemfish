from __future__ import annotations

from chemfish.caches.wf_caches import *
from chemfish.core.core_imports import *
from chemfish.core.valar_singleton import *
from chemfish.model.features import *
from chemfish.model.wf_builders import *


@abcd.auto_eq()
@abcd.auto_repr_str()
class CachingWellFrameBuilder(WellFrameBuilder):
    """
    A WellFrameBuilder backed by a FrameCache.
    The FrameCache saves WellFrames for full runs, but WellFrameBuilder will return only the wells of interest.
    If include_full_runs is set, WellFrameBuilder will return every well on runs where at least one well was queried.
    """

    def __init__(self, cache: WellCache, before_datetime: Optional[datetime]):
        super().__init__(before_datetime)
        self._cache = cache
        self._include_full_runs = False
        self._feature = cache.feature

    # noinspection PyMethodOverriding
    @classmethod
    def wells(
        cls, wells: Union[Union[int, Wells], Iterable[Union[int, Wells, str]]], cache: WellCache
    ) -> CachingWellFrameBuilder:
        """Convenience factory method to query by an exact set of wells with no addition WHEREs."""
        if isinstance(wells, str) or isinstance(wells, int) or isinstance(wells, Wells):
            wells = {Wells.fetch(wells).id}
        else:
            wells = {Wells.fetch(w).id for w in wells}
        wfb = cls(cache, None).where(Wells.id << wells)
        return wfb

    # noinspection PyMethodOverriding
    @classmethod
    def runs(
        cls,
        runs: Union[Union[int, Runs, str, Submissions], Iterable[Union[int, Runs, str]]],
        cache: WellCache,
    ) -> CachingWellFrameBuilder:
        """Convenience factory method to query by an exact set of runs with no addition WHEREs."""
        if (
            isinstance(runs, str)
            or isinstance(runs, int)
            or isinstance(runs, Runs)
            or isinstance(runs, Submissions)
        ):
            runs = {Tools.run(runs).id}
        else:
            runs = {Tools.run(r).id for r in runs}
        wfb = cls(cache, None).where(Runs.id << runs)
        wfb._required_runs = runs
        return wfb

    def include_full_runs(self) -> CachingWellFrameBuilder:
        """
        Makes CachingWellFrameBuilder.build() return all of the wells on a run if a single well matched the query.
        This won't make the actual querying any slower because the whole runs are cached to disk, not just the matching wells.
        """
        self._include_full_runs = True
        return self

    def with_feature(
        self, feature: Union[None, str, FeatureType], dtype=None
    ) -> CachingWellFrameBuilder:
        """
        In CachingWellFrameBuilder this is useless because it MUST be the same as the cache feature.
        :param feature: The FeatureType; for CachingWellFrameBuilder MUST be the same as the feature
        :param dtype:
        """
        feature = FeatureTypes.of(feature)
        if feature != self._cache.feature:
            raise ContradictoryRequestError(
                "Requested feature {}, but the cache uses {}".format(feature, self._cache.feature)
            )
        self._dtype = dtype
        return self

    def build(self) -> WellFrame:
        """
        Builds the WellFrame.
        Either loads the runs from disk and filters the wells by the query, or queries, caches, and returns.
        """
        query = WellFrameQuery().build(WellFrameQuery.no_fields())
        for where in self._wheres:
            query = query.where(where)
        query = query.order_by(*WellFrameQuery.sort_order())
        query = list(query)
        wells = {wt.well_id for wt in query}
        runs = {wt.well.run for wt in query}
        df = self._cache.with_dtype(self._dtype).load_multiple(runs)
        if not self._include_full_runs:
            df = WellFrame.of(df[df["well"].isin(wells)])
        if self._compound_namer is not None:
            df = df.with_new_compound_names(self._compound_namer)
        if self._namer is not None:
            df = df.with_new_names(self._namer)
        if self._display_namer is not None:
            df = df.with_new_display_names(self._display_namer)
        elif self._namer is not None:
            df = df.with_new_display_names(self._namer)
        if self._packer is not None:
            df = df.with_new_packs(self._packer)
        if self._sizer is not None:
            df = df.with_new_sizes(self._sizer)
        df = self._internal_limit(df)
        df = self._internal_restrict_to_gen(df)
        return df.sort_std()


__all__ = ["CachingWellFrameBuilder"]
