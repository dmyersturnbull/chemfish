"""
Metadata for this project.
"""

import logging
from pathlib import Path

from importlib.metadata import PackageNotFoundError, metadata as __load

logger = logging.getLogger(Path(__file__).parent.name)

__metadata = None
try:
    __metadata = __load(Path(__file__).absolute().parent.name)
    __status__ = "Development"
    __copyright__ = "Copyright 2016–2020"
    __date__ = "2020-08-14"
    __uri__ = __metadata["home-page"]
    __title__ = __metadata["name"]
    __summary__ = __metadata["summary"]
    __license__ = __metadata["license"]
    __version__ = __metadata["version"]
    __author__ = __metadata["author"]
    __maintainer__ = __metadata["maintainer"]
    __contact__ = __metadata["maintainer"]
except PackageNotFoundError:  # pragma: no cover
    logger.error(
        "Could not load package __metadata for {}. Is it installed?".format(
            Path(__file__).absolute().parent.name
        )
    )


if __name__ == "__main__":  # pragma: no cover
    if __metadata is not None:
        print("{} (v{})".format(__metadata["name"], __metadata["version"]))
    else:
        print("Unknown project info")
