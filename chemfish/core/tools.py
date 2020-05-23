from __future__ import annotations
import struct
import joblib, dill
from dscience.core import *
from kale.core._imports import *
from kale.core.environment import kale_env
from dscience.core.hasher import FileHasher
from dscience.full import Tools as _Tools
from dscience.core.iterators import *
from dscience.core.chars import *
from dscience.biochem.multiwell_plates import WB1
from kale.core.valar_singleton import *


class IncomptabileNumpyArrayDataType(XTypeError):
    pass


_hash_regex = re.compile("[0-9a-f]{12}$")


class KaleValarTools:
    @classmethod
    def query(cls, query: peewee.BaseQuery) -> pd.DataFrame:
        return pd.DataFrame([pd.Series(row.get_data()) for row in query])

    @classmethod
    def jvm_sbytes_to_ubytes(cls, data: bytes) -> np.array:
        """
        Used to convert "squashed" byte arrays from Valar into their true forms.
        Fundamentally these are unsigned bytes (0-255), but they were represented in Scala as signed bytes (-128 to 127) by subtracting 128.
        Then those bytes were inserted into MySQL blobs.
        To get them back, we read them into a signed byte Numpy array, cast to ints to avoid overflow, add 128, then convert to unsigned ints.
        :param data: Bytes from Scala-inserted values in Valar blobs
        :return: A Numpy ubyte (uint8) array
        """
        return (np.frombuffer(data, dtype=np.byte).astype(np.int32) + 128).astype(np.ubyte)

    @classmethod
    def signed_floats_to_blob(cls, data: np.array) -> bytes:
        return KaleValarTools.array_to_blob(data, np.float32)

    @classmethod
    def blob_to_signed_floats(cls, data: bytes) -> np.array:
        return np.copy(np.frombuffer(data, dtype=">f4"))

    @classmethod
    def blob_to_signed_ints(cls, data: bytes) -> np.array:
        return np.copy(np.frombuffer(data, dtype=">i4"))

    @classmethod
    def array_to_blob(cls, data: np.array, dtype) -> bytes:
        """
        Gets the bytes of a Numpy array, first requiring that the array is of the specified type.
        :param data: A numpy array
        :param dtype: A Numpy datatype, such as np.uint32
        :return: The bytes representation
        :raises IncomptabileNumpyArrayDataType: If the numpy array has the wrong data type
        :raises TypeError: If `data` is not a Numpy array at all
        """
        if data.dtype != dtype:
            raise IncomptabileNumpyArrayDataType("Type {} is not a {}".format(data.dtype, dtype))
        return struct.pack(
            ">" + "f" * len(data), *data
        )  # For now, we are assuming data is 1D np.array. Change this once it's not.

    @classmethod
    def wells(cls, wells: Union[int, Wells, Iterable[int, Wells]]) -> Sequence[Wells]:
        if Tools.is_true_iterable(wells):
            return Wells.fetch_all(wells)
        elif isinstance(wells, str) or isinstance(wells, int) or isinstance(wells, Wells):
            return [Wells.fetch(wells)]
        else:
            raise XTypeError(
                "{} is not a valid parameter type. Please use a well or an iterable of wells.".format(
                    type(wells)
                )
            )

    @classmethod
    def runs(cls, runs: RunsLike) -> Sequence[Runs]:
        """
        Fetchs one or more runs from flexible formats.
        Currently performs one query on Valar per run. In the future will only perform one query for all of them.
        :param runs: A run from a run ID, tag, name, instance, or submission hash or instance, or an iterable of any of these
        :return: The Runs row instances in the same order
        """
        runs = runs if Tools.is_true_iterable(runs) else [runs]
        # make sure there aren't any weird types
        bad_types = [r for r in runs if not isinstance(r, (int, float, str, Runs, Submissions))]
        if len(bad_types) > 0:
            raise IncompatibleDataError("Invalid type for run or list or runs {}".format(bad_types))
        # we'll build this up by setting individual indices
        blanks = [None for _ in runs]  # type: List[Optional[Runs]]
        # get by runs
        if any([b is None for b in blanks]):
            missing = [
                (i, r)
                for i, r in enumerate(runs)
                if blanks[i] is None
                and isinstance(
                    r,
                    (int, float, Runs)
                    or isinstance(r, str)
                    and not Tools.looks_like_submission_hash(r),
                )
            ]
            try:
                new = Runs.fetch_all_or_none([r for i, r in missing])
            except AssertionError:
                # TODO this shouldn't be raised
                raise LookupFailedError("At least one run is missing in {}".format(runs)) from None
            for i, n in zip_strict([i for i, r in missing], new):
                blanks[i] = n
        # get by submission objects
        if any([b is None for b in blanks]):
            missing = [
                (i, r)
                for i, r in enumerate(runs)
                if blanks[i] is None and isinstance(r, Submissions)
            ]
            new = {
                r.submission: r
                for r in Runs.select(Runs).where(Runs.submission_id << [s.id for i, s in missing])
            }
            for i, r in missing:
                blanks[i] = new.get(r)
        # get by submission hash
        if any([b is None for b in blanks]):
            missing = [
                (i, r) for i, r in enumerate(runs) if blanks[i] is None and isinstance(r, str)
            ]
            new = {
                r.submission.lookup_hash: r
                for r in Runs.select(Runs, Submissions)
                .join(Submissions)
                .where(Submissions.lookup_hash << [s for i, s in missing])
            }
            for i, r in missing:
                blanks[i] = new.get(r)
        # check that there are no missing items
        missing = {i: r for i, r in enumerate(runs) if blanks[i] is None}
        if len(missing) > 0:
            raise ValarLookupError("Didn't find {}".format(missing))
        return blanks

    @classmethod
    def run_ids_unchecked(cls, runs: RunsLike):
        if not Tools.is_true_iterable(runs):
            runs = [runs]
        if all([isinstance(r, int) for r in runs]):
            return runs
        else:
            return [r.id for r in Tools.runs(runs)]

    @classmethod
    def run(cls, run: RunLike, join: bool = False) -> Runs:
        """
        Fetchs a run from a flexible format.
        Fetches from Valar once. Use Tools.runs if you want to fetch multiple runs in a single query.
        :param run: A run from a run ID, tag, name, instance, or submission hash or instance
        :param join: Join on experiments, submissions, sauron_configs, saurons, plates, and plate_types
        :return: The Runs row instance
        """
        bq = lambda: (
            Runs.select(Runs, Submissions, Experiments, Plates, PlateTypes)
            .join(Submissions, JOIN.LEFT_OUTER)
            .switch(Runs)
            .join(Experiments)
            .switch(Runs)
            .join(SauronConfigs)
            .join(Saurons)
            .switch(Runs)
            .join(Plates)
            .join(PlateTypes, JOIN.LEFT_OUTER)
        )
        if isinstance(run, float):
            run = int(run)
        if (
            isinstance(run, Submissions)
            or isinstance(run, str)
            and KaleValarTools.looks_like_submission_hash(run)
        ):
            sub = Submissions.fetch_or_none(run)
            if sub is None:
                raise ValarLookupError("No run {}".format(run))
            if join:
                return bq().where(Submissions.id == sub.id).first()
            else:
                return Runs.get(Runs.submission_id == sub.id)
        if isinstance(run, str) and run.isdigit():
            run = int(run)
        if join and isinstance(run, int):
            return bq().where(Runs.id == run).first()
        elif join and isinstance(run, Runs):
            return bq().where(Runs.id == run.id).first()
        elif join and isinstance(run, str):
            attempt = bq().where(Runs.name == run).first()
            if attempt is not None:
                return attempt
            attempt = bq().where(Runs.tag == run).first()
            if attempt is not None:
                return attempt
            raise ValarLookupError("No run {}".format(run))
        return Runs.fetch(run)

    @classmethod
    def wb1_from_run(cls, run: RunLike) -> WB1:
        pt: PlateTypes = Tools.run(run, join=True).plate.plate_type
        return WB1(pt.n_rows, pt.n_columns)

    @classmethod
    def looks_like_submission_hash(cls, submission_hash: str) -> bool:
        """
        :param submission_hash: Any string
        :return: Whether the string could be a submission hash (is formatted correctly)
        """
        return submission_hash == "_" * 12 or _hash_regex.match(submission_hash) is not None

    @classmethod
    def tables(cls) -> Sequence[str]:
        """
        Lists the tables in Valar.
        :return: The names of tables in Valar
        """
        from valarpy.model import database

        return database.get_tables()


class Tools(_Tools, KaleValarTools):
    @classmethod
    def parallel(
        cls, things, function, n_jobs: Optional[int] = kale_env.n_cores, verbosity: int = 1
    ):
        return joblib.Parallel(n_jobs=n_jobs, verbose=verbosity)(
            joblib.delayed(function)(i) for i in things
        )

    @classmethod
    def prepped_file(cls, path: PLike) -> Path:
        cls.prep_file(path)
        return Path(path)

    @classmethod
    def prepped_dir(cls, path: PLike, exist_ok: bool = True) -> Path:
        cls.prep_dir(path, exist_ok=True)
        return Path(path)


__all__ = [
    "Tools",
    "FileHasher",
    "Chars",
    "SizedIterator",
    "SeqIterator",
    "TieredIterator",
    "OptRow",
]
