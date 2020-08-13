from chemfish.core.core_imports import *
from chemfish.viz._internal_viz import *
from chemfish.viz.color_schemes import KvrcColorSchemes


class MatrixAnnotator:
    """
    Adds labels and brackets around groups of y labels in a matrix that share the same 'target'.
    """

    def __init__(
        self,
        min_cluster_size: int = 1,
        fontsize: Optional[float] = None,
        colors: str = KvrcColorSchemes.qualitative_tol_dark_mod_6(),
        padding: float = 0.2,
        margin: float = 0.75,
        alpha: float = 0.25,
    ):
        self.min_cluster_size, self.fontsize, self.colors, self.padding, self.margin, self.alpha = (
            min_cluster_size,
            fontsize,
            colors,
            padding,
            margin,
            alpha,
        )

    def annotate(self, ax: Axes, name_to_target: Mapping[str, str]) -> None:
        ax.set_xlabel("")
        ax.set_ylabel("")
        qq = Tools.zip_list(
            [*[z.get_text() for z in ax.get_yticklabels()], ""],
            [*ax.get_yticks(), ax.get_yticks()[-1] + 1],
        )
        prev, prev_y = None, 0
        cycler = itertools.cycle(self.colors)
        x_jitter_iter = 5
        for name, y in [*qq, (None, qq[-1][1] + 1)]:
            if name is None or name in name_to_target and name_to_target[name] != prev:
                color = next(cycler)
                if abs(y - prev_y) >= self.min_cluster_size:
                    if prev is None or x_jitter_iter > len(qq) - y - len(prev):
                        x_jitter_iter = 0 if prev is None else len(prev)
                    y_center = prev_y + (y - prev_y) / 2
                    if abs(y - prev_y) == 1:
                        x_jitter_iter += len(prev)
                        self._hline(
                            ax,
                            y_center,
                            prev_y + 1,
                            y + x_jitter_iter,
                            prev,
                            y + x_jitter_iter + 1,
                            "left",
                            color,
                        )
                    elif len(qq) - y < 1:
                        self._box(
                            ax,
                            prev_y,
                            y - 1,
                            prev_y + 1,
                            y - 1 - self.margin,
                            y - 1 - self.margin,
                            y - 1 - self.margin,
                            prev,
                            y - 2,
                            "right",
                            color,
                        )
                    elif len(qq) - y < 10:
                        if prev is not None:
                            x_jitter_iter = len(prev)
                        self._box(
                            ax,
                            prev_y,
                            y,
                            prev_y + 1,
                            y + 2,
                            y + 1,
                            y + 2,
                            prev,
                            y + 1,
                            "right",
                            color,
                        )
                    else:
                        if prev is not None:
                            x_jitter_iter = len(prev)
                        self._box(
                            ax,
                            prev_y,
                            y,
                            prev_y + 1,
                            y + 2,
                            y + 1,
                            y + 2,
                            prev,
                            y + 3,
                            "left",
                            color,
                        )
                if name is not None:
                    prev, prev_y = name_to_target[name], y

    def _box(
        self,
        ax,
        top_y,
        bottom_y,
        top_x0,
        top_x1,
        bottom_x0,
        bottom_x1,
        text,
        text_x,
        text_halign,
        color,
    ):
        top_y, bottom_y = top_y - 0.5, bottom_y - 0.5
        y_adjust = self.padding
        ax.text(
            text_x,
            bottom_y + (top_y - bottom_y) / 2,
            text,
            horizontalalignment=text_halign,
            verticalalignment="center",
            fontsize=self.fontsize,
            color=color,
        )
        ax.hlines(top_y + y_adjust, top_x0, top_x1, color=color)
        ax.hlines(top_y, 0, top_x0, alpha=self.alpha, linestyle="-", color=color)
        ax.hlines(bottom_y - y_adjust, bottom_x0, bottom_x1, color=color)
        ax.hlines(bottom_y, 0, bottom_x0, alpha=self.alpha, linestyle="-", color=color)
        ax.vlines(bottom_x1, top_y + y_adjust, bottom_y - y_adjust, color=color)

    def _hline(self, ax, y, x0, x1, text, text_x, text_halign, color):
        y -= 0.5
        ax.text(
            text_x,
            y,
            text,
            horizontalalignment=text_halign,
            verticalalignment="center",
            fontsize=self.fontsize,
            color=color,
        )
        ax.hlines(y, x0, x1, color=color, linestyle="--")
        ax.hlines(y, 0, x0, alpha=self.alpha, color=color, linestyle="--")


__all__ = ["MatrixAnnotator"]
