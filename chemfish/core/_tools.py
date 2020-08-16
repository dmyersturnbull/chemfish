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

    Args:

    Returns:

    """

    @classmethod
    def download_frame_timestamps(cls, run_id: int) -> np.array:
        """
        Downloads the timestamps that SauronX recorded for the frame capture times, or None if the sensor was not defined.
        Will always return None for legacy data.
        In pre-PointGrey data, these are the timestamps that MATLAB received the frames.
        In PointGrey data, these are the timestamps that the image was taken (according to the camera firmware).

        Args:
          run_id: The ID of a runs row, only
          run_id: int:

        Returns:
          The numpy array of floats, or None

        """
        return InternalTools.convert_sensor_data(
            SensorData.select()
            .where(SensorData.run_id == run_id)
            .where(SensorData.sensor_id == 3)
            .first()
        )

    @classmethod
    def download_stimulus_timestamps(cls, run_id: int) -> Optional[np.array]:
        """
        Downloads the timestamps that SauronX recorded for the stimuli, or None if the sensor was not defined.
        Will always return None for legacy data.

        Args:
          run_id: The ID of a runs row, only
          run_id: int:

        Returns:
          The numpy array of floats, or None

        """
        return InternalTools.convert_sensor_data(
            SensorData.select()
            .where(SensorData.run_id == run_id)
            .where(SensorData.sensor_id == 4)
            .first()
        )

    @classmethod
    def convert_sensor_data(cls, data: SensorData) -> Union[None, np.array, bytes, str]:
        """
        Downloads and converts sensor data.
        See `InternalTools.convert_sensor_data_from_bytes` for details.

        Args:
          data: The ID or instance of a row in sensor_data
          data: SensorData:

        Returns:
          The converted data

        """
        data = SensorData.fetch(data)
        return InternalTools.convert_sensor_data_from_bytes(data.sensor, data.floats)

    @classmethod
    def convert_sensor_data_from_bytes(
        cls, sensor: Union[str, int, Sensors], data: bytes
    ) -> Union[None, np.array, bytes, str]:
        """
        Convert the sensor data to its appropriate type as defined by `sensors.data_type`.
        WARNING:
            Currently does not handle `sensors.data_type=='utf8_char'`. Currently there are no sensors in Valar with this data type.

        Args:
          sensor: The name, ID, or instance of the sensors row
          data: The data from `sensor_data.floats`; despite the name this is blob represented as bytes and may not correspond to floats at all
          sensor:
          data: bytes:

        Returns:
          The converted data, or None if `data` is None

        """
        sensor = Sensors.fetch(sensor)
        dt = sensor.data_type
        if data is None:
            return None
        if dt == "byte":
            return np.frombuffer(data, dtype=np.byte)
        if dt == "unsigned_byte":
            return np.frombuffer(data, dtype=np.byte) + 2 ** 7
        if dt == "short":
            return np.frombuffer(data, dtype=">i2").astype(np.int64)
        if dt == "unsigned_short":
            return np.frombuffer(data, dtype=">i2").astype(np.int64) + 2 ** 15
        if dt == "int":
            return np.frombuffer(data, dtype=">i4").astype(np.int64)
        if dt == "unsigned_int":
            return np.frombuffer(data, dtype=">i4").astype(np.int64) + 2 ** 31
        if dt == "float":
            return np.frombuffer(data, dtype=">f4").astype(np.float64)
        if dt == "double":
            return np.frombuffer(data, dtype=">f8").astype(np.float64)
        if dt == "utf8_char":
            return str(dt, encoding="utf-8")
        elif dt == "other":
            return data
        else:
            raise UnsupportedOpError(f"Oh no! Sensor cache doesn't recognize dtype {dt}")

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
    def from_kwargs(cls, kwargs, key: str, fallback: Any) -> Tup[Any, Dict[str, Any]]:
        """


        Args:
          kwargs:
          key: str:
          fallback: Any:

        Returns:

        """
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
          thing_class: Type[BaseModel]:

        Returns:
          The ID of the row

        Raises:
          A: ValarLookupError If the row was not found

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
          thing_class: Type[BaseModel]:
          keep_none: bool:  (Default value = False)

        Returns:
          The ID of the row

        Raises:
          A: ValarLookupError If the row was not found

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
          thing_class: Type[BaseModel]:

        Returns:
          The ID of the row

        Raises:
          A: ValarLookupError If the row was not found

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
          sequence_or_element: Any:

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
        Fetchs a well and its run in a single query.
        In contrast, calling Wells.fetch().run will perform two queries.

        Args:
          well: A well ID or instance
          well:
        Returns:
          A wells instance

        """
        well = Wells.select(Wells, Runs).join(Runs).where(Wells.id == well).first()
        if well is None:
            raise ValarLookupError(f"No well {well}")
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

        Args:
          collection: Any iterable of objects that might have `attr` defined on them
          attr: The name of the attribute; if None will use the elements themselves
          collection: Collection[Any]:
          attr: Optional[str]:

        Returns:
          A boolean or None

        """

        def isnull(x):
            """


            Args:
              x:

            Returns:

            """
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

        Args:
          collection: Any iterable of objects that might have `attr` defined on them
          attr: The name of the attribute; if None will use the elements themselves
          collection: Collection[Any]:
          attr: Optional[str]:

        Returns:
          A boolean or None

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


__all__ = ["InternalTools"]
