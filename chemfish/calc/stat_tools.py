from __future__ import annotations

from statsmodels.nonparametric.kde import KDEUnivariate

from chemfish.core.core_imports import *


class StatTools:
    """"""

    @classmethod
    def kde(
        cls, a: np.array, kernel: str = "gau", bw: str = "normal_reference"
    ) -> Tup[np.array, np.array]:
        """
        Calculates univariate KDE with statsmodel.
        (This function turned into a thin wrapper around statsmodel.)
        Note that scipy uses statsmodel for KDE if it's available. Otherwise, it silently falls back to scipy. That's clearly hazardous.

        Args:
            a: np.array:
            kernel:
            bw:

        Returns:

        """
        if isinstance(a, pd.Series):
            a = a.values
        dens = KDEUnivariate(a)
        dens.fit(kernel=kernel, bw=bw)
        return dens.support, dens.density

