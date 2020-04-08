import string
import typing

import parsec

from .identifiers import NamespaceIdentifier, RelativeIdentifier, AbsoluteIdentifier, Identifier
from .model import Def, GlobalRef, LocalRef, Val, Abs, App
from .namespace import Statement, ImportStatement, Namespace


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

    def parens(self, subparser: parsec.Parser):
        @parsec.generate
        def parser():
            yield parsec.string('(')
            val = yield subparser
            yield parsec.string(')')
            return val

        return parser

    def p_val(self, abss) -> parsec.Parser:
        @parsec.generate
        def parser() -> Val:
            identifier = yield parsec.try_choice(self.absolute_identifier(), self.relative_identifier())
            for index, abs in enumerate(abss[::-1]):
                if abs == identifier:
                    return Val(identifier, index)
            else:
                if isinstance(identifier, AbsoluteIdentifier):
                    return GlobalRef(identifier)
                else:
                    return LocalRef(identifier)
        return parser

    def p_abs(self, abss) -> parsec.Parser:
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
