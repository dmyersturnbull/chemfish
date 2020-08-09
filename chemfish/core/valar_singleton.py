# this could depend on internal_core_imports, but let's keep it light
import typing
from typing import Union, Iterable
import peewee
import os
from pathlib import PurePath
from datetime import datetime
import numpy as np
import decorateme as abcd
from valarpy.Valar import Valar as __Valar


@abcd.auto_singleton
class KaleValar(__Valar):
    def __init__(self):
        super().__init__()
        super().open()


Valar = KaleValar()
from valarpy.model import *

ExpressionLike = peewee.ColumnBase
ExpressionsLike = Union[ExpressionLike, Iterable[ExpressionLike]]
PLike = Union[str, PurePath, os.PathLike]
RunLike = Union[int, str, Runs, Submissions]
ControlLike = Union[int, str, ControlTypes]
SubmissionLike = Union[int, str, Submissions]
RoiLike = Union[int, Rois, typing.Tuple[Union[int, str, Wells], Union[int, str, Refs]]]
RunsLike = Union[RunLike, Iterable[RunLike]]
SauronLike = Union[int, str, Saurons]
SauronConfigLike = Union[int, SauronConfigs, typing.Tuple[Union[Saurons, int, str], datetime]]
BatteryLike = Union[int, str, Batteries]
AssayLike = Union[int, str, Assays]
UserLike = Union[int, str, Users]
RefLike = Union[int, str, Refs]
TempPlateLike = Union[int, str, TemplatePlates]
SupplierLike = Union[int, str, Suppliers]
BatchLike = Union[int, str, Batches]
CompoundLike = Union[int, str, Compounds]
NullableCompoundLike = Union[None, int, str, Compounds]
SensorLike = Union[int, str, Sensors]
SensorDataLike = Union[None, np.array, bytes, str]
StimulusLike = Union[Stimuli, int, str]

CompoundsLike = Union[CompoundLike, Iterable[CompoundLike]]
NullableCompoundsLike = Union[None, Compounds, int, str, Iterable[Union[None, Compounds, int, str]]]
BatchesLike = Union[BatchLike, Iterable[BatchLike]]
