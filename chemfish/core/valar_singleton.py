# this could depend on internal_core_imports, but let's keep it light
import decorateme as abcd
from valarpy import Valar as __Valar


@abcd.auto_singleton
class Valar(__Valar):
    """ """
    def __init__(self):
        super().__init__()
        super().open()


from valarpy.model import *
