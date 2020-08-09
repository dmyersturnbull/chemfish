from __future__ import annotations
from matplotlib import patches
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.font_manager
import matplotlib.legend as mlegend
import matplotlib.backends.backend_pdf
from chemfish.core.core_imports import *

# noinspection PyProtectedMember
from chemfish.core._tools import *

# noinspection PyProtectedMember
from chemfish.viz.kvrc_utils import KvrcColorSchemes as _iku
from chemfish.viz.internal_viz import *
from chemfish.viz.fig_savers import *


class Corner:
    """Just used for text alignment. I hate it, but at least I won't keep getting the wrong params."""

    def __init__(self, bottom: bool, left: bool):
        self.name = ("bottom" if bottom else "top") + " " + "left" if left else "right"
        self.x = 0.0 if left else 1.0
        self.y = 0.0 if bottom else 1.0
        self.horizontalalignment = "left" if left else "right"
        # yes, these should be reversed: we want them above or below the figures
        self.verticalalignment = "top" if bottom else "bottom"

    def params(self) -> Mapping[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "horizontalalignment": self.horizontalalignment,
            "verticalalignment": self.verticalalignment,
        }

    def __eq__(self, other):
        return type(self) == type(other) and self.x == other.x and self.y == other.y

    def __repr__(self):
        return "Corner(" + self.name + ")"

    def __str__(self):
        return repr(self)


class Corners:
    """The four corners of a Matplotlib axes with arguments for adding a text box."""

    BOTTOM_LEFT = Corner(True, True)
    TOP_LEFT = Corner(False, True)
    BOTTOM_RIGHT = Corner(True, False)
    TOP_RIGHT = Corner(False, False)


