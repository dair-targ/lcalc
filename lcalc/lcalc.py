# -*- coding: utf-8 -*-
import typing

import parsec
import string
import logging
import functools


LOGGER = logging.getLogger('lcalc')
LOGGER.setLevel(logging.INFO)


def log(fn):
    def log_result(self, args, kwargs, result):
        LOGGER.debug('%s --%s.%s(%s)--> %s' % (
            self,
            self.__class__.__name__,
            fn.__name__,
            ','.join(map(str, list(args) + ['%s=%s' % (k, v) for k, v in kwargs.items()])),
            result
        ))

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        log_result(self, args, kwargs, '...')
        result = fn.__call__(self, *args, **kwargs)
        log_result(self, args, kwargs, result)
        return result
    return wrapper


class Identifier(object):
    pass


class RelativeIdentifier(Identifier):
    def __init__(self, value: str):
        self._value = value

    def __str__(self):
        return self._value

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._value == other._value

    def __hash__(self):
        return hash(self._value)


class NamespaceIdentifier(Identifier):
    def __init__(self, value: str):
        self._value = value

    def __str__(self):
        return self._value

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self._value == other._value

    def __hash__(self):
        return hash(self._value)


class AbsoluteIdentifier(Identifier):
    def __init__(self, namespace_identifier: NamespaceIdentifier, relative_identifier: RelativeIdentifier):
        self._namespace_identifier = namespace_identifier
        self._relative_identifier = relative_identifier

    def __str__(self):
        return '%s/%s' % (repr(self._namespace_identifier), repr(self._relative_identifier))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._namespace_identifier == other._namespace_identifier and self._relative_identifier == other._namespace_identifier

    def __hash__(self):
        return hash((self._namespace_identifier, self._relative_identifier))

    @property
    def namespace_identifier(self) -> NamespaceIdentifier:
        return self._namespace_identifier

    @property
    def relative_identifier(self) -> RelativeIdentifier:
        return self._relative_identifier


class Def(object):
    def __init__(self):
        pass

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return self.__str__()

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


class FreeVal(Def):
    def __init__(self, identifier: Identifier):
        super(FreeVal, self).__init__()
        self._identifier = identifier

    def __str__(self):
        return '{free}%s' % self._identifier

    def __eq__(self, other):
        return isinstance(other, FreeVal) and self._identifier == other._identifier

    def link(self, namespace_identifier: NamespaceIdentifier):
        if isinstance(self._identifier, RelativeIdentifier):
            return FreeVal(AbsoluteIdentifier(namespace_identifier, self._identifier))
        else:
            return self

    @log
    def shift(self, d, c=0):
        return self

    @log
    def substitute(self, expr, j=0):
        return self

    @log
    def beta(self, context):
        return context.get_def(self._identifier.namespace_identifier, self._identifier)


class Val(Def):
    def __init__(self, identifier: Identifier, index: int):
        super(Val, self).__init__()
        assert index >= 0
        self._identifier = identifier
        self._index = index

    def __str__(self):
        return '{<-%d}%s' % (self._index, self._identifier)

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
        super(Abs, self).__init__()
        self._identifier: RelativeIdentifier = identifier
        self._body = body

    def __str__(self):
        return u'λ%s.%s' % (self._identifier, self._body)

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

    def __str__(self):
        sm = str(self._m)
        if isinstance(self._m, Abs):
            sm = '(' + sm + ')'
        sn = str(self._n)
        if isinstance(self._n, App):
            sn = '(' + sn + ')'
        return '%s %s' % (sm, sn)

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


class Statement(object):
    def __init__(self, relative_identifier: RelativeIdentifier, expr: Def):
        assert isinstance(relative_identifier, RelativeIdentifier)
        self._relative_identifier = relative_identifier
        self._expr = expr

    @property
    def relative_identifier(self) -> RelativeIdentifier:
        return self._relative_identifier

    @property
    def expr(self) -> Def:
        return self._expr


class ImportStatement(object):
    def __init__(self, identifier: NamespaceIdentifier):
        self._identifier = identifier

    @property
    def identifier(self):
        return self._identifier


