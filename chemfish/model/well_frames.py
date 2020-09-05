from __future__ import annotations

from chemfish.core.core_imports import *
from chemfish.model.compound_names import *
from chemfish.model.treatments import *
from chemfish.model.well_names import WellNamer
from chemfish.model.wf_tools import *


class InvalidWellFrameError(ConstructionError):
    """ """

    pass


class WellFrame(TypedDf):
    """
    A DataFrame where each row is a well.
    Implements TypedDf.
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
        - with_controls, wihtout_controls
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
        - sort_natural        Applies a natural sort using `natsort` to a column. (Inherited from TypedDf.)

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

    @classmethod
    @abcd.overrides
    def reserved_index_names(cls) -> Sequence[str]:
        """ """
        return WellFrameColumns.reserved_names

    @classmethod
    @abcd.overrides
    def required_index_names(cls) -> Sequence[str]:
        """ """
        return WellFrameColumns.required_names

    @classmethod
    @abcd.overrides
    def columns_to_drop(cls) -> Sequence[str]:
        """ """
        return ["__sort", "level_1"]

    @classmethod
    def of(cls, df: pd.DataFrame) -> WellFrame:
        """
        See ``convert``.
        """
        return cls.convert(df)

    def __getitem__(self, item) -> __qualname__:
        """

        """
        # TODO Shouldn't be needed
        if isinstance(item, str) and item in self.index.names:
            return self.index.get_level_values(item)
        else:
            return super().__getitem__(item)

    def meta(self) -> WellFrame:
        """
        Drops the feature columns, returning only the index.

        Returns:
            A copy as a WellFrame

        """
        # TODO Shouldn't be needed
        if len(self.columns) == 0:
            return self
        else:
            df: WellFrame = self[[self.columns[0]]]
            df = df.drop(self.columns[0], axis=1)
            return self.__class__.of(df)

    def before_first_nan(self) -> WellFrame:
        """
        Drops every feature column after (and including) the first NaN in any row.
        Also see after_last_nan and unify_last_nans_inplace.

        Returns:
            A copy as a WellFrame

        """
        return self.__class__.retype(self[self.columns[: -self.count_nans_at_end()]])

    def after_last_nan(self) -> WellFrame:
        """
        Drops every feature column before (and including) the last NaN spanning from the start of the features to the first non-NaN column, in any row.
        Also see before_first_nan.

        Returns:
            A copy as a WellFrame

        """
        return self.__class__.retype(self[self.columns[self.count_nans_at_start() :]])

    def count_nans_at_end(self) -> int:
        """
        Counts the number of columns, starting from the last, before all of the values are non-null.

        Returns:
            The number of columns
        """
        for i in range(0, len(self.columns)):
            if not self[self.columns[-i - 1]].isnull().values.any():
                return i
        return 0

    def count_nans_at_start(self) -> int:
        """
        Counts the number of columns, starting from the first, after which all of the values are non-null.

        Returns:
            The number of columns

        """
        for i in range(0, len(self.columns)):
            if not self[self.columns[i]].isnull().values.any():
                return i
        return 0

    def unify_last_nans_inplace(self, fill_value: float = np.NaN) -> int:
        """
        Replaces every column at the end containing a NaN with some value.
        Only affects NaNs that continue to the end.
        More technically, for every column from the last to the first, drops it if contains a single NaN, and returns if it doesn't.
        Also see unify_first_nans_inplace and before_first_nan.

        Args:
            fill_value: The number of columns filled

        Returns:

        """
        n_unified = 0
        for i in range(len(self.columns) - 1, 0, -1):
            if not self[self.columns[i]].isnull().values.any():
                return n_unified
            self[self.columns[i]] = fill_value
            n_unified += 1
        return n_unified

    def unify_first_nans_inplace(self, fill_value: float = np.NaN) -> int:
        """
        Replaces every column at the beginning containing a NaN with some value.
        Only affects NaNs that continue to the end.
        Also see unify_last_nans_inplace and after_first_nan.

        Args:
            fill_value: The number of columns filled

        Returns:

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

        Returns:
            A copy as a WellFrame

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

        Args:
            start_ms: The milliseconds to start at
            end_ms: The millseconds to end at
            override_fps: Correct the FPS from what's assumed from the battery

        Returns:
          A new WellFrame

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

        Args:
            start: The first MI index (snapshot)
            end: The last MI index (snapshot)

        Returns:
            The dataframe with only metadata and the MI values requested

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

        Returns:
            The exact number of features
        """
        return len(self.columns)

    def n_replicates(self) -> Mapping[str, int]:
        """ """
        return self.reset_index().groupby("name").count()["well"].to_dict()

    def xy(self) -> Tup[np.array, np.array]:
        """Returns a tuple of (features, names)."""
        return self.values, self.names().values

    def cross(self, column: str) -> Iterator[Tup[WellFrame, WellFrame]]:
        """ """
        for value in self[column].unique():
            yield self[self[column] == value], self[self[column] != value]

    def bootstrap(self, n: Optional[int] = None) -> WellFrame:
        """
        Subsamples WITH replacement.

        Args:
            n: If None, uses len(self)

        Returns:

        """
        n = len(self) if n is None else n
        return self.__class__.of(self.sample(n, replace=True))

    def subsample(self, n: Optional[int] = None) -> WellFrame:
        """
        Subsamples WITHOUT replacement.

        Args:
          n: If None, uses len(self)

        Returns:

        """
        if n is None:
            return self
        return self.__class__.of(self.sample(n, replace=False))

    def subsample_even(self, n: Optional[int] = None) -> WellFrame:
        """
        Subsamples WITHOUT replacement,
        keeping the min replicate counts for any name, for each name

        Args:
            n: If None, uses the max permitted

        Returns:

        """
        if n is None:
            n = min(self.n_replicates().values())
        return WellFrame.concat(
            *[self.with_name(name).subsample(n) for name in self.unique_names()]
        )

    def names(self) -> pd.Index:
        """ """
        return self.index.get_level_values("name")

    def display_names(self) -> pd.Index:
        """Gets the display_name column."""
        return self.index.get_level_values("display_name")

    def unique_names(self) -> Sequence[str]:
        """ """
        return self.index.get_level_values("name").unique().tolist()

    def unique_runs(self) -> Set[int]:
        """ """
        return self["run"].unique().tolist()

    def with_name(self, name: Union[Sequence[str], Set[str], str]) -> WellFrame:
        """
        Selects only the wells matching a name.

        Args:
            name: An entry in the name column, or list or set of them

        Returns:
            A modified copy of this WellFrame

        """
        name = Tools.to_true_iterable(name)
        return self.__class__.retype(self[self.names().isin(name)])

    def with_well(self, wells: Union[Iterable[Union[int, Wells]], Wells, int]):
        """


        Args:
            wells:

        Returns:

        """
        wells = InternalTools.fetch_all_ids_unchecked(Wells, Tools.to_true_iterable(wells))
        return self.__class__.retype(self[self["well"].isin(wells)])

    def with_run(self, runs: Union[Iterable[RunLike], RunLike]) -> WellFrame:
        """
        Selects only the wells matching a run ID.

        Args:
            runs: A run ID, or list or set of them

        Returns:
            A modified copy of this WellFrame

        """
        runs = set(Tools.run_ids_unchecked(runs))
        return self.__class__.retype(self[self["run"].isin(runs)])

    def without_run(self, runs: Union[int, Set[int]]) -> WellFrame:
        """


        Args:
            runs:

        Returns:

        """
        runs = set(Tools.run_ids_unchecked(runs))
        return self.__class__.retype(self[~self["run"].isin(runs)])

    def apply_by_name(self, function) -> WellFrame:
        """


        Args:
            function:

        Returns:

        """
        return self.__class__.of(self.group_by(level="name", sort=False).apply(function))

    def apply_by_run(self, function) -> WellFrame:
        """


        Args:
            function:

        Returns:

        """
        return self.__class__.of(self.group_by(level="run", sort=False).apply(function))

    def without_treatments(self) -> WellFrame:
        """
        Returns only the wells that were not treated with batches.

        Returns:

        """
        return self[self["b_ids"].map(str) == "[]"]

    def with_treatments_all_only(self, treatments: Treatments) -> WellFrame:
        """


        Args:
            treatments: Treatments:

        Returns:

        """
        treatments = Treatments.of(treatments)
        return self[self["treatments"] == treatments]

    def with_treatments_any_only(self, treatments: Treatments) -> WellFrame:
        """


        Args:
            treatments: Treatments:

        Returns:

        """
        treatments = Treatments.of(treatments)
        z = self.__class__.retype(
            self[self["treatments"].map(lambda ts: any([t in ts for t in treatments]))]
        )
        return self.__class__.retype(
            z[z["treatments"].map(lambda ts: all([t in treatments for t in ts]))]
        )

    def with_treatments_any(self, treatments: Treatments) -> WellFrame:
        """


        Args:
            treatments: Treatments:

        Returns:

        """
        treatments = Treatments.of(treatments)
        return self.__class__.retype(
            self[self["treatments"].map(lambda ts: any([t in ts for t in treatments]))]
        )

    def with_treatments_all(self, treatments: Treatments) -> WellFrame:
        """


        Args:
            treatments: Treatments:

        Returns:

        """
        treatments = Treatments.of(treatments)
        return self.__class__.retype(
            self[self["treatments"].map(lambda ts: all([t in ts for t in treatments]))]
        )

    def with_compound_at_dose_any(
        self, compound: Union[Compounds, int, str], dose: SupportsFloat
    ) -> WellFrame:
        """


        Args:
            compound:
            dose:

        Returns:

        """
        compound = Compounds.fetch(compound)
        dose = float(dose)
        d = self.with_compounds_all(compound)
        d = d[d["treatments"].map(lambda ts: dose in [t.dose for t in ts if t.cid == compound.id])]
        return self.__class__.retype(d)

    def with_compounds_all_only(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        """


        Args:
            compounds:

        Returns:

        """
        compounds = set(InternalTools.fetch_all_ids(Compounds, compounds))
        return self.__class__.retype(self[self["c_ids"].map(lambda cids: set(cids) == compounds)])

    def with_compounds_any_only(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        """


        Args:
            compounds:

        Returns:

        """
        compounds = set(InternalTools.fetch_all_ids(Compounds, compounds))
        z = self.__class__.retype(
            self[self["c_ids"].map(lambda cids: any([c in cids for c in compounds]))]
        )
        return self.__class__.retype(
            z[z["c_ids"].map(lambda cids: all([c in compounds for c in cids]))]
        )

    def with_batches_all_only(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        """


        Args:
            batches:

        Returns:

        """
        batches = set(InternalTools.fetch_all_ids(Batches, batches))
        return self.__class__.retype(self[self["b_ids"].map(lambda bids: set(bids) == batches)])

    def with_batches_any_only(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        """


        Args:
            batches:

        Returns:

        """
        batches = set(InternalTools.fetch_all_ids(Batches, batches))
        z = self.__class__.retype(
            self[self["b_ids"].map(lambda bids: any([c in bids for c in batches]))]
        )
        return self.__class__.retype(
            z[z["b_ids"].map(lambda bids: all([c in batches for c in bids]))]
        )

    def with_compounds_all(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        """


        Args:
            compounds:

        Returns:

        """
        compounds = tuple(InternalTools.fetch_all_ids(Compounds, compounds))
        return self.__class__.retype(
            self[self["c_ids"].map(lambda cids: all([c in cids for c in compounds]))]
        )

    def with_batches_all(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        """


        Args:
            batches:

        Returns:

        """
        batches = tuple(InternalTools.fetch_all_ids(Batches, batches))
        return self.__class__.retype(
            self[self["b_ids"].map(lambda bids: all([b in bids for b in batches]))]
        )

    def with_compounds_any(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        """


        Args:
            compounds:

        Returns:

        """
        compounds = InternalTools.fetch_all_ids(Compounds, compounds)
        return self.__class__.retype(
            self[self["c_ids"].map(lambda cids: any([c in cids for c in compounds]))]
        )

    def with_batches_any(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        """


        Args:
            batches:

        Returns:

        """
        batches = InternalTools.fetch_all_ids(Batches, batches)
        return self.__class__.retype(
            self[self["b_ids"].map(lambda bids: any([b in bids for b in batches]))]
        )

    def without_compounds_any(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        """


        Args:
            compounds:

        Returns:

        """
        compounds = InternalTools.fetch_all_ids(Compounds, compounds)
        return self.__class__.retype(
            self[self["c_ids"].map(lambda cids: all([c not in cids for c in compounds]))]
        )

    def without_batches_any(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        """


        Args:
            batches:

        Returns:

        """
        batches = InternalTools.fetch_all_ids(Batches, batches)
        return self.__class__.retype(
            self[self["b_ids"].map(lambda bids: all([b not in bids for b in batches]))]
        )

    def without_compounds_all(
        self, compounds: Union[int, str, Compounds, Set[Union[int, str, Compounds]]]
    ) -> WellFrame:
        """


        Args:
            compounds:

        Returns:

        """
        compounds = tuple(InternalTools.fetch_all_ids(Compounds, compounds))
        return self.__class__.retype(
            self[self["c_ids"].map(lambda cids: any([c not in cids for c in compounds]))]
        )

    def without_batches_all(
        self, batches: Union[int, str, Batches, Set[Union[int, str, Batches]]]
    ) -> WellFrame:
        """


        Args:
            batches:

        Returns:

        """
        batches = tuple(InternalTools.fetch_all_ids(Batches, batches))
        return self.__class__.retype(
            self[self["b_ids"].map(lambda bids: any([b not in bids for b in batches]))]
        )

    def with_controls(
        self, names: Union[None, str, Iterable[str]] = None, **attributes
    ) -> WellFrame:
        """
        Returns the subset of the wellframe containing the controls meeting certain criteria.
        See optional arguments for WellFrames.controls_matching for details on these criteria.

        Args:
            names:
            **attributes:

        Returns:

        """
        matches = self.unique_controls_matching(names, **attributes)
        return self.__class__.retype(self[self["control_type"].isin(matches)])

    def without_controls(
        self, names: Union[None, str, Iterable[str]] = None, **attributes
    ) -> WellFrame:
        """


        Args:
            names:
            **attributes:

        Returns:

        """
        matches = self.unique_controls_matching(names, **attributes)
        return self.__class__.retype(self[~self["control_type"].isin(matches)])

    def unique_controls_matching(
        self,
        names: Union[None, ControlTypes, str, int, Set[Union[ControlTypes, int, str]]] = None,
        **attributes,
    ) -> Set[str]:
        """
        Return the control types in this WellFrame matching ALL of the specified criteria.

        Args:
            names: The set of allowed control_types
            attributes: Any key-value pairs mapping an attribute of ControlTypes to a required value

        Returns:

        """
        return {
            c.name
            for c in ValarTools.controls_matching_all(names, **attributes)
            if c.name in self["control_type"].unique()
        }

    def sort_pretty(self, more_controls: Optional[Set[str]] = None) -> WellFrame:
        """
        Sorts by the names with a natural sort, but putting control names at the top.
        To do this, relies on the name to determine whether a row is a control.

        Args:
            more_controls:

        Returns:

        """
        return self.__class__.retype(
            ValarTools.sort_controls_first(self, "name", more_controls=more_controls)
        )

    def sort_first(self, names: Sequence[str]):
        """
        Sorts these names first, keeping the rest in the same order.

        Args:
            names:

        Returns:

        """
        return self.__class__.retype(ValarTools.sort_first(self, self["name"], names))

    def sort_values(
        self, by: Union[str, Sequence[str]], ascending: bool = True, **kwargs
    ) -> Union[WellFrame, pd.DataFrame]:
        """
        Either handles special cases or delegates to the superclass.
        WARNING: If inplace, na_position, kind, or axis is SET (even if default):
                Will simply delegate to the superclass method and return a plain pd.DataFrame.

        Args:
            by: What to sort by
            ascending: Pretty obvious
            kwargs: Delegated to DataFrame.sort_values

        Returns:
            Either a new WellFrame or a DataFrame for other cases.

        """
        if any([k in kwargs for k in ["axis", "inplace", "kind", "na_position"]]):
            return super().sort_values(by, ascending=ascending, **kwargs)
        return self.__class__.retype(
            pd.DataFrame.sort_values(self.__class__.vanilla(self), by, ascending=ascending)
        )

    def sort_standard(self) -> WellFrame:
        """
        Sorts by so-called 'important' information, then by run (datetime_run), then by well index.
        In order: control_type, treatments, variant_name, n_fish, age, well_group, datetime_run, well_index

        Returns:

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

        ``function`` can be any of three types:
            - None     ==> will sort by 'name'
            - str      ==> will sort by that column by delegating to pd.sort_values
            - function ==> preferred. See below.

        Args:
            function: A function mapping the pd.Series of each row to a value that will be used as input to pd.sort_values

        Returns:
            The sorted WellFrame

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

    def agg_by_name(self, function: Callable[[pd.DataFrame], pd.DataFrame] = np.mean) -> WellFrame:
        """
        Aggregates by the 'name' column alone. All other meta column will be dropped.

        Args:
            function:

        Returns:
            The aggregated WellFrame

        """
        return self.__class__.of(self.untyped().groupby(level="name", sort=False).apply(function))

    def agg_by_important(
        self, function: Callable[[pd.DataFrame], pd.DataFrame] = np.mean
    ) -> WellFrame:
        """
        Aggregates by battery, Sauron config, name, pack (if any), size (if any) and information about the contents of the well.
        Note that this excludes display_name.
        Meta columns not aggregated on (not in the above list) will be dropped.

        Args:
            function:

        Returns:
            The aggregated WellFrame

        """
        well_cols = WellFrameColumnTools.unimportant_cols
        return self._agg_by(function, well_cols)

    def agg_by_all(self, function: Callable[[pd.DataFrame], pd.DataFrame] = np.mean) -> WellFrame:
        """
        Aggregates by everything except for well, well_index, well_label, row, and column.
        All meta columns that are excluded will be dropped.

        Args:
            function:

        Returns:
            The aggregated df

        """
        well_cols = WellFrameColumnTools.well_position_cols
        return self._agg_by(function, well_cols)

    def agg_by_run(self, function: Callable[[pd.DataFrame], pd.DataFrame] = np.mean) -> WellFrame:
        """
        Aggregates by the 'run' column alone.
        All other meta column will be dropped.

        Args:
            function:

        Returns:
            The aggregated df

        """
        return self.__class__.of(self.groupby(level="run", sort=False).apply(function))

    def dose_to_size(
        self, fallback: Any = pd.NA, transform: Callable[[float], Any] = lambda s: s
    ) -> WellFrame:
        """


        Args:
            fallback:
            transform:

        Returns:
            A copy
        """

        def gsize(ts: Treatments):
            if ts.len() == 0:
                return fallback
            elif ts.len() > 1:
                raise MultipleMatchesError(f"Multiple treatments {ts}")
            else:
                return transform(ts[0].dose)

        return self.set_meta("size", self["treatments"].map(gsize).map(str))

    def smooth(
        self,
        function=lambda s: s.mean(),
        window_size: int = 10,
        window_type: Optional[str] = "triang",
    ) -> WellFrame:
        """
        Applies a function along a sliding window of the features using pd.DataFrame.rolling.

        Args:
            function:
            window_size: The number of features in each window
            window_type: An argument to pd.DataFrame.rolling ``win_type``

        Returns:
            The same WellFrame with smoothed features

        """
        results = function(self.rolling(window_size, axis=1, min_periods=1, win_type=window_type))
        return self.__with_new_features(results)

    def z_score(self, control_type: Union[None, str, int, ControlTypes]) -> WellFrame:
        """
        Takes Z-score of the features with respect the specified control wells.
        Concretely, calculates: (well - controls.mean()) / all_wells.std()

        Args:
            control_type: The name, ID, or instance of a ControlTypes

        Returns:
            The same WellFrame with new features

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

        Args:
            function: Maps (whole_df, controls_only) to a new DataFrame
            control_type: The name, ID, or object for a ControlType.
                          If None, is taken to mean all controls (which is potentially weird).

        Returns:
            A copy

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

        Args:
            name_to_subtract: The entry in the name column

        Returns:
            The same WellFrame

        """
        return self.name_subtract(
            lambda case, control: (case - control.mean()) / case.std(), name_to_subtract
        )

    def z_score_by_run(self, run_to_subtract: Optional[int]) -> WellFrame:
        """
        Calculates Z-scores with respect to rows with the run column matching pack_to_subtract`.
        See WellFrame.z_score for more info.

        Args:
            run_to_subtract: A run ID

        Returns:
          The same WellFrame

        """
        return self.run_subtract(
            lambda case, control: (case - control.mean()) / case.std(), run_to_subtract
        )

    def name_subtract(
        self,
        function: Callable[[pd.DataFrame, pd.DataFrame], pd.DataFrame],
        name: Optional[str] = None,
    ) -> WellFrame:
        """
        Analogous to control_subtract, but subtracts with respect to names (in the index) rather than actual control types.

        Args:
            function: Maps (whole_df, controls_only) to a new DataFrame
            name: The string in this_df.names()

        Returns:
            A new WellFrame

        """
        control_df = self.with_name(name)
        results = function(self, control_df)
        return self.__with_new_features(results)

    def run_subtract(
        self,
        function: Callable[[pd.DataFrame, pd.DataFrame], pd.DataFrame],
        run: Optional[int] = None,
    ) -> WellFrame:
        """
        Analogous to control_subtract, but subtracts with respect to runs (in the index) rather than actual control types.

        Args:
            function: Maps (whole_df, controls_only) to a new DataFrame
            run: The ID

        Returns:
            A new WellFrame

        """
        control_df = self.with_run(run)
        results = function(self, control_df)
        return self.__with_new_features(results)

    def unique_batch_ids(self) -> Sequence[int]:
        """
        Returns a list of the unique batches.id values among all wells.
        The values will be in the same order as they appear the rows (and then by their order in Treatments).

        Returns:

        """
        return Tools.unique([item for sublist in self["b_ids"] for item in sublist])

    def unique_compound_ids(self) -> Sequence[int]:
        """
        Returns a list of the unique compounds.id values among all wells.
        The values will be in the same order as they appear the rows (and then by their order in Treatments).

        Returns:

        """
        return Tools.unique([item for sublist in self["c_ids"] for item in sublist])

    def unique_compound_names(self) -> Sequence[str]:
        """
        Returns unique compound names in the order they appear in this WellFrame (by row, then by item in the Treatments instances).
            - If `namer` is passed, transforms self['treatments'] and returns the result
            - If `namer is not passed, returns the unique items in self['compound_names'] in order.

        Args:
            namer: None or a CompoundNamer

        Returns:
            A list of the compound names as strings, in order

        """
        return Tools.unique([item for sublist in self["compound_names"] for item in sublist])

    def unique_treatments(self) -> Treatments:
        """
        Returns a list of the unique Treatment values among all wells.
        The values will be in the same order as they appear the rows (and then by their order in Treatments).

        Returns:

        """
        return Treatments(
            Tools.unique([item for sublist in self["treatments"] for item in sublist])
        )

    def unique_batch_hashes(self) -> Sequence[str]:
        """
        Returns a list of the unique batch.lookup_hash values among all wells.
        The values will be in the same order as they appear the rows (and then by their order in Treatments).

        Returns:

        """
        return Tools.unique([item.bhash for sublist in self["treatments"] for item in sublist])

    def dose_of(self, batch: Union[Batches, str, int]) -> pd.Series:
        """
        Returns a Series of the specified batch, with 0.0 if the batch is not present.

        Args:
            batch: A batch ID, lookup_hash, or instance

        Returns:
            A Pandas Series with float values in which the entries match the rows in this WellFrame

        """
        batch = Batches.fetch(batch).lookup_hash

        def dof(treatments):
            ts = {t.bhash: t.dose for t in treatments}
            if batch in ts:
                return ts[batch]
            else:
                return 0.0

        return self["treatments"].map(dof)

    def constrain(self, lower: float, upper: float) -> WellFrame:
        """
        Returns a new WellFrame with the features bound between lower and upper.

        Args:
            lower: float:
            upper: float:

        Returns:

        """
        results = self.clip(lower, upper)
        return self.__with_new_features(results)

    def threshold_zeros(self, lower: float) -> WellFrame:
        """
        Returns a new WellFrame with features values under a certain (absolute value) threshold set to 0.

        Args:
            lower: float:

        Returns:

        """
        results = (self.abs() >= lower) * self.values
        return self.__with_new_features(results)

    def with_new_names(
        self, namer: Union[pd.Series, pd.Index, Sequence[str], WellNamer]
    ) -> WellFrame:
        """
        Returns a new WellFrame with new names set.

        Args:
            namer:

        Returns:
            A copy
        """
        return self._with_new("name", namer, str)

    def with_new_display_names(
        self, namer: Union[pd.Series, pd.Index, Sequence[str], WellNamer]
    ) -> WellFrame:
        """
        Returns a new WellFrame with new display_names set.

        Args:
            namer:

        Returns:
            A copy

        """
        return self._with_new("display_name", namer, str)

    def with_new_compound_names(self, namer: Optional[CompoundNamer]) -> WellFrame:
        """
        Returns a new WellFrame with the 'compound_names' meta column set.

        Args:
            namer:

        Returns:
            A copy
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

        Args:
            namer:

        Returns:
            A copy
        """
        return self._with_new("pack", namer, str)

    def with_new_sizes(
        self, namer: Union[pd.Series, pd.Index, Sequence[str], WellNamer]
    ) -> WellFrame:
        """
        Returns a new WellFrame with new sizes set.

        Args:
            namer:

        Returns:
            A copy
        """
        return self._with_new("size", namer, str)

    def with_new(self, meta_col: str, setter: Union[pd.Series, pd.Index, Sequence[str], WellNamer]):
        """


        Args:
            meta_col: str:
            setter:

        Returns:
            A copy
        """
        if meta_col not in WellFrameColumnTools.special_cols:
            raise RefusingRequestError(
                f"Can only set reserved cols ({WellFrameColumnTools.special_cols}), not {meta_col}. Use set_meta_col."
            )

        dtype = tuple if meta_col == "compound_namer" else str
        return self._with_new(meta_col, setter, dtype)

    def _with_new(self, col, namer, dtype):
        """


        Args:
            col:
            namer:
            dtype:

        Returns:
            A copy
        """
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

    def set_meta(self, name: str, values: Any) -> WellFrame:
        """
        Returns a copy with a meta/index column set

        Args:
            name: str:
            values: Any:

        Returns:
            A copy
        """
        df = self.copy().reset_index()
        df[name] = values
        return self.__class__.of(df)

    @classmethod
    def retype(cls, df: pd.DataFrame) -> WellFrame:
        """
        Sets the __class__ of `df` to WellFrame.
        Instantaneous and in-place.
        Does not perform any checks; see `of` for a safer but slower method.

        Args:
          df: A Pandas DataFrame or subclass
          df: pd.DataFrame:

        Returns:
          A WellFrame

        """
        df.__class__ = cls
        # noinspection PyTypeChecker
        return df

    @classmethod
    def new_empty(cls, n_features: int) -> WellFrame:
        """
        Returns a new empty DataFrame.

        Args:
            n_features: int:

        Returns:

        """
        cols = WellFrameColumns.reserved_names
        df = pd.DataFrame(columns=[*cols, *np.arange(0, n_features)])
        df = df.reset_index().set_index(cols)
        return cls.of(df)

    @classmethod
    def concat(cls, *wfs: Sequence[WellFrame]) -> WellFrame:
        """
        Concatenates WellFrames vertically.

        Args:
            *wfs: A var-args list of WellFrames or DataFrames

        Returns:
            A new WellFrame

        """
        return cls.of(pd.concat(wfs, sort=False))

    @classmethod
    def assemble(cls, meta: pd.DataFrame, features: pd.DataFrame) -> WellFrame:
        """
        Builds a new WellFrame from meta and features. Requires that both are in the same order
        The meta columns will then be made into index columns.
        WARNING: Ignores and discards indices on the features

        Args:
            meta: pd.DataFrame:
            features: pd.DataFrame:

        Returns:

        """
        meta = cls.of(meta).reset_index()
        features = features.reset_index(drop=True)
        df = pd.merge(meta, features, left_index=True, right_index=True)
        return cls.of(df)

    def _agg_by(
        self, function: Callable[[pd.DataFrame], pd.DataFrame] = np.mean, exclude: Set[str] = None
    ) -> WellFrame:
        """
        Aggregate and calculate on groups.
        This is hidden because it's dangerously misleading: the 2nd param is columns to exclude, not include.

        Args:
            function:
            exclude:

        Returns:

        """
        if exclude is None:
            exclude = []
        df = self.copy()  # we'll change this inplace
        # columns that can be null
        # we have to replace these or Pandas groupby will drop rows where it's None or NaN
        df = WellFrameColumnTools.from_nan(df.untyped().reset_index())
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


__all__ = ["WellFrame", "InvalidWellFrameError"]
