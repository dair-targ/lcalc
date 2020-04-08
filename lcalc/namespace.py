import typing

from .identifiers import RelativeIdentifier, NamespaceIdentifier
from .model import Def


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

    def has_def(self, relative_identifier: RelativeIdentifier) -> bool:
        return relative_identifier in self._exprs

    def get_def(self, relative_identifier: RelativeIdentifier) -> Def:
        if not self.has_def(relative_identifier):
            raise Exception('"%s" is not defined. Defined identifiers are:\n%s' % (
                relative_identifier,
                ''.join(f'  {n}\n' for n in self._exprs),
            ))
        return self._exprs[relative_identifier]

    @property
    def import_statements(self):
        return self._import_statements
