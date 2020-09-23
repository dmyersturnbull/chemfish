
import joblib
from sklearn.ensemble import RandomForestClassifier

from chemfish.core.core_imports import *
from chemfish.ml import ClassifierPath, SaveableTrainable
from chemfish.ml.decision_frames import *
from chemfish.construction.wf_builders import *
from chemfish.viz.utils.figures import *
from chemfish.ml.classifiers import *
from chemfish.ml.classifiers import AnySklearnClassifier, SklearnWellClassifier

class WellClassifiers:
    """"""

    _classifier_cache = {RandomForestClassifier.__qualname__: WellForestClassifier}

    @classmethod
    def forest(cls, **kwargs) -> WellForestClassifier:
        """


        Args:
            **kwargs:

        Returns:

        """
        return WellForestClassifier.build(**kwargs)

    @classmethod
    def new_class(
        cls, model: Type[AnySklearnClassifier], **default_kwargs
    ) -> Type[SklearnWellClassifier]:
        """


        Args:
            model: Type[AnySklearnClassifier]:
            **default_kwargs:

        Returns:

        """
        qname = (
            model.__qualname__
            + (":" + ",".join([str(k) + "=" + str(v) for k, v in default_kwargs.items()]))
            if len(default_kwargs) > 0
            else ""
        )
        if qname in WellClassifiers._classifier_cache:
            logger.debug(f"Loading existing type {qname}")
            return WellClassifiers._classifier_cache[qname]
        supers = WellClassifiers._choose_classes(model)

        class X(*supers):
            """ """

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
        logger.minor(f"Registered new type {qname}")
        return X

    @classmethod
    def _choose_classes(cls, model):
        """


        Args:
            model:

        Returns:

        """
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
