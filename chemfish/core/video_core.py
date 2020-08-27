"""
Non-changing settings tied to SauronX and the Shire.
"""
from pathlib import PurePath

from pocketutils.core.hasher import FileHasher

from chemfish.core._tools import InternalTools
from chemfish.core.valar_singleton import *


class VideoCore:

    shasum_filename: str = InternalTools.load_resource("core", "videos.properties")[
        "shasum_filename"
    ]
    sha_algorithm = InternalTools.load_resource("core", "videos.properties")["shasum_algorithm"]
    video_hasher = FileHasher(algorithm=sha_algorithm, extension=shasum_filename)
    shire_crf: int = int(InternalTools.load_resource("core", "videos.properties")["crf"])
    video_ext: str = InternalTools.load_resource("core", "videos.properties")["ext"]
    codec: str = InternalTools.load_resource("core", "videos.properties")["libx265"]
    bitrate: str = InternalTools.load_resource("core", "videos.properties")["bitrate"]
    filename: str = InternalTools.load_resource("core", "videos.properties")["filename"]
    path: str = InternalTools.load_resource("core", "videos.properties")["path"]
    hevc_params: str = InternalTools.load_resource("core", "videos.properties")["ffmpeg_params"]
    mp4_params: str = "-vf scale=1280:trunc(ow/a/2)*2 -pix_fmt yuv420p -y"

    @classmethod
    def get_remote_path(cls, run: Runs) -> PurePath:
        """

        Args:
          run: The runs instance

        Returns:
          The path to the video MKV file relative to (and under) the Shire.

        """
        # TODO hardcoded
        run = Runs.fetch(run)
        year = str(run.datetime_run.year).zfill(4)
        month = str(run.datetime_run.month).zfill(2)
        return PurePath(
            year,
            month,
            run.tag,
            *VideoCore.path.split("/"),
        )


__all__ = ["VideoCore"]
