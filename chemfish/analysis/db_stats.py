from chemfish.core.core_imports import *


class DbStatsFrame(SimpleFrame):
    pass


class DbStats:
    @classmethod
    def stats(cls, extended: bool = False) -> pd.DataFrame:
        video_days = round(
            sum(
                run.experiment.battery.length
                * (
                    1.0 / 25 / 60 / 60 / 24
                    if run.submission_id is None
                    else 1.0 / 1000 / 60 / 60 / 24
                )
                for run in Runs.select(
                    Runs.id,
                    Runs.submission_id,
                    Experiments.id,
                    Experiments.battery_id,
                    Batteries.id,
                    Batteries.length,
                )
                .join(Experiments)
                .join(Batteries)
            ),
            1,
        )
        million_fish = round(sum([w.n for w in Wells.select(Wells.n)]) / 1000 / 1000, 2)
        if extended:
            compounds_screened = len(
                {
                    t.batch.compound_id
                    for t in WellTreatments.select()
                    .where(WellTreatments.batch_id, Batches.id, Batches.compound_id)
                    .join(Batches)
                }
            )
        else:
            compounds_screened = "?"
        users = len(
            {
                r.experimentalist.id
                for r in Runs.select(Runs.experiment_id, Users.id, Users.username).join(Users)
                if r.experimentalist.username not in {"ucsf", "mgh", "tester", "goldberry"}
            }
        )
        by_generation = {g: 0 for g in DataGeneration}
        for run in Runs.select():
            by_generation[ValarTools.generation_of(run)] += 1
        df = pd.DataFrame(
            pd.Series(
                {
                    "runs": Runs.select(Runs.id).count(),
                    "active saurons": Saurons.select().where(Saurons.active).count(),
                    "sauronx runs": Runs.select().where(Runs.submission_id != None).count(),
                    "physical plates": Plates.select(Plates.id).count(),
                    "experiments": Experiments.select(Experiments.id).count(),
                    "projects": Projects.select().count(),
                    "compounds (k)": round(Compounds.select(Compounds.id).count() / 1000, 1),
                    "variants": GeneticVariants.select(GeneticVariants.id).count(),
                    "constructs": GeneticConstructs.select(GeneticConstructs.id).count(),
                    "experimentalists": users,
                    "template layouts": TemplatePlates.select().count(),
                    "batteries": Batteries.select(Batteries.id).count(),
                    "assays": Assays.select(Assays.id).count(),
                    "days of video (expected)": video_days,
                    "million fish screened": million_fish,
                    "mandos rules (k)": round(MandosRules.select(MandosRules.id).count() / 1000, 1),
                    "chem values (k)": round(MandosInfo.select(MandosInfo.id).count() / 1000, 1),
                    "compounds screened": compounds_screened,
                },
                dtype=str,
            )
        ).rename(columns={0: "value"})
        df = df.T
        for k, v in by_generation.items():
            df["generation :: " + str(k).lower()] = v
        return DbStatsFrame(df.T)


__all__ = ["DbStats"]
