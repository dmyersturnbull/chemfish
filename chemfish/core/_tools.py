from chemfish.core._imports import *
from chemfish.core.tools import *
from chemfish.core.valar_singleton import *

T = TypeVar("T")


@abcd.internal
class InternalTools:
    """
    A collection of utility functions for internal use in Chemfish.
    Equivalents of some of these functions are in the external-use Tools class, which delegates to this class.
    These functions do NOT depend on the Kokel Lab's specific structure of data in Valar.
    The most useful functions are:
        - Tools.run: Gets a run from a run ID, tag, name, instance, or submission hash or instance
        - Tools.runs: Delegates to Tools.run for either of the types accepted by Tools.run, or an iterable over them
    """

    @classmethod
    def verify_class_has_attrs(cls, class_, *attributes: Union[str, Iterable[str]]) -> None:
        attributes = InternalTools.flatten_smart(attributes)
        bad_attributes = [not hasattr(class_, k) for k in attributes]
        if any(bad_attributes):
            raise AttributeError("No {} attribute(s) {}".format(class_.__name__, bad_attributes))

    @classmethod
    def verify_unsed(cls, first: Collection[Any], second: Collection[Any]) -> None:
        bad = {k for k in first if k in second}
        if len(bad) > 0:
            raise AlreadyUsedError("{} were already used".format(bad))

    @classmethod
    def warn_overlap(cls, a: Collection[Any], b: Collection[Any]) -> Set[Any]:
        bad = set(a).intersection(set(b))
        if len(bad) > 0:
            logger.error("Values {} are present in both sets".format(", ".join(bad)))
        return bad

    @classmethod
    def from_kwargs(cls, kwargs, key: str, fallback: Any) -> Tup[Any, Dict[str, Any]]:
        # we'll get an error if this appears twice, so let's remove the one in kwargs
        value = kwargs[key] if key in kwargs else fallback
        return value, {k: v for k, v in kwargs.items() if k != key}

    @classmethod
    def load_resource(
        cls, *parts: Sequence[str]
    ) -> Union[
        str,
        bytes,
        Sequence[str],
        pd.DataFrame,
        Sequence[int],
        Sequence[float],
        Sequence[str],
        Mapping[str, str],
    ]:
        path = ChemfishResources.path(*parts)
        return Tools.read_any(path)

    @classmethod
    def fetch_all_ids(cls, thing_class: Type[BaseModel], things):
        """
        Fetches a single row from a table, returning the row IDs.
        Each returned row is guaranteed to exist in the table at the time the query is executed.
        :param thing_class: The table (peewee model)
        :param things: A list of lookup values -- each is an ID or unique varchar/char/enum field value
        :raises A ValarLookupError If the row was not found
        :return: The ID of the row
        """
        things = InternalTools.listify(things)
        return [thing_class.fetch(thing).id for thing in things]

    @classmethod
    def fetch_all(cls, thing_class: Type[BaseModel], things) -> Sequence[BaseModel]:
        """
        Fetches a single row from a table, returning the row instances.
        Each returned row is guaranteed to exist in the table at the time the query is executed.
        :param thing_class: The table (peewee model)
        :param things: A list of lookup values -- each is an ID or unique varchar/char/enum field value
        :raises A ValarLookupError If the row was not found
        :return: The ID of the row
        """
        # TODO make faster
        things = InternalTools.listify(things)
        return [thing_class.fetch(thing) for thing in things]

    @classmethod
    def fetch_all_ids_unchecked(cls, thing_class: Type[BaseModel], things):
        """
        Fetches a single row from a table, returning the row IDs.
        If just IDs are passed, just returns them -- this means that the return value is NOT GUARANTEED to be a valid row ID.
        :param thing_class: The table (peewee model)
        :param things: A list of lookup values -- each is an ID or unique varchar/char/enum field value
        :raises A ValarLookupError If the row was not found
        :return: The ID of the row
        """
        things = InternalTools.listify(things)
        return [
            thing if isinstance(thing, int) else thing_class.fetch(thing).id for thing in things
        ]

    @classmethod
    def fetch_all_ids_unchecked_keep_none(cls, thing_class: Type[BaseModel], things):
        things = InternalTools.listify(things)
        return [
            None
            if thing is None
            else (thing if isinstance(thing, int) else thing_class.fetch(thing).id)
            for thing in things
        ]

    @classmethod
    def fetch_id_unchecked(cls, thing_class: Type[BaseModel], thing) -> int:
        """
        Fetches a single row from a table, returning only the ID.
        If an ID is passed, just returns that -- this means that the return value is NOT GUARANTEED to be a valid row ID.
        :param thing_class: The table (peewee model)
        :param thing: The lookup value -- an ID or unique varchar/char/enum field value
        :raises A ValarLookupError If the row was not found
        :return: The ID of the row
        """
        return thing if isinstance(thing, int) else thing_class.fetch(thing).id

    @classmethod
    def flatten(cls, seq: Iterable[Any]) -> Sequence[Any]:
        y = []
        for z in seq:
            y.extend(z)
        return y

    @classmethod
    def flatten_smart(cls, seq: Iterable[Any]) -> Sequence[Any]:
        if not Tools.is_true_iterable(seq):
            return [seq]
        y = []
        for z in seq:
            if Tools.is_true_iterable(z):
                y.extend(z)
            else:
                y.append(z)
        return y

    @classmethod
    def flatten_nested(
        cls, seq: Iterable[Any], apply=lambda x: x, until=lambda x: True, discard_nulls: bool = True
    ) -> Iterator[Any]:
        for s in seq:
            if Tools.is_true_iterable(s):
                yield from InternalTools.flatten_nested(s, apply, until, discard_nulls)
            elif s is None and discard_nulls:
                pass
            elif until(s):
                yield apply(s)
            else:
                raise XTypeError("Wrong type {} for {}".format(type(s), s))

    @classmethod
    def listify(cls, sequence_or_element: Any) -> Sequence[Any]:
        """
        Makes a singleton list of a single element or returns the iterable.
        Will return (a list from) the sequence as-is if it is Iterable, not a string, and not a bytes object.
        The order of iteration from the sequence is preserved.
        :param sequence_or_element: A single element of any type, or an untyped Iterable of elements.
        :return: A list
        """
        return list(InternalTools.iterify(sequence_or_element))

    @classmethod
    def iterify(cls, sequence_or_element) -> Iterator[Any]:
        """
        Makes a singleton Iterator of a single element or returns the iterable.
        Will return (an iterator from) the sequence as-is if it is Iterable, not a string, and not a bytes object.
        :param sequence_or_element: A single element of any type, or an untyped Iterable of elements.
        :return: An Iterator
        """
        if Tools.is_true_iterable(sequence_or_element):
            return iter(sequence_or_element)
        else:
            return iter([sequence_or_element])

    @classmethod
    def well(cls, well: Union[int, Wells]) -> Wells:
        """
        Fetchs a well and its run in a single query.
        In contrast, calling Wells.fetch().run will perform two queries.
        :param well A well ID or instance
        :returns A wells instance
        """
        well = Wells.select(Wells, Runs).join(Runs).where(Wells.id == well).first()
        if well is None:
            raise ValarLookupError("No well {}".format(well))
        return well

    @classmethod
    def all_or_none_are_none(
        cls, collection: Collection[Any], attr: Optional[str]
    ) -> Optional[bool]:
        """
        Returns None, True, or False on either a sequence of elements (`attr` is None),
        or a sequence of attributes of those elements (`attr` is defined).
        Returns:
            - True if the attribute of every element is None
            - False if the attribute of every element is not None.
            - None if the attribute is not defined on one or more elements.
            - None if the attribute is TNonerue on some elements and not None on others
        :param collection: Any iterable of objects that might have `attr` defined on them
        :param attr: The name of the attribute; if None will use the elements themselves
        :return: A boolean or None
        """

        def isnull(x):
            return x is None if attr is None else getattr(x, attr) is None

        if all(isnull(r) for r in collection):
            return True
        if all(not isnull(r) for r in collection):
            return False
        return None

    @classmethod
    def all_or_none_are_true(
        cls, collection: Collection[Any], attr: Optional[str]
    ) -> Optional[bool]:
        """
        Returns None, True, or False on either a sequence of elements (`attr` is True),
        or a sequence of attributes of those elements (`attr` is defined).
        Returns:
            - True if the attribute of every element is true
            - False if the attribute of every element is false.
            - None if the attribute is not defined on one or more elements.
            - None if the attribute is True on some elements and False on others
        :param collection: Any iterable of objects that might have `attr` defined on them
        :param attr: The name of the attribute; if None will use the elements themselves
        :return: A boolean or None
        """
        if attr is not None:
            if all(getattr(r, attr) for r in collection):
                return True
            if all(not getattr(r, attr) for r in collection):
                return False
        else:
            if all(r for r in collection):
                return True
            if all(not r for r in collection):
                return False
        return None


# TODO move to test
got = list(
    InternalTools.flatten_nested(
        [1, 2, [3, (5, {7, None})]],
        until=lambda s: isinstance(s, int),
        apply=lambda s: s + 10,
        discard_nulls=True,
    )
)
assert got == [11, 12, 13, 15, 17]

__all__ = ["InternalTools"]
