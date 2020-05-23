#!/usr/bin/env python3
# coding=utf-8

import enum
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime
from kale.core import KaleResources, logger, log_factory
from dscience.tools.string_tools import StringTools
from dscience.core import SmartEnum
from dscience.tools.call_tools import CallTools
from dscience.tools.filesys_tools import FilesysTools

ch = logging.StreamHandler()
logger.addHandler(ch)
ch.setFormatter(log_factory.formatter)
logger.setLevel(logging.INFO)


class KaleCmd(SmartEnum):
    init = enum.auto()
    parrot = enum.auto()
    video = enum.auto()


class KaleProcessor:
    def run(self, args) -> None:
        import argparse

        parser = argparse.ArgumentParser("""Install, update, or initialize Kale""")
        # noinspection PyTypeChecker
        parser.add_argument("cmd", type=KaleCmd.of, choices=[s for s in KaleCmd])
        parser.add_argument("args", nargs="*")
        opts = parser.parse_args(args)
        self.process(opts.cmd, opts.args)

    def process(self, cmd: KaleCmd, args) -> None:
        if cmd is KaleCmd.init:
            self.init()
        elif cmd is KaleCmd.video:
            self.download_video(args)
        else:
            print(KaleResources.text("art", cmd.name + ".txt"))

    # noinspection PyTypeChecker
    def init(self) -> None:
        logger.notice("Setting up kale configuration...")
        n_created = sum(
            [
                self._copy_if(
                    Path.home() / ".kale" / "valar_config.json",
                    KaleResources.path("example_valar_config.json"),
                ),
                self._copy_if(
                    Path.home() / ".kale" / "kale.config", KaleResources.path("example.kale.config")
                ),
                self._copy_if(
                    Path.home() / ".kale" / "jupyter_template.txt",
                    KaleResources.path("jupyter_template.txt"),
                ),
                self._copy_if(
                    Path.home() / ".kale" / "kale.mplstyle",
                    KaleResources.path("styles/basic.mplstyle"),
                ),
                self._copy_if(
                    Path.home() / ".kale" / "kale_viz.properties",
                    KaleResources.path("styles/basic.viz.properties"),
                ),
            ]
        )
        if n_created > 0:
            logger.notice("Finished. Edit these files as needed.")
        else:
            logger.notice("Finished. You already have all required config files.")

    def download_video(self, args):
        from kale.caches.video_cache import VideoCache

        cache = VideoCache()
        n_exists = sum([not cache.has_video(v) for v in args])
        for arg in args:
            cache.download(arg)
        logger.notice("Downloaded {} videos.".format(n_exists))

    def _copy_if(self, dest: Path, source: Path) -> bool:
        import shutil

        if not dest.exists():
            # noinspection PyTypeChecker
            dest.parent.mkdir(parents=True, exist_ok=True)
            # noinspection PyTypeChecker
            shutil.copy(source, dest)
            logger.info("Copied {} → {}".format(source, dest))
            return True
        else:
            logger.info("Skipping {}".format(dest))
            return False


def main():
    # noinspection PyBroadException
    try:
        KaleProcessor().run(None)
    except Exception:
        logger.fatal("Failed while running command.", exc_info=True)


if __name__ == "__main__":
    main()

__all__ = ["KaleProcessor", "KaleCmd"]
