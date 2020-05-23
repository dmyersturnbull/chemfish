"""
A better and simpler implementation of well classifiers introduced in kale 1.13.0.
"""

from kale.core.core_imports import *
import joblib
from sklearn.ensemble import RandomForestClassifier
from kale.model.wf_builders import *
from kale.ml.decision_frames import *
from kale.ml import ClassifierPath
from kale.viz.figures import *


class ClassifierFailedError(AlgorithmError):
    pass


class ClassifierTrainFailedError(ClassifierFailedError):
    pass


class ClassifierPredictFailedError(ClassifierFailedError):
    pass


class TrainTestOverlapWarning(StrangeRequestWarning):
    """
    Training and test data overlap.
    """


class NotTrainedError(OpStateError):
    pass


class AlreadyTrainedError(OpStateError):
    pass


# just for good tab completion
AnySklearnClassifier = RandomForestClassifier


class WellClassifier(SaveableTrainable):
    """
    The important methods are:
        - train(df)
        - test(df)
        - load(path)
        - save(path)
    Some classifiers may also implement:
        - training_decision
        - oob_score
        - weights
    Only three methods need to be implemented: train, test, and the property params.
    When trained, `info` contains:
        - wells, labels, features
        - started, finished, seconds_taken
    The saved .info file contains the above, plus the contents of `params` and any statistics.
    """

    @abcd.abstractmethod
    def train(self, df: WellFrame) -> None:
        raise NotImplementedError()

    @abcd.abstractmethod
    def test(self, df: WellFrame) -> DecisionFrame:
        raise NotImplementedError()

    @property
    @abcd.abstractmethod
    def params(self) -> Mapping[str, Any]:
        raise NotImplementedError()

    @property
    def is_trained(self):
        return "finished" in self.info

    def _update_wf_info(self, df: WellFrame):
        self.info.update(
            {
                "wells": df["well"].values,
                "runs": df["run"].values,
                "labels": df["name"].values,
                "features": df.columns.values.astype(np.int32),
            }
        )

    def _verify_trained(self):
        if not self.is_trained:
            raise NotTrainedError("Model is not trained")

    def _verify_untrained(self):
        if self.is_trained:
            raise AlreadyTrainedError("Model is already trained")

    def _verify_train(self, wells: np.array, names: Sequence[str], features):
        self._verify_untrained()
        if len(wells) == 0:
            raise EmptyCollectionError("Cannot train on an empty WellFrame")
        if len(set(names)) == 1:
            logger.warning("Training a classifier for only 1 label: {}".format(names[0]))
        if len(set(names)) > 50:
            logger.warning("Training a classifier on >50 labels")

    def _verify_test(self, wells: np.array, names: Sequence[str], features):
        self._verify_trained()
        overlap = set(names).difference(set(self.info["labels"]))
        if len(overlap) > 0:
            raise LengthMismatchError(
                "Test labels {} are not in the train labels {}".format(
                    set(names), set(self.info["labels"])
                )
            )
        intersec = set(self.info["labels"]).intersection(set(wells.values))
        if len(intersec) > 0:
            logger.warning("Test wells {} overlap with training wells")
        if features != self.info["features"]:
            logger.warning("Features don't match")

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__, "trained" if self.is_trained else "untrained"
        )

    def __str__(self):
        return repr(self)


class HasOob(WellClassifier, metaclass=abc.ABCMeta):
    @property
    @abcd.abstractmethod
    def oob_score(self) -> float:
        raise NotImplementedError()

    @property
    @abcd.abstractmethod
    def training_decision(self) -> DecisionFrame:
        raise NotImplementedError()


class HasWeights(WellClassifier, metaclass=abc.ABCMeta):
    @property
    @abcd.abstractmethod
    def weights(self) -> Sequence[float]:
        raise NotImplementedError()


class BuildableWellClassifier(abcd.ABC):
    """
    A WellClassifier with a classmethod `build` that returns a new instance from kwargs.
    This method is separated from the constructor, which might provide a different, more direct interface.
    The idea here is that `build` may be willing to assume default parameters.
    """

    @classmethod
    @abcd.abstractmethod
    def build(cls, **kwargs):
        """
        Returns a new classifier from parameters.
        """
        raise NotImplementedError()

    @classmethod
    def load_(cls, path: PLike):
        x = cls.build()
        x.load(path)
        return x


