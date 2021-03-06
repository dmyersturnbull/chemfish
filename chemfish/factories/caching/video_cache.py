from chemfish.core.core_imports import *
from chemfish.core.video_core import VideoCore
from chemfish.factories.caches import AVideoCache
from chemfish.model.videos import *

DEFAULT_SHIRE_STORE = PurePath(chemfish_env.shire_path) / "store"


class VideoDownloadError(DownloadError):
    """ """

    pass


@abcd.auto_eq()
@abcd.auto_repr_str()
class VideoCache(AVideoCache):
    """
    A cache for videos for runs.
    Downloads videos from the Shire, saves the native h265 video files, and loads them with moveipy.

    """

    def __init__(
        self,
        cache_dir: PathLike = chemfish_env.video_cache_dir,
        shire_store: PathLike = DEFAULT_SHIRE_STORE,
    ):
        """
        Constructor.

        Args:
            cache_dir: The directory to save video files under.
            shire_store: The local or remote path to the Shire.
                         If local, will copy the files.
                         If remote, will download with SCP on Windows and rsync on other systems.
        """
        self._cache_dir = Tools.prepped_dir(cache_dir)
        self.shire_store = PurePath(shire_store)

    @property
    def cache_dir(self) -> Path:
        """ """
        return self._cache_dir

    @abcd.overrides
    def path_of(self, run: RunLike) -> Path:
        """


        Args:
            run: RunLike:

        Returns:

        """
        run = Runs.fetch(run)
        return self.cache_dir / str(run.id) / (str(run.id) + VideoCore.video_ext)

    @abcd.overrides
    def key_from_path(self, path: PathLike) -> RunLike:
        """


        Args:
            path: PathLike:

        Returns:

        """
        path = Path(path).relative_to(self.cache_dir)
        return int(re.compile(r"^([0-9]+)\..+$").fullmatch(path.name).group(1))

    @abcd.overrides
    def load(self, run: RunLike) -> SauronxVideo:
        """
        Loads from the cache, downloading if necessary, and loads.

        Args:
            run: A run ID, instance, name, tag, or submission hash or instance

        Returns:
            A SauronxVideo

        """
        self.download(run)
        return self._load(run)

    @abcd.overrides
    def download(self, *runs: RunLike) -> None:
        """


        Args:
            *runs: RunLike:

        """
        for run in Runs.fetch_all(runs):
            video_path = self.path_of(run)
            t0 = time.monotonic()
            if video_path.exists():
                logger.debug(f"Run {run.id} is already at {video_path}")
            else:
                generation = ValarTools.generation_of(run)
                logger.minor(
                    f"Downloading {generation.name} video of r{run.id} to {video_path} ..."
                )
                remote_path = self.shire_store / VideoCore.get_remote_path(run)
                self._copy_from_shire(remote_path, video_path)
                # TODO check for properties file
                logger.notice(
                    f"Downloaded video of r{run.id}. Took {round(time.monotonic() - t0, 1)}s."
                )

    def _load(self, run: RunLike) -> SauronxVideo:
        """
        Loads from the cache. Will raise an error if the video is not already in the cache.

        Args:
            run: A run ID, instance, name, tag, or submission hash or instance

        Returns:
          A SauronxVideo

        """
        return SauronxVideos.of(self.path_of(run), run)

    def validate(self, run: RunLike) -> None:
        """
        Raises a HashValidationFailedException if the hash doesn't validate.

        Args:
            run: RunLike:

        """
        path = self.path_of(run)
        if not VideoCore.video_hasher.check_hash(path):
            raise HashValidationFailedError(f"Video at {path} did not validate")

    def _copy_from_shire(self, remote_path, local_path) -> None:
        """


        Args:
            remote_path:
            local_path:

        """
        try:
            ValarTools.download_file(remote_path, local_path, False)
            ValarTools.download_file(
                str(remote_path) + ".sha256", str(local_path) + ".sha256", False
            )
        except Exception as e:
            raise VideoDownloadError(f"Failed to copy from the Shire at path {remote_path}") from e
        if not Path(local_path).exists():
            raise VideoDownloadError(
                f"Video directory was downloaded to {local_path}, but the video does not exist"
            )


__all__ = ["VideoCache"]
