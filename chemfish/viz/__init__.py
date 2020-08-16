"""
Visualization code.
Can depend on core, calc, and model.
"""
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from chemfish.core.core_imports import *


class CakeComponent(metaclass=abc.ABCMeta):
    """ """
    pass


class CakeLayer(metaclass=abc.ABCMeta):
    """ """
    @abcd.abstractmethod
    def plot(self, **kwargs) -> Axes:
        """
        

        Args:
          **kwargs: 

        Returns:

        """
        raise NotImplementedError()


__oldfig = copy(plt.figure)
__oldsubplots = copy(plt.subplots)


def fix_fig(fig: Figure, **kwargs):
    """
    

    Args:
      fig: Figure: 
      **kwargs: 

    Returns:

    """
    # using kwargs.get('figsize', plt.rcParams['figure.figsize']) if figsize is passed as None
    if kwargs.get("figsize") is None:
        w, h = plt.rcParams["figure.figsize"]
    else:
        w, h = kwargs["figsize"]
    label = kwargs.get("label")
    if hasattr(fig, "canvas") and hasattr(fig.canvas, "layout"):
        # https://github.com/matplotlib/jupyter-matplotlib/issues/117
        # There's a recommended workaround
        fig.canvas.layout.height = str(h) + "in"
        fig.canvas.layout.width = str(w) + "in"
    # fig.set_size_inches(w, h)
    if label is not None:  # maybe super() actually has defaults
        fig.set_label(label)
    logger.trace(f"New figure of dimensions {h},{w}")


def new_fig(**kwargs):
    """
    

    Args:
      **kwargs: 

    Returns:

    """
    fig = __oldfig(**kwargs)
    fix_fig(fig, **kwargs)
    return fig


def subplots(**kwargs):
    """
    

    Args:
      **kwargs: 

    Returns:

    """
    fig, ax = __oldsubplots(**kwargs)
    fix_fig(fig, **kwargs)
    return fig, ax


new_fig.__doc__ = plt.figure.__doc__
subplots.__doc__ = plt.subplots.__doc__
plt.figure = new_fig
plt.subplots = subplots

__all__ = ["CakeComponent", "CakeLayer", "plt"]