class SklearnWellClassifier(WellClassifier, BuildableWellClassifier, metaclass=abc.ABCMeta):
    """
    A well classifier backed by a single scikit-learn classifier.
    Note that the constructer is typed as requiring a `ForestClassifier`, but this is only for better tab completion.
    It can accept any scikit-learn classifier.
    """

    def __init__(self, model: AnySklearnClassifier):
        super().__init__()
        self.model = model
        self._trained_decision = None

    @classmethod
    def model_class(cls) -> Type:
        raise NotImplementedError()

    @property
    def params(self) -> Mapping[str, Any]:
        return self.model.get_params()

    @params.setter
    def params(self, **params):
        self._verify_untrained()
        self.model.set_params(**params)

    @abcd.override_recommended
    def statistics(self) -> Mapping[str, Any]:
        return {}

    def load(self, path: PLike) -> None:
        self._verify_untrained()
        path = Path(path)
        if path.suffix == ".pkl":
            path = path.parent
        path = ClassifierPath(path)
        path.exists()
        try:
            try:
                self.info = path.load_info()
            except Exception:
                raise LoadError("Failed to load model metadata at {}".format(path.info_json))
            try:
                self.model = joblib.load(str(path.model_pkl))
            except Exception:
                raise LoadError("Failed to load model at {}".format(path.model_pkl))
            if self.info["params"] != self.params:
                logger.error(
                    "Loaded model params don't match: {} in info and {} in classifier".format(
                        self.info["params"], self.params
                    )
                )
            self.info["params"] = self.params
        except:  # don't allow a partial state
            self.info = None
            self.model = None
            raise
        logger.debug("Loaded model at {}".format(path.model_pkl))

    def save(self, path: PLike) -> None:
        self._verify_trained()
        path = Path(path)
        if str(path).endswith("model.pkl"):
            path = path.parent
        path = ClassifierPath(path)
        logger.debug("Saving model to {} ...".format(path.model_pkl))
        info = copy(self.info)
        info["params"] = self.params
        info["stats"] = self.statistics()
        try:
            path.prep()
            path.save_info(info)
        except Exception:
            raise LoadError("Failed to save model metadata to {}".format(path.info_json))
        try:
            joblib.dump(self.model, str(path.model_pkl), protocol=kale_env.pickle_protocol)
        except Exception:
            raise LoadError("Failed to save model to {}".format(path.model_pkl))
        logger.debug("Saved model to {}".format(path.model_pkl))

    def train(self, df: WellFrame) -> None:
        self._verify_train(df["well"].values, df["name"].values, df.columns.values)
        logger.info(self._startup_string(df))
        reps = df.n_replicates()
        logger.minor(
            "Training with replicates: {}".format(
                ", ".join([k + "=" + str(v) for k, v in reps.items()])
            )
        )
        if len(set(reps.values())) > 1:
            logger.caution("Training with an imbalanced set")
        # fit
        t0, d0 = time.monotonic(), datetime.now()
        try:
            self.model.fit(*df.xy())
        except Exception:
            raise ClassifierTrainFailedError(
                "Failed to train (names {} and runs {})".format(df.unique_names(), df.unique_runs())
            )
        t1, d1 = time.monotonic(), datetime.now()
        # update info
        self._update_wf_info(df)
        self.info["started"], self.info["finished"], self.info["seconds_taken"] = d0, d1, t1 - t0
        # show stats, but don't overwhelm
        # note that calling statistics() here can add some time (ex oob_score)
        # this "inflates" the training time, which is arguably more useful
        stats = [
            str(k) + "=" + ("%.3g" % v if isinstance(v, (int, float)) else str(v))
            for k, v in self.statistics().items()
        ]
        logger.info(
            "Finished training. Took {}s. {}".format(
                round(t1 - t0), ", ".join(stats) if len(stats) < 4 else ""
            )
        )
        if 4 <= len(stats) <= 50:
            logger.minor("Statistics: {}".format(", ".join(stats)))

    def test(self, df: WellFrame) -> DecisionFrame:
        logger.minor(
            "Testing on names {} and runs {} ...".format(df.unique_names(), df.unique_runs())
        )
        self._verify_test(df["well"].values, df["name"].values, df.columns.values)
        X, y = df.xy()
        labels = self.model.classes_
        try:
            predictions = self.model.predict_proba(X)
        except Exception:
            raise ClassifierPredictFailedError(
                "Failed to test (names {} and runs {})".format(df.unique_names(), df.unique_runs())
            )
        return DecisionFrame.of(y, labels, predictions, df["well"].values)

    def _startup_string(self, df):
        return "Training on {} labels and {} features using {} examples, {} runs, and {} estimators on {} core(s).".format(
            len(df.unique_names()),
            df.feature_length(),
            len(df),
            len(df["run"].unique()),
            self.model.n_estimators,
            1 if self.model.n_jobs is None else self.model.n_jobs,
        )


