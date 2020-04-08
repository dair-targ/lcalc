import unittest
from .. import lcalc
import logging


logging.basicConfig(level=logging.DEBUG)


class ParserTestCase(unittest.TestCase):
    def test_comment(self):
        expr1 = lcalc.parse_def(u'{}\\{}x{}.{}x{}')
        expr2 = lcalc.parse_def(u'\\x.x')
        self.assertEquals(expr1, expr2)

    def test_parse_alpha_equiv(self):
        expr1 = lcalc.parse_def(u'\\x.x')
        expr2 = lcalc.parse_def(u'\\y.y')
        self.assertEquals(expr1, expr2)

    def test_parse_alpha_equiv2(self):
        expr1 = lcalc.parse_def(u'\\x.\\x.x')
        expr2 = lcalc.parse_def(u'\\x.\\y.y')
        self.assertEquals(expr1, expr2)

    def test_parse_brackets(self):
        expr1 = lcalc.parse_def(u'\\x.x')
        expr2 = lcalc.parse_def(u'\\y.(y)')
        self.assertEquals(expr1, expr2)

    def test_parse_bracketsless_app(self):
        expr2 = lcalc.parse_def(u'\\x.\\y.(x y)')
        expr1 = lcalc.parse_def(u'\\x.\\y.x y')
        self.assertEquals(expr1, expr2)

    def test_parse_bracketsless_app2(self):
        expr1 = lcalc.parse_def(u'\\x.\\y.\\z.x y z')
        expr2 = lcalc.parse_def(u'\\x.\\y.\\z.((x y) z)')
        self.assertEquals(expr1, expr2)

    def test_0(self):
        self.assertEquals(
            lcalc.Abs('x', lcalc.App(lcalc.Abs('z', lcalc.Val('z', 0)), lcalc.Val('x', 0))),
            lcalc.parse_def('λx.(λz.z) x')
        )


class CloneTestCase(unittest.TestCase):
    def test0(self):
        expr = lcalc.parse_def('\\b.b')
        assert expr
        cloned = expr.shift(1)
        self.assertEquals(
            lcalc.Abs('b', lcalc.Val('b', 0)),
            cloned
        )

    def test(self):
        self.assertEquals(
            lcalc.Abs('b', lcalc.App(lcalc.Val('a', 2), lcalc.Val('b', 0))),
            lcalc.Abs('b', lcalc.App(lcalc.Val('a', 1), lcalc.Val('b', 0))).shift(1)
        )

    def test_negative_index_delta(self):
        self.assertEquals(
            lcalc.Abs('b', lcalc.App(lcalc.Val('a', 1), lcalc.Val('b', 0))),
            lcalc.Abs('b', lcalc.App(lcalc.Val('a', 2), lcalc.Val('b', 0))).shift(-1)
        )


class SubstituteTestCase(unittest.TestCase):
    def test_val_val(self):
        self.assertEquals(
            lcalc.Val('z', 42),
            lcalc.Val('x', 42).substitute(lcalc.Val('z', 0))
        )

    def test_val_val_1(self):
        self.assertEquals(
            lcalc.Val('z', 42),
            lcalc.Val('x', 42).substitute(lcalc.Val('z', 24), 24)
        )

    def test3(self):
        self.assertEquals(
            lcalc.parse_def('\\x.x \\z.z').shift(1),
            lcalc.parse_def('\\a.\\x.x a')._body.substitute(lcalc.parse_def('\\z.z'))
        )

    def test4(self):
        self.assertEquals(
            lcalc.parse_def('\\z.z').shift(3),
            lcalc.parse_def('\\a.\\b.\\c.c')._body._body._body.substitute(lcalc.parse_def('\\z.z'))
        )


class BetaTestCase(unittest.TestCase):
    def test(self):
        self.assertEquals(
            lcalc.parse_def('λy.λz.z'),
            lcalc.parse_def('(λx.λy.x) λz.z').beta(lcalc.DictContext())
        )

    def test2(self):
        self.assertEquals(
            lcalc.parse_def('λa.λa.λa.λy.λz.z'),
            lcalc.parse_def('λa.λa.λa.(λx.λy.x) λz.z').beta(lcalc.DictContext())
        )

    def test3(self):
        self.assertEquals(
            lcalc.parse_def('λf.f'),
            lcalc.parse_def('(λn.λf.f) λf.λx.x').beta(lcalc.DictContext())
        )
        self.assertEquals(
            lcalc.parse_def('λf.λx.f'),
            lcalc.parse_def('(λn.λf.λx.f) λf.λx.x').beta(lcalc.DictContext())
        )

    def test_beta_4(self):
        self.assertEquals(
            lcalc.parse_def('λf.(λx.((λx.{<-0}x) {<-0}f) (((λx.{<-0}x) {<-0}f) {<-0}x))'),
            lcalc.parse_def('λf.(λf.λx.{<-1}f ({<-1}f {<-0}x)) ((λx.{<-0}x) {<-0}f)').beta(lcalc.DictContext())
        )


class ProgramTest(unittest.TestCase):
    def test_order_insignificance(self):
        self.assertEquals(
            lcalc.DictContext({'main': '''
        main = (λzero.
        (λsucc.
          succ zero
        ) λn.λf.λx.f (n f x)
        ) λf.λx.x;
        '''}).eval(),
            lcalc.DictContext({'main': '''
        succ = λn.λf.λx.f (n f x);
        zero = λf.λx.x;
        main = succ zero;
        '''}).eval(),
        )

    def test_boolean(self):
        c = lcalc.DictContext({'main': '''
        TRUE = λx.λy.x;
        FALSE = λx.λy.x;
        AND = λp.λq.p q p;
        OR = λp.λq.p p q;
        NOT = λp.p FALSE TRUE;
        IFTHENELSE = λp.λa.λb.p a b;
        
        main = AND TRUE FALSE;
        '''})
        self.assertEqual(
            c.eval(),
            lcalc.parse_def('λx.λy.x')
        )

    def test_numbers(self):
        c = lcalc.DictContext({'main': '''
        1 = λf.λx.f x;
        SUCC = λn.λf.λx.f (n f x);
        main = SUCC 1;
        '''})
        self.assertEqual(
            c.eval(),
            lcalc.parse_def('λf.λx.f (f x)')
        )

    #@unittest.skip('takes 50 seconds to complete')
    def test_recursion(self):
        c = lcalc.DictContext({'main': '''
                0 = λf.λx.x;
                1 = SUCC 0;
                2 = SUCC 1;
                3 = SUCC 2;
                PRED = λn.λf.λx.n (λg.λh.h (g f)) (λu.x) (λu.u);
                SUB = λm.λn.n PRED m;
                SUCC = λn.λf.λx.f (n f x);
                PLUS = λm.λn.m SUCC n;
                MULT = λm.λn.m (PLUS n) 0;
                FALSE = λx.λy.y;
                TRUE = λx.λy.x;
                ISZERO = λn.n (λx.FALSE) TRUE;
                IFTHENELSE = λp.λa.λb.p a b;
                G = λn.IFTHENELSE (ISZERO n) 0 (PLUS n (G (SUB n 1)));

                main = G 3;
                '''})
        self.assertEqual(
            c.eval(),
            lcalc.church_numerals[6]
        )


class NamespaceTestCase(unittest.TestCase):
    def test_parser(self):
        context = lcalc.DictContext(dict(
            lib='''
                succ = λn.λf.λx.f (n f x);
                ''',
            main='''import lib;
            1 = λf.λx.f x;
            main = lib/succ 1;
            ''',
        ))
        self.assertEqual(
            lcalc.church_numerals[2],
            context.eval()
        )