class Namespace(object):
    def __init__(self, import_statements: typing.List[ImportStatement], statements: typing.List[Statement]):
        self._import_statements = import_statements
        self._exprs: typing.Dict[RelativeIdentifier, Def] = {
            statement.relative_identifier: statement.expr
            for statement in statements
        }

    def link(self, namespace_identifier: NamespaceIdentifier):
        for identifier in self._exprs.keys():
            self._exprs[identifier] = self._exprs[identifier].link(namespace_identifier)

    def get_def(self, relative_identifier: RelativeIdentifier) -> Def:
        if relative_identifier not in self._exprs:
            raise Exception('"%s" is not defined. Defined identifiers are:\n%s' % (
                relative_identifier,
                ''.join('  %s\n' % n for n in self._exprs),
            ))
        return self._exprs[relative_identifier]

    @property
    def import_statements(self):
        return self._import_statements


class Parser(object):
    def white(self):
        @parsec.generate
        def parser():
            yield parsec.one_of(' \t\n').desc('white')
        return parser

    def whites(self):
        @parsec.generate
        def parser():
            yield parsec.many(self.white()).desc('whites')
        return parser

    def optional(self, p):
        return parsec.times(p, 0, 1)

    def comment(self):
        @parsec.generate
        def parser():
            yield self.optional(self.whites())
            opened = yield self.optional(parsec.string('{'))
            if opened:
                yield parsec.many(parsec.none_of('}'))
                body = yield parsec.string('}')
                yield self.whites()
                return body
        return parser

    def eof(self):
        @parsec.generate
        def parser():
            yield self.comment()
            yield parsec.eof()
        return parser

    def namespace_identifier(self):
        @parsec.generate
        def parser():
            yield self.comment()
            rest = yield parsec.many1(parsec.one_of(string.ascii_letters + '_' + string.digits))
            yield self.comment()
            return NamespaceIdentifier(''.join(rest))
        return parser

    def relative_identifier(self):
        @parsec.generate
        def parser():
            yield self.comment()
            rest = yield parsec.many1(parsec.one_of(string.ascii_letters + '_' + string.digits))
            yield self.comment()
            return RelativeIdentifier(''.join(rest))
        return parser

    def absolute_identifier(self) -> Identifier:
        @parsec.generate
        def parser():
            namespace_identifier = yield self.namespace_identifier()
            yield parsec.string('/')
            relative_identifier = yield self.relative_identifier()
            return AbsoluteIdentifier(namespace_identifier, relative_identifier)
        return parser

    def parens(self, subparser):
        @parsec.generate
        def parser():
            yield parsec.string('(')
            val = yield subparser
            yield parsec.string(')')
            return val

        return parser

    def p_val(self, abss):
        @parsec.generate
        def parser() -> Val:
            identifier = yield parsec.try_choice(self.absolute_identifier(), self.relative_identifier())
            for index, abs in enumerate(abss[::-1]):
                if abs == identifier:
                    return Val(identifier, index)
            else:
                return FreeVal(identifier)
        return parser

    def p_abs(self, abss):
        @parsec.generate
        def parser() -> Abs:
            yield parsec.try_choice(parsec.string('λ'), parsec.string('\\'))
            identifier = yield self.relative_identifier()
            yield parsec.string('.')
            body = yield self.p_expr(abss + [identifier])
            return Abs(identifier, body)
        return parser

    def p_non_app(self, abss):
        @parsec.generate
        def parser():
            yield self.comment()
            expr = yield parsec.try_choice(
                self.parens(self.p_expr(abss)),
                parsec.try_choice(
                    self.p_abs(abss),
                    self.p_val(abss)
                )
            )
            yield self.comment()
            return expr

        return parser

    def p_app(self, abss):
        @parsec.generate
        def parser():
            term = yield self.p_non_app(abss)
            while True:
                next_term = yield parsec.try_choice(
                    self.p_non_app(abss),
                    parsec.string(''),
                )
                if next_term is '':
                    break
                term = App(term, next_term)
            return term

        return parser

    def p_expr(self, abss):
        @parsec.generate
        def parser():
            yield self.comment()
            expr = yield parsec.try_choice(
                self.p_abs(abss),
                parsec.try_choice(
                    self.p_app(abss),
                    self.p_val(abss)
                )
            )
            yield self.comment()
            return expr

        return parser

    def p_statement(self):
        @parsec.generate
        def parser():
            identifier = yield self.relative_identifier()
            yield parsec.string('=')
            expr = yield self.p_expr([])
            yield parsec.string(';')
            return Statement(identifier, expr)
        return parser

    def p_import_statement(self):
        @parsec.generate
        def parser():
            yield self.optional(self.whites())
            yield parsec.string('import')
            yield self.optional(self.whites())
            identifier = yield self.namespace_identifier()
            yield self.optional(self.whites())
            yield parsec.string(';')
            yield self.optional(self.whites())
            return ImportStatement(identifier)
        return parser

    def p_namespace(self):
        @parsec.generate
        def parser():
            import_statements = yield parsec.many(self.p_import_statement())
            statements = yield parsec.many(self.p_statement())
            yield self.eof()
            return Namespace(import_statements, statements)
        return parser


