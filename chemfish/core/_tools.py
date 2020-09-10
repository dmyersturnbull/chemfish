import h5py

from chemfish.core._imports import *
from chemfish.core.tools import *
from chemfish.core.valar_singleton import *

T = TypeVar("T")


@abcd.internal
class InternalTools:
    """
    A collection of utility functions for internal use in Chemfish.
    Equivalents of some of these functions are in the external-use Tools class, which delegates to this class.
    The most useful functions are:
        - Tools.run: Gets a run from a run ID, tag, name, instance, or submission hash or instance
        - Tools.runs: Delegates to Tools.run for either of the types accepted by Tools.run, or an iterable over them

    """

    def _load_h5(self, path: Path) -> np.array:
        with h5py.File(str(path)) as f:
            return f["data"]

    def _save_h5(self, data: np.array, path: Path) -> None:
        try:
            with h5py.File(str(path), "w") as f:
                f.create_dataset("data", data=data)
        except:
            path.unlink(missing_ok=True)
            raise

    @classmethod
    def verify_class_has_attrs(cls, class_, *attributes: Union[str, Iterable[str]]) -> None:
        """


        Args:
            class_:
            *attributes:

        Returns:

        """
        attributes = InternalTools.flatten_smart(attributes)
        bad_attributes = [not hasattr(class_, k) for k in attributes]
        if any(bad_attributes):
            raise AttributeError(f"No {class_.__name__} attribute(s) {bad_attributes}")

    @classmethod
    def warn_overlap(cls, a: Collection[Any], b: Collection[Any]) -> Set[Any]:
        """


        Args:
            a: Collection[Any]:
            b: Collection[Any]:

        Returns:

        """
        bad = set(a).intersection(set(b))
        if len(bad) > 0:
            logger.error(f"Values {', '.join(bad)} are present in both sets")
        return bad

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
        """


        Args:
            *parts: Sequence[str]:

        Returns:

        """
        path = ChemfishResources.path(*parts)
        return Tools.read_any(path)

    @classmethod
    def fetch_all_ids(cls, thing_class: Type[BaseModel], things):
        """
        Fetches a single row from a table, returning the row IDs.
        Each returned row is guaranteed to exist in the table at the time the query is executed.

        Args:
            thing_class: The table (peewee model)
            things: A list of lookup values -- each is an ID or unique varchar/char/enum field value

        Returns:
            The ID of the row

        Raises:
            ValarLookupError: If the row was not found

        """
        things = InternalTools.listify(things)
        return [thing_class.fetch(thing).id for thing in things]

    @classmethod
    def fetch_all_ids_unchecked(cls, thing_class: Type[BaseModel], things, keep_none: bool = False):
        """
        Fetches a single row from a table, returning the row IDs.
        If just IDs are passed, just returns them -- this means that the return value is NOT GUARANTEED to be a valid row ID.

        Args:
            thing_class: The table (peewee model)
            things: A list of lookup values -- each is an ID or unique varchar/char/enum field value
            keep_none: Include None values

        Returns:
            The ID of the row

        Raises:
            ValarLookupError: If the row was not found

        """
        things = InternalTools.listify(things)
        # noinspection PyTypeChecker
        return [
            thing
            if isinstance(thing, int) or thing is None and keep_none
            else thing_class.fetch(thing).id
            for thing in things
        ]

    @classmethod
    def fetch_id_unchecked(cls, thing_class: Type[BaseModel], thing) -> int:
        """
        Fetches a single row from a table, returning only the ID.
        If an ID is passed, just returns that -- this means that the return value is NOT GUARANTEED to be a valid row ID.

        Args:
            thing_class: The table (peewee model)
            thing: The lookup value -- an ID or unique varchar/char/enum field value

        Returns:
            The ID of the row

        Raises:
            ValarLookupError: If the row was not found

        """
        return thing if isinstance(thing, int) else thing_class.fetch(thing).id

    @classmethod
    def flatten(cls, seq: Iterable[Any]) -> Sequence[Any]:
        """


        Args:
            seq: Iterable[Any]:

        Returns:

        """
        y = []
        for z in seq:
            y.extend(z)
        return y

    @classmethod
    def flatten_smart(cls, seq: Iterable[Any]) -> Sequence[Any]:
        """


        Args:
            seq: Iterable[Any]:

        Returns:

        """
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
    def listify(cls, sequence_or_element: Any) -> Sequence[Any]:
        """
        Makes a singleton list of a single element or returns the iterable.
        Will return (a list from) the sequence as-is if it is Iterable, not a string, and not a bytes object.
        The order of iteration from the sequence is preserved.

        Args:
            sequence_or_element: A single element of any type, or an untyped Iterable of elements.

        Returns:
            A list

        """
        return list(InternalTools.iterify(sequence_or_element))

    @classmethod
    def iterify(cls, sequence_or_element) -> Iterator[Any]:
        """
        Makes a singleton Iterator of a single element or returns the iterable.
        Will return (an iterator from) the sequence as-is if it is Iterable, not a string, and not a bytes object.

        Args:
            sequence_or_element: A single element of any type, or an untyped Iterable of elements.

        Returns:
            An Iterator

        """
        if Tools.is_true_iterable(sequence_or_element):
            return iter(sequence_or_element)
        else:
            return iter([sequence_or_element])

    @classmethod
    def well(cls, well: Union[int, Wells]) -> Wells:
        """
        Fetches a well and its run in a single query.
        In contrast, calling Wells.fetch().run will perform two queries.

        Args:
            well: A well ID or instance

        Returns:
            A wells instance

        """
        well = Wells.select(Wells, Runs).join(Runs).where(Wells.id == well).first()
        if well is None:
            raise ValarLookupError(f"No well {well}")
        return well


__all__ = ["InternalTools"]