class FigureTools:
    darken_palette = _iku.darken_palette
    darken_color = _iku.darken_color

    @classmethod
    def cm2in(cls, tup):
        if Tools.is_true_iterable(tup):
            return [x / 2.54 for x in tup]
        else:
            return float(tup) / 2.54

    @classmethod
    def open_figs(cls) -> Sequence[Figure]:
        """
        Returns all currently open figures.
        """
        return [plt.figure(num=i) for i in plt.get_fignums()]

    @classmethod
    def open_fig_map(cls) -> Mapping[str, Figure]:
        """
        Returns all currently open figures as a dict mapping their labels `Figure.label` to their instances.
        Note that `Figure.label` is often empty in practice.
        """
        return {label: plt.figure(label=label) for label in plt.get_figlabels()}

    @classmethod
    @contextmanager
    def clearing(cls, yes: bool = True) -> Generator[None, None, None]:
        """
        Context manager to clear and close all figures created during its lifespan.
        When the context manager exits, calls `clf` and `close` on all figures created under it.
        :param yes: If False, does nothing
        """
        oldfigs = copy(plt.get_fignums())
        yield
        if yes:
            for fig in [plt.figure(num=i) for i in plt.get_fignums() if i not in oldfigs]:
                fig.clf()
                plt.close(fig)

    @classmethod
    @contextmanager
    def hiding(cls, yes: bool = True) -> Generator[None, None, None]:
        """
        Context manager to hide figure display by setting `plt.interactive(False)`.
        :param yes: If False, does nothing
        """
        isint = plt.isinteractive()
        if yes:
            plt.interactive(False)
        yield
        if yes:
            plt.interactive(isint)

    @classmethod
    @contextmanager
    def using(cls, *args, **kwargs) -> Generator[None, None, None]:
        """
        Provided for convenience as a shorthand to using both chemfish_rc.using, Figs.hiding, and Figs.clearing.
        :param args: Passed to chemfish_rc.using
        :param kwargs: Passed to chemfish_rc.using, except for 'path', 'hide', and 'clear'
        :return: A context manager
        """
        path, hide, clear, reload = (
            str(kwargs.get("path")),
            bool(kwargs.get("hide")),
            bool(kwargs.get("clear")),
            bool(kwargs.get("reload")),
        )
        kwargs = {k: v for k, v in kwargs.items() if k not in {"path", "hide", "clear"}}
        with KVRC.using(*args, **kwargs):
            with FigureTools.clearing(clear):
                with FigureTools.hiding(hide):
                    yield

    @classmethod
    def save(
        cls, figure: FigureSeqLike, path: PLike, names: Optional[Iterator[str]] = None, **kwargs
    ) -> None:
        """
        Save a figure or sequence of figures to `FigureSaver`.
        See that class for more info.
        """
        path = str(path).replace("/", os.sep)
        FigureSaver(**kwargs).save(figure, path, names=names)

    @classmethod
    def plot1d(
        cls,
        values: np.array,
        figsize: Optional[Tup[float, float]] = None,
        x0=None,
        y0=None,
        x1=None,
        y1=None,
        **kwargs,
    ) -> Axes:
        """
        Plots a 1D array and returns the axes.
        kwargs are passed to `Axes.plot`.
        """
        figure = plt.figure(figsize=figsize)
        ax = figure.add_subplot(1, 1, 1)  # Axes
        ax.plot(values, **kwargs)
        ax.set_xlim((x0, x1))
        ax.set_ylim((y0, y1))
        return ax

    @classmethod
    def add_aligned_colorbar(
        cls, ax: Axes, mat, size: str = "5%", number_format: Optional[str] = None
    ):
        """
        Creates a colorbar on the right side of `ax`.
        A padding of chemfish_rc.general_colorbar_left_pad will be applied between `ax` and the colorbar.
        Technically description: Adds a new `Axes` on the right side with width `size`%.
        If chemfish_rc.general_colorbar_on is False, will add the colorbar and make it invisible.
        (This is weirdly necessary to work around a matplotlib bug.)
        :param ax: The Axes, modified in-place
        :param mat: This must be the return value from `matshow` or `imshow`
        :param size: The width of the colorbar
        :param number_format: Formatting string for the text labels on the colorbar (passed to `ax.figure.colorbar`)
        :return:
        """
        #
        # of ax and the padding between cax and ax will be fixed at 0.05 inch.
        # This is crazy, but if we don't have a colorbar, save_fig errors about vmin not being less than vmax
        # So we'll make it and then remove it
        # BUT! We can't remove the cax, so we'll decrease its size
        # This is really important because if we skip the cbar, it's likely to save valuable space
        divider = make_axes_locatable(ax)
        if KVRC.general_colorbar_on:
            pad = KVRC.general_colorbar_left_pad
        else:
            size = "0%"
            pad = 0
        cax = divider.append_axes("right", size=size, pad=pad)
        cbar = ax.figure.colorbar(mat, cax=cax, format=number_format)
        if not KVRC.general_colorbar_on:
            cbar.remove()
        return cbar

    @classmethod
    def text_matrix(
        cls,
        ax: Axes,
        data: pd.DataFrame,
        color_fn: Optional[Callable[[str], str]] = None,
        adjust_x: float = 0,
        adjust_y: float = 0,
        **kwargs,
    ) -> None:
        """
        Adds a matrix of text.
        :param ax: Axes
        :param data: The matrix of any text values; will be converted to strings and empty strings will be ignored
        :param color_fn: An optional function mapping (pre-conversion-to-str) values to colors
        :param adjust_x: Add this value to the x coordinates
        :param adjust_y: Add this value to the y coordinates
        :param kwargs: Passed to `ax.text`
        """
        for r, row in enumerate(data.index):
            for c, col in enumerate(data.columns):
                value = data.iat[r, c]
                if str(value) != "":
                    ax.text(
                        r + adjust_x,
                        c + adjust_y,
                        str(value),
                        color=None if color_fn is None else color_fn(value),
                        **kwargs,
                    )

    @classmethod
    def manual_legend(
        cls,
        ax: Axes,
        labels: Sequence[str],
        colors: Sequence[str],
        patch_size: float = KVRC.legend_marker_size,
        patch_alpha=1.0,
        **kwargs,
    ) -> mlegend.Legend:
        """
        Creates legend handles manually and adds them as the legend on the Axes.
        This is unfortunately necessary in cases where, for ex, only a handle per color is wanted -- not a handle per color and marker shape.
        Applies `FigureTools.fix_labels` and applies chemfish_rc defaults unless they're overridden in kwargs.
        """
        labels, colors = list(labels), list(colors)
        kwargs = copy(kwargs)
        kwargs["ncol"] = kwargs.get("ncol", KVRC.legend_n_cols)
        kwargs["bbox_to_anchor"] = kwargs.get("bbox_to_anchor", KVRC.legend_bbox)
        kwargs["mode"] = "expand" if KVRC.legend_expand else None
        kwargs["loc"] = kwargs.get("loc")
        if "patch_size" in kwargs:
            raise XValueError("patch_size cannot be passed as an argument and kwargs")
        if "patch_alpha" in kwargs:
            raise XValueError("patch_alpha cannot be passed as an argument and kwargs")
        handles = FigureTools.manual_legend_handles(
            labels, colors, patch_size=patch_size, patch_alpha=patch_alpha
        )
        return ax.legend(handles=handles, **kwargs)

    @classmethod
    def manual_legend_handles(
        cls,
        labels: Sequence[str],
        colors: Sequence[str],
        patch_size: float = KVRC.legend_marker_size,
        patch_alpha=1.0,
        **patch_properties,
    ) -> Sequence[patches.Patch]:
        """
        Creates legend handles manually. Does not add the patches to the Axes.
        Also see `FigureTools.manual_legend`.
        This is unfortunately necessary in cases where, for ex, only a handle per color is wanted -- not a handle per color and marker shape.
        Applies `FigureTools.fix_labels`.
        """
        assert len(labels) == len(colors), "{} labels but {} colors".format(
            len(labels), len(colors)
        )
        legend_dict = {e: colors[i] for i, e in enumerate(labels)}
        patch_list = []
        for key in legend_dict:
            data_key = patches.Patch(
                color=legend_dict[key],
                label=FigureTools.fix_labels(key),
                linewidth=patch_size,
                alpha=patch_alpha,
                **patch_properties,
            )
            patch_list.append(data_key)
        return patch_list

    @classmethod
    def fix_labels(
        cls, name: Union[Iterable[str], str], inplace: bool = False
    ) -> Union[Iterable[str], str]:
        """
        Fixes common issues with label names.
        Examples:
            - (-) gets a minus sign: (−)
            - 'uM' is changed to 'µM'
            - --> is changed to →
            - __a and __b are made nicer
            - math is escaped in TeX if necessary
        """

        # noinspection PyProtectedMember
        def fix_u(s: str) -> str:
            return (
                str(s)
                .replace("(-)", "(−)")
                .replace("killed (+)", "lethal (+)")
                .replace("-->", Chars.right)
                .replace("<--", Chars.left)
                .replace("uM", "µM")
                .replace("__a", ":" + Chars.angled("a"))
                .replace("__b", ":" + Chars.angled("b"))
            )

        def fix_ltext(s: str) -> str:
            # escape: # $ % & ~ _ ^ \ { } \( \) \[ \]
            return (
                Tools.strip_paired(s, [("$", "$")])
                .replace("killed (+)", "lethal (+)")
                .replace("__a", ":`a'")
                .replace("__b", ":`b'")
                .replace("_", r"\_")
                .replace("uM", r"\micro M")
                .replace(
                    Chars.micro, r"\micro "
                )  # always append a space to avoid 'undefined control sequence'
            )

        def fix_lmath(s: str) -> str:
            return (
                ("$" + Tools.strip_paired(s, [("$", "$")]) + "$")
                .replace("killed (+)", "lethal (+)")
                .replace("__a", r"\langle a \rangle")
                .replace("__b", r"\langle b \rangle")
                .replace("-->", r"\rightarrow")
                .replace("<--", r"\leftarrow")
                .replace("_", "\\_")
                .replace("uM", r"\micro M")
                .replace(
                    Chars.micro, r"\micro "
                )  # always append a space to avoid 'undefined control sequence'
            )

        def choose_fix(s: str) -> str:
            if not plt.rcParams["text.usetex"]:
                return fix_u(s)
            elif KVRC.label_force_text_mode or not KVRC.label_force_math_mode and "$" not in s:
                return fix_ltext(s)
            elif (
                KVRC.label_force_math_mode
                or s.startswith("$")
                and s.endswith("$")
                and s.count("$") == 2
            ):
                return fix_lmath(s)
            else:
                logger.error("Cannot fix mixed-math mode string {}".format(Chars.shelled(s)))
                return s

        def fix(s0: str) -> str:
            is_label = hasattr(s0, "get_text")
            if is_label:
                # noinspection PyUnresolvedReferences
                s = s0.get_text()  # for matplotlib tick labels
            elif inplace:
                logger.caution("Cannot set inplace; type str")
                s = s0
            else:
                s = s0
            s = KVRC.label_replace_dict.get(s, s)
            r = choose_fix(s) if KVRC.label_fix else s
            r = KVRC.label_replace_dict.get(r, r)
            if inplace and is_label:
                # noinspection PyUnresolvedReferences
                s0.set_text(r)
            if r != s:
                logger.debug("Fixed {} → {}".format(s, r))
            return r

        if Tools.is_true_iterable(name):
            return (fix(s) for s in name)
        else:
            return fix(name)

    @classmethod
    def despine(cls, ax: Axes) -> Axes:
        """
        Removes all spines and ticks on an Axes.
        """
        ax.set_yticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])
        return ax

    @classmethod
    def clear(cls) -> int:
        """
        Removes all matplotlib figures from memory.
        Here because it's confusing to remember.
        Logs an error if not all figures were closed.
        :returns The number of closed figures
        """
        n = len(plt.get_fignums())
        plt.clf()
        plt.close("all")
        m = len(plt.get_fignums())
        if m == 0:
            logger.debug("Cleared {} {}.".format(n, "figures" if n > 1 else "figure"))
        else:
            logger.error("Failed to close figures. Cleared {}; {} remain.".format(n - m, m))
        return n

    @classmethod
    def font_paths(cls) -> Sequence[str]:
        return matplotlib.font_manager.findSystemFonts(fontpaths=None)

    @classmethod
    def add_note_01_coords(cls, ax: Axes, x: float, y: float, s: str, **kwargs) -> Axes:
        """
        Adds text without a box, using chemfish_rc['general_note_font_size'] (unless overridden in kwargs).
        `x` and `y` are in coordinates (0, 1).
        """
        fontsize, kwargs = InternalTools.from_kwargs(
            kwargs, "fontsize", KVRC.general_note_font_size
        )
        t = ax.text(x, y, s=s, fontsize=fontsize, transform=ax.transAxes, **kwargs)
        t.set_bbox(dict(alpha=0.0))
        return ax

    @classmethod
    def add_note_data_coords(cls, ax: Axes, x: float, y: float, s: str, **kwargs) -> Axes:
        """
        Adds text without a box, using chemfish_rc['general_note_font_size'] (unless overridden in kwargs).
        `x` and `y` are in data coordinates.
        """
        fontsize, kwargs = InternalTools.from_kwargs(
            kwargs, "fontsize", KVRC.general_note_font_size
        )
        t = ax.text(x, y, s=s, fontsize=fontsize, **kwargs)
        t.set_bbox(dict(alpha=0.0))
        return ax

    @classmethod
    def stamp(cls, ax: Axes, text: str, corner: Corner, **kwargs) -> Axes:
        """
        Adds a "stamp" in the corner. Ex:
        ```
        FigureTools.stamp(ax, 'hello', Corners.TOP_RIGHT)
        ```
        """
        return FigureTools._text(ax, text, corner, **kwargs)

    @classmethod
    def stamp_runs(cls, ax: Axes, run_ids: Iterable[int]) -> Axes:
        """
        Stamps the run ID(s) in the upper-left corner.
        Only shows if chemfish_rc.stamp_on is True AND len(run_ids) <= chemfish_rc.stamp_max_runs.
        """
        if KVRC.stamp_on:
            run_ids = InternalTools.fetch_all_ids_unchecked(Runs, run_ids)
            run_ids = Tools.unique(run_ids)
            if len(run_ids) <= KVRC.stamp_max_runs:
                text = Tools.join(run_ids, sep=", ", prefix="r")
                return FigureTools._text(ax, text, Corners.TOP_LEFT)

    @classmethod
    def stamp_time(cls, ax: Axes) -> Axes:
        """
        If chemfish_rc.stamp_on is on, stamps the datetime to the top right corner.
        """
        if KVRC.stamp_on:
            text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return FigureTools._text(ax, text, Corners.TOP_RIGHT)

    @classmethod
    def _text(cls, ax: Axes, text: str, corner: Corner, **kwargs) -> Axes:
        fontsize, kwargs = InternalTools.from_kwargs(kwargs, "fontsize", KVRC.stamp_font_size)
        t = ax.text(s=text, **corner.params(), fontsize=fontsize, transform=ax.transAxes, **kwargs)
        t.set_bbox(dict(alpha=0.0))
        return ax


