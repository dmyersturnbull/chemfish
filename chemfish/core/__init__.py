from __future__ import annotations

"""
Contains the lowest-level code in Kale.
This package cannot not depend on any other packages in Kale.
"""
import os, logging, warnings, time, enum
from functools import total_ordering
from copy import deepcopy
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from typing import Union, Mapping, Generator
from dscience.support.fancy_logger import *
from dscience.support.log_format import *
from kale import __version__ as kale_version

warnings.filterwarnings(
    action="ignore",
    message=".*Monkey-patching ssl after ssl has already been imported may lead to errors.*",
)


class KaleResources:
    @classmethod
    def path(cls, *parts) -> Path:
        return Path(Path(__file__).parent.parent, "resources", *parts)

    @classmethod
    def text(cls, *parts) -> str:
        return KaleResources.path(*parts).read_text(encoding="utf8")

    @classmethod
    def binary(cls, *parts) -> bytes:
        return KaleResources.path(*parts).read_bytes()


LogLevel.initalize()
logger = AdvancedLogger.create("kale")
log_factory = PrettyRecordFactory(7, 13, 5).modifying(logger)
logger.setLevel("INFO")  # good start; can be changed

kale_start_time = datetime.now()
kale_start_clock = time.monotonic()

__all__ = [
    "kale_version",
    "kale_start_time",
    "kale_start_clock",
    "LogLevel",
    "KaleResources",
    "logger",
    "log_factory",
]