class SklearnWfClassifierWithOob(
    SklearnWellClassifier, HasOob, BuildableWellClassifier, metaclass=abc.ABCMeta
):
    def __init__(self, model: AnySklearnClassifier):
        model.oob_score = True  # ignore user preference so that oob_score() is defined
        super().__init__(model)
        self._trained_decision = None

    def statistics(self) -> Mapping[str, Any]:
        return {**super().statistics(), **{"oob_score": self.oob_score}}

    def save_to_dir(
        self,
        path: PLike,
        exist_ok: bool = True,
        figures: bool = False,
        sort: bool = True,
        runs: Optional[Sequence[int]] = None,
        label_colors: Optional[Mapping[str, str]] = None,
    ):
        from kale.viz.figures import FigureSaver

        path = Tools.prepped_dir(path, exist_ok=exist_ok)
        path = ClassifierPath(path)
        logger.debug("Saving info{} to {}".format(path, " and figures" if figures else ""))
        self._verify_trained()
        self.save(path.model_pkl)
        decision = self.training_decision
        decision.to_csv(path.decision_csv)
        confusion = decision.confusion()
        if sort:
            with logger.suppressed_other("clana", below="WARNING"):
                confusion = confusion.sort(deterministic=True)
        confusion.to_csv(path.confusion_csv, index_label="name")
        accuracy = decision.accuracy()
        accuracy.to_csv(path.accuracy_csv)
        if isinstance(self, HasWeights):
            weights = self.weights
            pd.Series(weights, name="weight").to_hdf(str(path.weight_h5), path.weight_h5_key)
        if figures:
            with FigureTools.clearing():
                FigureSaver().save(accuracy.swarm(), path.swarm_pdf)
                FigureSaver().save(
                    confusion.heatmap(runs=runs, label_colors=label_colors), path.confusion_pdf
                )

    @property
    def oob_score(self) -> float:
        self._verify_trained()
        logger.debug("Calculating out-of-bag score...")
        return self.model.oob_score_

    @property
    def training_decision(self) -> DecisionFrame:
        logger.debug("Calculating training decision function...")
        self._verify_trained()
        if self._trained_decision is None:
            correct_labels = self.info["labels"]
            labels = self.model.classes_
            self._trained_decision = DecisionFrame.of(
                correct_labels, labels, self.model.oob_decision_function_, self.info["wells"]
            )
        return self._trained_decision


class SklearnWfClassifierWithWeights(SklearnWellClassifier, HasWeights, metaclass=abc.ABCMeta):
    def __init__(self, model: AnySklearnClassifier):
        super().__init__(model)
        self._weights = None

    @property
    def weights(self) -> Sequence[float]:
        logger.debug("Calculating weights...")
        if self._weights is None:
            self._weights = self.model.feature_importances_
        return self._weights


class Ut:
    """Tiny utilities."""

    @classmethod
    def depths(cls, model) -> Sequence[int]:
        return [t.tree_.max_depth for t in model.model.estimators_]


class WellForestClassifier(SklearnWfClassifierWithOob, SklearnWfClassifierWithWeights):
    cached_name = "WellForestClassifier"

    @classmethod
    def build(cls, **kwargs):
        kwargs = copy(kwargs)
        if "n_estimators" not in kwargs:
            kwargs["n_estimators"] = 1000
        return WellForestClassifier(RandomForestClassifier(**kwargs))

    @classmethod
    def model_class(cls) -> Type[AnySklearnClassifier]:
        return RandomForestClassifier

    def depths(self) -> Sequence[int]:
        return Ut.depths(self)


class WellClassifiers:
    _classifier_cache = {RandomForestClassifier.__qualname__: WellForestClassifier}

    @classmethod
    def forest(cls, **kwargs):
        return WellForestClassifier.build(**kwargs)

    @classmethod
    def new_class(
        cls, model: Type[AnySklearnClassifier], **default_kwargs
    ) -> Type[SklearnWellClassifier]:
        qname = (
            model.__qualname__
            + (":" + ",".join([str(k) + "=" + str(v) for k, v in default_kwargs.items()]))
            if len(default_kwargs) > 0
            else ""
        )
        if qname in WellClassifiers._classifier_cache:
            logger.debug("Loading existing type {}".format(qname))
            return WellClassifiers._classifier_cache[qname]
        supers = WellClassifiers._choose_classes(model)

        class X(*supers):
            @classmethod
            def model_class(cls) -> Type[AnySklearnClassifier]:
                return model

            @classmethod
            def build(cls, **kwargs):
                args = copy(default_kwargs)
                args.update(kwargs)
                return X(model(**args))

        X.cached_name = qname
        X.__name__ = "Well" + str(model.__name__)
        if isinstance(model, AnySklearnClassifier):
            X.depths = Ut.depths
        WellClassifiers._classifier_cache[qname] = X
        logger.minor("Registered new type {}".format(qname))
        return X

    @classmethod
    def _choose_classes(cls, model):
        has_oob = hasattr(model, "oob_score_") and hasattr(model, "oob_decision_function_")
        has_weights = hasattr(model, "feature_importances_")
        supers = []
        if has_oob:
            supers.append(SklearnWfClassifierWithOob)
        if has_weights:
            supers.append(SklearnWfClassifierWithOob)
        if len(supers) == 0:
            supers = [SklearnWellClassifier]
        return supers


__all__ = [
    "WellClassifier",
    "SklearnWfClassifierWithOob",
    "SklearnWfClassifierWithWeights",
    "WellForestClassifier",
    "WellClassifiers",
]
