from __future__ import annotations

import sklearn.metrics as skmetrics

from chemfish.core.core_imports import *
from dataclasses import dataclass

@dataclass(frozen=True)
class MetricInfo:
    """A type of 2D metric such as ROC or Precision-Recall."""

    name: str
    score: str
    false: str
    true: str

    @classmethod
    def roc(cls):
        """ """
        return MetricInfo("ROC", "AUC (%)", "FPR (%)", "TPR (%)")

    @classmethod
    def pr(cls):
        """"""
        return MetricInfo(
            "Precision" + Chars.en + "Recall",
            "average precision (%)",
            "precision (%)",
            "recall (%)",
        )


@dataclass(frozen=True)
class MetricData:
    """
    Typically either ROC or Precision-Recall curves.
    """

    label: str
    control: Optional[str]
    score: float
    false: Sequence[float]
    true: Sequence[float]

    def __post_init__(self):
        if len(self.false) != len(self.true):
            raise LengthMismatchError(
                f"FPR has length {len(self.false)} but TPR has length {len(self.true)}"
            )

    @classmethod
    def roc(
        cls, label: str, control: Optional[str], true: Sequence[bool], scores: Sequence[float]
    ) -> MetricData:
        """


        Args:
            label: str:
            control: Optional[str]:
            true: Sequence[bool]:
            scores: Sequence[float]:

        Returns:

        """
        auc = skmetrics.roc_auc_score(true, scores)
        fpr, tpr, thresholds = skmetrics.roc_curve(true, scores)
        return MetricData(label, control, auc * 100.0, fpr * 100.0, tpr * 100.0)

    @classmethod
    def pr(
        cls, label: str, control: Optional[str], true: Sequence[bool], scores: Sequence[float]
    ) -> MetricData:
        """


        Args:
            label: str:
            control: Optional[str]:
            true: Sequence[bool]:
            scores: Sequence[float]:

        Returns:

        """
        score = skmetrics.average_precision_score(true, scores)
        precision, recall, thresholds = skmetrics.precision_recall_curve(true, scores)
        return MetricData(label, control, score * 100.0, precision * 100.0, recall * 100.0)


@dataclass(frozen=True)
class KdeData:
    """
    Kernel density estimation data.
    """

    samples: np.array
    support: Sequence[float]
    density: Sequence[float]
    params: Optional[Mapping[str, Any]]

    def density_df(
        self, support_start: Optional[float] = None, support_end: Optional[float] = None
    ) -> UntypedDf:
        """


        Args:
            support_start:
            support_end:

        Returns:

        """
        df = UntypedDf({"support": self.support, "density": self.density})
        if support_start is not None:
            df = df[df["support"] >= support_start]
        if support_end is not None:
            df = df[df["support"] <= support_end]
        return df

    @classmethod
    def from_scores(cls, df: BaseScoreFrame, **kwargs) -> KdeData:
        """


        Args:
            df:
            **kwargs:

        Returns:

        """
        return cls.from_samples(df["score"], **kwargs)

    @classmethod
    def from_samples(cls, samples: Sequence[float], **kwargs) -> KdeData:
        """


        Args:
            samples:
            **kwargs:

        Returns:

        """
        support, density = StatTools.kde(samples, **kwargs)
        return KdeData(samples, support, density, params=kwargs)


__all__ = ["MetricData", "MetricInfo", "BaseScoreFrame", "ScoreFrameWithPrediction", "KdeData"]
