import IPython
from IPython.display import HTML, Markdown, display
from pandas.plotting import register_matplotlib_converters
from pocketutils.notebooks.j import J, JFonts

from chemfish.core.core_imports import *
from chemfish.startup import *

pd.Series.reverse = pd.DataFrame.reverse = lambda self: self[::-1]
from pocketutils.notebooks.magic_template import *

from chemfish import __version__
from chemfish.core.environment import chemfish_env

(
    MagicTemplate.from_path(chemfish_env.jupyter_template)
    .add_version(__version__)
    .add_datetime()
    .add("username", chemfish_env.username)
    .add("author", chemfish_env.username.title())
    .add("config", chemfish_env.config_file)
).register_magic("chemfish")

J.full_width()
# noinspection PyTypeChecker
display(HTML("<style>.container { width:100% !important; }</style>"))
logger.debug("Set Jupyter & Pandas display options")

register_matplotlib_converters()
