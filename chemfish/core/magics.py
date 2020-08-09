"""
Magic functions for Jupyter.
"""
from chemfish.core.tools import *
from chemfish import __version__
from chemfish.core.environment import chemfish_env
from pocketutils.support.magic_template import *

(
    MagicTemplate.from_path(chemfish_env.jupyter_template)
    .add_version(__version__)
    .add_datetime()
    .add("username", chemfish_env.username)
    .add("author", chemfish_env.username.title())
    .add("config", chemfish_env.config_file)
).register_magic("chemfish")

__all__ = []
