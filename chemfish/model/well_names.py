from __future__ import annotations
from chemfish.core.core_imports import *
from chemfish.model.treatment_names import *


class WellNamer:
    """
    A way to set the name meta column in a WellFrame.
    """

    @abcd.abstractmethod
    def __call__(self, df: pd.DataFrame) -> Sequence[str]:
        raise NotImplementedError()

    def name(self) -> str:
        return self.__class__.__name__


class CompositeWellNamer(WellNamer):
    def __init__(self, *namers):
        self.namers = namers

    def __call__(self, df):
        names = ["" for _ in df]
        for namer in self.namers:
            names += namer(df)
        return names

    def __add__(self, other):
        if not isinstance(other, WellNamer):
            raise XTypeError("Got {}, not namer".format(type(other)))
        return CompositeWellNamer([*self.namers, other])


@abcd.auto_repr_str()
class SimpleMappingWellNamer(WellNamer):
    """
    A namer for discrete categories of some column.
    Useful for machine learning classifiers.
    For example, we can get a simple string like "etomidate+mk-801" from the c_ids.
    """

    def __init__(self, column: str, mapping: Mapping[[Any], str]):
        self.column = column
        self.mapping = mapping

    def __call__(self, df):
        return df[self.column].map(lambda c: self.mapping[c])


class BuiltWellNamer(WellNamer):
    def __init__(self):
        self._bits = []
        self._labels = []
        self._modification = None

    def __call__(self, df):
        names = ["" for _ in df.iterrows()]
        for bit in self._bits:
            names = [name + bt for name, bt in zip(names, bit(df))]
        if self._modification is not None:
            names = [self._modification(name) for name in names]
        if any(("\t" in name for name in names)):
            raise RefusingRequestError("Name should not contain tabs")
        return [name.rstrip() for name in names]

    def __repr__(self):
        return "Namer({} ⟦ {} 〛 @ {})".format(
            "" if self._modification is None else Tools.pretty_function(self._modification) + " ∘",
            (" " + Chars.brokenbar + " ").join(self._labels),
            hex(id(self)),
        )

    def __str__(self):
        return repr(self)

    def _repr_html(self):
        return repr(self)