def parse_def(source: str) -> Def:
    """
    Parses a single Def
    """
    return Parser().p_expr([]).parse(source)


def parse_namespace(source: str) -> Namespace:
    return Parser().p_namespace().parse(source)


class Context(object):
    def __init__(self, namespaces: typing.Dict[NamespaceIdentifier, Namespace]):
        self._namespaces = namespaces
        self.link()

    def link(self):
        for namespace_name, namespace in self._namespaces.items():
            namespace.link(namespace_name)

    def get_namespace(self, namespace_identifier: NamespaceIdentifier):
        if namespace_identifier in self._namespaces:
            return self._namespaces[namespace_identifier]
        else:
            raise Exception('No such namespace: %s' % namespace_identifier)

    def get_def(self, namespace_identifier: NamespaceIdentifier, identifier: Identifier) -> Def:
        if isinstance(identifier, AbsoluteIdentifier):
            namespace = self.get_namespace(identifier.namespace_identifier)
            relative_identifier: RelativeIdentifier = identifier.relative_identifier
        elif isinstance(identifier, RelativeIdentifier):
            namespace = self.get_namespace(namespace_identifier)
            relative_identifier: RelativeIdentifier = identifier
        else:
            raise Exception()
        if relative_identifier._value.isdigit():
            return church_numerals[int(relative_identifier._value)]
        return namespace.get_def(relative_identifier)

    def eval(self, absolute_identifier: AbsoluteIdentifier=AbsoluteIdentifier(NamespaceIdentifier('main'), RelativeIdentifier('main'))):
        expr = self.get_def(absolute_identifier.namespace_identifier, absolute_identifier)
        old = None
        step = 0
        LOGGER.info('Given: %s' % expr)
        while expr != old:
            old = expr
            expr = expr.beta(self)
            LOGGER.info('Step %d, beta -> %s' % (step, expr))
            step += 1
        LOGGER.info('Result: %s' % expr)
        return expr


class DictContext(Context):
    def __init__(self, sources: typing.Optional[typing.Dict[str, str]]=None):
        super(DictContext, self).__init__({
            NamespaceIdentifier(namespace_name): parse_namespace(namespace_source)
            for namespace_name, namespace_source in sources.items()
        } if sources is not None else {})


class FSContext(Context):
    def __init__(self, namespace_identifier: NamespaceIdentifier):
        namespaces = {}
        to_load = {namespace_identifier}
        while to_load:
            namespace_identifier = to_load.pop()
            namespace = self._load_namespace(namespace_identifier)
            namespaces[namespace_identifier] = namespace
            for import_statement in namespace.import_statements:
                if import_statement.identifier not in namespaces:
                    to_load.add(import_statement.identifier)
        super(FSContext, self).__init__(namespaces)

    def _load_namespace(self, namespace_identifier: NamespaceIdentifier) -> Namespace:
        logging.debug('Loading %s' % namespace_identifier)
        with open('%s.lcalc' % namespace_identifier._value) as f:
            source = f.read()
            return parse_namespace(source)


_RI_x = RelativeIdentifier('x')
_RI_f = RelativeIdentifier('f')
ID = Abs(_RI_x, Val(_RI_x, 0))


class _ChurchNumerals(object):
    ZERO = Abs(_RI_f, ID)
    ONE = Abs(_RI_f, Abs(_RI_x, App(Val(_RI_f, 1), Val(_RI_x, 0))))

    def __init__(self):
        self._x = Val(_RI_x, 0)
        self._f = Val(_RI_f, 1)
        self._cache = [self._x]

    def _cached(self, item):
        """
        :type item: int
        :rtype: Val | App
        """
        if item < 0:
            raise ValueError('item (%d) must be > 0' % item)
        elif item < len(self._cache):
            return self._cache[item]
        else:
            self._cache.append(App(self._f, self._cached(item - 1)))
            return self._cache[-1]

    def __getitem__(self, item):
        """
        :type item: int
        """
        if item == 0:
            return self.ZERO
        elif item == 1:
            return self.ONE
        else:
            return Abs(_RI_f, Abs(_RI_x, self._cached(item)))


church_numerals = _ChurchNumerals()
