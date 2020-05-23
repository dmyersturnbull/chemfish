from __future__ import annotations
import colorsys
from matplotlib.colors import Colormap
from matplotlib import colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
from kale.core.core_imports import *


class KvrcColorSchemes:
    """
    Color schemes that can be used.
    Each is a list of hex color codes.
    Most are not used directly in kale, but are here for convenience.
    The "tol" palettes (ex `qualitative_tol_vibrant_7`) are safe for red-green color blindness.
    """

    @classmethod
    def darken_color(cls, color, shading: float):
        color = mcolors.colorConverter.to_rgb(color)
        h, l, s = colorsys.rgb_to_hls(*mcolors.to_rgb(color))
        return colorsys.hls_to_rgb(h, shading * 1, s)

    @classmethod
    def darken_palette(cls, palette: Iterable[str], shading: float) -> Sequence[str]:
        return [KvrcColorSchemes.darken_color(c, shading) for c in palette]

    @classmethod
    def grayscales(cls) -> Sequence[str]:
        return [
            "#000000",
            "#555555",
            "#999999",
            "#cccccc",
            "#300000",
            "#000030",
            "#003333",
            "#333300",
            "#775555",
            "#555577",
            "#557777",
            "#777755",
        ]

    @classmethod
    def qualitiative_26(cls) -> Sequence[str]:
        """
        Special color scheme of 26.
        """
        # the first 11 of these were *[c for c in InternalKvrcUtils.darken_palette(qualitative.Set3_12.hex_colors, 0.38) if c != '#787878']
        # some were slightly modified to work better with the rest
        return [
            "#367c7d",
            "#daca00",
            "#44337e",
            "#bc1805",
            "#32699a",
            "#cc6016",
            "#719f23",
            "#b70b63",
            "#816161",
            "#7e007e",
            "#ff9000",
            "#c2aa00",
            "#11e022",
            "#0000ff",
            "#00bb00",
            "#fb9a99",
            "#ff0000",
            "#cc8700",
            "#006400",
            "#554411",
            "#191970",
            "#00aa66",
            "#dd6666",
            "#2288ee",
            "#009900",
            "#c71588",
        ]

    @classmethod
    def qualitative_tol_dark_mod_6(cls) -> Sequence[str]:
        """
        "Dark" color scheme from https://personal.sron.nl/~pault/#sec:qualitative
        No black and reordered red and yellow.
        """
        return ["#222255", "#225555", "#225522", "#663333", "#666633", "#551144"]

    @classmethod
    def qualitative_tol_high_contrast_6(cls) -> Sequence[str]:
        """
        "High-contrast" color scheme from https://personal.sron.nl/~pault/#sec:qualitative
        Reordered. No gray.
        """
        return ["#0077bb", "#ee3377", "#33bbee", "#cc3311", "#009988", "#ee7733"]

    @classmethod
    def qualitative_tol_vibrant_7(cls) -> Sequence[str]:
        """
        "Vibrant" color scheme from https://personal.sron.nl/~pault/#sec:qualitative
        Reordered: black was moved to the front.
        """
        return ["#000000", "#0077BB", "#CC3311", "#009988", "#EE7733", "#33BBEE", "#EE3377"]

    @classmethod
    def qualitative_tol_vibrant_6(cls) -> Sequence[str]:
        """
        "Vibrant" color scheme from https://personal.sron.nl/~pault/#sec:qualitative
        Gray was removed.
        """
        return ["#0077BB", "#CC3311", "#009988", "#EE7733", "#33BBEE", "#EE3377"]

    @classmethod
    def qualitative_tol_vibrant_7_black(cls) -> Sequence[str]:
        """
        "Vibrant" color scheme from https://personal.sron.nl/~pault/#sec:qualitative
        Gray was removed and gray was added to the front.
        """
        return ["#000000", "#0077BB", "#CC3311", "#009988", "#EE7733", "#33BBEE", "#EE3377"]

    @classmethod
    def qualitative_tol_muted_9(cls) -> Sequence[str]:
        """
        "Muted" color scheme from https://personal.sron.nl/~pault/#sec:qualitative
        Gray was removed.
        """
        return [
            "#332288",
            "#88CCEE",
            "#44AA99",
            "#117733",
            "#999933",
            "#DDCC77",
            "#CC6677",
            "#882255",
            "#AA4499",
        ]

    @classmethod
    def qualitative_tol_muted_10_black(cls) -> Sequence[str]:
        """
        "Muted" color scheme from https://personal.sron.nl/~pault/#sec:qualitative
        Black was added to the front and gray was removed.
        """
        return [
            "#000000",
            "#332288",
            "#88CCEE",
            "#44AA99",
            "#117733",
            "#999933",
            "#DDCC77",
            "#CC6677",
            "#882255",
            "#AA4499",
        ]


class FancyCmaps:
    """
    Very useful colormaps. Most importantly:
        - white_red
        - white_blue
        - blue_white
        - white_black
    The built-in matplotlib ones don't actually go between pure color values!!
    For ex, 'Greys' doesn't go from pure white to pure black!
    So colormaps to consider avoiding include Greys, Blues, Greens, (etc), bwr, and seismic.
    Matplotlib still has good built-in colormaps, including viridis and plasma.
    """

    @classmethod
    def white_red(cls) -> Colormap:
        """A colormap from pure white to pure red."""
        cmap = LinearSegmentedColormap.from_list("white_red", ["#ffffff", "#ff0000"])
        cmap.set_bad(color="#333333")
        return cmap

    @classmethod
    def white_blue(cls) -> Colormap:
        """A colormap from pure white to pure blue."""
        cmap = LinearSegmentedColormap.from_list("white_blue", ["#ffffff", "#0000ff"])
        cmap.set_bad(color="#333333")
        return cmap

    @classmethod
    def blue_white(cls) -> Colormap:
        """A colormap from pure white to pure blue."""
        cmap = LinearSegmentedColormap.from_list("blue_white", ["#0000ff", "#ffffff"])
        cmap.set_bad(color="#333333")
        return cmap

    @classmethod
    def white_black(cls) -> Colormap:
        """A colormap from pure white to pure black."""
        cmap = LinearSegmentedColormap.from_list("white_black", ["#ffffff", "#000000"])
        cmap.set_bad(color="#dd0000")
        return cmap

    @classmethod
    def blue_white_red(cls) -> Colormap:
        """A colormap from pure blue to pure red."""
        cmap = LinearSegmentedColormap.from_list(
            "blue_white_red", ["#0000ff", "#ffffff", "#ff0000"]
        )
        cmap.set_bad(color="#aaaaaa")
        return cmap


__all__ = ["KvrcColorSchemes", "FancyCmaps"]
