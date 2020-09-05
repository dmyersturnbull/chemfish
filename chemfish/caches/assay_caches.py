from __future__ import annotations

from chemfish.core.core_imports import *
from chemfish.model.cache_interfaces import AAssayCache
from chemfish.model.assay_frames import AssayFrame

DEFAULT_CACHE_DIR = chemfish_env.cache_dir / "assays"


@abcd.auto_repr_str()
@abcd.auto_eq()
class AssayFrameCache(AAssayCache):
    """
    A cache for AssayFrameCaches.
    """

    def __init__(self, cache_dir: PathLike = None):
        """

        Args:
            cache_dir:
        """
        if cache_dir is None:
            cache_dir = DEFAULT_CACHE_DIR
        self._cache_dir = Tools.prepped_dir(cache_dir)

    @property
    def cache_dir(self) -> Path:
        """"""
        return self._cache_dir

    @abcd.overrides
    def path_of(self, battery: BatteryLike) -> Path:
        """


        Args:
            battery:

        Returns:

        """
        if not isinstance(battery, int):  # avoid query
            battery = Batteries.fetch(battery).id
        return self.cache_dir / (str(battery) + ".csv")

    @abcd.overrides
    def key_from_path(self, path: PathLike) -> BatteryLike:
        """


        Args:
            path: PathLike:

        Returns:

        """
        path = Path(path).relative_to(self.cache_dir)
        return int(re.compile(r"^([0-9]+)\.csv$").fullmatch(path.name).group(1))

    @abcd.overrides
    def load(self, battery: BatteryLike) -> AssayFrame:
        """


        Args:
            battery:

        Returns:

        """
        battery = Batteries.fetch(battery)
        self.download(battery)
        return AssayFrame.read_csv(self.path_of(battery.id))

    @abcd.overrides
    def download(self, *batteries: BatteryLike) -> None:
        """


        Args:
            *batteries:

        """
        for battery in batteries:
            battery = Batteries.fetch(battery)
            if battery not in self:
                afs = AssayFrame.of(battery)
                # noinspection PyTypeChecker
                afs.to_csv(self.path_of(battery.id))

    def __repr__(self):
        return f"{type(self).__name__}('{self.cache_dir}')"

    def __str__(self):
        return repr(self)


__all__ = ["AssayFrameCache"]
