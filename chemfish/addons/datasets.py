from chemfish.caches.caching_wfs import *
from chemfish.caches.wf_caches import *
from chemfish.core.core_imports import *
from chemfish.model.compound_names import *
from chemfish.model.treatment_names import *
from chemfish.model.well_frames import *
from chemfish.model.well_names import *


class ChemfishDatasetTools:
    """"""

    @classmethod
    def filter_fewer(cls, df: WellFrame, cutoff: int) -> WellFrame:
        """
        For any compound with fewer than `cutoff` wells containing exactly that compound, filters the corresponding wells.

        Args:
            df: A WellFrame with 0 or 1 compounds per well
            cutoff: Minimum

        Returns:
            The filtered WellFrame

        """
        if np.any(df["c_ids"].map(len) > 1):
            raise RefusingRequestError(
                "Won't run filter_fewer because some wells contain more than 1 compound."
                "The results are too likely to be different than you want."
                "You should implement a more general function instead."
            )
        for c in df.unique_compound_ids():
            m = len(df[df["c_ids"] == (c,)])
            if m < cutoff:
                df = df[df["c_ids"] != (c,)]
                logger.info(f"Discarded c{c} with {m}<{cutoff} replicates")
                m = len(df[df["c_ids"] == (c,)])
                assert m == 0, f"{m} left"
        return df

    @classmethod
    def qc_compound_namer(cls, today: datetime) -> CompoundNamer:
        """


        Args:
            today: datetime:

        Returns:

        """
        return CompoundNamers.tiered(as_of=today)

    @classmethod
    def qc_namer(cls, today: datetime) -> WellNamer:
        """


        Args:
            today: datetime:

        Returns:

        """
        return (
            WellNamers.builder()
            .control_type()
            .treatments("${name/lower}", if_missing_col="control_type")
            .build()
        )

    @classmethod
    def qc_dr_namer(cls, today: datetime) -> WellNamer:
        """


        Args:
            today: datetime:

        Returns:

        """
        return (
            WellNamers.builder()
            .control_type()
            .treatments("${name/lower} ${dose}", if_missing_col="control_type")
            .build()
        )

    @classmethod
    def biomol_compound_namer(cls, today: datetime) -> CompoundNamer:
        """


        Args:
            today: datetime:

        Returns:

        """
        return CompoundNamers.chembl(today)

    @classmethod
    def biomol_namer(cls, today: datetime) -> WellNamer:
        """


        Args:
            today: datetime:

        Returns:

        """
        return (
            WellNamerBuilder()
            .column("control_type", transform=lambda s: "" if s == "low drug transfer" else s)
            .treatments(StringTreatmentNamer("${cid}"), ignore_cids={1, 2, 13576})
            .build()
        )

    @classmethod
    def biomol_display_namer(cls, today: datetime) -> WellNamer:
        """


        Args:
            today: datetime:

        Returns:

        """
        return WellNamers.screening_plate()

    @classmethod
    def dmt_simple_namer(cls, today: datetime) -> WellNamer:
        """


        Args:
            today: datetime:

        Returns:

        """
        displayer = StringTreatmentNamer("${tag}")
        return (
            WellNamerBuilder()
            .column("control_type", transform=lambda s: s.replace("solvent (-)", "vehicle"))
            .treatments(
                displayer,
                if_missing_col="control_type",
                transform=lambda s: s.replace("olson.", ""),
            )
            .build()
        )


class ChemfishDataset(metaclass=abc.ABCMeta):
    """ """

    def __call__(self):
        logger.info(f"Downloading {self.name}...")
        df = self._download()
        logger.notice(
            f"Downloaded {self.name} w/ {len(df.unique_runs())} runs, {len(df.unique_names())} names, {len(df)} wells."
        )
        return df

    @property
    @abcd.override_recommended
    def name(self) -> str:
        """ """
        return self.__class__.__name__

    def _download(self):
        """ """
        raise NotImplementedError()


