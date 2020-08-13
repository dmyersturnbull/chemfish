from __future__ import annotations

from matplotlib.backends.backend_pdf import PdfPages

from chemfish.core.core_imports import *
from chemfish.viz._internal_viz import *

KNOWN_EXTENSIONS = ["jpg", "png", "pdf", "svg", "eps", "ps"]


@abcd.auto_repr_str()
class FigureSaver:
    """
    Offers some small, specific extensions over matplotlib's `figure.savefig`:
    - can remove the figure from memory on each iteration
    - creates directories as needed
    - can save a multi-figure PDF
    - complains about issues
    - the `FigureSaver.save` function handles iterators of different types.
    See `FigureSaver.save` for more info.
    `clear` defines the behavior after saving a single figure:
        - False    ==> do nothing
        - True     ==> clear it
        - callable ==> call it with the Figure instance
    """

    def __init__(
        self,
        save_under: Optional[PLike] = None,
        clear: Union[bool, Callable[[Figure], Any]] = False,
        warnings: bool = True,
        as_type: Optional[str] = None,
        kwargs: Mapping[str, Any] = None,
    ):
        self._save_under = None if save_under is None else Path(save_under)
        if clear is not None and not isinstance(clear, bool) and not callable(clear):
            raise XTypeError(type(clear))
        self._clear = clear
        self._warnings = warnings
        if as_type is not None and not as_type.startswith("."):
            as_type = "." + as_type
        self._as_type = as_type
        self._kwargs = {} if kwargs is None else kwargs

    def __mod__(self, tup):
        self.save_one(*tup)

    def __idiv__(self, tup):
        self.save(*tup)

    def save(
        self, figure: FigureSeqLike, path: PLike = "", names: Optional[Iterator[str]] = None
    ) -> None:
        """
        Saves either:
        1. a single figure `figure` to path `path`
        2. a bunch of figures to directory `path` if `figure` is an iterable (list, dict, etc) over figures
        3. a single PDF with multiple figures, if `path` ends in `.pdf`
        If `figure` is iterable (case 2), it can be either:
        - an iterable over Figures
        - an iterable over (name, Figure) pairs, where `name` is a string that provides the filename (under the directory `path`)
        If it's the first case and `names` is set, will use those to provide the filenames.
        Otherwise, falls back to numbering them (ex: directory/1.png, etc)
        """
        if Tools.is_true_iterable(figure) and path.endswith(".pdf"):
            self.save_all_as_pdf(figure, path, names=names)
        elif Tools.is_true_iterable(figure):
            self.save_all(figure, path, names=names)
        else:
            self.save_one(figure, path)

    def save_all_as_pdf(
        self, figures: FigureSeqLike, path: PLike, names: Optional[Iterator[str]] = None
    ) -> None:
        """
        Save a single PDF with potentially many figures.
        """
        # note! this is weird
        cp = copy(self)
        cp._as_type = ".pdf"
        path = cp._sanitized_file(path)
        with PdfPages(str(path)) as pdf:
            for name, figure in self._enumerate(figures, names):
                pdf.savefig(figure, **self._kwargs)
                # TODO does clearing break this?
                self._clean_up(figure)

    def save_all(
        self, figures: FigureSeqLike, directory: PLike = "", names: Optional[Iterator[str]] = None
    ) -> None:
        for name, figure in self._enumerate(figures, names):
            # DO NOT prepend self.__save_under here!! It's done in save_one.
            path = Path(directory) / Tools.sanitize_path_node(name, is_file=True)
            self._save_one(figure, path)  # clears if needed

    def save_one(self, figure: Figure, path: PLike) -> None:
        self._save_one(figure, path)

    def _save_one(self, figure: Figure, path: PLike) -> None:
        path = self._sanitized_file(path)
        figure.savefig(path, **self._kwargs)
        self._clean_up(figure)

    def _enumerate(
        self, figures, names: Optional[Sequence[str]]
    ) -> Generator[Tup[str, Figure], None, None]:
        if isinstance(figures, Mapping):
            figures = figures.items()
        for i, figure in enumerate(figures):
            if names is not None:
                yield next(names), figure
            elif isinstance(figure, tuple):
                yield figure[0], figure[1]
            else:
                yield str(i), figure

    def _clean_up(self, figure: Figure) -> None:
        if self._clear is None:
            pass
        elif self._clear is True:
            pass
            figure.clear()
            figure.clf()
        elif callable(self._clear):
            self._clear(figure)

    def _sanitized_file(self, path: PLike) -> Path:
        """
        Sanitizes a file path:
            - prepends self._save_under if needed
            - warns about issues
        :param path: The path, including directory, but excluding self._save_under
        :return: The Path
        """
        path = Path(path)
        if self._save_under is not None and Path(path).is_absolute():
            logger.warning(
                "_save_under is {} but path {} is absolute".format(self._save_under, path)
            )
        elif self._save_under is not None:
            path = self._save_under / path
        ext_valid = any((str(path).endswith("." + s) for s in KNOWN_EXTENSIONS))
        # can't just detect no suffix, because 12.5uM will have suffix 5uM
        # also, don't use with_suffix for this same reason
        if not ext_valid:
            pt = "." + plt.rcParams["savefig.format"] if self._as_type is None else self._as_type
            path = Path(str(path) + pt)
        path = Tools.prepped_file(path)
        logger.minor(path)
        return path


__all__ = ["FigureSaver"]
