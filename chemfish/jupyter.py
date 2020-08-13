import IPython
from IPython.display import HTML, Markdown, display
from pandas.plotting import register_matplotlib_converters
from pocketutils.j import J, JFonts

from chemfish.core.core_imports import *
from chemfish.core.magics import *
from chemfish.startup import *

pd.Series.reverse = pd.DataFrame.reverse = lambda self: self[::-1]

# pd.set_option("display.max_rows", 120)
# pd.set_option('display.max_colwidth', 400)
# pd.set_option('display.max_columns', 50)
J.full_width()
# noinspection PyTypeChecker
display(HTML("<style>.container { width:100% !important; }</style>"))
logger.debug("Set Jupyter & Pandas display options")

register_matplotlib_converters()