@abcd.auto_eq()
@abcd.auto_hash()
@abcd.auto_repr_str()
class OptisepDataset(ChemfishDataset, metaclass=abc.ABCMeta):
    """ """

    def __init__(self, training_experiment: int, is_test_set: bool):
        self.training_experiment = training_experiment
        self.is_test_set = is_test_set

    @abcd.overrides
    def _download(self):
        """ """
        today = datetime(2019, 6, 17)
        sep = datetime(2018, 3, 24)
        # noinspection PyTypeChecker
        where: ExpressionLike = Experiments.id == self.training_experiment
        query = (
            CachingWellFrameBuilder(WellCache("cd(10)"), today)
            .with_feature("cd(10)")
            .where(where)
            .with_compound_names(ChemfishDatasetTools.qc_compound_namer(today))
            .with_names(ChemfishDatasetTools.qc_namer(today))
        )
        if self.is_test_set:
            query = query.where(Runs.datetime_run > sep)
        else:
            query = query.where(Runs.datetime_run < sep)
        df = query.build()
        return df.before_first_nan().slice_ms(0, 1000000).sort_by()


class LeoDataset1(ChemfishDataset):
    """ """

    def _download(self):
        """ """
        today = datetime(2019, 6, 17)
        n_replicates = 5
        df = (
            CachingWellFrameBuilder(WellCache("cd(10)"), today)
            .with_feature("cd(10)", np.float32)
            .where(Projects.name == "reference :: Leo BIOMOL")
            .where(~(Runs.id << [5315, 6315]))
            .with_compound_names(CompoundNamers.inchikey())
            .with_names(WellNamers.screening_plate())
            .build()
        )
        df = df.without_controls(names={"no drug transfer", "low drug transfer"})
        df = df.sort_values(["datetime_run", "well_index"])
        df = df.groupby("experiment_id").head(n_replicates * 96)
        treatments = df.without_controls().groupby("c_ids").head(n_replicates)
        treatments = ChemfishDatasetTools.filter_fewer(treatments, n_replicates)
        df = WellFrame.concat(df.with_controls("solvent (-)"), treatments)
        return df.sort_values(["run", "well_index"])


class LeoDataset2(ChemfishDataset):
    """ """

    def _download(self):
        """ """
        pattern = re.compile(r".*BM ([0-9]{1,2})\.([1-9]{1,2}).*")
        today = datetime(2019, 10, 30)
        df = (
            CachingWellFrameBuilder(WellCache("cd(10)-i").with_dtype(np.float16), today)
            .with_feature("cd(10)-i", np.float32)
            .where(Projects.id == 780)
            .where(
                ~(
                    Runs.id
                    << {
                        7631,
                        7646,
                        7650,
                        7680,
                        7684,
                        7708,
                        7732,
                        7742,
                        7756,
                        7761,
                        8029,
                        8193,
                        8205,
                    }
                )
            )
            .with_compound_names(ChemfishDatasetTools.biomol_compound_namer(today))
            .with_names(ChemfishDatasetTools.biomol_namer(today))
            .with_display_names(ChemfishDatasetTools.biomol_display_namer(today))
            .build()
        )
        original_length = df.feature_length()
        df = df.after_last_nan().before_first_nan()
        logger.minor(
            f"Lost {original_length - df.feature_length()} features: {original_length} → {df.feature_length()}"
        )
        nreps = {
            k.replace("screen :: BIOMOL :: Leo :: on Thor :: Leo", ""): v
            for k, v in df.reset_index()
            .groupby("experiment_name")
            .count()["well"]
            .to_dict()
            .items()
        }
        logger.minor(f"N replicates by experiment: {nreps}")
        return (
            df.sort_values(["run", "well_index"])
            .subset(1, None)
            .without_controls({"no drug transfer"})
        )


class _SimpleFlamesDataset(ChemfishDataset):
    """
    Any simple dataset for the flames battery on pointgrey.
    FYI:
        - Removes the first and last frames
        - Datetime 2019-09-01

    """

    def __init__(self, name: str, wheres, namer, compound_namer):
        super().__init__()
        self.__name, self.namer, self.compound_namer = name, namer, compound_namer
        self.wheres = [wheres] if isinstance(wheres, ExpressionLike) else wheres

    @property
    @abcd.overrides
    def name(self) -> str:
        """ """
        return self.__name

    def _download(self):
        """ """
        today = datetime(2019, 9, 1)
        query = (
            CachingWellFrameBuilder(WellCache("cd(10)-i"), today)
            .with_feature("cd(10)-i")
            .with_compound_names(self.compound_namer)
            .with_names(self.namer)
        )
        for where in self.wheres:
            query = query.where(where)
        return query.build().subset(1, 101998)


