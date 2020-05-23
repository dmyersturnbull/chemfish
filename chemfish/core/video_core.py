"""
Non-changing settings tied to SauronX and the Shire.
"""
import hashlib
from dscience.core.hasher import FileHasher
from kale.core.valar_singleton import *

video_hasher = FileHasher(algorithm=hashlib.sha256, extension=".sha256sum")
shire_crf = 15
video_ext = ".mkv"
codec = "libx265"
# We don't know what this should be, but the default seems fine
bitrate = "500M"


def get_video_filename(crf: int) -> str:
    return "x265-crf" + str(crf)


def get_video_path_on_shire(run: Runs, full_dir: bool = False) -> PurePath:
    """
    :param run: The runs instance
    :param full_dir: If true, gets the whole directory instead of the video
    :return: The path to the video MKV file relative to (and under) the Shire.
    """
    run = Runs.fetch(run)
    year = str(run.datetime_run.year).zfill(4)
    month = str(run.datetime_run.month).zfill(2)
    if full_dir:
        return PurePath(year, month, run.tag)
    else:
        return PurePath(
            year,
            month,
            run.tag,
            "camera",
            "x265-crf" + str(shire_crf),
            "x265-crf" + str(shire_crf) + ".mkv",
        )


custom_ffmpeg_params = "-c:v libx265 -vf scale=1280:trunc(ow/a/2)*2 -crf 15 -pix_fmt yuv420p -y".split(
    " "
)
custom_ffmpeg_params_mp4 = "-vf scale=1280:trunc(ow/a/2)*2 -pix_fmt yuv420p -y".split(" ")

# encourage using import * for this
