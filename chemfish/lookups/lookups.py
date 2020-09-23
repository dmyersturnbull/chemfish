

class LookupTool(metaclass=abc.ABCMeta):
    """
    A class that provides static functions to look up data from Valar into Lookup DataFrames.
    These functions resemble SQL views.

    """

    @classmethod
    def _expressions_use(cls, expressions, any_of):
        """


        Args:
            expressions:
            any_of:

        Returns:

        """
        return len(LookupTool._expressions_using(expressions, any_of)) > 0

    @classmethod
    def _expressions_using(cls, expressions, any_of):
        """

        Args:
            expressions:
             any_of:

        Returns:

        """
        expressions = InternalTools.flatten_smart(expressions)
        return [
            expression
            for expression in expressions
            if (
                hasattr(expression, "lhs")
                and isinstance(expression.lhs, peewee.Field)
                and expression.lhs.model in any_of
                or hasattr(expression, "rhs")
                and isinstance(expression.rhs, peewee.Field)
                and expression.rhs.model in any_of
            )
        ]

    @classmethod
    def _expressions_not_using(cls, expressions, any_of):
        """
        X.

        Args:
          expressions:
          any_of:

        Returns:

        """
        expressions = InternalTools.flatten_smart(expressions)
        return [
            expression
            for expression in expressions
            if (
                hasattr(expression, "lhs")
                and isinstance(expression.lhs, peewee.Field)
                and expression.lhs.model in any_of
                or hasattr(expression, "rhs")
                and isinstance(expression.rhs, peewee.Field)
                and expression.rhs.model in any_of
            )
        ]

    @classmethod
    def _simple(cls, table, query, like, regex, wheres, *data):
        """
        For backwards compatibility

        Args:
            table:
            query:
            like:
            regex:
            wheres:
            *data:

        Returns:

        """
        return (
            LookupBuilder(table)
            .set_query(query)
            .like_regex(like, regex)
            .add_all(*data)
            .query(wheres)
        )


class Column:
    """"""

    def __init__(
        self,
        name: str,
        attribute: Optional[str] = None,
        function: Optional[Callable[[Any], Any]] = None,
    ):
        """

        Args:
            name:
            attribute:
            function:
        """
        self.name = name
        self.attribute = attribute
        self.function = (lambda x: x) if function is None else function

    def get(self, data: Any) -> Any:
        """


        Args:
            data: Any:

        Returns:

        """
        if self.attribute:
            return self.function(Tools.look(data, self.attribute))
        else:
            return self.function(data)


T = TypeVar("T")
V = TypeVar("V")

