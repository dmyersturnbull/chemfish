from __future__ import annotations
from datetime import datetime, date

from chemfish.core.valar_singleton import *

def _save(self: Model):
    self.save()
    return self
Model.sv = _save

from hypothesis import strategies as ST

class Strategies:
    def __init__(self):
        self.used_text = set()

    def text(self, optional: bool, min_size: int = 1, max_size: int = 30):
        txt = ST.text(min_size=min_size, max_size=max_size, blacklist_categories=("Cc", "Co", "Cs", "Cn"))
        txt = txt.filter(lambda s: s not in self.used_text)
        return ST.one_of(ST.just(None), txt) if optional else txt

    def name(self):
        return self.text(False, 1, 30)

    def desc(self):
        return self.text(True, 1, 50)

    def datetime(self):
        return ST.datetimes(min_value=datetime(1970, 1, 1), max_value=datetime.now())

    def date(self):
        return ST.dates(min_value=date(1970, 1, 1), max_value=date.today())

    def reset(self) -> None:
        self.used_text = set()


S = Strategies()


class ValarStrategies:

    @ST.composite
    def user(
        self,
        username: S.name(),
        first_name: S.name(),
        last_name: S.name(),
        write_access: ST.booleans
    ) -> Users:
        return Users(
            username=username,
            first_name=first_name,
            last_name=last_name,
            write_access=write_access,
            bcrypt_hash=None
        ).sv()

    @ST.composite
    def audio_file(
        self,
        choice: ST.from_regex(r"a:b"),
        filename: ST.from_regex(r".{1,20}\.wav")
    ) -> AudioFiles:
        af = AudioFiles()

    @ST.composite
    def led(
        self,
        name: S.name(),
        description: S.desc(),
        analog = ST.booleans()
    ) -> Stimuli:
        pass

    @ST.composite
    def assay(
        self,
        name: S.name(),
        description: S.desc(),

    ) -> Assays:
        pass

    def battery(self) -> Batteries:
        pass

    def compound(self) -> Compounds:
        pass

    def batch(self) -> Batches:
        pass

    def variant(self) -> GeneticVariants:
        pass

    def project(self) -> Projects:
        pass

    def experiment(self) -> Experiments:
        pass

    def ref(self) -> Refs:
        pass

    def supplier(self) -> Suppliers:
        pass

    def locations(self) -> Locations:
        pass

    def run(self) -> Runs:
        pass