class ChemfishDatasets:
    """ """

    @classmethod
    @abcd.copy_docstring(LeoDataset1)
    def leo_biomol(cls) -> WellFrame:
        """ """
        return LeoDataset1()()

    @classmethod
    @abcd.copy_docstring(LeoDataset2)
    def leo_biomol_thor(cls) -> WellFrame:
        """ """
        return LeoDataset2()()

    @classmethod
    def opti_train_a(cls) -> WellFrame:
        """ """
        return OptisepDataset(1231, False)()

    @classmethod
    def opti_train_b(cls) -> WellFrame:
        """ """
        return OptisepDataset(1238, False)()

    @classmethod
    def opti_test_a(cls) -> WellFrame:
        """ """
        return OptisepDataset(1238, True)()

    @classmethod
    def opti_test_b(cls) -> WellFrame:
        """ """
        return OptisepDataset(1231, True)()

    @classmethod
    def qc_opt_full(cls) -> WellFrame:
        """ """
        today = datetime(2019, 9, 1)
        namer, compound_namer = (
            ChemfishDatasetTools.qc_namer(today),
            ChemfishDatasetTools.qc_compound_namer(today),
        )
        return _SimpleFlamesDataset(
            "QC-OPT",
            [Experiments.id == 1578, ~(Runs.id << [1578, 7519, 7585, 7348, 7350])],
            namer,
            compound_namer,
        )()

    @classmethod
    def qc_dr_full(cls) -> WellFrame:
        """ """
        today = datetime(2019, 9, 1)
        namer, compound_namer = (
            ChemfishDatasetTools.qc_dr_namer(today),
            ChemfishDatasetTools.qc_compound_namer(today),
        )
        return _SimpleFlamesDataset(
            "QC-DR", [Experiments.id == 1575, Runs.id != 7034], namer, compound_namer
        )()

    @classmethod
    def dmt(cls) -> WellFrame:
        """Experiment 1744 with all concentrations excluding empty wells.."""
        today = datetime(2019, 1, 1)
        compound_namer = CompoundNamers.tiered(as_of=today)
        displayer = StringTreatmentNamer("${tag} ${um}")
        namer = (
            WellNamerBuilder()
            .control_type()
            .treatments(
                displayer,
                if_missing_col="control_type",
                transform=lambda s: s.replace("olson.", ""),
            )
            .build()
        )
        df = _SimpleFlamesDataset("DMT-ALL", [Experiments.id == 1744], namer, compound_namer)()
        df = df.without_controls(["no drug transfer", "low drug transfer"])
        return df

    @classmethod
    def dmt_small(cls) -> WellFrame:
        """DMT and DMT and isoDMT analogs at 200uM with solvent controls. Experiment 1744 with run ID 7887 and low-volume wells dropped."""
        today = datetime(2019, 1, 1)
        compound_namer = CompoundNamers.tiered(as_of=today)
        namer = ChemfishDatasetTools.dmt_simple_namer(today)
        wheres = [
            Experiments.id == 1744,
            Runs.id != 7887,
            (ControlTypes.name == "solvent (-)") | (WellTreatments.micromolar_dose == 200),
        ]
        df = _SimpleFlamesDataset("DMT-SMALL", wheres, namer, compound_namer)()
        return df

    @classmethod
    def dmt_paper1(cls) -> WellFrame:
        """
        DMT and isoDMT analogs at 200uM with solvent controls. Experiment 1744 with run ID 7887 dropped.
        Replaces low-volume wells with their intended treatments.
        What was used in the paper.

        Args:

        Returns:

        """
        today = datetime(2019, 1, 1)
        compound_namer = CompoundNamers.tiered(as_of=today)
        namer = ChemfishDatasetTools.dmt_simple_namer(today)
        wheres = [Experiments.id == 1744, Runs.id != 7887, Compounds.id != 34261]
        df = _SimpleFlamesDataset("DMT-PAPER1", wheres, namer, compound_namer)()
        df["control_type"] = df["control_type"].map(
            lambda c: None if c in {"no drug transfer", "low drug transfer"} else c
        )
        df["control_type_id"] = df["control_type_id"].map(lambda c: None if c in [45, 46] else c)
        df = WellFrame.of(df)
        df = df.without_controls("killed (+)")
        return df


__all__ = ["ChemfishDatasets", "ChemfishDatasetTools"]
