"""
Standard imports for internal code inside core.
Can depend on very common Python packages, and limited functions in pocketutils.core
Should only be used in modules that are strictly tied to chemfish (will always be specific to chemfish).
"""

from __future__ import annotations

import abc
import enum
import functools
import hashlib
import itertools
import json
import logging
import math
import operator
import os
import random
import re
import string
import sys
import time
import typing
from abc import ABCMeta
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
from copy import copy, deepcopy
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from functools import partial, partialmethod
from operator import attrgetter, itemgetter, methodcaller
from pathlib import Path, PurePath
from typing import (
    Any,
    ByteString,
    Callable,
    Collection,
    DefaultDict,
    Dict,
    FrozenSet,
    Generator,
    Generic,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Sized,
    SupportsBytes,
    SupportsFloat,
    SupportsInt,
)
from typing import Tuple as Tup
from typing import Type, TypeVar, Union, ValuesView
from warnings import warn

import decorateme as abcd
import numpy as np
import pandas as pd
from pocketutils.core import SmartEnum
from pocketutils.core.exceptions import *
from pocketutils.tools.common_tools import CommonTools

from chemfish.core import (
    ChemfishResources,
    chemfish_start_clock,
    chemfish_start_time,
    chemfish_version,
    logger,
)

zip_strict, zip_list = CommonTools.zip_strict, CommonTools.zip_list

PLike = Union[str, PurePath, os.PathLike]


def get1st(it: Iterable[Collection[Any]]):
    return [i[0] for i in it]


def get2nd(it: Iterable[Collection[Any]]):
    return [i[1] for i in it]


from pocketutils.core.exceptions import *


class NoFeaturesError(MissingResourceError):
    """The function required an array of video-calculated features, which were not available."""


class MultipleFrameratesError(MismatchedDataError):
    """More than one framerate value is included."""


class MultipleGenerationsError(MismatchedDataError):
    """Multiple data generations are included."""


class IncompatibleGenerationError(IncompatibleDataError):
    """The operation is not compatible with the Sauron data type given."""


class SauronxOnlyError(IncompatibleGenerationError):
    """A function called is available only for SauronX data."""


class ChemfishJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            # noinspection PyUnresolvedReferences
            import peewee

            if isinstance(obj, peewee.Field):
                return type(obj).__name__
        except ImportError:
            pass  # let the encode fail
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)
