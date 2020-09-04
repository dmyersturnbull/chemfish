# this could depend on internal_core_imports, but let's keep it light
import os
from pathlib import Path

import decorateme as abcd
from valarpy import Valar as __Valar


@abcd.auto_singleton
class Valar(__Valar):
    """"""

    def __init__(self):
        config_path = os.environ.get(
            "VALARPY_CONFIG", Path.home() / ".chemfish" / "connection.json"
        )
        super().__init__(config_path)
        super().open()


VALAR = Valar()
# noinspection PyUnresolvedReferences
from valarpy.model import *
