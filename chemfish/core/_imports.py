"""
Standard imports for internal code inside core.
Can depend on very common Python packages, and limited functions in pocketutils.core
Should only be used in modules that are strictly tied to chemfish (will always be specific to chemfish).
"""

from __future__ import annotations

import typing
from typing import (
    Set,
    Iterator,
    Generic,
    Type,
    TypeVar,
    Collection,
    SupportsFloat,
    SupportsBytes,
    SupportsInt,
    ByteString,
    Iterable,
    Any,
    Sequence,
    Union,
    Optional,
    Callable,
    Mapping,
    KeysView,
    ValuesView,
    ItemsView,
    Dict,
    List,
    DefaultDict,
    FrozenSet,
    Sized,
    Iterator,
    Generator,
)
from typing import Tuple as Tup
import operator
import functools
from functools import partial, partialmethod
from operator import itemgetter, attrgetter, methodcaller
import enum, string, re, math, time, random, hashlib
from enum import Enum
import os, sys, json, itertools
from copy import copy, deepcopy
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from pathlib import Path, PurePath
import logging
from collections import OrderedDict, defaultdict
from contextlib import contextmanager
from warnings import warn
import abc
from abc import ABCMeta

import numpy as np
import pandas as pd

import decorateme as abcd
from pocketutils.tools.common_tools import CommonTools
from pocketutils.core import SmartEnum
from pocketutils.core.exceptions import *

from chemfish.core import (
    KaleResources,
    chemfish_version,
    chemfish_start_time,
    chemfish_start_clock,
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


class KaleJsonEncoder(json.JSONEncoder):
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
