import logging
import re
import warnings

warnings.filterwarnings(action="ignore", module=".*dtypes.py")
import humanfriendly as friendly
import tensorboard
import tensorflow as tf
import tensorflow.keras as keras
import tensorflow.keras.activations as activations
import tensorflow.keras.layers as layers
import tensorflow.keras.losses as losses
import tensorflow.keras.models as models
import tensorflow.keras.preprocessing as preprocessing
import tensorflow.keras.regularizers as regularizers
from tensorflow.keras.layers import (
    ELU,
    Activation,
    AveragePooling2D,
    BatchNormalization,
    Conv2D,
    Conv2DTranspose,
    Conv3D,
    Dense,
    Dropout,
    Embedding,
    Flatten,
    Input,
    Lambda,
    MaxPooling2D,
    Permute,
    Reshape,
)
from tensorflow.keras.losses import binary_crossentropy, mse
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import SGD, Adam, RMSprop
from tensorflow.keras.regularizers import l2
from tensorflow.keras.utils import Progbar
from tensorflow.python.client import device_lib

from chemfish.core import logger

devices = device_lib.list_local_devices()


def __name_device(x):
    pat = re.compile("name: [^,]+")
    return (
        x.name.replace("/device:", "").replace(":", ": #")
        + (
            ""
            if x.physical_device_desc == "" or pat.search(x.physical_device_desc) is None
            else ", " + pat.search(x.physical_device_desc).group(0)
        )
        + ", memory: "
        + friendly.format_size(x.memory_limit, binary=True)
    )


logger.notice("Loaded tensorflow {} and keras {}.".format(tf.__version__, keras.__version__))
logger.notice(
    "GPU(s) are {}available. Using {} devices:\n".format(
        "" if tf.test.is_gpu_available() else "NOT ", len(devices)
    )
    + "\n".join([__name_device(x) for x in devices])
)
