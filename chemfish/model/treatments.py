from __future__ import annotations

from chemfish.core.core_imports import *


@abcd.total_ordering
class Treatment:
    """
    A drug (batch) and micromolar dose from a WellConditions with pretty printing.
    Two Treatments are equal iff their ordered_compound IDs and doses are equal.
    Less than, greater than, etc. are implemented by comparing, in order:
        1. Compound ID
        2. Batch ID
        3. Dose

    """

    def __init__(
        self,
        bid: int,
        oc: str,
        compound_id: Optional[int],
        inchikey: Optional[str],
        dose: float,
        tag: Optional[str] = None,
        chembl: Optional[str] = None,
        chemspider: Optional[str] = None,
    ):
        """
        Constructor.

        Args:
            bid: The batch id
            oc: The batch hash
            compound_id: The compound ID
            inchikey: The Inchikey
            dose: The dose in micromolar
            tag: The value in batches.tag
            chembl: The ChEMBL ID
            chemspider: The ChemSpider ID
        """
        if bid is None:
            raise XValueError("Batch ID cannot be None")
        if oc is None:
            raise XValueError(f"Batch lookup_hash for b{bid} is None")
        if dose is None:
            raise XValueError(f"Dose for b{bid} is None")
        self.bid = bid
        self.oc = oc
        self.compound_id = compound_id
        self.inchikey = inchikey
        self.dose = dose
        self.tag = tag
        self.chembl = chembl
        self.chemspider = chemspider

    @property
    def id(self) -> int:
        """ """
        return self.bid

    @property
    def cid(self) -> int:
        """ """
        return self.compound_id

    @classmethod
    def from_well_treatment(cls, condition: WellTreatments) -> Treatment:
        """


        Args:
          condition: WellTreatments:

        Returns:

        """
        batch = condition.batch
        compound = batch.compound
        return Treatment(
            batch.id,
            batch.lookup_hash,
            None if compound is None else compound.id,
            None if compound is None else compound.inchikey,
            condition.micromolar_dose,
            batch.tag,
            None if compound is None else compound.chembl,
            None if compound is None else compound.chemspider,
        )

    @classmethod
    def from_info(cls, batch: Union[Batches, int, str], dose: float) -> Treatment:
        """


        Args:
          batch:
          dose: float:

        Returns:

        """
        batch = Batches.fetch(batch)
        compound = batch.compound
        return Treatment(
            batch.id,
            batch.lookup_hash,
            None if compound is None else compound.id,
            None if compound is None else compound.inchikey,
            dose,
            batch.tag,
            None if compound is None else compound.chembl,
            None if compound is None else compound.chemspider,
        )

    def __str__(self):
        return f"b{self.id}({self.dose}µM)" if self.id is not None else "-"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return other.bid == self.bid and other.dose == self.dose

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        def i(r: int):
            """


            Args:
              r: int:

            Returns:

            """
            return -1 if r is None else r

        return (i(self.compound_id), self.id, self.dose) < (
            i(other.compound_id),
            other.id,
            other.dose,
        )

    def __hash__(self):
        return hash((self.bid, self.dose))

    def copy(self) -> Treatment:
        """ """
        return Treatment(self.bid, self.oc, self.compound_id, self.inchikey, self.dose, self.tag)


@abcd.total_ordering
class Treatments:
    """
    A wrapper for a list of Treatment objects.
    Any duplicate Treatment instances (determined by Treatent.__eq__ will be removed,
    and the instances will be sorted by Treatment.__lt__.
    This has a __str__ and __repr__ that simplify the Treatment contents.

    Args:

    Returns:

    """

    def __init__(self, treatments):
        self.treatments = sorted(set(treatments))

    def single(self) -> Treatment:
        """ """
        return Tools.only(self.treatments, name="treatments")

    def __eq__(self, other):
        return self.treatments == other.treatments

    def __lt__(self, other):
        return tuple(self.treatments) < tuple(other.treatments)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self._format(lambda t: "b" + str(t.bid))

    def str_with_hash(self):
        """ """
        return self._format(lambda t: t.oc)

    def _format(self, function: Callable[[Treatment], Any]):
        """


        Args:
          function: Callable[[Treatment]:
          Any]:

        Returns:

        """
        if self.len() > 0:
            ocs = {function(t): [] for t in self}
            for t in self:
                ocs[function(t)].append(t.dose)
            return " ".join(
                (
                    [
                        "{} ({})".format(oc, ", ".join([Tools.nice_dose(d) for d in sorted(doses)]))
                        for oc, doses in ocs.items()
                    ]
                )
            )
        else:
            return "-"

    def __repr__(self):
        return str(self)

    def _repr_html_(self):
        """ """
        return str(self)

    def __hash__(self):
        return hash("".join(str(self.treatments)))

    def __getitem__(self, treatment_index: int) -> Treatment:
        return self.treatments[treatment_index]

    # unfortunate workaround for https://github.com/pandas-dev/pandas/issues/17695
    def len(self):
        """ """
        return len(self.treatments)

    def copy(self) -> Treatments:
        """ """
        return Treatments(self.treatments)

    @classmethod
    def of(cls, treatments: Union[Treatments, Treatment, Collection[Treatment]]) -> Treatments:
        """


        Args:
          treatments: Union[Treatments:
          Treatment:
          Collection[Treatment]]:

        Returns:

        """
        if isinstance(treatments, Treatments):
            return treatments
        elif isinstance(treatments, Treatment):
            return Treatments([treatments])
        elif Tools.is_true_iterable(treatments):
            return Treatments(treatments)
        else:
            raise XTypeError(f"Invalid type {type(treatments)} for treatments {treatments}")


TreatmentLike = Union[Treatments, Treatment, Collection[Treatment]]

__all__ = ["Treatment", "Treatments", "TreatmentLike"]
