from kale.core.core_imports import *
from kale.calc.chem import *


class MassBatchLoader:
    def __init__(self, ref: RefLike, prefix: str, start_box: int, n_wells: int):
        self.ref, self.prefix, self.start_box = Refs.fetch_or_none(ref), prefix, start_box
        if self.ref is None and isinstance(ref, str):
            self.ref = Refs(name=ref)
            self.ref.save()
        elif self.ref is None:
            raise LookupError(ref)
        self.n_wells = n_wells
        self.box, self.well = 1, 0
        self._solvents = {v: k for k, v in ValarTools.known_solvent_names().items()}

    def load(self, df: Union[PLike, pd.DataFrame]):
        if isinstance(df, (str, PurePath)) and (df.endswith(".xlsx") or df.endswith(".xls")):
            df = pd.read_excel(df)
        elif isinstance(df, (str, PurePath)):
            df = pd.read_csv(df)
        for row in df.itertuples():
            self.add(OptRow(row))
        logger.notice("Loaded from {} rows".format(len(df)))

    def add(self, row: OptRow):
        if "inchi" in row:
            compound = self._add_compound(row.inchi, row)
        elif "smiles" in row:
            compound = self._add_compound(row.smiles, row)
        else:
            compound = None
        batch = self._add_batch(row, compound)
        logger.debug("Added batch {} / compound {}".format(batch, compound))

    def _add_batch(self, row: OptRow, compound: Optional[Compounds]):
        if self.well >= self.n_wells:
            self.well = 0
            self.box += 1
        self.well += 1
        supplier = Suppliers.fetch_or_none(row.supplier)
        if supplier is None:
            supplier = Suppliers(name=row.supplier, description=row.supplier)
            supplier.save()
        legacy = self.prefix + str(self.box).zfill(2) + str(self.well).zfill(2)
        batch = Batches.select().where(Batches.legacy_internal == legacy).first()
        if batch is None:
            batch = Batches(
                amount=str(row.amount),
                box_number=self.start_box + self.box,
                well_number=self.well,
                compound=compound,
                concentration_milimolar=row.concentration_milimolar,
                legacy_internal=legacy,
                location=Locations.fetch(row.location),
                location_note=row.location_note,
                lookup_hash=ValarTools.generate_batch_hash(),
                made_from=row.opt("made_from", Batches.fetch),
                molecular_weight=row.molecular_weight,
                notes=row.notes,
                person_ordered=Users.fetch(row.person_ordered),
                ref=self.ref,
                solvent=Compounds.fetch(row.solvent)
                if isinstance(row.solvent, int)
                else self._solvents[row.solvent],
                supplier=supplier,
                supplier_catalog_number=row.supplier_catalog_number,
                tag=row.tag,
            )
            batch.save()
        for col in row.keys():
            if col.startswith("blabel_") and col in row:
                name = row.req(col)
                if name is not None and name.lower() != "none":
                    ref_name = self.ref.name + ":" + Tools.strip_off_start(col, "clabel_")
                    label_ref = Refs.fetch_or_none(ref_name)
                    if label_ref is None:
                        label_ref = Refs(name=ref_name, description=ref_name)
                        label_ref.save()
                    label = BatchLabels(batch=batch, ref=label_ref, name=name)
                    label.save()
        return batch

    def _add_compound(self, data: str, row: OptRow):
        wrap = WrappedInchi(data)
        if wrap.compound is not None:
            return wrap.compound
        compound = Compounds(
            inchi=wrap.inchi,
            inchikey=wrap.inchikey,
            inchikey_connectivity=wrap.inchikey.split("-")[0],
            smiles=wrap.smiles,
            chemspider=None,
            chembl=None,
        )
        compound.save()
        for col in row.keys():
            if col.startswith("clabel_") and col in row:
                name = row.req(col)
                if name is not None and name.lower() != "none":
                    ref_name = self.ref.name + ":" + Tools.strip_off_start(col, "clabel_")
                    label_ref = Refs.fetch_or_none(ref_name)
                    if label_ref is None:
                        label_ref = Refs(name=ref_name, description=ref_name)
                        label_ref.save()
                    label = CompoundLabels(compound=compound, ref=label_ref, name=name)
                    label.save()
        return compound


__all__ = ["MassBatchLoader"]
