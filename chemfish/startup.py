"""
Sets up standard imports and settings for Chemfish.
"""
import os

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

from chemfish.core import log_factory, logger
from chemfish.core.environment import chemfish_env

logging.getLogger("chemspipy").setLevel(logging.WARNING)
logging.getLogger("url_query").setLevel(logging.WARNING)

import traceback
from collections import OrderedDict, namedtuple

################################
# external imports
################################
from decimal import Decimal
from io import StringIO
from tempfile import NamedTemporaryFile, TemporaryDirectory, TemporaryFile

# external packages
import joblib
import matplotlib
import matplotlib.gridspec as gridspec
import seaborn as sns
import sklearn
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from natsort import natsorted
from pocketutils.biochem.multiwell_plates import *

# pocketutils
from pocketutils.core import frozenlist
from pocketutils.core.dot_dict import *
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC, LinearSVC

from chemfish.analysis.auto_analyses import *
from chemfish.analysis.mandos_searches import *

# analysis
from chemfish.analysis.phenosearches import *
from chemfish.caches.audio_caches import *
from chemfish.caches.caching_wfs import *

# caches
from chemfish.caches.sensor_caches import *
from chemfish.caches.stim_caches import *
from chemfish.caches.wf_caches import *

# core
from chemfish.core.core_imports import *
from chemfish.core.tools import *
from chemfish.lookups.fuzzy import *

# lookups
from chemfish.lookups.layouts import *
from chemfish.lookups.lookups import *
from chemfish.lookups.mandos import *
from chemfish.lookups.submissions import *
from chemfish.lookups.templates import *

# ml
from chemfish.ml import ClassifierPath
from chemfish.ml.accuracy_frames import *
from chemfish.ml.classifiers import *
from chemfish.ml.confusion_matrices import *
from chemfish.ml.decision_frames import *
from chemfish.ml.multi_trainers import *
from chemfish.ml.spindles import *
from chemfish.ml.transformers import *

# model
from chemfish.model import *
from chemfish.model.app_frames import *
from chemfish.model.assay_frames import *
from chemfish.model.audio import *
from chemfish.model.case_control_comparisons import *
from chemfish.model.compound_names import *
from chemfish.model.concerns import *
from chemfish.model.features import *
from chemfish.model.metrics import *
from chemfish.model.plate_frames import *
from chemfish.model.responses import *
from chemfish.model.roi_tools import *
from chemfish.model.sensors import *
from chemfish.model.stim_frames import *
from chemfish.model.treatment_names import *
from chemfish.model.treatments import *
from chemfish.model.well_frames import *
from chemfish.model.well_names import *
from chemfish.model.wf_builders import *
from chemfish.model.wf_tools import WellFrameColumns

# root
from chemfish.quick import *
from chemfish.viz import plt
from chemfish.viz.accuracy_plots import *
from chemfish.viz.breakdown_plots import *
from chemfish.viz.confusion_plots import *
from chemfish.viz.figures import *

# viz
from chemfish.viz.heatmaps import *
from chemfish.viz.importance_plots import *
from chemfish.viz.kvrc import KvrcDefaults, chemfish_rc
from chemfish.viz.response_plots import *
from chemfish.viz.stim_plots import *
from chemfish.viz.timeline_plots import *
from chemfish.viz.trace_plots import *
from chemfish.viz.well_plots import *

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
