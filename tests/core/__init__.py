import os


def resource_path(name: str) -> str:
    return os.path.join(os.environ["KALE"], "tests", "resources", "core", name)