class WellNamerBuilder(BuiltWellNamer):
    """
    A builder for Namers.
    Example usage:
        >>> namer = WellNamerBuilder()\
        >>>     .text('be warned! ', if_missing_col='control_type')\
        >>>     .column('control_type', suffix='; ')\
        >>>     .treatments(displayer=StringTreatmentDisplayer('c${cid} (${um}µM)'))\
        >>>     .build()
        >>> namer(df)  # something like ['solvent (-)', 'be warned! c55 (55.23µM)']
    """

    def __init__(self):
        super().__init__()

    def text(self, txt: str, if_missing_col: Optional[str] = None) -> WellNamerBuilder:
        """
        Adds a literal string.
        :param txt: The string to append
        :param if_missing_col: Only append for rows that have this column empty ('none', 'nan', or ''; lowercased)
        :return: This builder
        """

        def function(df):
            missing_col = ([""] * len(df)) if if_missing_col is None else df[if_missing_col]
            return [(txt if WellNamerBuilder._is_null(x) else "") for x in missing_col]

        self._bits.append(function)
        self._labels.append(
            ("" if if_missing_col is None else Chars.angled("∄" + if_missing_col))
            + Chars.squoted(txt)
        )
        return self

    def run(self, suffix: str = " ") -> WellNamerBuilder:
        """
        Adds 'r' followed by the run ID.
        Equivalent to `column('run', 0, prefix='r', suffix=suffix)`.
        :param suffix: A suffix like ': '
        :return: This builder
        """
        self.column("run", 0, prefix="r", suffix=suffix)
        self._labels[-1] = Chars.angled("run")  # simplify what .column just added
        return self

    def control_type(
        self, prefix: str = "", suffix: str = "", correct: bool = True
    ) -> WellNamerBuilder:
        self.column(
            "control_type",
            0,
            prefix=prefix,
            suffix=suffix,
            transform=ValarTools.control_display_name if correct else None,
        )
        self._labels[-1] = Chars.angled("control_type")  # simplify what .column just added
        return self

    def important_columns(
        self, displayer: TreatmentDisplayer, variant_and_treatments_for_controls: bool = False
    ) -> WellNamerBuilder:
        """
        Convenience function that adds control_type, variant_name, age, n_fish, and well_group as necessary, using nice delimiters.
        """
        missing = None if variant_and_treatments_for_controls else "control_type"
        self.column("control_type", suffix=" ")
        self.column("variant_name", suffix=" ", if_missing_col=missing)
        self.column("age", prefix="", suffix="dpf ")
        self.column("n_fish", prefix="n=", suffix=" ")
        self.column("well_group", prefix="{", suffix="} ", or_null="-")
        self.treatments(displayer, if_missing_col=missing)
        return self

    def column(
        self,
        col_name: str,
        min_unique: Optional[int] = None,
        prefix: str = "",
        suffix: str = "",
        transform: Callable[[str], str] = Tools.truncate40,
        or_null: str = "",
        if_missing_col: Optional[str] = None,
    ) -> WellNamerBuilder:
        """
        Adds the value of a column in the WellFrame.
        :param col_name: The name of the column; ex 'variant_name'
        :param min_unique: Only include this if there are at least `min_unique` unique values in the column; otherwise, do nothing. None is equivalent to 0.
        :param prefix: Prepend this literal text; applies only to rows that are not empty ('none', 'nan', or ''; lowercased) and that match by `if_missing_col`.
        :param suffix: Append this literal text; applies only to rows that are not empty ('none', 'nan', or ''; lowercased) and that match by `if_missing_col`.
        :param transform: Transform the value of the column for display (happens after everyting else). Useful for things like converting case, truncating, and abbreviating.
        :param or_null: If the value is empty ('none', 'nan', or ''; lowercased), write it as `or_null`.
        :param if_missing_col: Only apply this to rows that have this column empty ('none', 'nan', or ''; lowercased). (This will NOT be applied if `if_missing_col` doesn't match.)
        :return: This builder
        """
        had_min_unique = min_unique is not None
        if min_unique is None:
            min_unique = 2 if col_name in {"variant_name", "age", "n_fish", "well_group"} else 1

        def function(df):
            return WellNamerBuilder._bit(
                df,
                col_name,
                lambda v: prefix + str(transform(str(v))) + suffix,
                min_unique=min_unique,
                or_null=or_null,
                if_missing_col=if_missing_col,
            )

        self._bits.append(function)
        self._labels.append(
            ("" if if_missing_col is None else Chars.angled("∄" + if_missing_col))
            + ("" if not had_min_unique else Chars.angled(Chars.geq + str(min_unique)))
            + ("" if transform is None else Tools.pretty_function(transform))
            + ("" if len(prefix) == 0 else Chars.squoted(prefix))
            + col_name
            + ("" if len(suffix) == 0 else Chars.squoted(suffix))
            + ("" if or_null == "" else "/" + Chars.squoted(or_null))
        )
        return self

    def modify(self, function: Callable[[str], str]) -> WellNamerBuilder:
        """
        Apply a free modification of the names after everything else has been applied.
        :param function: A function mapping names to new names
        :return: This builder
        """
        self._modification = function
        return self

    def treatments(
        self,
        displayer: Union[str, TreatmentDisplayer] = TreatmentDisplayers.name_with_id(),
        prefix: str = "",
        suffix: str = "",
        or_null: str = "",
        if_missing_col: Optional[str] = None,
        transform: Optional[Callable[[str], str]] = None,
        sep: str = ", ",
        ignore_cids: Optional[Set[int]] = None,
        ignore_bids: Optional[Set[int]] = None,
    ) -> WellNamerBuilder:
        """
        Adds the values from `df['treatments'].
        This could be done using `NamerBuilder.column`, but this is more user-friendly.
        :param displayer: Transform the `Treatment` objects using this `TreatmentDisplayer`.
                See StringTreatmentDisplayer for the most flexible way to build these.
        :param prefix: Prepend this literal text; applies only to rows that are not empty ('none', 'nan', or ''; lowercased) and that match by `if_missing_col`.
        :param suffix: Append this literal text; applies only to rows that are not empty ('none', 'nan', or ''; lowercased) and that match by `if_missing_col`.
        :param or_null: If the value is empty ('none', 'nan', or ''; lowercased), write it as `or_null`.
        :param if_missing_col: Only apply this to rows that have this column empty ('none', 'nan', or ''; lowercased). (This will NOT be applied if `if_missing_col` doesn't match.)
        :return: This builder
        :param transform: Transform the final strings using this function
        :param sep: Separate multiple treatments with this string
        :param ignore_cids: Ignore compounds with these IDs
        :param ignore_bids: Ignore batches with these IDs
        """
        if isinstance(displayer, str):
            displayer = StringTreatmentDisplayer(displayer)
        # in case they're iterators
        if ignore_bids is not None:
            ignore_bids = set(ignore_bids)
        if ignore_cids is not None:
            ignore_cids = set(ignore_cids)

        # yay
        def function(df):
            df = df.reset_index()
            compound_names = {}
            q = df[["c_ids", "compound_names"]].set_index("c_ids").to_dict()
            dictionary = q["compound_names"]
            for cps, nms in dictionary.items():
                for c, n in Tools.zip_strict(cps, nms):
                    if n is not None:
                        # we'll assume it's okay to overwrite duplicates
                        compound_names[c] = n

            def exclude_treatment(t):
                return (
                    ignore_bids is not None
                    and t.bid in ignore_bids
                    or ignore_cids is not None
                    and t.cid is not None
                    and t.cid in ignore_cids
                )

            _fake_trans = transform if transform is not None else lambda s: s
            trans_fn = lambda ls: _fake_trans(
                prefix
                + sep.join(
                    [displayer.display(t, compound_names) for t in ls if not exclude_treatment(t)]
                )
                + suffix
            )
            return WellNamerBuilder._bit(
                df, "treatments", trans_fn, or_null=or_null, if_missing_col=if_missing_col
            )

        self._bits.append(function)
        self._labels.append(
            ("" if if_missing_col is None else Chars.angled("∄" + if_missing_col))
            + ("" if transform is None else Tools.pretty_function(transform))
            + (
                ""
                if ignore_cids is None
                else Chars.angled("¬" + Tools.join(ignore_cids, ",", prefix="c"))
            )
            + (
                ""
                if ignore_bids is None
                else Chars.angled("¬" + Tools.join(ignore_bids, ",", prefix="b"))
            )
            + ("" if len(prefix) == 0 else Chars.squoted(prefix))
            + str(displayer)
            + ("" if sep == ", " else Chars.braced(sep))
            + ("" if len(suffix) == 0 else Chars.squoted(suffix))
            + ("" if or_null == "" else "/" + Chars.squoted(or_null))
        )
        return self

    def build(self) -> BuiltWellNamer:
        """
        Builds the namer.
        This builder can be used again, and the Namer won't be affected. (Though it's not clear why you would want to do that.)
        :return: The Namer from this builder
        """
        cp = copy(self)
        cp.__class__ = BuiltWellNamer
        return cp

    @classmethod
    def _is_null(cls, x):
        return str(x).strip().lower() in {"none", "nan", ""}

    @classmethod
    def _bit(
        cls,
        df: pd.DataFrame,
        col: str,
        formatter=lambda v: v,
        min_unique: int = 1,
        or_null: str = "",
        if_missing_col: Optional[str] = None,
    ) -> Sequence[str]:
        x = list(filter(lambda v: v is not None, df[col].unique()))
        missing_col = ([""] * len(df)) if if_missing_col is None else df[if_missing_col]
        if len(x) < min_unique:
            return ["" for _ in df[col]]
        else:
            return [
                (or_null if WellNamerBuilder._is_null(v) else str(formatter(v)))
                if (m is None or WellNamerBuilder._is_null(m))
                else ""
                for v, m in Tools.zip_strict(df[col], missing_col)
            ]


