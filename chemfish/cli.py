#!/usr/bin/env python3
# coding=utf-8

import enum
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from pocketutils.core import SmartEnum
from pocketutils.tools.call_tools import CallTools
from pocketutils.tools.filesys_tools import FilesysTools
from pocketutils.tools.string_tools import StringTools

from chemfish.core import ChemfishResources, log_factory, logger

ch = logging.StreamHandler()
logger.addHandler(ch)
ch.setFormatter(log_factory.formatter)
logger.setLevel(logging.INFO)


class ChemfishCmd(SmartEnum):
    init = enum.auto()
    parrot = enum.auto()
    video = enum.auto()


class ChemfishProcessor:
    def run(self, args) -> None:
        import argparse

        parser = argparse.ArgumentParser("""Install, update, or initialize Chemfish""")
        # noinspection PyTypeChecker
        parser.add_argument("cmd", type=ChemfishCmd.of, choices=[s for s in ChemfishCmd])
        parser.add_argument("args", nargs="*")
        opts = parser.parse_args(args)
        self.process(opts.cmd, opts.args)

    def process(self, cmd: ChemfishCmd, args) -> None:
        if cmd is ChemfishCmd.init:
            self.init()
        elif cmd is ChemfishCmd.video:
            self.download_video(args)
        else:
            print(ChemfishResources.text("art", cmd.name + ".txt"))

    # noinspection PyTypeChecker
    def init(self) -> None:
        logger.notice("Setting up chemfish configuration...")
        n_created = sum(
            [
                self._copy_if(
                    Path.home() / ".chemfish" / "valar_config.json",
                    ChemfishResources.path("example_valar_config.json"),
                ),
                self._copy_if(
                    Path.home() / ".chemfish" / "chemfish.config",
                    ChemfishResources.path("example.chemfish.config"),
                ),
                self._copy_if(
                    Path.home() / ".chemfish" / "jupyter_template.txt",
                    ChemfishResources.path("jupyter_template.txt"),
                ),
                self._copy_if(
                    Path.home() / ".chemfish" / "chemfish.mplstyle",
                    ChemfishResources.path("styles/basic.mplstyle"),
                ),
                self._copy_if(
                    Path.home() / ".chemfish" / "chemfish_viz.properties",
                    ChemfishResources.path("styles/basic.viz.properties"),
                ),
            ]
        )
        if n_created > 0:
            logger.notice("Finished. Edit these files as needed.")
        else:
            logger.notice("Finished. You already have all required config files.")

    def download_video(self, args):
        from chemfish.caches.video_caches import VideoCache

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
        ChemfishProcessor().run(None)
    except Exception:
        logger.fatal("Failed while running command.", exc_info=True)


if __name__ == "__main__":
    main()

__all__ = ["ChemfishProcessor", "ChemfishCmd"]