class _Pub:
    """
    Functions to save figures as PDFs in a "publication" mode.
    Provides a context manager that yields a FigureSaver.
    Clears all figures (inc. pre-existing) before entering and on every save.
    Hides all display.
    """

    @contextmanager
    def __call__(
        self, width: str, height: str, save_under: PLike = "", *args, **kwargs
    ) -> Generator[FigureSaver, None, None]:
        """
        A context manager with a `FigureSaver`, non-interactive, auto-clearing, and optional chemfish_rc params.
        :param width: A string passed to `chemfish_rc`; ex: `1/2 2_col` (defined in chemfish_rc params file)
        :param height: A string passed to `chemfish_rc`; ex: `1/2 2_col` (defined in chemfish_rc params file)
        :param save_under: Save everything under this directory (but passing absolute paths will invalidate this)
        :param args: Functions of chemfish_rc passed to `chemfish_rc.using`
        :param kwargs: Kwargs of chemfish_rc and matplotlib params passed to `chemfish_rc.using`.
        :return:
        """
        save_under = str(save_under).replace("/", os.sep)
        save_under = Tools.prepped_dir(save_under)
        # the_fn, kwargs = InternalTools.from_kwargs(kwargs, 'fn', None)
        # args = [*args, the_fn if the_fn is not None else copy(args)]
        pretty_dir = str(save_under) if len(str(save_under)) > 0 else "."
        logger.debug(
            "::Entered:: saving environment {} under {}".format(kwargs.get("scale", ""), pretty_dir)
        )
        FigureTools.clear()
        saver = FigureSaver(save_under=save_under, clear=lambda fig: FigureTools.clear())
        with FigureTools.hiding():
            with KVRC.using(width=width, height=height, *args, savefig_format="pdf", **kwargs):
                yield saver
        logger.debug(
            "::Left:: saving environment {} under {}".format(kwargs.get("scale", ""), pretty_dir)
        )


Pub = _Pub()

__all__ = ["FigureTools", "FigureSaver", "FancyCmaps", "Corners", "Corner", "Pub"]
