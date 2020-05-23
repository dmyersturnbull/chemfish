from __future__ import annotations
from kale.core.core_imports import *
from kale.model.treatments import Treatments as Treatments
from kale.model.well_namers import WellNamer, WellNamers
from kale.model.compound_names import *
from kale.model.well_frames import *
from kale.model.features import FeatureType, FeatureTypes
from kale.model.wf_tools import *


class WellFrameBuildError(ConstructionError):
    pass


class WellFrameQuery:
    """
    Has static methods that return the fields to be used in a SELECT query for generating WellFrames.
    """

    @classmethod
    def simple(
        cls, as_of: datetime, feature: Union[Features, int, str], wheres: Iterable[ExpressionLike]
    ) -> peewee.Query:
        if isinstance(feature, FeatureType):
            feature = feature.valar_feature
        query = WellFrameQuery().build(WellFrameQuery.fields())
        query = query.where(Runs.created > as_of)
        query = query.where(Features.id == feature.id)
        for where in wheres:
            query = query.where(where)
        return query.order_by(*WellFrameQuery.sort_order())

    @classmethod
    def sort_order(cls):
        """ALWAYS use this."""
        return Wells.run_id, Wells.id

    @classmethod
    def no_fields(cls):
        return [Wells.id, Wells.run_id]

    @classmethod
    def fields(cls):
        return [
            WellTreatments,
            Batches,
            Compounds,
            Refs,
            Wells,
            ControlTypes,
            GeneticVariants,
            Runs,
            Submissions,
            Plates,
            PlateTypes,
            Users,
            SauronConfigs,
            Saurons,
            Experiments,
            Projects,
            ProjectTypes,
            Batteries,
            TemplatePlates,
            TransferPlates,
        ]

    def build(self, select_fields):
        return (
            WellTreatments.select(*select_fields)
            .join(Batches)
            .join(Compounds, JOIN.LEFT_OUTER)
            .switch(Batches)
            .join(Refs, JOIN.LEFT_OUTER)
            .switch(WellTreatments)
            .join(Wells, JOIN.RIGHT_OUTER)
            .join(ControlTypes, JOIN.LEFT_OUTER)
            .switch(Wells)
            .join(GeneticVariants, JOIN.LEFT_OUTER)
            .switch(Wells)
            .join(Runs)
            .join(Plates)
            .join(PlateTypes, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(Users, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(Submissions, JOIN.LEFT_OUTER)
            .join(SubmissionRecords, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(SauronConfigs, JOIN.LEFT_OUTER)
            .join(Saurons, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(Experiments)
            .join(Projects, JOIN.LEFT_OUTER)
            .join(ProjectTypes, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(Batteries)
            .switch(Experiments)
            .join(TemplatePlates, JOIN.LEFT_OUTER)
            .switch(Experiments)
            .join(TransferPlates, JOIN.LEFT_OUTER)
        )


class AbstractWellFrameBuilder:
    def build(self) -> WellFrame:
        raise NotImplementedError()


@abcd.auto_repr_str()
@abcd.auto_eq()
class WellFrameBuilder(AbstractWellFrameBuilder):
    """
    A builder pattern for WellFrame instances.
    There are three ways:
        - WellFrameBuilder(datetime) constructor for arbitrary wells for runs inserted before some datetime.
        - WellFrameBuilder.wells for a specific set of wells.
        - WellFrameBuilder.runs for all wells in a specific set of runs.
    """

    def __init__(self, before_datetime: Optional[datetime]) -> None:
        # hide the fact that this can be None
        self._before_datetime = before_datetime
        if before_datetime is None:
            self._wheres = []
        else:
            if before_datetime > datetime.now() - timedelta(seconds=1):
                # raise RefusingRequestError("Must query at least 1 second in the past")
                logger.warning("Should query at least 1 second in the past")
            self._wheres = [Runs.created < before_datetime]  # type: List[ExpressionLike]
        self._required_runs: Set[Runs] = set()
        self._required_wells: Set[Wells] = set()
        self._columns = dict(
            WellFrameColumns.required
        )  # type: Dict[str, Callable[[Wells, Treatments], Any]]
        self._feature = None  # type: Optional[FeatureType]
        self._namer = WellNamers.well()  # type: WellNamer
        # make sure to leave this as None!
        # we'll use self._namer if it's None
        self._display_namer: Union[None, WellNamer] = None
        self._packer: Optional[Callable[[pd.DataFrame], pd.Series]] = None
        self._sizer: Optional[Callable[[pd.DataFrame], pd.Series]] = None
        self._compound_namer = None
        self._generation: Optional[DataGeneration] = None
        self._limit: Optional[int] = None
        self._dtype = None

    @classmethod
    def wells(
        cls, wells: Union[Union[int, Wells], Iterable[Union[int, Wells, str]]]
    ) -> WellFrameBuilder:
        well_ids = Tools.wells(wells)
        wfb = cls(None).where(Wells.id << well_ids)
        wfb._required_wells = wells
        return wfb

    @classmethod
    def runs(cls, runs: RunsLike) -> WellFrameBuilder:
        runs = Tools.runs(runs)
        wfb = cls(None).where(Runs.id << runs)
        wfb._required_runs = runs
        return wfb

    def where(self, where: ExpressionsLike) -> WellFrameBuilder:
        if isinstance(where, ExpressionLike):
            self._wheres.append(where)
        elif Tools.is_true_iterable(where):
            self._wheres.extend(where)
        else:
            raise XTypeError("Strange WHERE type {}".format(type(where)))
        return self

    def with_generation(self, generation: DataGeneration) -> WellFrameBuilder:
        # I consider this currently slightly unsafe because the logic could change
        if self._generation is not None:
            raise ContradictoryRequestError("Generation {} already set".format(self._generation))
        if generation is not None:
            wheres = InternalValarTools.generation_wheres(generation)
            self._wheres.extend(wheres)
            logger.warning(
                "Restricting to generation {} with {} new WHEREs. This may not always work.".format(
                    generation, len(wheres)
                )
            )
            self._generation = generation
        return self

    def limit_to(self, limit: Optional[int]) -> WellFrameBuilder:
        """
        Gets the first `limit` rows/wells, ordered by run ID, then well index
        :param limit:
        :return:
        """
        if self._limit is not None:
            raise ContradictoryRequestError("Limit {} already set".format(self._limit))
        if limit is not None:
            logger.warning(
                "Setting limit {} in WellFrameBuilder. This may not always work.".format(limit)
            )
            self._limit = limit
        return self

    def with_feature(self, feature: Union[None, str, FeatureType], dtype=None) -> WellFrameBuilder:
        if self._feature is not None:
            raise ContradictoryRequestError("Feature {} already added".format(self._feature))
        if feature is not None:
            self._feature = FeatureTypes.of(feature)
        self._dtype = dtype
        return self

    def with_column(
        self, name: str, function: Callable[[Wells, Treatments], Any]
    ) -> WellFrameBuilder:
        """
        Add a new, non-reserved meta column.
        :param name: The name of the new column
        :param function: A function mapping the Wells instance and Treatments to the column value
        """
        if name in [c[0] for c in WellFrameColumns.reserved]:
            raise ReservedError(
                "Column name {} is reserved. See the attributes in WellFrameColumns to use one of those or choose a different name.".format(
                    name
                )
            )
        if not (isinstance(name, str)):
            raise XTypeError(
                "Name parameter must be a string. The name you provided is of type: {} ".format(
                    type(name)
                )
            )
        self._columns[name] = function
        return self

    def with_names(self, namer: WellNamer) -> WellFrameBuilder:
        """
        Set the 'name' column using this function.
        :param namer: A Namer or function mapping pd.DataFrame to a Series with str type.
        """
        self._namer = namer
        return self

    def with_display_names(self, namer: WellNamer) -> WellFrameBuilder:
        """
        Set the 'display_name' column using this function.
        :param namer: A Namer or function mapping pd.DataFrame to a Series with str type.
        """
        self._display_namer = namer
        return self

    def with_packs(self, packer: Callable[[pd.DataFrame], pd.Series]) -> WellFrameBuilder:
        """
        Set the 'pack' column using this function.
        :param packer: A function mapping pd.DataFrame to a Series with str type.
        """
        self._packer = packer
        return self

    def with_sizes(self, sizer: Callable[[pd.DataFrame], pd.Series]) -> WellFrameBuilder:
        """
        Set the 'size' column using this function.
        :param sizer: A function mapping pd.DataFrame to a Series with float type.
        :return: self
        """
        self._sizer = sizer
        return self

    def with_compound_names(self, namer: CompoundNamer) -> WellFrameBuilder:
        """
        Add a 'compound_names' column using the CompoundNamer passed.
        :param namer: A CompoundNamer
        """
        self._compound_namer = namer
        return self

    def build(self) -> WellFrame:
        """
        Builds the WellFrame, actually performing the query.
        """
        query = self._select_query()  # takes no time
        return self._build_outer(query)

    def _build_outer(self, query) -> WellFrame:
        t0 = time.monotonic()
        if self._required_runs is None or len(self._required_runs) == 0 or len(self._wheres) > 1:
            logger.info(
                "Fetching WellFrame with feature {} from {} condition{}...".format(
                    self._feature, len(self._wheres), "s" if len(self._wheres) >> 1 else ""
                )
            )
        elif len(self._required_runs) <= 50:
            logger.info(
                "Fetching WellFrame with feature {} for run(s) {} ...".format(
                    self._feature, ", ".join(["r" + str(r) for r in self._required_runs])
                )
            )
        else:
            logger.info(
                "Fetching WellFrame with feature {} for {} runs ...".format(
                    self._feature, len(self._required_runs)
                )
            )
        df = self._build_inner(query)
        logger.info(
            "Fetched WellFrame with {} rows and {} columns. Took {}s.".format(
                len(df), len(df.columns), round(time.monotonic() - t0, 1)
            )
        )
        return df

    def _build_inner(self, query) -> WellFrame:
        # run select statement
        treatments = list(query)
        if not treatments:
            raise EmptyCollectionError(
                "Query is completely empty. Please make sure the where statements and constructors have appropriate arguments."
            )
        all_wells = {t.well for t in treatments}
        all_runs = {t.well.run for t in treatments}
        assert None not in all_runs, "'None' is a run ID"
        for req in self._required_runs:
            assert req in all_runs, "Run r{} was required but not found".format(req)
        # map each well to its associated treatments
        well_to_treatments = {w: [] for w in all_wells}
        all_well_ids = {w.id for w in all_wells}
        for well in self._required_wells:
            assert well.id in all_well_ids, "Well {} was required but not found.".format(well)
        for t in treatments:
            if t.batch_id is not None:  # generally not needed
                well_to_treatments[t.well].append(t)
        # now get the features
        features = self._select_features(well_to_treatments)
        # now merge the two into a dict from wells to columns
        df = self._build_df(well_to_treatments, features)
        self._fix_df(df)
        df = self._transform_to_wf(df)
        df = self._internal_restrict_to_gen(df)
        if self._dtype is not None:
            df = df.astype(self._dtype)
        return df.sort_std()

    def _internal_limit(self, df: WellFrame) -> WellFrame:
        """
        Calling this is required for subclasses.
        WellFrameBulider._build_inner calls this itself though.
        This guarantees that the head wells are taken in the correct order.
        """
        if self._limit is not None:
            df = df.sort_values(["run", "well_index"]).head(self._limit)
        return df

    def _internal_restrict_to_gen(self, df: WellFrame) -> WellFrame:
        """
        Calling this is required for subclasses.
        WellFrameBulider._build_inner calls this itself though.
        Restricting the Peewee query cuts down on the data returned for performance,
        but does not guarantee that all runs have the correct generation.
        You need to do this too.
        """
        if self._generation is not None:
            # we already restricted the query, but now we make sure to exclude all others
            good_runs = {
                r for r in df.unique_runs() if ValarTools.generation_of(r) is self._generation
            }
            df = df.with_run(good_runs)
        return df

    def _transform_to_wf(self, df) -> WellFrame:
        df["name"] = df["well"]  # needed to have a valid WellFrame
        if self._compound_namer is None:
            df["compound_names"] = df["c_ids"].map(
                lambda cids: tuple(None for _ in range(len(cids)))
            )
        else:
            df["compound_names"] = self._compound_namer.map_to(df["c_ids"])
        df["name"] = str(df["well"]) if self._namer is None else self._namer(df)
        df["name"] = df["name"].map(str).astype(str)
        df["display_name"] = df["name"] if self._display_namer is None else self._display_namer(df)
        df["pack"] = "" if self._packer is None else self._packer(df)
        if self._sizer is not None:  # optional column
            df["size"] = self._sizer(df).astype(str)
        return WellFrame.of(df)

    def _select_query(self) -> peewee.Query:
        query = WellFrameQuery().build(WellFrameQuery.fields())
        for where in self._wheres:
            query = query.where(where)
        query = query.order_by(*WellFrameQuery.sort_order())
        if self._limit is not None:
            query = query.limit(self._limit)
        return query

    def _select_features(self, well_to_treatments):
        if self._feature is None:
            return None
        return {
            f.well.id: self._feature.calc(f, f.well)
            for f in WellFeatures.select(
                WellFeatures.id, WellFeatures.well_id, WellFeatures.type_id, WellFeatures.floats
            )
            .where(WellFeatures.type_id == self._feature.id)
            .where(WellFeatures.well_id << [w.id for w in well_to_treatments.keys()])
        }

    def _build_df(self, well_to_treatments, features):
        def capture(well: Wells, well_ts: Sequence[WellTreatments]) -> Mapping[int, np.array]:
            dct1 = OrderedDict()
            for column_name, column_fn in self._columns.items():
                dct1[column_name] = column_fn(well, well_ts)
            if features is not None:
                if well.id not in features:
                    raise NoFeaturesError(
                        "The feature {} is not defined on well {}".format(self._feature, well.id)
                    )
                if self._dtype is None:
                    dct2 = {i: mi for i, mi in enumerate(features[well.id])}
                else:
                    dct2 = {i: mi.astype(self._dtype) for i, mi in enumerate(features[well.id])}
                dct1.update(dct2)
            # noinspection PyTypeChecker
            return dct1

        return pd.DataFrame(
            [
                pd.Series(capture(well, treatments))
                for well, treatments in well_to_treatments.items()
            ]
        )

    def _fix_df(self, df):
        if len(df) > 0:
            for s in WellFrameColumnTools.int32_cols:
                df[s] = df[s].astype(np.int32)
        else:
            for c in [k for k, thefn in WellFrameColumns.required]:
                df[c] = None
            logger.warning("The WellFrame is empty")

    def __repr__(self):
        return "WellFrameBuilder(feature={}, {} wheres @ {})".format(
            self._feature, len(self._wheres), hex(id(self))
        )

    def __str__(self):
        return repr(self)


__all__ = ["WellFrame", "WellFrameBuilder", "WellFrameQuery", "InvalidWellFrameError"]
