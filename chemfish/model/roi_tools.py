from chemfish.core.core_imports import *


class RoiBounds:
    """ """

    def __init__(self, x0: int, y0: int, x1: int, y1: int) -> None:
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    def __repr__(self) -> str:
        return f"({self.x0},{self.y0})→({self.x1},{self.y1})"

    def __str__(self):
        return repr(self)


class WellRoi(RoiBounds):
    """ """

    def __init__(self, row: int, column: int, x0: int, y0: int, x1: int, y1: int) -> None:
        self.row_index = row
        self.column_index = column
        super().__init__(x0, y0, x1, y1)

    def __repr__(self) -> str:
        return (
            f"{self.row_index},{self.column_index}  = ({self.x0},{self.y0})→({self.x1},{self.y1})"
        )


class RoiTools:
    """ """

    @classmethod
    def verify_roi(cls, roi: Rois, width: int, height: int, desc: str = "") -> None:
        """


        Args:
          roi: Rois:
          width: int:
          height: int:
          desc:

        Returns:

        """
        return cls.verify_coords(roi.x0, roi.y0, roi.x1, roi.y1, width, height, desc=desc)

    @classmethod
    def verify_coords(
        cls, x0: int, y0: int, x1: int, y1: int, width: int, height: int, desc: str = ""
    ) -> None:
        """


        Args:
          x0: int:
          y0: int:
          x1: int:
          y1: int:
          width: int:
          height: int:
          desc:

        Returns:

        """
        msg = " for " + str(desc) if len(desc) > 0 else ""
        if x0 < 0 or y0 < 0 or x1 < 0 or y1 < 0:
            raise OutOfRangeError(f"Cannot crop to negative bounds {(x0, y0, x1, y1)}: '{msg}'")
        if x0 >= x1 or y0 >= y1:
            raise OutOfRangeError(
                f"x0 is past x1 or y0 is past y1 (or equal): {(x0, y0, x1, y1)} / '{msg}'"
            )
        if x1 > width or y1 > height:
            raise OutOfRangeError(
                f"Cannot crop video of size {(width, height)} to {(x0, y0, x1, y1)}: '{msg}'"
            )


__all__ = ["RoiTools", "RoiBounds", "WellRoi"]
