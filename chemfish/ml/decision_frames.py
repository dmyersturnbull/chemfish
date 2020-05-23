from __future__ import annotations
from dscience.ml.decision_frame import DecisionFrame as _DF
from kale.ml.accuracy_frames import AccuracyFrame
from kale.ml.confusion_matrices import ConfusionMatrix


class DecisionFrame(_DF):
    def confusion(self) -> ConfusionMatrix:
        return ConfusionMatrix(super().confusion())

    def accuracy(self) -> AccuracyFrame:
        return AccuracyFrame(super().accuracy())


__all__ = ["DecisionFrame"]
