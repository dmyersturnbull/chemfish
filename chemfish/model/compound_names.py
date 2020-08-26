from chemfish.core.core_imports import *


@abcd.auto_repr_str()
@abcd.auto_eq()
class CompoundNamer(metaclass=abc.ABCMeta):
    """
    A way to look up and choose a single name for any compound (or give up).
    Has a slightly weird interface to make querying from Valar more performant:
        - fetch returns a map from compound IDs to selected names
        - map_to calls fetch and returns a list of names in the same order as the list passed

    Args:

    Returns:

    """

    def __init__(self, as_of: Optional[datetime] = datetime.now()):
        self.as_of = as_of

    def get(self, compound: NullableCompoundLike) -> Optional[str]:
        """
        Get a single name for a single compound, or None if a name wasn't found.

        Args:
          compound: NullableCompoundLike:

        Returns:

        """
        if compound is None:
            return None
        dct = list(self.fetch(compound).values())
        if len(dct) == 0:
            return None
        return dct[0]

    def map_to(self, compounds: NullableCompoundsLike) -> Sequence[Optional[str]]:
        """
        Maps each compound (or null) in a (non-nested) sequence to its name or None.
        Ex:
        ```
        namer.map([1, 1, None])
        # returns ['water', 'water', None]
        ```

        Args:
          compounds: NullableCompoundsLike:

        Returns:

        """
        dct = self.fetch(compounds)
        return [
            dct.get(c)
            for c in InternalTools.fetch_all_ids_unchecked(Compounds, compounds, keep_none=True)
        ]

    def map_2d(
        self, compounds: Iterable[Iterable[Optional[CompoundLike]]]
    ) -> Sequence[Sequence[Optional[str]]]:
        """
        Maps a list of lists/tuples of compounds.
        This is notably useful for processing wells on a plate, where each well has a list of compounds.
        Ex:
        ```
        namer.map_2d([1, [1, Compounds.fetch(126)], [], None])
        # returns [['water'], ['water', 'Haloperidol'], [], [None]]
        ```

        Args:
          compounds: Iterable[Iterable[Optional[CompoundLike]]]:

        Returns:

        """
        dct = self.fetch(self._flatten_to_id_set(compounds))
        lst = []
        for clist in compounds:
            clist = InternalTools.fetch_all_ids_unchecked(Compounds, clist, keep_none=True)
            lst.append([dct.get(c) for c in clist])
        return lst

    def __call__(self, compound_ids: NullableCompoundsLike):
        return self.fetch(compound_ids)

    @abcd.abstractmethod
    def fetch(self, compound_ids: NullableCompoundsLike) -> Mapping[int, str]:
        """


        Args:
          compound_ids: NullableCompoundsLike:

        Returns:

        """
        raise NotImplementedError()

    def _flatten_to_id_set(self, compounds):
        """


        Args:
          compounds:

        Returns:

        """
        cs = InternalTools.flatten_smart(compounds)
        return set(InternalTools.fetch_all_ids_unchecked(Compounds, cs, keep_none=True))


@abcd.auto_repr_str()
@abcd.auto_eq()
class BatchNamer(metaclass=abc.ABCMeta):
    """ """
    def __init__(self, as_of: Optional[datetime] = datetime.now()):
        self.as_of = as_of

    @abcd.abstractmethod
    def fetch(self, batches: BatchesLike) -> Mapping[int, str]:
        """


        Args:
          batches: BatchesLike:

        Returns:

        """
        raise NotImplementedError()

    def _flatten_to_id_set(self, batches):
        """


        Args:
          batches:

        Returns:

        """
        if isinstance(batches, int) or isinstance(batches, str):
            return [batches]
        all_cpids = set(InternalTools.flatten_smart(batches))
        return set(InternalTools.fetch_all_ids_unchecked(Batches, all_cpids))


class BatchNamerWrapping(BatchNamer):
    """Get batch names from compound names, falling back to batch tags."""

    def __init__(self, compound_namer: CompoundNamer, use_bid_if_empty: bool = False):
        super().__init__(compound_namer.as_of)
        self.compound_namer = compound_namer
        self.use_bid_if_empty = use_bid_if_empty

    def fetch(self, batches: BatchesLike) -> Mapping[int, str]:
        """


        Args:
          batches: BatchesLike:

        Returns:

        """
        all_batches = Batches.fetch_all(self._flatten_to_id_set(batches))
        batches_with_cids = [batch for batch in all_batches if batch.compound_id is not None]
        cids_to_batches = Tools.multidict(batches_with_cids, "compound_id")
        dct = {batch.id: batch.tag for batch in all_batches if batch.compound_id is None}
        for cid, name in self.compound_namer.fetch(cids_to_batches.keys()).items():
            for batch in cids_to_batches[cid]:
                dct[batch.id] = name
        if self.use_bid_if_empty:
            dct = {bid: "b" + str(bid) if name is None else name for bid, name in dct.items()}
        return dct


class BatchNamerTag(BatchNamer):
    """ """
    def fetch(self, batches: BatchesLike) -> Mapping[int, str]:
        """


        Args:
          batches: BatchesLike:

        Returns:

        """
        return {b.id: b.tag for b in Batches.fetch_all(self._flatten_to_id_set(batches))}


