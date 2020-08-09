"""
Plotting code for distributions by class,
especially for info from Mandos.
"""

from chemfish.core.core_imports import *
from chemfish.viz.internal_viz import *
from chemfish.viz.figures import *


class BarSlicer(KvrcPlotting):
    def __init__(self, bar_width: float = KVRC.acc_bar_width_fraction, kwargs=None):
        self.bar_width = bar_width
        self.kwargs = {} if kwargs is None else kwargs

    def plot(self, labels, sizes, colors=None, ax=None):
        if ax is None:
            figure = plt.figure()
            ax = figure.add_subplot(1, 1, 1)
        if colors is True:
            colors = InternalVizTools.assign_colors(labels)
        elif colors is False or colors is None:
            colors = ["black" for _ in labels]
        bars = ax.bar(labels, sizes, **self.kwargs)
        if colors is not None:
            for bar, color in zip(bars, colors):
                patch = bar
                current_width = patch.get_width()
                diff = current_width - self.bar_width
                patch.set_width(self.bar_width)
                patch.set_x(patch.get_x() + diff * 0.5)  # recenter
                bar.set_color(color)
                # bar.set_linewidth(1)
                bar.set_edgecolor("black")
        ax.set_ylabel("N compounds")
        ax.set_xticklabels(FigureTools.fix_labels(labels), rotation=90)
        ax.set_xlim(-0.5, len(set(labels)) - 0.5)
        return ax.get_figure()


@abcd.auto_eq()
@abcd.auto_repr_str()
class PieSlicer(KvrcPlotting):
    """
    Code to make pretty pie charts with holes in the center.
    """

    def __init__(self, figsize=None, radius: float = 1.0, kwargs=None):
        self._figsize = (KVRC.width, KVRC.width) if figsize is None else figsize
        self._radius = radius
        self._kwargs = {} if kwargs is None else kwargs

    def plot(self, labels, sizes, colors=None, explode=None, ax=None):
        if colors is False or colors is None:
            colors = ["black" for _ in labels]
        if explode is None:
            explode = [0.0 for _ in sizes]
        if ax is None:
            figure = plt.figure(figsize=self._figsize)
            ax = figure.add_subplot(1, 1, 1)
        wedges, labs = ax.pie(
            sizes,
            colors=colors,
            labels=labels,
            autopct=None,
            startangle=90,
            pctdistance=KVRC.mandos_pie_pct_distance,
            explode=explode,
            wedgeprops={
                "edgecolor": "black",
                "linewidth": KVRC.mandos_pie_outline_width,
                "linestyle": "-",
                "antialiased": True,
            },
            textprops={"linespacing": KVRC.general_linespacing},
            radius=self._radius,
            **self._kwargs,
        )
        for i, t in enumerate(labs):
            t.set_color(colors[i])
        # draw circle
        centre_circle = plt.Circle(
            (0, 0),
            KVRC.mandos_pie_center_circle_fraction,
            lw=KVRC.mandos_pie_outline_width,
            fc="white",
            edgecolor="black",
        )
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
        # Equal aspect ratio ensures that pie is drawn as a circle
        # ax.axis('equal')
        ax.set_aspect("equal", adjustable="box")
        return ax.get_figure()


__all__ = ["PieSlicer", "BarSlicer"]
