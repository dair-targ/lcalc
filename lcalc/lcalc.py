# -*- coding: utf-8 -*-
import parsec
import string
import logging
import functools


LOGGER = logging.getLogger('lcalc')


def log(fn):
    log_result = lambda self, args, kwargs, result: LOGGER.debug('%s --%s.%s(%s)--> %s' % (
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


class Def(object):
    def __init__(self):
        pass

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        raise NotImplementedError()

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

    def beta(self):
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


class Val(Def):
    def __init__(self, name, index):
        """
        :type name: str
        :type index: int
        """
        super(Val, self).__init__()
        assert index >= 0
        self._name = name
        self._index = index

    def __str__(self):
        return '{<-%d}%s' % (self._index, self._name)

    def __eq__(self, other):
        return isinstance(other, Val) and self._index == other._index

    @log
    def shift(self, d, c=0):
        return Val(self._name, self._index + d) if self._index >= c else self

    @log
    def substitute(self, expr, j=0):
        return expr if self._index == j else self

    @log
    def beta(self):
        return self


class Abs(Def):
    """Abstraction"""
    def __init__(self, name, body):
        """
        :type name: str
        :type body: Def
        """
        super(Abs, self).__init__()
        self._name = name
        self._body = body

    def __str__(self):
        return u'λ%s.%s' % (self._name, self._body)

    def __eq__(self, other):
        return isinstance(other, Abs) and self._body == other._body

    @log
    def shift(self, d, c=0):
        return Abs(self._name, self._body.shift(d, c + 1))

    @log
    def substitute(self, expr, j=0):
        return Abs(
            self._name,
            self._body.substitute(
                expr.shift(1),
                j + 1
            )
        )

    @log
    def beta(self):
        return Abs(self._name, self._body.beta())


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
    def beta(self):
        if isinstance(self._m, Abs):
            return self._m._body.substitute(
                expr=self._n.shift(1)
            ).shift(-1)
        else:
            return App(
                self._m.beta(),
                self._n.beta()
            )


def parse(source):
    """
    :rtype: Def
    """
    white = parsec.one_of(' \t\n').desc('white')
    whites = parsec.many(white).desc('whites')

    optional = lambda p: parsec.times(p, 0, 1)

    @parsec.generate
    def comment():
        yield optional(whites)
        opened = yield optional(parsec.string('{'))
        if opened:
            yield parsec.many(parsec.none_of('}'))
            body = yield parsec.string('}')
            yield whites
            return body

    @parsec.generate
    def identifier():
        yield comment
        first = yield parsec.one_of(string.ascii_letters + '_')
        rest = yield parsec.many(parsec.one_of(string.ascii_letters + '_' + string.digits))
        yield comment
        return first + ''.join(rest)

    def parens(subparser):
        @parsec.generate
        def parser():
            yield parsec.string('(')
            val = yield subparser
            yield parsec.string(')')
            return val
        return parser

    def p_val(abss):
        @parsec.generate
        def parser():
            name = yield identifier
            for index, abs in enumerate(abss[::-1]):
                if abs == name:
                    return Val(name, index)
            else:
                raise Exception('Free value: %s' % name)
                #return FreeVal(name)
        return parser

    def p_abs(abss):
        @parsec.generate
        def parser():
            yield parsec.try_choice(parsec.string('λ'), parsec.string('\\'))
            name = yield identifier
            yield parsec.string('.')
            body = yield p_expr(abss + [name])
            return Abs(name, body)
        return parser

    def p_non_app(abss):
        @parsec.generate
        def parser():
            yield comment
            expr = yield parsec.try_choice(
                parens(p_expr(abss)),
                parsec.try_choice(
                    p_abs(abss),
                    p_val(abss)
                )
            )
            yield comment
            return expr
        return parser

    def p_app(abss):
        @parsec.generate
        def parser():
            term = yield p_non_app(abss)
            while True:
                next_term = yield parsec.try_choice(p_non_app(abss), parsec.string(''))
                if next_term is '':
                    break
                term = App(term, next_term)
            return term
        return parser

    def p_expr(abss):
        @parsec.generate
        def parser():
            yield comment
            expr = yield parsec.try_choice(
                p_abs(abss),
                parsec.try_choice(
                    p_app(abss),
                    p_val(abss)
                )
            )
            yield comment
            return expr
        return parser

    @parsec.generate
    def parser():
        expr = yield p_expr([])
        yield parsec.eof()
        return expr

    return parser.parse(source)


def try_parse(source):
    """
    :rtype: Def | None
    """
    try:
        return parse(source)
    except parsec.ParseError as pe:
        line, col = parsec.ParseError.loc_info(source, pe.index)
        print(pe)
        print(source.split('\n')[line])
        print('-' * col + '^')


def evaluate(expr):
    """
    :rtype: Def
    """
    old = None
    step = 0
    LOGGER.info('Given: %s' % expr)
    while expr != old:
        old = expr
        expr = expr.beta()
        LOGGER.info('Step %d, beta -> %s' % (step, expr))
        step += 1
    LOGGER.info('Result: %s' % expr)
    return expr


ID = Abs('x', Val('x', 0))


class _ChurchNumerals(object):
    ZERO = Abs('f', ID)
    ONE = Abs('f', Abs('x', App(Val('f', 1), Val('x', 0))))

    def __init__(self):
        self._x = Val('x', 0)
        self._f = Val('f', 1)
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
            return Abs('f', Abs('x', self._cached(item)))

church_numerals = _ChurchNumerals()


__all__ = [
    'Val',
    'Abs',
    'App',
    'parse',
    'try_parse',
    'evaluate',
    'church_numerals',
]
