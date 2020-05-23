import IPython
from IPython.display import display, Markdown, HTML
from pandas.plotting import register_matplotlib_converters
from dscience.j import J, JFonts
from kale.core.core_imports import *
from kale.core.magics import *
from kale.startup import *

pd.Series.reverse = pd.DataFrame.reverse = lambda self: self[::-1]

# pd.set_option("display.max_rows", 120)
# pd.set_option('display.max_colwidth', 400)
# pd.set_option('display.max_columns', 50)
J.full_width()
# noinspection PyTypeChecker
display(HTML("<style>.container { width:100% !important; }</style>"))
logger.debug("Set Jupyter & Pandas display options")

register_matplotlib_converters()
