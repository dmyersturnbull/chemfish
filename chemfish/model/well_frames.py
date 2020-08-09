from __future__ import annotations
from chemfish.core.core_imports import *
from chemfish.model.treatments import *
from chemfish.model.well_names import WellNamer
from chemfish.model.compound_names import *
from chemfish.model.wf_tools import *


class InvalidWellFrameError(ConstructionError):
    pass


class WellFrame(OrganizingFrame):
    """
    A DataFrame where each row is a well.
    Implements OrganizingFrame.
    Has a number of required index columns. Some additional columns are reserved (have special meaning) but are not required.
    The index names ("meta columns") contain metadata for the well,
    and the columns, if any, contain the features and are named 0, 1, ... with int32 types.
    Containing no features and thereby no columns is acceptable.
    Additional custom meta columns can be added freely.
    Note that when placed in a WellFrame, any columns with str-typed names will be converted to index columns.
    You can convert a plain DataFrame to a WellFrame using `self.__class__.of`.
    If you need to convert back to a DataFrame (a very rare need), call `WellFrame.vanilla`.

    Some meta columns are important to note:
        - 'name':           A potentially non-unique string that is used extensively for labeling, grouping, and other purposes.
                            A concise representation of what you care about in a WellFrame at some point.
        - 'display_name':   Used as labels by plotting code. Str-typed and non-null. (This is technically optional, but set to 'name' by self.__class__.of and WellFrameBuilder.)
        - 'pack':           A string that is occasionally used for grouping wells to be handled separately in analyses;
                            For example, code might plot a barplot with one bar per unique 'name', but a separate figure for each 'pack'.
        - 'size':            Optional reserved column, str-typed or None. To indicate "strength" or "dose". Some plotting code will use this for point sizes or color gradients.
        - 'well':           The ID in the wells table
        - 'run':            The ID in the runs table
        - 'treatments':     A Treatments instance, which is hashed nicely to work with Pandas
        - 'c_ids':          Compound IDs as a list, in the same order as Treatments
        - 'b_ids':          Batch IDs as a list, in the same order as Treatments
        - 'compound_names': Fully optional compound names, in the same order as Treatments. Tuples of str type if it exists.

    Implements a number of methods for common ways to select, transform features, etc.
    All the operations will return a new view (won't modify in place), unless they end with _inplace.
    You can get the features with .values and meta columns without features with .meta().

    Among the functions for selecting by rows are:
        - with_run, with_name, with_pack
        - with_controls, with_controls_matching, wihtout_controls, without_controls_matching
        - with_all_treatments, with_any_treatments, with_compound_at_dose, with_batch_at_dose
        - with_all_compounds, with_any_compounds, without_all_compounds, without_any_compounds
        - with_all_batches, with_any_batches, without_all_batches, without_any_batches

    About with_all vs with_any vs with_only:
        - The with_all_ functions will include a row iff it contains all of the items passed in the list.
        - The with_all_ functions will include a row iff it contains all of the items passed in the list.
        - The with_only_any_ functions will include a row iff it contains one or more of the items passed in the list, but no others.
        - The with_only_all_ functions will include a row iff it contains all of the items passed in the list, and no others.

    There are two feature-slicing columns:
        - slice_ms:        Slices between start and end milliseconds, including the start and excluding the end.
        - subset:          Slices by feature indices

    And some functions to control-subtract:
        - control_subtract: Accepts a control_types name or ID
        - name_subtract:    Accepts a value in the 'name' column
        - pack_subtract:    Accepts a value in the 'pack' column
        - run_subtract:     Accepts a value in the 'run' column
        - z_score:          Calculates a Z-score with respect to a control type

    Among the feature-manipulation functions are:
        - smooth            Applies a smoothing sliding window
        - threshold_zeros   Makes any value near to zero exactly 0.

    There are three sorting functions:
        - sort_std:         Sorts by a list of columns in order,
                            falling back on later columns in turn as they are needed to resolve differences.
                            This sort order is generally useful for displaying figures, etc.
        - sort_values       Sorts by a single column or list of columns. Delegates to pd.DataFrame.sort_values.
        - sort_by           Sorts by a function of rows.
        - sort_natural        Applies a natural sort using `natsort` to a column. (Inherited from OrganizingFrame.)

    There are five functions that group rows and apply a reduction / aggregation function to rows (potentially resulting in fewer rows):
        - agg_by_name:      Aggregates rows with the same 'name' column
        - agg_by_pack:      Aggregates rows with the same 'pack'
        - agg_by_run:       Aggregates rows with the same run ID
        - agg_by_important: Aggregates rows by information about the contents of the wells, along with battery and sauron_config.
                            This excludes columns such as well, row, column, well_index, and well_label,
                            as well as run, experiment, project, and template_plate.
                            See WellFrameColumnTools.unimportant_cols for full info.
                            Generally, this is the most useful agg function, though it is slower than agg_by_name and agg_by_pack.
                            It is important to note that some magic happens to make this work; see WellFrameColumnTools for more info.
        - agg_by_all:       Aggregates rows that share all of a set of columns that multiple wells can potentially share.
                            This excludes columns such as well, row, column, well_index, and well_label,
                            but will include treatments, run, and all other columns.
                            See WellFrameColumnTools.well_position_cols for full info.
    """

    def __init__(self, data=None, index=None, columns=None, dtype=None, copy=False):
        super().__init__(data=data, index=index, columns=columns, dtype=dtype, copy=copy)

    @abcd.overrides
    @abcd.copy_docstring(pd.DataFrame.copy)
    def copy(self, deep=True):
        return self.__class__.retype(super().copy())

    @abcd.overrides
    @abcd.copy_docstring(pd.DataFrame.astype)
    def astype(self, dtype, copy=True, errors="raise", **kwargs):
        return self.__class__.retype(super().astype(dtype, copy=copy, errors=errors, **kwargs))

    def head(self, n: Optional[int] = 5):
        if n is None:
            return self
        return self.__class__.retype(super().head())

    @abcd.overrides
    def abs(self):
        return self.__class__.retype(super().abs())

    @abcd.overrides
    def replace(
        self, to_replace=None, value=None, inplace=False, limit=None, regex=False, method="pad"
    ):
        return self.__class__.retype(
            super().replace(
                to_replace=to_replace,
                value=value,
                inplace=inplace,
                limit=limit,
                regex=regex,
                method=method,
            )
        )

    @classmethod
    @abcd.overrides
    def reserved_index_names(cls) -> Sequence[str]:
        return WellFrameColumns.reserved_names

    @classmethod
    @abcd.overrides
    def required_index_names(cls) -> Sequence[str]:
        return WellFrameColumns.required_names

    @classmethod
    @abcd.overrides
    def columns_to_drop(cls) -> Sequence[str]:
        return ["__sort", "level_0", "index", "level_1"]

    def __setitem__(self, key, value):
        # freely set meta cols; avoid ValueError: cannot insert name, already exists
        ind = copy(self.index.names)
        if isinstance(key, str) and key in ind:
            self.reset_index(inplace=True)
            super().__setitem__(key, value)
            self.set_index(ind, inplace=True)
        else:
            super().__setitem__(key, value)

    def __getitem__(self, item):
        if isinstance(item, str) and item in self.index.names:  # indexing a column
            return self.index.get_level_values(item)
        ret = pd.DataFrame.__getitem__(self, item)
        if isinstance(ret, pd.DataFrame) and (
            "name" in ret.columns or "name" in ret.index.names
        ):  # Boolean-indexing
            return self.__class__.of(ret)
        # if isinstance(ret, pd.DataFrame) and all([c in ret.columns or c in ret.index.names for c in WellFrameColumns.required_names]):
        #     return self.__class__.of(ret)
        return ret

    def safe_reset_index(self):
        bad = InternalTools.warn_overlap(self.columns, self.index.names)
        df = self.__class__.drop_cols(self, bad)
        df = self.__class__.vanilla(df)
        return self.__class__.of(df.reset_index())

    def meta(self) -> WellFrame:
        """
        Drops the feature columns, returning only the index.
        :return: A copy as a WellFrame
        """
        if len(self.columns) == 0:
            return self
        else:
            df = self[[self.columns[0]]]
            df = df.drop(self.columns[0], axis=1)
            return self.__class__.of(df)

    def before_first_nan(self) -> WellFrame:
        """
        Drops every feature column after (and including) the first NaN in any row.
        Also see after_last_nan and unify_last_nans_inplace.
        :return: A copy as a WellFrame
        """
        return self.__class__.retype(self[self.columns[: -self.count_nans_at_end()]])

    def after_last_nan(self) -> WellFrame:
        """
        Drops every feature column before (and including) the last NaN spanning from the start of the features to the first non-NaN column, in any row.
        Also see before_first_nan.
        :return: A copy as a WellFrame
        """
        return self.__class__.retype(self[self.columns[self.count_nans_at_start() :]])

    def count_nans_at_end(self) -> int:
        """
        Counts the number of columns, starting from the last, before all of the values are non-null.
        :return: The number of columns
        """
        for i in range(0, len(self.columns)):
            if not self[self.columns[-i - 1]].isnull().values.any():
                return i
        return 0

    def count_nans_at_start(self) -> int:
        """
        Counts the number of columns, starting from the first, after which all of the values are non-null.
        :return: The number of columns
        """
        for i in range(0, len(self.columns)):
            if not self[self.columns[i]].isnull().values.any():
                return i
        return 0

    def unify_last_nans(self, fill_value: float = np.NaN) -> WellFrame:
        """
        See `WellFrame.unify_last_nans_inplace`. This returns a copy, which requires more memory.
        """
        df = self.copy()
        df.unify_last_nans_inplace(fill_value)
        return df

    def unify_last_nans_inplace(self, fill_value: float = np.NaN) -> int:
        """
        Replaces every column at the end containing a NaN with some value.
        Only affects NaNs that continue to the end.
        More technically, for every column from the last to the first, drops it if contains a single NaN, and returns if it doesn't.
        Also see unify_first_nans_inplace and before_first_nan.
        :param fill_value: The number of columns filled
        """
        n_unified = 0
        for i in range(len(self.columns) - 1, 0, -1):
            if not self[self.columns[i]].isnull().values.any():
                return n_unified
            self[self.columns[i]] = fill_value
            n_unified += 1
        return n_unified

    def unify_first_nans(self, fill_value: float = np.NaN) -> WellFrame:
        """
        See `WellFrame.unify_first_nans_inplace`. This returns a copy, which requires more memory.
        """
        df = self.copy()
        df.unify_first_nans_inplace(fill_value)
        return df

    def unify_first_nans_inplace(self, fill_value: float = np.NaN) -> int:
        """
        Replaces every column at the beginning containing a NaN with some value.
        Only affects NaNs that continue to the end.
        Also see unify_last_nans_inplace and after_first_nan.
        :param fill_value: The number of columns filled
        """
        n_unified = 0
        for i in range(0, len(self.columns)):
            if not self[self.columns[i]].isnull().values.any():
                return n_unified
            self[self.columns[i]] = fill_value
            n_unified += 1
        return n_unified

    def completion(self) -> WellFrame:
        """
        Interpolates any NaN or 0.0 with the value from the previous frame, returning a view. The metadata is preserved.
        You may want to call unify_last_nans() first.
        Will warn if some but not all of the values of the last frame are NaN, suggesting that you should call unify_last_nans() before.
        :return: A copy as a WellFrame
        """
        last_col = self.columns[len(self.columns) - 1]
        if self[last_col].isnull().values.any() and not self[last_col].isnull().values.all():
            logger.warning(
                "In the last feature column, some, but not all, values are NaN. Consider calling unify_last_nans first."
            )
        return self.__with_new_features(
            self.fillna(value=0.0, method="ffill", axis=1).fillna(method="ffill", axis=1)
        )

    def slice_ms(self, start_ms, end_ms, override_fps: Optional[int] = None):
        """
        Approximates the correct start and end frames by detecting the framerate.
        Note that this is a less sophisticated, subtly more error-prone method than going by the exact timestamps.
        Will fail if this WellFrame contains runs with different FPSes.
        :param start_ms: The milliseconds to start at
        :param end_ms: The millseconds to end at
        :param override_fps: Correct the FPS from what's assumed from the battery
        :return: A new WellFrame
        """
        if override_fps is None:
            fps = Tools.only(
                {ValarTools.frames_per_second(r) for r in self["run"].unique()}, name="framerates"
            )
        else:
            fps = override_fps
        return self.__class__.retype(
            self.subset(
                None if start_ms is None else int(np.floor(start_ms * fps / 1000)),
                None if end_ms is None else int(np.ceil(end_ms * fps / 1000)),
            )
        )

    def subset(self, start: Optional[int] = None, end: Optional[int] = None) -> WellFrame:
        """
        Slices the features by index.
        :param start: The first MI index (snapshot)
        :param end: The last MI index (snapshot)
        :return: The dataframe with only metadata and the MI values requested
        """
        if start is None:
            start = 0
        if end is None:
            end = len(self.columns)
        columns = self.columns[start:end].tolist()
        return WellFrame(self[columns])

    def feature_length(self) -> int:
        """
        Counts the number of features.
        :return: The exact number of features
        """
        return len(self.columns)

    def n_replicates(self) -> Mapping[str, int]:
        return self.reset_index().groupby("name").count()["well"].to_dict()

    def xy(self) -> Tup[np.array, np.array]:
        """Returns a tuple of (features, names)."""
        return self.values, self.names().values

    def cross_runs(self) -> Iterator[Tup[WellFrame, WellFrame]]:
        for run in self.unique_runs():
            yield self.without_run_id(run), self.with_run(run)

    def bootstrap(self, n: Optional[int] = None) -> WellFrame:
        """
        Subsamples WITH replacement.
        :param n: If None, uses len(self)
        """
        n = len(self) if n is None else n
        return self.__class__.of(self.sample(n, replace=True))

    def subsample(self, n: Optional[int] = None) -> WellFrame:
        """
        Subsamples WITHOUT replacement.
        :param n: If None, uses len(self)
        """
        if n is None:
            return self
        return self.__class__.of(self.sample(n, replace=False))

    def subsample_even(self, n: Optional[int] = None) -> WellFrame:
        """
        Subsamples WITHOUT replacement,
        keeping the min replicate counts for any name, for each name
        :param n: If None, uses the max permitted
        """
        if n is None:
            n = min(self.n_replicates().values())
        return WellFrame.concat(
            *[self.with_name(name).subsample(n) for name in self.unique_names()]
        )

    def names(self) -> pd.Series:
        return self.index.get_level_values("name")

    def display_names(self) -> pd.Series:
        """Gets the display_name column, or name if display_name is not present."""
        return (
            self.index.get_level_values("display_name")
            if "display_name" in self.index.names
            else self.index.get_level_values("name")
        )

    def packs(self) -> pd.Series:
        return self.index.get_level_values("name")

    def unique_names(self) -> Sequence[str]:
        return self.index.get_level_values("name").unique().tolist()

    def unique_packs(self) -> Sequence[str]:
        return self.index.get_level_values("pack").unique().tolist()

    def unique_runs(self) -> Set[int]:
        return self["run"].unique().tolist()

    def with_name(self, name: Union[Sequence[str], Set[str], str]) -> WellFrame:
        """
        Selects only the wells matching a name.
        :param name: An entry in the name column, or list or set of them
        :return: A modified copy of this WellFrame
        """
        name = Tools.to_true_iterable(name)
        return self.__class__.retype(self[self.names().isin(name)])

    def with_wells(self, wells: Union[Iterable[Union[int, Wells]], Wells, int]):
        wells = InternalTools.fetch_all_ids_unchecked(Wells, Tools.to_true_iterable(wells))
        return self.__class__.retype(self[self["well"].isin(wells)])

    def with_run(self, runs: Union[Iterable[RunLike], RunLike]) -> WellFrame:
        """
        Selects only the wells matching a run ID.
        :param runs: A run ID, or list or set of them
        :return: A modified copy of this WellFrame
        """
        runs = set(Tools.run_ids_unchecked(runs))
        return self.__class__.retype(self[self["run"].isin(runs)])

    def with_run_id(self, run_id: Union[int, Set[int]]) -> WellFrame:
        return self.with_run(run_id)

    def without_run(self, runs: Union[int, Set[int]]) -> WellFrame:
        runs = set(Tools.run_ids_unchecked(runs))
        return self.__class__.retype(self[~self["run"].isin(runs)])

    def without_run_id(self, run_id: Union[int, Set[int]]) -> WellFrame:
        return self.without_run(run_id)

    def with_pack(self, pack: Union[Sequence[str], Set[str], str]) -> WellFrame:
        pack = Tools.to_true_iterable(pack)
        return self.__class__.retype(self[self.packs().isin(pack)])

    def with_issue(self, key: str) -> WellFrame:
        if "issues" not in self.index.names:
            raise MissingColumnError("No issues column")
        return self.__class__.retype(
            self[self["issues"].map(partial(WellIssues.contains, key=key))]
        )

    def without_issue(self, key: str) -> WellFrame:
        if "issues" not in self.index.names:
            raise MissingColumnError("No issues column")
        return self.__class__.retype(self[self["issues"].map(partial(WellIssues.dne, key=key))])

    def apply_by_name(self, function) -> WellFrame:
        return self.__class__.of(self.group_by(level="name", sort=False).apply(function))

    def apply_by_run(self, function) -> WellFrame:
        return self.__class__.of(self.group_by(level="run", sort=False).apply(function))

    def apply_by_pack(self, function) -> WellFrame:
        return self.__class__.of(self.group_by(level="pack", sort=False).apply(function))

    def without_treatments(self) -> WellFrame:
        """
        :return: Only the wells that were not treated with batches
        """
        return self[self["b_ids"].map(str) == "[]"]

    def with_only_all_treatments(self, treatments: Treatments) -> WellFrame:
        treatments = Treatments.of(treatments)
        return self[self["treatments"] == treatments]

    def with_only_any_treatments(self, treatments: Treatments) -> WellFrame:
        treatments = Treatments.of(treatments)
        z = self.__class__.retype(
            self[self["treatments"].map(lambda ts: any([t in ts for t in treatments]))]
        )
        return self.__class__.retype(
            z[z["treatments"].map(lambda ts: all([t in treatments for t in ts]))]
        )

    def with_any_treatments(self, treatments: Treatments) -> WellFrame:
        treatments = Treatments.of(treatments)
        return self.__class__.retype(
            self[self["treatments"].map(lambda ts: any([t in ts for t in treatments]))]
        )

    def with_all_treatments(self, treatments: Treatments) -> WellFrame:
        treatments = Treatments.of(treatments)
        return self.__class__.retype(
            self[self["treatments"].map(lambda ts: all([t in ts for t in treatments]))]
        )

    def with_compound_at_dose_any(
        self, compound: Union[Compounds, int, str], dose: SupportsFloat
    ) -> WellFrame:
        compound = Compounds.fetch(compound)
        dose = float(dose)
        d = self.with_all_compounds(compound)
        d = d[
            d["treatments"].map(
                lambda ts: dose in [t.dose for t in ts if t.compound_id == compound.id]
            )
        ]
        return self.__class__.retype(d)

    def with_batch_at_dose_any(
        self, batch: Union[Batches, int, str], dose: SupportsFloat
    ) -> WellFrame:
        batch = Batches.fetch(batch)
        dose = float(dose)
        d = self.with_all_batches(batch)
        d = d[d["treatments"].map(lambda ts: dose in [t.dose for t in ts if t.id == batch.id])]
        return self.__class__.retype(d)

    def with_only_all_compounds(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        compounds = set(InternalTools.fetch_all_ids(Compounds, compounds))
        return self.__class__.retype(self[self["c_ids"].map(lambda cids: set(cids) == compounds)])

    def with_only_any_compounds(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        compounds = set(InternalTools.fetch_all_ids(Compounds, compounds))
        z = self.__class__.retype(
            self[self["c_ids"].map(lambda cids: any([c in cids for c in compounds]))]
        )
        return self.__class__.retype(
            z[z["c_ids"].map(lambda cids: all([c in compounds for c in cids]))]
        )

    def with_only_all_batches(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        batches = set(InternalTools.fetch_all_ids(Batches, batches))
        return self.__class__.retype(self[self["b_ids"].map(lambda bids: set(bids) == batches)])

    def with_only_any_batches(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        batches = set(InternalTools.fetch_all_ids(Batches, batches))
        z = self.__class__.retype(
            self[self["b_ids"].map(lambda bids: any([c in bids for c in batches]))]
        )
        return self.__class__.retype(
            z[z["b_ids"].map(lambda bids: all([c in batches for c in bids]))]
        )

    def with_all_compounds(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        compounds = tuple(InternalTools.fetch_all_ids(Compounds, compounds))
        return self.__class__.retype(
            self[self["c_ids"].map(lambda cids: all([c in cids for c in compounds]))]
        )

    def with_all_batches(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        batches = tuple(InternalTools.fetch_all_ids(Batches, batches))
        return self.__class__.retype(
            self[self["b_ids"].map(lambda bids: all([b in bids for b in batches]))]
        )

    def with_any_compounds(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        compounds = InternalTools.fetch_all_ids(Compounds, compounds)
        return self.__class__.retype(
            self[self["c_ids"].map(lambda cids: any([c in cids for c in compounds]))]
        )

    def with_any_batches(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        batches = InternalTools.fetch_all_ids(Batches, batches)
        return self.__class__.retype(
            self[self["b_ids"].map(lambda bids: any([b in bids for b in batches]))]
        )

    def without_any_compounds(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        compounds = InternalTools.fetch_all_ids(Compounds, compounds)
        return self.__class__.retype(
            self[self["c_ids"].map(lambda cids: all([c not in cids for c in compounds]))]
        )

    def without_any_batches(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        batches = InternalTools.fetch_all_ids(Batches, batches)
        return self.__class__.retype(
            self[self["b_ids"].map(lambda bids: all([b not in bids for b in batches]))]
        )

    def without_all_compounds(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        compounds = tuple(InternalTools.fetch_all_ids(Compounds, compounds))
        return self.__class__.retype(
            self[self["c_ids"].map(lambda cids: any([c not in cids for c in compounds]))]
        )

    def without_all_batches(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        batches = tuple(InternalTools.fetch_all_ids(Batches, batches))
        return self.__class__.retype(
            self[self["b_ids"].map(lambda bids: any([b not in bids for b in batches]))]
        )

    def with_controls(
        self, names: Union[None, str, Iterable[str]] = None, **attributes
    ) -> WellFrame:
        return self.with_controls_matching(names=names, **attributes)

    def with_controls_matching(
        self, names: Union[None, str, Iterable[str]] = None, **attributes
    ) -> WellFrame:
        """
        Returns the subset of the wellframe containing the controls meeting certain criteria. See optional arguments for WellFrames.controls_matching for details on these criteria.
        """
        matches = self.unique_controls_matching(names, **attributes)
        return self.__class__.retype(self[self["control_type"].isin(matches)])

    def without_controls_matching(
        self, names: Union[None, str, Iterable[str]] = None, **attributes
    ) -> WellFrame:
        matches = self.unique_controls_matching(names, **attributes)
        return self.__class__.retype(self[~self["control_type"].isin(matches)])

    def only_control_matching(
        self, names: Union[None, str, Iterable[str]] = None, **attributes
    ) -> str:
        """
        Returns a unique control matching the conditions, or raises a MultipleMatchesError or LookupError.
        """
        return Tools.only(
            self.unique_controls_matching(names, **attributes), name="control types"
        ).name

    def unique_controls_matching(
        self,
        names: Union[None, ControlTypes, str, int, Set[Union[ControlTypes, int, str]]] = None,
        **attributes,
    ) -> Set[str]:
        """
        Return the control types in this WellFrame matching ALL of the specified criteria.
        :param names: The set of allowed control_types
        :param attributes: Any key-value pairs mapping an attribute of ControlTypes to a required value
        """
        return {
            c.name
            for c in ValarTools.controls_matching_all(names, **attributes)
            if c.name in self["control_type"].unique()
        }

    # TODO the same, right?
    # @abcd.overrides
    # def sort_natural(self, column: str, alg: int = ns.INT):
    #     return self.__class__.retype(super().sort_natural(column, alg))

    def sort_pretty(self, more_controls: Optional[Set[str]] = None) -> WellFrame:
        """
        Sorts by the names with a natural sort, but putting control names at the top.
        To do this, relies on the name to determine whether a row is a control.
        """
        return self.__class__.retype(
            ValarTools.sort_controls_first(self, "name", more_controls=more_controls)
        )

    def sort_first(self, names: Sequence[str]):
        """
        Sorts these names first, keeping the rest in the same order.
        """
        return self.__class__.retype(ValarTools.sort_first(self, self["name"], names))

    def sort_values(
        self, by: Union[str, Sequence[str]], ascending: bool = True, **kwargs
    ) -> Union[WellFrame, pd.DataFrame]:
        """
        Either handles special cases or delegates to the superclass.
        WARNING: If inplace, na_position, kind, or axis is SET (even if default):
                Will simply delegate to the superclass method and return a plain pd.DataFrame.
        :param by: What to sort by
        :param ascending: Pretty obvious
        :param kwargs: Delegated to DataFrame.sort_values
        :return: Either a new WellFrame or a DataFrame for other cases.
        """
        if any([k in kwargs for k in ["axis", "inplace", "kind", "na_position"]]):
            return super().sort_values(by, ascending=ascending, **kwargs)
        return self.__class__.retype(
            pd.DataFrame.sort_values(self.__class__.vanilla(self), by, ascending=ascending)
        )

    def sort_std(self) -> WellFrame:
        """
        Sorts by so-called 'important' information, then by run (datetime_run), then by well index.
        In order: control_type, treatments, variant_name, n_fish, age, well_group, datetime_run, well_index
        """
        return self.sort_values(
            [
                "control_type",
                "treatments",
                "variant_name",
                "n_fish",
                "age",
                "well_group",
                "datetime_run",
                "well_index",
            ]
        )

    def sort_by(
        self, function: Union[None, Callable[[pd.Series], Any], pd.Series, Sequence[Any]] = None
    ) -> WellFrame:
        """
        Sorts by a function of the rows.
        `function` can be any of three types:
            - None     ==> will sort by 'name'
            - str      ==> will sort by that column by delegating to pd.sort_values
            - function ==> preferred. See below.
        :param function: A function mapping the pd.Series of each row to a value that will be used as input to pd.sort_values
        :return: The sorted WellFrame
        """
        # we'll add in a __sort column and then call sort_values
        # this column will be removed by self.__class__.of
        ValarTools.sort_controls_first(self, self["name"])
        if function is None:
            self["__sort"] = self.names()
        elif isinstance(function, str):
            return self.sort_values(function)
        elif Tools.is_true_iterable(function):
            self["__sort"] = function
        elif callable(function):
            self["__sort"] = self.reset_index().apply(function, axis=1)
        return self.sort_values("__sort")

    def agg_by_name(self, function=np.mean) -> WellFrame:
        """
        Aggregates by the 'name' column alone. All other meta column will be dropped.
        :param function: The function to use in aggregation
        :return: The aggregated WellFrame
        """
        return self.__class__.of(self.groupby(level="name", sort=False).apply(function))

    def agg_by_important(self, function=np.mean) -> WellFrame:
        """
        Aggregates by battery, Sauron config, name, pack (if any), size (if any) and information about the contents of the well.
        Note that this excludes display_name.
        Meta columns not aggregated on (not in the above list) will be dropped.
        :param function: The function to use in aggregation
        :return: The aggregated WellFrame
        """
        well_cols = WellFrameColumnTools.unimportant_cols
        return self._agg_by(function, well_cols)

    def agg_by_all(self, function=np.mean) -> WellFrame:
        """
        Aggregates by everything except for well, well_index, well_label, row, and column.
        All meta columns that are excluded will be dropped.
        :param function: The function to use in aggregation
        :return: The aggregated df
        """
        well_cols = WellFrameColumnTools.well_position_cols
        return self._agg_by(function, well_cols)

    def agg_by_pack(self, function=np.mean) -> WellFrame:
        """
        Aggregates by the 'pack' column alone.
        All other meta column will be dropped.
        :param function: The function to use in aggregation
        :return: The aggregated df
        """
        return self.__class__.of(self.groupby(level="pack", sort=False).apply(function))

    def agg_by_run(self, function=np.mean) -> WellFrame:
        """
        Aggregates by the 'run' column alone.
        All other meta column will be dropped.
        :param function: The function to use in aggregation
        :return: The aggregated df
        """
        return self.__class__.of(self.groupby(level="run", sort=False).apply(function))

    def log2_dose_to_size(self, fallback: str = "N/A"):
        # noinspection PyTypeChecker
        return self.dose_to_size(fallback, np.log2)

    def dose_to_size(self, fallback: str = "N/A", transform: Callable[[float], Any] = lambda s: s):
        def gsize(ts: Treatments):
            if ts.len() == 0:
                return fallback
            elif ts.len() > 1:
                raise MultipleMatchesError("Multiple treatments {}".format(ts))
            else:
                return transform(ts[0].dose)

        return self.set_meta_col("size", self["treatments"].map(gsize).map(str))

    def feature_means(self) -> WellFrame:
        """
        :return: A new WellFrame with a single feature column, 0, which has the mean.
        """
        return self.apply_to_features(lambda d: pd.DataFrame(d.mean(axis=1)))

    def apply_to_features(self, function: Callable[[pd.DataFrame], pd.DataFrame]) -> WellFrame:
        """Applies a function to the features only, and then merges it back with meta.
        :param function: Actually a function of WellFrame; can return a DataFrame or WellFrame
        :return: A new WellFrame
        """
        return self.__with_new_features(function(self))

    def smooth(
        self,
        function=lambda s: s.mean(),
        window_size: int = 10,
        window_type: Optional[str] = "triang",
    ) -> WellFrame:
        """
        Applies a function along a sliding window of the features using pd.DataFrame.rolling.
        :param function: A smoothing function mapping pd.Series to pd.Series
        :param window_size: The number of features in each window
        :param window_type: An argument to pd.DataFrame.rolling `win_type`
        :return: The same WellFrame with smoothed features
        """
        results = function(self.rolling(window_size, axis=1, min_periods=1, win_type=window_type))
        return self.__with_new_features(results)

    def z_score(self, control_type: Union[None, str, int, ControlTypes]) -> WellFrame:
        """
        Takes Z-score of the features with respect the specified control wells.
        Concretely, calculates: (well - controls.mean()) / all_wells.std()
        :param control_type: The name, ID, or instance of a ControlTypes
        :return: The same WellFrame with new features
        """
        zs = lambda case, control: (case - control.mean()) / case.std()
        return self.control_subtract(zs, control_type)

    def control_subtract(
        self,
        function: Callable[[pd.DataFrame, pd.DataFrame], pd.DataFrame],
        control_type: Union[None, str, int, ControlTypes],
    ) -> WellFrame:
        """
        Applies a function to the whole dataframe with respect to the controls.
        :param function: Maps (whole_df, controls_only) to a new DataFrame
        :param control_type: The name, ID, or object for a ControlType. If None, is taken to mean all controls (which is potentially weird).
        :return: The same WellFrame
        """
        if control_type is None:
            control_df = self.__class__.retype(self[self["control_type_id"].isnull()])
            logger.warning("Subtracting all control types. Is this really what you want?")
        else:
            control_type = ControlTypes.fetch(control_type)
            control_df = self.__class__.retype(self[self["control_type_id"] == control_type.id])
        results = function(self, control_df)
        return self.__with_new_features(results)

    def z_score_by_names(self, name_to_subtract: Optional[str]) -> WellFrame:
        """
        Calculates Z-scores with respect to rows with the name column matching `name_to_subtract`.
        See WellFrame.z_score for more info.
        :param name_to_subtract: The entry in the name column
        :return: The same WellFrame
        """
        return self.name_subtract(
            lambda case, control: (case - control.mean()) / case.std(), name_to_subtract
        )

    def z_score_by_pack(self, pack_to_subtract: Optional[str]) -> WellFrame:
        """
        Calculates Z-scores with respect to rows with the name column matching pack_to_subtract`.
        See WellFrame.z_score for more info.
        :param pack_to_subtract: The entry in the pack column
        :return: The same WellFrame
        """
        return self.pack_subtract(
            lambda case, control: (case - control.mean()) / case.std(), pack_to_subtract
        )

    def z_score_by_run(self, run_to_subtract: Optional[int]) -> WellFrame:
        """
        Calculates Z-scores with respect to rows with the run column matching pack_to_subtract`.
        See WellFrame.z_score for more info.
        :param run_to_subtract: A run ID
        :return: The same WellFrame
        """
        return self.run_subtract(
            lambda case, control: (case - control.mean()) / case.std(), run_to_subtract
        )

    def name_subtract(
        self,
        function: Callable[[pd.DataFrame, pd.DataFrame], pd.DataFrame],
        name: Optional[str] = None,
    ) -> WellFrame:
        """Analogous to control_subtract, but subtracts with respect to names (in the index) rather than actual control types.
        :param function: Maps (whole_df, controls_only) to a new DataFrame
        :param name: The string in this_df.names()
        :return: A new WellFrame
        """
        control_df = self.with_name(name)
        results = function(self, control_df)
        return self.__with_new_features(results)

    def pack_subtract(
        self,
        function: Callable[[pd.DataFrame, pd.DataFrame], pd.DataFrame],
        pack: Optional[str] = None,
    ) -> WellFrame:
        """Analogous to control_subtract, but subtracts with respect to packs (in the index) rather than actual control types.
        :param function: Maps (whole_df, controls_only) to a new DataFrame
        :param pack: The string in this_df.packs()
        :return: A new WellFrame
        """
        control_df = self.with_pack(pack)
        results = function(self, control_df)
        return self.__with_new_features(results)

    def run_subtract(
        self,
        function: Callable[[pd.DataFrame, pd.DataFrame], pd.DataFrame],
        run: Optional[int] = None,
    ) -> WellFrame:
        """Analogous to control_subtract, but subtracts with respect to runs (in the index) rather than actual control types.
        :param function: Maps (whole_df, controls_only) to a new DataFrame
        :param run: The ID
        :return: A new WellFrame
        """
        control_df = self.with_run(run)
        results = function(self, control_df)
        return self.__with_new_features(results)

    def unique_batch_ids(self) -> Sequence[int]:
        """
        :return: A list of the unique batches.id values among all wells.
                The values will be in the same order as they appear the rows (and then by their order in Treatments).
        """
        return Tools.unique([item for sublist in self["b_ids"] for item in sublist])

    def unique_compound_ids(self) -> Sequence[int]:
        """
        :return: A list of the unique compounds.id values among all wells.
                The values will be in the same order as they appear the rows (and then by their order in Treatments).
        """
        return Tools.unique([item for sublist in self["c_ids"] for item in sublist])

    def unique_compound_names(self, namer: Optional[CompoundNamer] = None) -> Sequence[str]:
        """
        Returns unique compound names in the order they appear in this WellFrame (by row, then by item in the Treatments instances).
            - If `namer` is passed, transforms self['treatments'] and returns the result
            - If `namer is not passed, returns the unique items in self['compound_names'] in order.
        :param namer: None or a CompoundNamer
        :return: A list of the compound names as strings, in order
        """
        if namer is None:
            return Tools.unique([item for sublist in self["compound_names"] for item in sublist])
        else:
            cids = self.unique_compound_ids()
            return namer.map_to(cids)

    def unique_treatments(self) -> Treatments:
        """
        :return: A list of the unique Treatment values among all wells.
                The values will be in the same order as they appear the rows (and then by their order in Treatments).
        """
        return Treatments(
            Tools.unique([item for sublist in self["treatments"] for item in sublist])
        )

    def unique_batch_hashes(self) -> Sequence[str]:
        """
        :return: A list of the unique batch.lookup_hash values among all wells.
                The values will be in the same order as they appear the rows (and then by their order in Treatments).
        """
        return Tools.unique([item.oc for sublist in self["treatments"] for item in sublist])

    def dose_of(self, batch: Union[Batches, str, int]) -> pd.Series:
        """
        Returns a Series of the specified batch, with 0.0 if the batch is not present.
        :param batch: A batch ID, lookup_hash, or instance
        :return: A Pandas Series with float values in which the entries match the rows in this WellFrame
        """
        batch = Batches.fetch(batch).lookup_hash

        def dof(treatments):
            ts = {t.oc: t.dose for t in treatments}
            if batch in ts:
                return ts[batch]
            else:
                return 0.0

        return self["treatments"].map(dof)

    def constrain(self, lower: float, upper: float) -> WellFrame:
        """
        Returns a new WellFrame with the features bound between lower and upper.
        """
        results = self.clip(lower, upper)
        return self.__with_new_features(results)

    def threshold_zeros(self, lower: float) -> WellFrame:
        """
        Returns a new WellFrame with features values under a certain (absolute value) threshold set to 0.
        """
        results = (self.abs() >= lower) * self.values
        return self.__with_new_features(results)

    def with_new_names(
        self, namer: Union[pd.Series, pd.Index, Sequence[str], WellNamer]
    ) -> WellFrame:
        """
        Returns a new WellFrame with new names set.
        Copies.
        """
        return self._with_new("name", namer, str)

    def with_new_display_names(
        self, namer: Union[pd.Series, pd.Index, Sequence[str], WellNamer]
    ) -> WellFrame:
        """
        Returns a new WellFrame with new display_names set.
        Copies.
        """
        return self._with_new("display_name", namer, str)

    def with_new_compound_names(self, namer: Optional[CompoundNamer]) -> WellFrame:
        """
        Returns a new WellFrame with the 'compound_names' meta column set.
        """
        if namer is None:
            return self._with_new(
                "compound_names",
                self["c_ids"].map(lambda cids: [None for _ in range(len(cids))]),
                tuple,
            )
        else:
            x = namer.map_2d(self["c_ids"])
            return self._with_new("compound_names", x, tuple)

    def with_new_packs(
        self, namer: Union[pd.Series, pd.Index, Sequence[str], WellNamer]
    ) -> WellFrame:
        """
        Returns a new WellFrame with new packs set.
        Copies.
        """
        return self._with_new("pack", namer, str)

    def with_new_sizes(
        self, namer: Union[pd.Series, pd.Index, Sequence[str], WellNamer]
    ) -> WellFrame:
        """
        Returns a new WellFrame with new sizes set.
        Copies.
        """
        return self._with_new("size", namer, str)

    def with_new(self, meta_col: str, setter: Union[pd.Series, pd.Index, Sequence[str], WellNamer]):
        if meta_col not in WellFrameColumnTools.special_cols:
            raise RefusingRequestError(
                "Can only set special meta columns ({}), not {}. See `set_meta_col` instead.".format(
                    WellFrameColumnTools.special_cols, meta_col
                )
            )

        dtype = tuple if meta_col == "compound_namer" else str
        return self._with_new(meta_col, setter, dtype)

    def _with_new(self, col, namer, dtype):
        df = self.__class__.retype(self.copy().reset_index().drop(col, axis=1))
        if isinstance(namer, pd.Series):
            df[col] = namer.values
        elif isinstance(namer, dtype):
            df[col] = namer
        elif isinstance(namer, pd.MultiIndex):
            df[col] = namer.get_level_values(col).values
        elif isinstance(namer, pd.Index):
            df[col] = namer.values
        elif callable(namer):
            df[col] = namer(df)
        else:
            df[col] = namer
        df[col] = df[col].map(dtype)
        return self.__class__.of(df)

    def set_meta_col(self, name: str, values: Any) -> WellFrame:
        """
        Returns a copy with a meta/index column set
        """
        df = self.copy().reset_index()
        df[name] = values
        return self.__class__.of(df)

    @classmethod
    def of(
        cls, df: pd.DataFrame, require_full: bool = False, ignore_extra_meta: bool = False
    ) -> WellFrame:
        """
        Turns a DataFrame into a WellFrame. Actually changes the class of the passed argument to WellFrame.
        Will perform even if `df` is already a WellFrame.
        Also see

        First, resets the index so it can be set correctly. Then, the following assumes no index columns:
        If ignore_extra_meta is False (default), sets every str-typed column as the index.
        This should be fine because feature columns should always be the only int-typed ones.
        If a column is neither int-typed nor str-typed, will leave these as columns. However, this is weird.
        If ignore_extra_meta is True, sets only the columns in WellFrameColumns.reserved_names, if they are present.
        Assumes that, if features exist, no meta columns will be in the middle of them.
        Meta columns after the first int column (feature) and before the last will be left as-is, potentially causing subtle calculation errors.
        Therefore, don't ever do that.
        If require_full is True, will additionally require that every column in WellFrameColumns.required_names is present.
        Otherwise, will only require a 'name' column.
        Raises a InvalidWellFrameError if these conditions are not met.

        Also fixes common mistakes:
            -   Removes columns called  'index', '__sort', or 'level_0'.
                These are not allowed in a WellFrame and are often added by mistake.
            -   Converts compound_names into tuples so that they can be hashed.

        WARNING: Does not make a copy. Changes the class of df to WellFrame in place.
        WARNING: Will drop any column called 'index', '__sort', or 'level_0'.

        :param ignore_extra_meta: If True, leaves str-typed columns in the index.
        :param df: A Pandas Dataframe to convert
        :param require_full: If true, checks that the WellFrame has every 'required' (pseudo-required) column
        :return: A WellFrame from this DataFrame, NOT a copy
        :raises TypeError If the argument is not a WellFrame or DataFrame
        :raises InvalidWellFrameError If the input is not valid
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Can only build a WellFrame from a Pandas DataFrame.")
        # if isinstance(df, WellFrame): return df
        try:
            df = WellFrame.__fix_columns(df, require_full, ignore_extra_meta)
        except Exception:
            logger.error(
                "Couldn't convert WellFrame with columns meta columns {} and columns {}".format(
                    df.index.names, df.columns
                )
            )
            raise
        df.__class__ = cls
        # noinspection PyTypeChecker
        return df

    @classmethod
    def retype(cls, df: pd.DataFrame) -> WellFrame:
        """
        Sets the __class__ of `df` to WellFrame.
        Instantaneous and in-place.
        Does not perform any checks; see `of` for a safer but slower method.
        :param df: A Pandas DataFrame or subclass
        :return: A WellFrame
        """
        df.__class__ = cls
        # noinspection PyTypeChecker
        return df

    @classmethod
    def new_empty(cls, n_features: int) -> WellFrame:
        """Returns a new empty DataFrame."""
        cols = WellFrameColumns.reserved_names
        df = pd.DataFrame(columns=[*cols, *np.arange(0, n_features)])
        df = df.reset_index().set_index(cols)
        return cls.of(df)

    @classmethod
    def concat(cls, *wfs: Sequence[WellFrame]) -> WellFrame:
        """
        Concatenates WellFrames vertically.
        :param wfs: A var-args list of WellFrames or DataFrames
        :return: A new WellFrame
        """
        return cls.of(pd.concat(wfs, sort=False))

    @classmethod
    def assemble(cls, meta: pd.DataFrame, features: pd.DataFrame) -> WellFrame:
        """
        Builds a new WellFrame from meta and features. Requires that both are in the same order
        The meta columns will then be made into index columns.
        WARNING: Ignores and discards indices on the features
        """
        meta = cls.of(meta).reset_index()
        features = features.reset_index(drop=True)
        df = pd.merge(meta, features, left_index=True, right_index=True)
        return cls.of(df)

    def _agg_by(self, function=np.mean, exclude: Set[str] = None) -> WellFrame:
        if exclude is None:
            exclude = []
        df = self.copy()  # we'll change this inplace
        # columns that can be null
        # we have to replace these or Pandas groupby will drop rows where it's None or NaN
        df = WellFrameColumnTools.from_nan(df.reset_index())
        groupby_cols = [r for r in self.index.names if r not in exclude]
        for c in exclude:
            if c in df.columns:
                df = df.drop(c, axis=1)
        df = df.reset_index().set_index(groupby_cols)
        df = df.groupby(level=groupby_cols, sort=False).apply(function)
        df = WellFrameColumnTools.to_nan(df.reset_index())
        return self.__class__.of(df)

    def __with_new_features(self, features: pd.DataFrame):
        return self.__class__.assemble(self.meta(), features)

    @classmethod
    def __fix_columns(
        cls, df: pd.DataFrame, require_full: bool, ignore_extra_meta: bool
    ) -> pd.DataFrame:
        # TODO this shouldn't be needed
        if "compound_names" in df.columns and "compound_names" in df.index.names:
            df = df.drop("compound_names", axis=1)
        # we're going to reset the index and partition every column into meta or features
        df = df.reset_index()
        # tabs can interfere with saving in various formats
        bad = {name for name in df["name"] if "\t" in str(name)}
        if len(bad) > 0:
            raise InvalidWellFrameError("Names {} contain tab characters".format(bad))
        # display_name is best to have in general
        if "display_name" not in df.columns:
            df["display_name"] = df["name"]
        if "size" not in df.columns:
            df["size"] = "1"
        if "color" not in df.columns:
            df["color"] = "#000000"
        if "marker" not in df.columns:
            df["marker"] = "."
        # compound namers return lists, which aren't hashable
        # this is the easiest and probably most robust solution
        if "c_ids" in df.columns and "compound_names" not in df.columns:
            df["compound_names"] = df["c_ids"].map(
                lambda cids: tuple(None for _ in range(len(cids)))
            )
        if "compound_names" in df.columns:
            df["compound_names"] = df["compound_names"].map(tuple)
        # 'name' is the only fully required meta column
        if "name" not in df.columns:
            raise InvalidWellFrameError(
                "Required column {} not in index; got {} for columns and {} for index".format(
                    "name", df.columns, df.index.names
                )
            )
        df["name"] = df["name"].map(str).astype(str)
        # optionally require every 'required' column
        if require_full:
            for c in WellFrameColumns.required_names:
                if c not in df.columns:
                    raise InvalidWellFrameError(
                        "Required column {} not in index; got {} for columns and {} for index".format(
                            c, df.columns, df.index.names
                        )
                    )
        df = WellFrame.__drop(df)
        # if we don't allow additional meta columns, only set those in reserved_names (if they exist)
        # otherwise, set every column that is a string type: features will always be int type
        # in theory, ignore_extra_meta should never be set, but it is for backwards-compatibility
        if ignore_extra_meta:
            df = df.set_index(
                [
                    x
                    for x in WellFrameColumns.reserved_names
                    if x in df.columns or x in df.index.names
                ]
            )
        else:
            df = WellFrame.__set_cols_to_index(df)
        return df

    @classmethod
    def __set_cols_to_index(cls, df: pd.DataFrame) -> pd.DataFrame:
        # preserve the order
        desired = [
            x for x in WellFrameColumns.reserved_names if x in df.columns or x in df.index.names
        ]
        # go from the start to the end and the end to the start
        # assume that there are no meta columns in the middle of features
        # this is almost always MUCH faster than iterating through all of the columns
        for x in df.columns:
            if isinstance(x, int):
                break
            if isinstance(x, str) and x not in desired:
                desired.append(x)
        for x in reversed(df.columns):
            if isinstance(x, int):
                break
            if isinstance(x, str) and x not in desired:
                desired.append(x)
        return df.set_index(desired)

    @classmethod
    def __drop(cls, d: pd.DataFrame) -> pd.DataFrame:
        # drop twice in case one of these is in both the index and the columns
        # otherwise df.reset_index() will raise an error about duplicate columns
        for x in {"level_0", "__sort", "index"}:
            if x in d.columns:
                d = d.drop(x, axis=1)
        d = d.reset_index()
        for x in {"level_0", "__sort", "index"}:
            if x in d.columns:
                d = d.drop(x, axis=1)
        return d


__all__ = ["WellFrame", "InvalidWellFrameError"]
