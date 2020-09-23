"""

"""
import IPython
from IPython.display import HTML, Markdown, display
from pandas.plotting import register_matplotlib_converters
from pocketutils.notebooks.j import J, JFonts

from chemfish.core.core_imports import *
from chemfish.startup import *

pd.Series.reverse = pd.DataFrame.reverse = lambda self: self[::-1]
from pocketutils.notebooks.magic_template import *
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from chemfish import __version__
from chemfish.startup import *
import pydub
import librosa.display as ldisplay

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


def _plot_all(it: Iterable[Tup[str, Figure]]) -> None:
    """

    Args:
        it:
    """
    for name, figure in it:
        print(f"Plotting {name}")
        plt.show(figure)


plt.show_all = _plot_all

Namers = WellNamers
Cols = WellFrameColumns



class AudioTools:
    """ """

    @classmethod
    def listen(cls, path: Union[str, PurePath, bytes]):
        """
        Returns an audio container that Jupyter notebook will display.
        Must be run from a Jupyter notebook.
        Will raise an ImportError if IPython cannot be imported.

        Args:
            path: The local path to the audio file

        Returns:
            A jupyter notebook ipd.Audio object

        """
        # noinspection PyPackageRequirements
        import IPython.display as ipd

        if isinstance(path, (str, PurePath)):
            path = str(Path(path))
            return ipd.Audio(filename=path)
        else:
            return ipd.Audio(data=path)

    @classmethod
    def save(
        cls, audio_segment: pydub.AudioSegment, path: PathLike, audio_format: str = "flac"
    ) -> None:
        """


        Args:
            audio_segment:
            path: PathLike:
            audio_format:

        Returns:

        """
        path = Tools.prepped_file(path)
        audio_segment.export(path, format=audio_format)

    @classmethod
    def load_pydub(cls, path: PathLike) -> pydub.AudioSegment:
        """


        Args:
            path: PathLike:

        Returns:

        """
        path = str(Path(path))
        # TODO sample_width=2, frame_rate=44100, channels=1 ???
        return pydub.AudioSegment.from_file(path)


register_matplotlib_converters()
