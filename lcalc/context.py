import typing
import logging
import pathlib

from .identifiers import NamespaceIdentifier, RelativeIdentifier, AbsoluteIdentifier
from .model import Def
from .parser import Namespace, parse_namespace


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
        return namespace.get_def(absolute_identifier.relative_identifier)

    def eval(self, absolute_identifier: AbsoluteIdentifier):
        expr = self.get_def(absolute_identifier)
        old: typing.Optional[Def] = None
        while expr != old:
            old = expr
            expr: Def = expr.beta(self)
        return expr


class DictContext(Context):
    def __init__(self, sources: typing.Optional[typing.Dict[str, str]]=None):
        super(DictContext, self).__init__({
            NamespaceIdentifier(namespace_name): parse_namespace(namespace_source)
            for namespace_name, namespace_source in sources.items()
        } if sources is not None else {})


class FSContext(Context):
    def __init__(self, namespace_identifier: NamespaceIdentifier, root_path: pathlib.Path = pathlib.Path('.')):
        self._root_path = root_path
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
        path = self._root_path / f'{namespace_identifier._value}.lcalc'
        with open(path.absolute()) as f:
            source = f.read()
            return parse_namespace(source)
