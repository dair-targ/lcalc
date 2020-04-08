# -*- coding: utf-8 -*-
import typing

import logging

from .identifiers import NamespaceIdentifier, RelativeIdentifier, AbsoluteIdentifier
from .context import Namespace
from .model import Def, Abs, Val, App
from .parser import parse_namespace, parse_def


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

    def get_def(self, absolute_identifier: AbsoluteIdentifier) -> Def:
        namespace = self.get_namespace(absolute_identifier.namespace_identifier)
        relative_identifier = absolute_identifier.relative_identifier
        return namespace.get_def(relative_identifier)

    def eval(self, absolute_identifier: AbsoluteIdentifier = AbsoluteIdentifier(NamespaceIdentifier('main'), RelativeIdentifier('main'))):
        expr = self.get_def(absolute_identifier)
        old: typing.Optional[Def] = None
        step = 0
        while expr != old:
            old = expr
            expr = expr.beta(self)
            step += 1
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
