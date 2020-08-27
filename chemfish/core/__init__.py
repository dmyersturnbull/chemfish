"""
Contains the lowest-level code in Chemfish.
This package cannot not depend on any other packages in Chemfish.
"""

from __future__ import annotations

import enum
import logging
import os
import time
import warnings
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from functools import total_ordering
from pathlib import Path
from typing import Generator, Mapping, Union

from pocketutils.logging.fancy_logger import *
from pocketutils.logging.log_format import *

from chemfish import __version__ as chemfish_version

warnings.filterwarnings(
    action="ignore",
    message=".*Monkey-patching ssl after ssl has already been imported may lead to errors.*",
)


class ChemfishResources:
    """ """

    @classmethod
    def path(cls, *parts) -> Path:
        """


        Args:
          *parts:

        Returns:

        """
        return Path(Path(__file__).parent.parent, "resources", *parts)

    @classmethod
    def text(cls, *parts) -> str:
        """


        Args:
          *parts:

        Returns:

        """
        return ChemfishResources.path(*parts).read_text(encoding="utf8")

    @classmethod
    def binary(cls, *parts) -> bytes:
        """


        Args:
          *parts:

        Returns:

        """
        return ChemfishResources.path(*parts).read_bytes()


LogLevel.initalize()
logger = AdvancedLogger.create("chemfish")
log_factory = PrettyRecordFactory(7, 13, 5).modifying(logger)
logger.setLevel("INFO")  # good start; can be changed

chemfish_start_time = datetime.now()
chemfish_start_clock = time.monotonic()

__all__ = [
    "chemfish_version",
    "chemfish_start_time",
    "chemfish_start_clock",
    "LogLevel",
    "ChemfishResources",
    "logger",
    "log_factory",
]
