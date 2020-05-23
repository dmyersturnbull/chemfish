"""
Sets up standard imports and settings for Kale.
"""
import os

################################
# set up warnings
################################

from dscience.core.warning_utils import *

__filterer = (
    GlobalWarningUtils.init()
    .filter_common_numeric()
    .substring_once("Number of features and number of timestamps differ by 1")
)

################################
# set up logger for Jupyter
################################
import logging

from kale.core import logger, log_factory
from kale.core.environment import kale_env

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

# dscience
from dscience.core import frozenlist
from dscience.core.io import DelegatingWriter, LogWriter
from dscience.support.toml_data import *
from dscience.biochem.multiwell_plates import *
from dscience.ml.sklearn_utils import *
from dscience.analysis.stats import *

################################
# kale imports
################################

# core
from kale.core.core_imports import *
from kale.core.tools import *

# calc
from kale.calc.chem import *

# model
from kale.model import *
from kale.model.sensors import *
from kale.model.concerns import *
from kale.model.metrics import *
from kale.model.well_namers import *
from kale.model.stim_frames import *
from kale.model.assay_frames import *
from kale.model.well_frames import *
from kale.model.wf_builders import *
from kale.model.wf_tools import WellFrameColumns
from kale.model.features import *
from kale.model.videos import *
from kale.model.compound_names import *
from kale.model.treat_displayers import *
from kale.model.treatments import *
from kale.model.app_frames import *
from kale.model.roi_tools import *
from kale.model.audio import *
from kale.model.responses import *
from kale.model.comp_iters import *
from kale.model.plate_frames import *
from kale.model.aug_well_frames import *

# caches
from kale.caches.sensor_caches import *
from kale.caches.audio_caches import *
from kale.caches.stim_caches import *
from kale.caches.video_cache import *
from kale.caches.wf_caches import *
from kale.caches.caching_wfs import *
from kale.caches.datasets import *

# viz
from kale.viz.heatmaps import *
from kale.viz.timelines import *
from kale.viz.stim_plots import *
from kale.viz.importance_plots import *
from kale.viz.breakdown_plots import *
from kale.viz.well_plots import *
from kale.viz import plt
from kale.viz.figures import *
from kale.viz.traces import *
from kale.viz.accuracy_plots import *
from kale.viz.confusion_plots import *
from kale.viz.biomarker_plots import *
from kale.viz.response_plots import *

from kale.viz.kvrc import KvrcDefaults, KVRC as kale_rc

# ml
from kale.ml import ClassifierPath
from kale.ml.classifiers import *
from kale.ml.decision_frames import *
from kale.ml.transformers import *
from kale.ml.accuracy_frames import *
from kale.ml.confusion_matrices import *
from kale.ml.multi_trainers import *
from kale.ml.spindles import *

# analysis
from kale.analysis.phenosearch import *
from kale.analysis.mandos_search import *
from kale.analysis.auto_traces import *

# lookups
from kale.lookups.layouts import *
from kale.lookups.lookups import *
from kale.lookups.biomarkers import *
from kale.lookups.submission_tools import *
from kale.lookups.template_tools import *
from kale.lookups.mandos import *
from kale.lookups.fuzzy import *

# root
from kale.quick import *

################################
# package overrides
################################

# and this was reset
logging.getLogger().setLevel(kale_env.global_log_level)

# I don't know why this needs to happen twice
__filterer.substring_never(".*libuv only supports.*")

################################
# startup messages
################################

if not kale_env.quiet:
    logger.notice(
        "Kale version {}. Started in {}s.".format(
            kale_version.strip(), round(time.monotonic() - kale_start_clock), 1
        )
    )
    logger.debug("Figure dimensions: {}{}{}".format(kale_rc.height, Chars.times, kale_rc.width))
    logger.info("Severity key: " + Severity.key_str())
if not kale_env.quiet and matplotlib.get_backend().endswith("backend_inline"):
    logger.error("Using inline backend. Use '%matplotlib widget' instead.")
else:
    logger.debug("Using backend: {}".format(matplotlib.get_backend()))
