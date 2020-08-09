from chemfish.core._imports import *

from chemfish.core.valar_singleton import *
from chemfish.core import KaleResources, log_factory
from pocketutils.tools.common_tools import CommonTools
from pocketutils.tools.filesys_tools import FilesysTools

# I really don't understand why this is needed here
for handler in logging.getLogger().handlers:
    handler.setFormatter(log_factory.formatter)

# NOTE!!
# The environment variable used to be 'KALE_CONFIG_PATH'
# We changed it to 'KALE_CONFIG' in 1.13.0 to prefer not using it, unless it was created by the installer
MAIN_DIR = Path.home() / ".chemfish"
CONFIG_PATH = os.environ.get("KALE_CONFIG", MAIN_DIR / "chemfish.config")
if CONFIG_PATH is None:
    raise FileDoesNotExistError("No config file at {}".format(CONFIG_PATH))
VIZ_PATH = MAIN_DIR / "chemfish_viz.properties"


@abcd.auto_repr_str()
@abcd.auto_eq(exclude=None)
@abcd.auto_info()
class KaleEnvironment:
    """
    A collection of settings for Kale.
    Python files in Kale use this singleton class directly.
    This is loaded from a file in the user's home directory at ~/chemfish.config.
        : username: The username in valar.users; no default
        : cache_dir: The location of the top-level cache path; defaults to ~/valar-cache
        : video_cache_dir:  The location of the cache for videos; defaults to  ~/valar-cache/videos
        : shire_path: The local or remote path to the Shire (raw data storage); by default this a location on Valinor
        : audio_waveform: Kale will **save** StimFrame objects to the cache with audio waveforms; Enabling this will cause audio_waveform= arguments to be always true
        : chembl_cache_path: The path to the ChEMBL cache SQLlite file; by default this is 'chembl.sqlite' under the valar cache.
        : matplotlib_style: The path to a Matplotlib stylesheet; defaults to Matplotlib default
        : use_multicore_tsne: Enable the multicore_tsne package
        : pickle_protocol: Protocol used in Python pickle; see https://docs.python.org/3/library/pickle.html#pickle.HIGHEST_PROTOCOL; 4 by default
        : joblib_compression_level: Used in joblib.dump compress parameter if the filename ends with one of (‘.z’, ‘.gz’, ‘.bz2’, ‘.xz’ or ‘.lzma’); 3 by default
        : chemfish_log_level: The log level recommended to be used for logging statements within Kale; set up by jupyter.py
        : global_log_level: The log level recommended to be used for logging statements globally; set up by jupyter.py
        : viz_file: Path to chemfish-specific visualization options in the style of Matplotlib RC
        : n_cores: Default number of cores for some jobs, including with parallelize()
        : jupyter_template: Path to a Jupyter template text file
        : quiet: Ignore startup messages, etc, for knowledgable users
    """

    def __init__(self):
        self.config_file = Path(CONFIG_PATH).expanduser()
        if not self.config_file.exists():
            raise MissingResourceError("No config file at path {}".format(self.config_file))
        props = self._get_props()

        def _try(key: str, fallback=None):
            return props.get(key, fallback)

        self.home = Path(__file__).parent.parent
        self.username = _try("username")
        if self.username is None:
            raise MissingConfigKeyError("Must specify username in {}".format(self.config_file))
        self.user = Users.fetch(self.username)
        self.user_ref = Refs.fetch("manual:" + self.username)
        self.chemfish_log_level = _try("chemfish_log_level", "INFO")
        self.global_log_level = _try("global_log_level", "INFO")
        self.cache_dir = _try("cache", Path.home() / "valar-cache")
        self.video_cache_dir = Path(
            _try("video_cache", Path(self.cache_dir, "videos")).expanduser()
        )
        self.shire_path = _try("shire_path", "valinor:/shire/")
        self.audio_waveform = CommonTools.parse_bool(_try("save_with_audio_waveform", False))
        self.matplotlib_style = Path(
            _try("matplotlib_style", KaleResources.path("styles", "basic.mplstyle"))
        ).expanduser()
        self.use_multicore_tsne = CommonTools.parse_bool(_try("multicore_tsne", False))
        self.joblib_compression_level = int(_try("joblib_compression_level", 3))
        self.n_cores = int(_try("n_cores", 1))
        self.jupyter_template = Path(
            _try("jupyter_template", KaleResources.path("jupyter_template.txt"))
        ).expanduser()
        self._configure_chembl(_try)
        self.viz_file = Path(_try("viz_file", VIZ_PATH)).expanduser()
        self.quiet = CommonTools.parse_bool(_try("quiet", False))
        if not self.viz_file.exists():
            raise MissingResourceError("No viz file at path {}".format(self.viz_file))
        self._adjust_logging()
        if not self.quiet:
            logger.info("Read {} .".format(self.config_file))
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        if not self.quiet:
            logger.info(
                "Set {} chemfish config items. Run 'print(chemfish_env.info())' for details.".format(
                    len(props)
                )
            )

    def _get_props(self):
        try:
            props = {
                k: v.strip("\t '\"")
                for k, v in FilesysTools.read_properties_file(self.config_file).items()
            }
        except ParsingError as e:
            raise MissingConfigKeyError("Bad chemfish config file {}".format(self.config_file)) from e
        return props

    def _adjust_logging(self):
        logger.setLevel(self.chemfish_log_level)
        logging.getLogger(self.global_log_level)
        if not self.quiet:
            logger.info(
                "Set global log level to {} and chemfish to {}.".format(
                    self.global_log_level, self.chemfish_log_level
                )
            )

    def _configure_chembl(self, _try):
        # the default is to never expire; clear manually instead
        self.chembl_cache_path = _try("chembl_cache_path", Path(self.cache_dir, "chembl.sqlite"))
        self._chembl_settings = None
        try:
            from chembl_webresource_client.settings import Settings
        except ImportError:
            logger.error("Could not set ChEMBL cache settings: Could not import ChEMBL")
        else:
            try:
                self._chembl_settings = Settings.Instance()
                Settings.Instance().CACHE_NAME = str(self.chembl_cache_path)
                Settings.Instance().CACHING = bool(_try("chembl_caching", True))
                Settings.Instance().TOTAL_RETRIES = int(_try("chembl_total_retries", 1))
                Settings.Instance().FAST_SAVE = bool(_try("chembl_fast_save", True))
                Settings.Instance().TIMEOUT = _try(
                    "chembl_cache_expire_seconds", 100 * 365 * 24 * 60 * 60
                )
            except Exception as e:
                raise ConfigError("Failed to set ChEMBL settings: Bad variable format") from e


chemfish_env = KaleEnvironment()

__all__ = ["KaleEnvironment", "chemfish_env"]