class CidCompoundNamer(CompoundNamer):
    """ """
    def fetch(self, compound_ids: CompoundsLike) -> Mapping[int, str]:
        """


        Args:
          compound_ids: CompoundsLike:

        Returns:

        """
        return {c: c for c in self._flatten_to_id_set(compound_ids)}


class SingleThingCompoundNamer(CompoundNamer):
    """ """
    def __init__(self, attribute: str, as_of: datetime = datetime.now()):
        super().__init__(as_of)
        self.attribute = attribute

    def fetch(self, compound_ids: CompoundsLike) -> Mapping[int, str]:
        """


        Args:
          compound_ids: CompoundsLike:

        Returns:

        """
        all_cpids = self._flatten_to_id_set(compound_ids)
        return {
            compound.id: getattr(compound, self.attribute)
            for compound in Compounds.select().where(Compounds.id << all_cpids)
        }


class TieredCompoundNamer(CompoundNamer):
    """Checks sources in order, preferring sources with lower index."""

    # high-precedence, manual, drugbank:5.0.10:secondary_id, chembl:api:fda_name, chembl:api:inn_name, chembl:api:usan_name, valinor, dmso_stocks, chembl:api:preferred_name
    elegant_sources: Sequence[RefLike] = [x for x in Refs.fetch_all_or_none(
        InternalTools.load_resource("chem", "refs_few.lines")
    ) if x is not None]
    elegant_sources_extended: Sequence[RefLike] = [x for x in Refs.fetch_all_or_none(
        InternalTools.load_resource("chem", "refs_more.lines")
    ) if x is not None]

    def __init__(
        self,
        sources: Sequence[RefLike] = None,
        max_length: Optional[int] = None,
        use_cid_if_empty: bool = False,
        as_of: datetime = datetime.now(),
        allow_numeric: bool = False,
        transform: Optional[Callable[[str], str]] = None,
    ):
        super().__init__(as_of)
        self.sources = [r.id for r in self._choose_refs(sources)]
        self.max_length = max_length
        self.use_cid_if_empty = use_cid_if_empty
        self.allow_numeric = allow_numeric
        self.transform = lambda s: s if transform is None else transform

    @classmethod
    def _choose_refs(cls, sources: Optional[Sequence[RefLike]] = None) -> Sequence[Refs]:
        """


        Args:
          sources:

        Returns:

        """
        if isinstance(sources, str):
            sources = InternalTools.load_resource("chem", Path(sources).with_suffix(".lines"))
        if sources is not None and not Tools.is_true_iterable(sources):
            sources = [sources]
        return Refs.fetch_all(TieredCompoundNamer.elegant_sources if sources is None else sources)

    def fetch(self, compound_ids: CompoundsLike) -> Mapping[int, str]:
        """


        Args:
          compound_ids: CompoundsLike:

        Returns:

        """
        all_cpids = self._flatten_to_id_set(compound_ids)
        query = (
            CompoundLabels.select(CompoundLabels)
            .where(CompoundLabels.compound_id << all_cpids)
            .where(CompoundLabels.ref_id << self.sources)
        )
        if self.as_of is not None:
            query = query.where(CompoundLabels.created < self.as_of)
        query = query.order_by(CompoundLabels.ref_id.desc(), CompoundLabels.created)
        data = {x: "c" + str(x) if self.use_cid_if_empty else None for x in all_cpids}
        indices = {x: 99999 for x in all_cpids}
        for cn in query:
            ind = self.sources.index(cn.ref_id)
            if (
                ind < indices[cn.compound_id]
                and (self.max_length is None or len(cn.name) < self.max_length)
                and (not cn.name.isdigit() or self.allow_numeric)
            ):
                data[cn.compound_id] = cn.name
                indices[cn.compound_id] = ind
        return {k: self.transform(v) for k, v in data.items()}


class CompoundNamerEmpty(BatchNamer):
    """ """
    def fetch(self, compound_ids: CompoundsLike) -> Mapping[int, str]:
        """


        Args:
          compound_ids: CompoundsLike:

        Returns:

        """
        return {}


class BatchNamerEmpty(BatchNamer):
    """ """
    def fetch(self, batches: BatchesLike) -> Mapping[int, str]:
        """


        Args:
          batches: BatchesLike:

        Returns:

        """
        return {}


@abcd.copy_docstring(TieredCompoundNamer)
class CleaningTieredCompoundNamer(TieredCompoundNamer):
    """ """
    def __init__(
        self,
        sources: Sequence[int] = None,
        max_length: Optional[int] = None,
        use_cid_if_empty: bool = False,
        as_of: datetime = datetime.now(),
        allow_numeric: bool = False,
        transform: Optional[Callable[[str], str]] = None,
    ):
        cleaner = CompoundNameCleaner()
        transform = lambda s: cleaner.clean(transform(s))
        super().__init__(sources, max_length, use_cid_if_empty, as_of, allow_numeric, transform)


