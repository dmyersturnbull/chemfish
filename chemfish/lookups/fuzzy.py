from __future__ import annotations
from chemfish.core.core_imports import *
from chemfish.model.compound_names import TieredCompoundNamer
from fuzzywuzzy import fuzz, process
from chemfish.lookups import *
from chemfish.lookups.lookups import *
from chemfish.lookups.mandos import *

look = Tools.look
_users = {u.id: u.username for u in Users.select()}
_compound_namer = TieredCompoundNamer(max_length=50)


class Fuzzy:
    """Fuzzy matching of labels for compounds, batches, and mandos objects."""

    @classmethod
    def projects(cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100):
        logger.debug("Searching project names for '{}'...".format(s))
        query = Projects.select()
        data = list(query)
        raw = process.extract(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        projects = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug("Done. Found {} projects.".format(len(projects)))
        df = Lookups.projects(Projects.id << set(projects.keys()))
        df["name"] = df["id"].map(projects.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def experiments(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100
    ):
        logger.debug("Searching experiment names for '{}'...".format(s))
        query = Experiments.select()
        data = list(query)
        raw = process.extract(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        experiments = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug("Done. Found {} experiments.".format(len(experiments)))
        df = Lookups.experiments(Experiments.id << set(experiments.keys()))
        df["name"] = df["id"].map(experiments.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def batteries(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100
    ):
        logger.debug("Searching batteries for '{}'...".format(s))
        query = Batteries.select()
        data = list(query)
        raw = process.extract(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        batteries = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug("Done. Found {} batteries.".format(len(batteries)))
        df = Lookups.batteries(Batteries.id << set(batteries.keys()))
        df["name"] = df["id"].map(batteries.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def assays(cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100):
        logger.debug("Searching assays for '{}'...".format(s))
        query = Assays.select()
        data = list(query)
        raw = process.extract(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        assays = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug("Done. Found {} assays.".format(len(assays)))
        df = Lookups.assays(Assays.id << set(assays.keys()))
        df["name"] = df["id"].map(assays.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def runs(cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100):
        logger.debug("Searching run descriptions for '{}'...".format(s))
        query = Runs.select()
        data = list(query)
        raw = process.extract(s, {x.description for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        runs = {x.id: x.description for x in data if x.description in matches.keys()}
        logger.debug("Done. Found {} runs.".format(len(runs)))
        df = Lookups.runs(Runs.id << set(runs.keys()))
        df["name"] = df["id"].map(runs.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def variants(cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100):
        logger.debug("Searching variant names for '{}'...".format(s))
        query = GeneticVariants.select()
        data = list(query)
        raw = process.extract(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        variants = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug("Done. Found {} variants.".format(len(variants)))
        df = Lookups.variants(variants.keys())
        df["name"] = df["id"].map(variants.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def constructs(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100
    ):
        logger.debug("Searching constructs for '{}'...".format(s))
        query = GeneticConstructs.select()
        data = list(query)
        raw = process.extract(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        constructs = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug("Done. Found {} constructs.".format(len(constructs)))
        df = Lookups.constructs(constructs.keys())
        df["name"] = df["id"].map(constructs.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def genes(cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100):
        logger.debug("Searching genes for '{}'...".format(s))
        query = Genes.select()
        data = list(query)
        raw = process.extract(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        genes = {x.id: x.name for x in data if x.name in matches.keys()}
        logger.debug("Done. Found {} genes.".format(len(genes)))
        df = Lookups.genes(genes.keys())
        df["name"] = df["id"].map(genes.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def compounds(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: int = 100
    ):
        logger.debug("Searching compound labels for '{}'...".format(s))
        query = CompoundLabels.select()
        if ref is not None:
            query = query.where(CompoundLabels.ref_id == Refs.fetch(ref).id)
        data = list(query)
        raw = process.extract(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        compounds = {x.compound_id: x.name for x in data if x.name in matches.keys()}
        logger.debug("Done. Found {} compounds.".format(len(compounds)))
        df = Lookups.compounds(compounds.keys())
        df["name"] = df["id"].map(compounds.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def batches(cls, s: str, ref: Optional[RefLike] = None, min_score: int = 70, limit: int = 100):
        logger.debug("Searching batch labels for '{}'...".format(s))
        query = BatchLabels.select()
        if ref is not None:
            query = query.where(BatchLabels.ref_id == Refs.fetch(ref).id)
        data = list(query)
        raw = process.extract(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        batches = {x.batch_id: x.name for x in data if x.name in matches.keys()}
        logger.debug("Done. Found {} batches.".format(len(batches)))
        df = Lookups.batches(batches.keys())
        df["name"] = df["id"].map(batches.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)

    @classmethod
    def mandos_objects(
        cls, s: str, ref: Optional[RefLike] = None, min_score: int = 75, limit: Optional[int] = 100
    ):
        logger.debug("Searching mandos_object_tags for '{}'...".format(s))
        query = MandosObjectTags.select()
        if ref is not None:
            query = query.where(MandosObjectTags.ref_id == Refs.fetch(ref).id)
        data = list(query)
        raw = process.extract(s, {x.name for x in data}, limit=limit)
        matches = {name: score for name, score in raw if score >= min_score}
        objects = {x.object_id: x.name for x in data if x.name in matches.keys()}
        logger.debug("Done. Found {} mandos_objects.".format(len(objects)))
        df = MandosLookups.objects(objects.keys())
        df["name"] = df["id"].map(objects.get)
        df["score"] = df["name"].map(matches.get)
        df = df.sort_values("score", ascending=False)
        return Lookup(df)


__all__ = ["Fuzzy"]