class WellNamers:
    """Contains some common namers."""

    @classmethod
    def builder(cls) -> WellNamerBuilder:
        return WellNamerBuilder()

    @classmethod
    def general(
        cls, displayer: TreatmentDisplayer = TreatmentDisplayers.id_with_dose()
    ) -> WellNamer:
        return WellNamerBuilder().run().important_columns(displayer).build()

    @classmethod
    def elegant(
        cls, displayer: TreatmentDisplayer = TreatmentDisplayers.name_with_id_with_dose()
    ) -> WellNamer:
        return WellNamerBuilder().important_columns(displayer).build()

    @classmethod
    def well(cls) -> WellNamer:
        return WellNamerBuilder().column("well").build()

    @classmethod
    def screening_plate(
        cls,
        displayer: TreatmentDisplayer = TreatmentDisplayers.id(),
        ignore_batch_ids: Iterable[int] = None,
    ):
        return (
            WellNamerBuilder()
            .column("well_label", suffix=" ")
            .column("control_type")
            .treatments(displayer, ignore_bids=ignore_batch_ids, if_missing_col="control_type")
            .build()
        )

    screening_plate_with_labels = screening_plate

    @classmethod
    def arbitrary(cls, column: str, name_dict: Mapping[str, str]):
        return WellNamerBuilder().column(column, transform=name_dict.get)

    @classmethod
    def false_label(cls, well_index_to_false_label: Mapping[int, str]) -> WellNamer:
        return WellNamerBuilder().column(
            "well_index", transform=lambda w: well_index_to_false_label[int(w)]
        )


__all__ = ["WellNamer", "WellNamers", "WellNamerBuilder"]
