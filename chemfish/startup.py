"""
Sets up standard imports and settings for Chemfish.
"""

from pocketutils.logging.warning_utils import *

################################
# set up warnings
################################


__filterer = (
    GlobalWarningUtils.init()
    .filter_common_numeric()
    .substring_once("Number of features and number of timestamps differ by 1")
)

################################
# set up logger for Jupyter
################################
import logging

logging.getLogger("chemspipy").setLevel(logging.WARNING)
logging.getLogger("url_query").setLevel(logging.WARNING)

################################
# external imports
################################

# external packages
import matplotlib

# pocketutils

# analysis

# caches

# core
from chemfish.core.core_imports import *

# lookups

# ml

# model
from chemfish.model.concerns import *

# root

# viz
from chemfish.viz.utils.kale_rc import chemfish_rc

################################
# package overrides
################################

# and this was reset
logging.getLogger().setLevel(chemfish_env.global_log_level)

# I don't know why this needs to happen twice
__filterer.substring_never(".*libuv only supports.*")

# numexpr's default is 8, which is excessive for most applications
# let's keep it between 1 and min(6, nCPU-1)
# setting this has the advantage of silencing the "NumExpr defaulting to 8 threads." logging
os.environ.setdefault("NUMEXPR_MAX_THREADS", str(max(1, min(6, os.cpu_count() - 1))))


################################
# startup messages
################################

logger.notice(
    f"Chemfish version {chemfish_version.strip()}. Started in {round(time.monotonic() - chemfish_start_clock)}s."
)
logger.debug(f"Figure dimensions: {chemfish_rc.height}×{chemfish_rc.width}")
logger.info("Severity key: " + Severity.key_str())
logger.debug(f"Using backend  {matplotlib.get_backend()}")