class CompoundNameCleaner:
    """
    Contains an ordered list of substrings of compound names to discard.
    By default, will use resources/chem/unimportant_substrings.lines.txt
    Also replaces names of Greek letters with their Unicode equivalents.

    Args:

    Returns:

    """

    def __init__(self, to_discard: Optional[Set[str]] = None):
        self.to_discard = to_discard
        if self.to_discard is None:
            self.to_discard = InternalTools.load_resource(
                "chem", "unimportant_substrings.lines.txt"
            )

    def clean(self, thestring: Optional[str]) -> Optional[str]:
        """


        Args:
          thestring: Optional[str]:

        Returns:

        """
        if thestring is None:
            return None
        if not isinstance(thestring, str):
            return thestring
        thestring = Tools.fix_greek(thestring)
        for e in self.to_discard:
            if thestring.lower().endswith(" " + e.lower()):
                thestring = thestring[: -len(e)].strip()
                break
            elif thestring.lower().endswith(" " + e.lower() + " (-)"):
                thestring = thestring[: -len(e)].strip() + " (-)"
                break
            elif thestring.lower().endswith(" " + e.lower() + " (+)"):
                thestring = thestring[: -len(e)].strip() + " (+)"
                break
        thestring = thestring.strip()
        if len(thestring) > 4:
            return thestring.lower()
        return thestring


class CompoundNamers:
    """ """
    @classmethod
    def empty(cls) -> CompoundNamerEmpty:
        """ """
        return CompoundNamerEmpty()

    @classmethod
    def inchikey(cls, as_of: Optional[datetime] = None):
        """


        Args:
          as_of: Optional[datetime]:  (Default value = None)

        Returns:

        """
        return SingleThingCompoundNamer("inchikey", as_of)

    @classmethod
    def chembl(cls, as_of: Optional[datetime] = None):
        """


        Args:
          as_of: Optional[datetime]:  (Default value = None)

        Returns:

        """
        return SingleThingCompoundNamer("chembl", as_of)

    @classmethod
    def tiered(
        cls,
        sources: Optional[Sequence[RefLike]] = None,
        max_length: int = 30,
        as_of: Optional[datetime] = None,
    ):
        """


        Args:
          sources:
          max_length: int:  (Default value = 30)
          as_of: Optional[datetime]:  (Default value = None)

        Returns:

        """
        return TieredCompoundNamer(sources, max_length=max_length, as_of=as_of)

    @classmethod
    def tiered_fallback(
        cls,
        sources: Optional[Sequence[RefLike]] = None,
        max_length: int = 30,
        as_of: Optional[datetime] = None,
    ):
        """


        Args:
          sources:
          max_length: int:  (Default value = 30)
          as_of: Optional[datetime]:  (Default value = None)

        Returns:

        """
        return TieredCompoundNamer(
            sources, max_length=max_length, as_of=as_of, use_cid_if_empty=True
        )

    @classmethod
    def tiered_cleaning(
        cls,
        sources: Optional[Sequence[RefLike]] = None,
        max_length: int = 30,
        as_of: Optional[datetime] = None,
    ):
        """


        Args:
          sources:
          max_length: int:  (Default value = 30)
          as_of: Optional[datetime]:  (Default value = None)

        Returns:

        """
        return CleaningTieredCompoundNamer(
            sources, max_length=max_length, as_of=as_of, use_cid_if_empty=True
        )


class BatchNamers:
    """ """
    @classmethod
    def empty(cls) -> BatchNamerEmpty:
        """ """
        return BatchNamerEmpty()

    @classmethod
    def tag(cls) -> BatchNamerTag:
        """ """
        return BatchNamerTag()

    @classmethod
    def wrapping_tiered(
        cls,
        sources: Optional[Sequence[RefLike]] = None,
        max_length: int = 30,
        as_of: Optional[datetime] = None,
    ) -> BatchNamerWrapping:
        """


        Args:
          sources:
          max_length: int:  (Default value = 30)
          as_of: Optional[datetime]:  (Default value = None)

        Returns:

        """
        return BatchNamerWrapping(
            TieredCompoundNamer(
                sources, max_length=max_length, as_of=as_of, use_cid_if_empty=False
            ),
            use_bid_if_empty=True,
        )

    @classmethod
    def wrapping_tiered_cleaning(
        cls,
        sources: Optional[Sequence[RefLike]] = None,
        max_length: int = 30,
        as_of: Optional[datetime] = None,
    ) -> BatchNamerWrapping:
        """


        Args:
          sources:
          max_length: int:  (Default value = 30)
          as_of: Optional[datetime]:  (Default value = None)

        Returns:

        """
        return BatchNamerWrapping(
            CleaningTieredCompoundNamer(
                sources, max_length=max_length, as_of=as_of, use_cid_if_empty=False
            ),
            use_bid_if_empty=True,
        )


__all__ = [
    "CompoundNamer",
    "CidCompoundNamer",
    "SingleThingCompoundNamer",
    "CompoundNamerEmpty",
    "TieredCompoundNamer",
    "CompoundNameCleaner",
    "CleaningTieredCompoundNamer",
    "BatchNamer",
    "BatchNamerWrapping",
    "BatchNamerEmpty",
    "CompoundNamers",
    "BatchNamers",
]
