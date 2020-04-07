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
