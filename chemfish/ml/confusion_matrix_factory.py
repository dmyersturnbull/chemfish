
class ConfusionMatrices:
    """ """

    @classmethod
    def average(cls, matrices: Sequence[ConfusionMatrix]) -> ConfusionMatrix:
        """
        Averages a list of confusion matrices.

        Args:
            matrices: An iterable of ConfusionMatrices (does not need to be a list)

        Returns:
            A new ConfusionMatrix

        """
        if len(matrices) < 1:
            raise EmptyCollectionError("Cannot average 0 matrices")
        matrices = [m.unsort() for m in matrices]
        rows, cols, mx0 = matrices[0].rows, matrices[0].columns, matrices[0]
        if any((not m.is_symmetric() for m in matrices)):
            raise RefusingRequestError(
                "Refusing to average matrices because"
                "for at least one matrix the rows and columns are different"
            )
        for m in matrices[1:]:
            if m.rows != rows:
                raise RefusingRequestError(
                    "At least one confusion matrix has different rows than another"
                    "(or different columns than another)"
                )
            mx0 += m
        # noinspection PyTypeChecker
        return ConfusionMatrix((1.0 / len(matrices)) * mx0)

    @classmethod
    def agg_matrices(
        cls,
        matrices: Sequence[ConfusionMatrix],
        aggregation: Callable[[Sequence[pd.DataFrame]], None],
    ) -> ConfusionMatrix:
        """
        Averages a list of confusion matrices.

        Args:
            matrices: An iterable of ConfusionMatrices (does not need to be a list)
            aggregation: to perform, such as np.mean

        Returns:
            A new ConfusionMatrix

        """
        if len(matrices) < 1:
            raise EmptyCollectionError("Cannot aggregate 0 matrices")
        matrices = [mx.unsort() for mx in matrices]
        rows, cols, mx = matrices[0].rows, matrices[0].columns, matrices[0]
        if rows != cols:
            raise RefusingRequestError(
                "Refusing to aggregate matrices because for at least one matrix the rows and columns are different"
            )
        ms = []
        for m in matrices[1:]:
            if m.rows != rows or m.columns != cols:
                raise RefusingRequestError(
                    "At least one confusion matrix has different rows than another (or different columns than another)"
                )
            ms.append(m)
        return ConfusionMatrix(aggregation(ms))

    @classmethod
    def zeros(cls, classes: Sequence[str]) -> ConfusionMatrix:
        """


        Args:
            classes: Sequence[str]:

        Returns:

        """
        return ConfusionMatrix(
            pd.DataFrame(
                [pd.Series({"class": r, **{c: 0.0 for c in classes}}) for r in classes]
            ).set_index("class")
        )

    @classmethod
    def perfect(cls, classes: Sequence[str]) -> ConfusionMatrix:
        """


        Args:
            classes: Sequence[str]:

        Returns:

        """
        return ConfusionMatrix(
            pd.DataFrame(
                [
                    pd.Series({"class": r, **{c: 1.0 if r == c else 0.0 for c in classes}})
                    for r in classes
                ]
            ).set_index("class")
        )

    @classmethod
    def uniform(cls, classes: Sequence[str]) -> ConfusionMatrix:
        """


        Args:
            classes: Sequence[str]:

        Returns:

        """
        return ConfusionMatrix(
            pd.DataFrame(
                [
                    pd.Series({"class": r, **{c: 1.0 / len(classes) for c in classes}})
                    for r in classes
                ]
            ).set_index("class")
        )

