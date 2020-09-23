from __future__ import annotations

from clana.optimize import simulated_annealing
from matplotlib.figure import Figure

from chemfish.core.core_imports import *
from chemfish.viz.confusion_plots import *

logger = logging.getLogger("chemfish")


class ConfusionMatrix(UntypedDf):
    """
    A wrapper around a confusion matrix as a Pandas DataFrame.
    The rows are the correct labels, and the columns are the predicted labels.

    """

    def warn_if_asymmetric(self) -> None:
        """"""
        if self.rows != self.cols:
            logger.warning(f"Rows {self.rows} != columns {self.columns}")

    def is_symmetric(self) -> bool:
        """"""
        return self.rows == self.cols

    def _repr_html_(self) -> str:
        """"""
        return "<strong>{}: {} {}</strong>\n{}".format(
            self.__class__.__name__,
            self._dims(),
            Chars.check if self.rows == self.cols else Chars.x,
            pd.DataFrame._repr_html_(self),
            len(self),
        )

    def sub(self, names: Set[str]) -> ConfusionMatrix:
        """


        Args:
            names: Set[str]:

        Returns:

        """
        return ConfusionMatrix(self.loc[names][names])

    def shuffle(self) -> ConfusionMatrix:
        """
        Returns a copy with every value mapped to a new location.
        Destroys the correct links between labels and values.
        Useful for permutation tests.

        Args:

        Returns:

        """
        cp = deepcopy(self.flatten())
        np.random.shuffle(cp)
        vals = cp.reshape((len(self.rows), len(self.columns)))
        return ConfusionMatrix(vals, index=self.rows, columns=self.columns)

    def diagonals(self) -> np.array:
        """
        Returns diagonal elements.
        """
        return np.array([self.iat[i, i] for i in range(len(self))])

    def off_diagonals_quantiles(self, q: float = 0.5) -> np.array:
        """


        Args:
            q:

        Returns:

        """
        lst = []
        for i in range(len(self)):
            lst.append(np.quantile([self.iat[i, j] for j in range(len(self))], q))
        return np.array(lst)

    def off_diagonals_means(self) -> np.array:
        """"""
        lst = []
        for i in range(len(self)):
            lst.append(np.mean([self.iat[i, j] for j in range(len(self))]))
        return np.array(lst)

    def flatten(self) -> np.array:
        """"""
        return self.values.flatten()

    def sum_diagonal(self) -> float:
        """"""
        s = 0
        for i in range(len(self)):
            s += self.iat[i, i]
        return s

    def sum_off_diagonal(self) -> float:
        """"""
        s = 0
        for i in range(len(self)):
            for j in range(len(self)):
                if i != j:
                    s += self.iat[i, j]
        return s

    def score_df(self) -> UntypedDf:
        """
        Get the diagonal elements as a Pandas DataFrame with columns 'name' and 'score'.

        Returns:

        """
        sers = []
        for score, name in self.scores():
            sers.append(pd.Series({"name": name, "score": score}))
        return UntypedDf(sers)

    def symmetrize(self) -> ConfusionMatrix:
        """
        Averages with its transpose, forcing it to be symmetric.

        Returns:
            A copy
        """
        return ConfusionMatrix(0.5 * (self + self.T))

    def triagonalize(self) -> ConfusionMatrix:
        """
        NaNs out the upper triangle, returning a copy.
        You may consider calling symmetrize first.
        WARNING: Do NOT call a sorting method after this.

        Args:

        Returns:

        """
        return ConfusionMatrix(self.where(np.tril(np.ones(self.shape)).astype(np.bool)))

    def sort(self, **kwargs) -> ConfusionMatrix:
        """
        Sorts this confusion matrix to show clustering. The same ordering is applied to the rows and columns.
        Call this first. Do not call symmetrize(), log(), or triagonalize() before calling this.
        Returns a copy.

        Args:
            **kwargs:

        Returns:
            A dictionary mapping class names to their new positions (starting at 0)

        """
        permutation = self.permutation(**kwargs)
        return self.sort_with(permutation)

    def permutation(self, **kwargs) -> Mapping[str, int]:
        """
        Sorts this confusion matrix to show clustering. The same ordering is applied to the rows and columns.
        Returns the sorting. Does not alter this ConfusionMatrix.

        Args:
            **kwargs:

        Returns:
            A dictionary mapping class names to their new positions (starting at 0)

        """
        if not self.is_symmetric():
            raise AmbiguousRequestError(
                f"Can't sort because rows {self.rows} and columns {self.columns} differ"
            )
        optimized = simulated_annealing(self.values, **kwargs)
        perm = list(reversed(optimized.perm))
        perm = {name: perm.index(i) for i, name in enumerate(self.rows)}
        logger.info(f"Permutation for rows {self.rows}: {perm}")
        return perm

    def sort_alphabetical(self) -> ConfusionMatrix:
        """
        Sort by the labels alphabetically.

        Returns:
            A copy
        """
        labels = sorted(self.rows)
        return self.sort_first(labels)

    def sort_with(self, permutation: Union[Sequence[str], Mapping[str, int]]) -> ConfusionMatrix:
        """
        Sorts this ConfusionMatrix's rows and columns by a predefined ordering. Returns a copy.

        Args:
            permutation: Maps names (strings) to their 0-indexed positions (integers)
                         If a mapping, takes as-is; these are returned by permutation()
                         If a DataFrame, must have 2 columns 'key' (name) and 'value' (position), and 1 row per name
                         If a str, tries to read a CSV file at that path into a DataFrame; uses Tools.csv_to_dict

        Returns:
            A new ConfusionMatrix with sorted rows and columns

        """
        if not self.is_symmetric():
            raise AmbiguousRequestError(
                f"Cannot sort because rows {self.rows} and columns {self.columns} differ"
            )
        if isinstance(permutation, Sequence):
            if set(permutation) != set(self.rows):
                permutation = {name: i for i, name in enumerate(permutation)}
            else:
                raise RefusingRequestError(
                    f"{len(permutation)} permutation elements instead of {len(self)}. See sort_first."
                )
        data = self.reindex(sorted(self.rows, key=lambda s: permutation[s]), axis=1)
        xx = [permutation[name] for name in self.rows]
        data["__sort"] = xx
        data = data.sort_values("__sort").drop("__sort", axis=1)
        return ConfusionMatrix(data)

    def sort_first(self, first: Sequence[str]) -> ConfusionMatrix:
        """
        Put these elements first.

        Args:
            first: Sequence[str]:

        Returns:

        """
        first = [*first, *[r for r in self.rows if r not in first]]
        permutation = {name: i for i, name in enumerate(first)}
        return self.sort_with(permutation)

    @property
    def rows(self):
        """"""
        return self.index.tolist()

    @property
    def cols(self):
        """"""
        return self.columns.tolist()

    @property
    def length(self) -> int:
        """
        Gets a safe length, verifying that the len(rows) == len(cols).
        """
        if len(self.rows) != len(self.cols):
            raise LengthMismatchError(f"{len(self.rows)} rows != {len(self.cols)} cols")
        return len(self.rows)

    def __repr__(self) -> str:
        return f"ConfusionMatrix({len(self.rows)} labels @ {hex(id(self))})"

    def __str__(self) -> str:
        return repr(self)

    def heatmap(
        self,
        vmin: float = 0,
        vmax: float = 1,
        runs: Optional[Sequence[int]] = None,
        renamer: Union[None, Mapping[str, str], Callable[[str], str]] = None,
        label_colors: Union[bool, Mapping[str, str]] = False,
    ) -> Figure:
        """
        Generates a heatmap.

        Args:
            vmin: Set this as the minimum accuracy (white on the colorbar)
            vmax: Set this as the maximum accuracy (black on the colorbar)
            runs: Run stamps in the upper-left corner with these runs (not verified)
            renamer: A function that maps the class names to new names for plotting
            label_colors: Mapping from names to colors for the labels; or a string for all control colors

        Returns:
            The figure, which was not displayed

        """
        return ConfusionPlots.plot(
            self, vmin=vmin, vmax=vmax, renamer=renamer, runs=runs, label_colors=label_colors
        )




__all__ = ["ConfusionMatrix", "ConfusionMatrices"]
