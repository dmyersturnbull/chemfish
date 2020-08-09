"""
Sets up standard imports and settings for Kale.
"""
import os

################################
# set up warnings
################################

from pocketutils.logging.warning_utils import *

__filterer = (
    GlobalWarningUtils.init()
    .filter_common_numeric()
    .substring_once("Number of features and number of timestamps differ by 1")
)

################################
# set up logger for Jupyter
################################
import logging

from chemfish.core import logger, log_factory
from chemfish.core.environment import chemfish_env

logging.getLogger("chemspipy").setLevel(logging.WARNING)
logging.getLogger("url_query").setLevel(logging.WARNING)

################################
# external imports
################################
from decimal import Decimal
import traceback
from io import StringIO
from tempfile import TemporaryDirectory, TemporaryFile, NamedTemporaryFile
from collections import OrderedDict, namedtuple

# external packages
import dill
import matplotlib
import sklearn
import joblib
from natsort import natsorted
import seaborn as sns
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.gridspec as gridspec
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC, SVC

# pocketutils
from pocketutils.core import frozenlist
from pocketutils.core.io import DelegatingWriter, LogWriter
from pocketutils.support.toml_data import *
from pocketutils.biochem.multiwell_plates import *
from pocketutils.ml.sklearn_utils import *
from pocketutils.analysis.stats import *

################################
# chemfish imports
################################

# core
from chemfish.core.core_imports import *
from chemfish.core.tools import *

# calc
from chemfish.calc.chem import *

# model
from chemfish.model import *
from chemfish.model.sensors import *
from chemfish.model.concerns import *
from chemfish.model.metrics import *
from chemfish.model.well_names import *
from chemfish.model.stim_frames import *
from chemfish.model.assay_frames import *
from chemfish.model.well_frames import *
from chemfish.model.wf_builders import *
from chemfish.model.wf_tools import WellFrameColumns
from chemfish.model.features import *
from chemfish.model.videos import *
from chemfish.model.compound_names import *
from chemfish.model.treatment_names import *
from chemfish.model.treatments import *
from chemfish.model.app_frames import *
from chemfish.model.roi_tools import *
from chemfish.model.audio import *
from chemfish.model.responses import *
from chemfish.model.comp_iters import *
from chemfish.model.plate_frames import *
from chemfish.model.aug_well_frames import *

# caches
from chemfish.caches.sensor_caches import *
from chemfish.caches.audio_caches import *
from chemfish.caches.stim_caches import *
from chemfish.caches.video_cache import *
from chemfish.caches.wf_caches import *
from chemfish.caches.caching_wfs import *
from chemfish.caches.datasets import *

# viz
from chemfish.viz.heatmaps import *
from chemfish.viz.timelines import *
from chemfish.viz.stim_plots import *
from chemfish.viz.importance_plots import *
from chemfish.viz.breakdown_plots import *
from chemfish.viz.well_plots import *
from chemfish.viz import plt
from chemfish.viz.figures import *
from chemfish.viz.traces import *
from chemfish.viz.accuracy_plots import *
from chemfish.viz.confusion_plots import *
from chemfish.viz.biomarker_plots import *
from chemfish.viz.response_plots import *

from chemfish.viz.kvrc import KvrcDefaults, KVRC as chemfish_rc

# ml
from chemfish.ml import ClassifierPath
from chemfish.ml.classifiers import *
from chemfish.ml.decision_frames import *
from chemfish.ml.transformers import *
from chemfish.ml.accuracy_frames import *
from chemfish.ml.confusion_matrices import *
from chemfish.ml.multi_trainers import *
from chemfish.ml.spindles import *

# analysis
from chemfish.analysis.phenosearch import *
from chemfish.analysis.mandos_search import *
from chemfish.analysis.auto_traces import *

# lookups
from chemfish.lookups.layouts import *
from chemfish.lookups.lookups import *
from chemfish.lookups.biomarkers import *
from chemfish.lookups.submission_tools import *
from chemfish.lookups.template_tools import *
from chemfish.lookups.mandos import *
from chemfish.lookups.fuzzy import *

# root
from chemfish.quick import *

################################
# package overrides
################################

# and this was reset
logging.getLogger().setLevel(chemfish_env.global_log_level)

# I don't know why this needs to happen twice
__filterer.substring_never(".*libuv only supports.*")

################################
# startup messages
################################

if not chemfish_env.quiet:
    logger.notice(
        "Kale version {}. Started in {}s.".format(
            chemfish_version.strip(), round(time.monotonic() - chemfish_start_clock), 1
        )
    )
    logger.debug("Figure dimensions: {}{}{}".format(chemfish_rc.height, Chars.times, chemfish_rc.width))
    logger.info("Severity key: " + Severity.key_str())
if not chemfish_env.quiet and matplotlib.get_backend().endswith("backend_inline"):
    logger.error("Using inline backend. Use '%matplotlib widget' instead.")
else:
    logger.debug("Using backend: {}".format(matplotlib.get_backend()))
