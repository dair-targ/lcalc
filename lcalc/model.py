from .log import log
from .identifiers import NamespaceIdentifier, AbsoluteIdentifier, RelativeIdentifier, Identifier


class Def(object):
    def __str__(self, comment: bool = True):
        raise NotImplementedError()

    def __repr__(self, comment: bool = True):
        return self.__str__(comment=comment)

    def __eq__(self, other):
        raise NotImplementedError()

    def link(self, namespace_identifier: NamespaceIdentifier):
        raise NotImplementedError(self.__class__.__name__)

    def shift(self, d, c=0):
        """
        :type: c: int
        :param c: How deep we are in a term (in the abstract syntax tree)
        :type d: int
        :param d: Specifies by how much we want to shift the free variables
        :rtype: Def
        :returns: A copy of expression with all free values having
        de Brujin index changed by `index_delta`.
        A value considered "free" whenever it is not definied
        by the innermost `value._index` abstractions.
        """
        raise NotImplementedError(self.__class__.__name__)

    def substitute(self, expr, j=0):
        """
        :type: j: int
        :type: pointer to the abstraction to substitute
        :type expr: Def
        :rtype: Def
        :returns: A copy of expression with all values
        defined by `root_index` abstraction
        replaced with a copies of expr
        """
        raise NotImplementedError(self.__class__.__name__)

    def beta(self, context):
        """
        :rtype: Def
        """
        raise NotImplementedError(self.__class__.__name__)

    def eta(self):
        """
        :rtype: Def
        """
        raise NotImplementedError(self.__class__.__name__)

    def bound_to(self, root_index=0):
        raise NotImplementedError(self.__class__.__name__)


class GlobalRef(Def):
    def __init__(self, absolute_identifier: AbsoluteIdentifier):
        self._absolute_identifier = absolute_identifier

    def __str__(self, comment: bool = True):
        return f'{"{absref}" if comment else ""}{self._absolute_identifier}'

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._absolute_identifier == other._absolute_identifier

    def link(self, namespace_identifier: NamespaceIdentifier):
        return self

    @log
    def shift(self, d, c=0):
        return self

    @log
    def substitute(self, expr, j=0):
        return self

    @log
    def beta(self, context) -> Def:
        return context.get_def(self._absolute_identifier)


class LocalRef(Def):
    def __init__(self, relative_identifier: RelativeIdentifier):
        self._relative_identifier = relative_identifier

    def __str__(self, comment: bool = True):
        return f'{"{locref}" if comment else ""}{self._relative_identifier}'

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._relative_identifier == other._relative_identifier

    def link(self, namespace_identifier: NamespaceIdentifier):
        return GlobalRef(AbsoluteIdentifier(namespace_identifier, self._relative_identifier))

    @log
    def shift(self, d, c=0):
        return self

    @log
    def substitute(self, expr, j=0):
        return self

    @log
    def beta(self, context):
        return self


class Val(Def):
    def __init__(self, identifier: Identifier, index: int):
        assert index >= 0
        self._identifier = identifier
        self._index = index

    def __str__(self, comment: bool = True):
        return f'{"{<-" + self._index + "}" if comment else ""}{self._identifier}'

    def __eq__(self, other):
        return isinstance(other, Val) and self._index == other._index

    def link(self, namespace_identifier: NamespaceIdentifier,):
        return self

    @log
    def shift(self, d, c=0):
        return Val(self._identifier, self._index + d) if self._index >= c else self

    @log
    def substitute(self, expr, j=0):
        return expr if self._index == j else self

    @log
    def beta(self, context):
        return self


class Abs(Def):
    """Abstraction"""
    def __init__(self, identifier: RelativeIdentifier, body: Def):
        self._identifier: RelativeIdentifier = identifier
        self._body = body

    def __str__(self, comment: bool = True):
        return f'λ{self._identifier}.{self._body.__str__(comment=comment)}'

    def __eq__(self, other):
        return isinstance(other, Abs) and self._body == other._body

    def link(self, namespace_identifier):
        return Abs(self._identifier, self._body.link(namespace_identifier))

    @log
    def shift(self, d, c=0):
        return Abs(self._identifier, self._body.shift(d, c + 1))

    @log
    def substitute(self, expr, j=0):
        return Abs(
            self._identifier,
            self._body.substitute(
                expr.shift(1),
                j + 1
            )
        )

    @log
    def beta(self, context):
        return Abs(self._identifier, self._body.beta(context))


class App(Def):
    """Application"""
    def __init__(self, m, n):
        """
        :type m: Def
        :type n: Def
        """
        super(App, self).__init__()
        self._m = m
        self._n = n

    def __str__(self, comment: bool = True):
        sm = self._m.__str__(comment=comment)
        if isinstance(self._m, Abs):
            sm = '(' + sm + ')'
        sn = self._n.__str__(comment=comment)
        if isinstance(self._n, App):
            sn = '(' + sn + ')'
        return f'{sm} {sn}'

    def __eq__(self, other):
        return isinstance(other, App) and self._m == other._m and self._n == other._n

    def link(self, namespace_identifier):
        return App(
            self._m.link(namespace_identifier),
            self._n.link(namespace_identifier),
        )

    @log
    def shift(self, d, c=0):
        return App(self._m.shift(d, c), self._n.shift(d, c))

    @log
    def substitute(self, expr, j=0):
        return App(
            self._m.substitute(expr, j),
            self._n.substitute(expr, j)
        )

    @log
    def beta(self, context):
        if isinstance(self._m, Abs):
            return self._m._body.substitute(
                expr=self._n.shift(1)
            ).shift(-1)
        else:
            return App(
                self._m.beta(context),
                self._n.beta(context)
            )
