from chemfish.core.core_imports import *
from chemfish.core.video_core import *
from chemfish.model.cache_interfaces import AVideoCache
from chemfish.model.videos import *

DEFAULT_SHIRE_STORE = PurePath(chemfish_env.shire_path) / "store"


class VideoDownloadError(DownloadError):
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
        cache_dir: PLike = chemfish_env.video_cache_dir,
        shire_store: PLike = DEFAULT_SHIRE_STORE,
    ):
        """
        :param cache_dir: The directory to save video files under.
        :param shire_store: The local or remote path to the Shire.
                If local, will copy the files. If remote, will download with SCP on Windows and rsync on other systems.
        """
        self._cache_dir = Tools.prepped_dir(cache_dir)
        self.shire_store = PurePath(shire_store)

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @abcd.overrides
    def path_of(self, run: RunLike) -> Path:
        run = Tools.run(run)
        return self.cache_dir / str(run.id) / (str(run.id) + video_ext)

    @abcd.overrides
    def key_from_path(self, path: PLike) -> RunLike:
        path = Path(path).relative_to(self.cache_dir)
        return int(re.compile(r"^([0-9]+)\..+$").fullmatch(path.name).group(1))

    @abcd.overrides
    def load(self, run: RunLike) -> SauronxVideo:
        """
        Loads from the cache, downloading if necessary, and loads.
        :param run: A run ID, instance, name, tag, or submission hash or instance
        :return: A SauronxVideo
        """
        self.download(run)
        return self._load(run)

    @abcd.overrides
    def download(self, *runs: RunLike) -> None:
        for run in Tools.runs(runs):
            video_path = self.path_of(run)
            t0 = time.monotonic()
            if video_path.exists():
                logger.debug("Run {} is already at {}".format(run.id, video_path))
            else:
                generation = ValarTools.generation_of(run)
                logger.info(
                    "Downloading {} video of r{} to {} ...".format(
                        generation.name, run.id, video_path
                    )
                )
                remote_path = self.shire_store / get_video_path_on_shire(run, full_dir=False)
                self._copy_from_shire(remote_path, video_path)
                # TODO check for properties file
                logger.notice(
                    "Downloaded video of r{}. Took {}s.".format(
                        run.id, round(time.monotonic() - t0, 1)
                    )
                )

    def _load(self, run: RunLike) -> SauronxVideo:
        """
        Loads from the cache. Will raise an error if the video is not already in the cache.
        :param run: A run ID, instance, name, tag, or submission hash or instance
        :return: A SauronxVideo
        """
        return SauronxVideos.of(self.path_of(run), run)

    def validate(self, run: RunLike) -> None:
        """
        Raises a HashValidationFailedException if the hash doesn't validate.
        """
        path = self.path_of(run)
        if not video_hasher.check_hash(path):
            raise HashValidationFailedError("Video at {} did not validate".format(path))

    def _copy_from_shire(self, remote_path, local_path):
        try:
            ValarTools.download_file(remote_path, local_path, False)
            ValarTools.download_file(
                str(remote_path) + ".sha256", str(local_path) + ".sha256", False
            )
        except Exception as e:
            raise VideoDownloadError(
                "Failed to copy from the Shire at path {}".format(remote_path)
            ) from e
        if not Path(local_path).exists():
            raise VideoDownloadError(
                "Video directory was downloaded to {}, but the video does not exist".format(
                    local_path
                )
            )


__all__ = ["VideoCache"]