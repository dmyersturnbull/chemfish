import os
from pathlib import Path

os.environ.setdefault(
    "VALARPY_CONFIG", str((Path(__file__).parent / "valar_config.json").absolute())
)
