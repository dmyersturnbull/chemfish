"""
Magic functions for Jupyter.
"""
from kale.core.tools import *
from kale import __version__
from kale.core.environment import kale_env
from dscience.support.magic_template import *

(
    MagicTemplate.from_path(kale_env.jupyter_template)
    .add_version(__version__)
    .add_datetime()
    .add("username", kale_env.username)
    .add("author", kale_env.username.title())
    .add("config", kale_env.config_file)
).register_magic("kale")

__all__ = []
