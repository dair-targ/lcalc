import unittest
from .. import lcalc
import logging


logging.basicConfig(level=logging.DEBUG)


class ParserTestCase(unittest.TestCase):
    def test_comment(self):
        expr1 = lcalc.try_parse(u'{}\\{}x{}.{}x{}')
        expr2 = lcalc.try_parse(u'\\x.x')
        self.assertEquals(expr1, expr2)

    def test_parse_alpha_equiv(self):
        expr1 = lcalc.try_parse(u'\\x.x')
        expr2 = lcalc.try_parse(u'\\y.y')
        self.assertEquals(expr1, expr2)

    def test_parse_alpha_equiv2(self):
        expr1 = lcalc.try_parse(u'\\x.\\x.x')
        expr2 = lcalc.try_parse(u'\\x.\\y.y')
        self.assertEquals(expr1, expr2)

    def test_parse_brackets(self):
        expr1 = lcalc.try_parse(u'\\x.x')
        expr2 = lcalc.try_parse(u'\\y.(y)')
        self.assertEquals(expr1, expr2)

    def test_parse_bracketsless_app(self):
        expr2 = lcalc.parse(u'\\x.\\y.(x y)')
        expr1 = lcalc.parse(u'\\x.\\y.x y')
        self.assertEquals(expr1, expr2)

    def test_parse_bracketsless_app2(self):
        expr1 = lcalc.parse(u'\\x.\\y.\\z.x y z')
        expr2 = lcalc.parse(u'\\x.\\y.\\z.((x y) z)')
        self.assertEquals(expr1, expr2)

    def test_0(self):
        self.assertEquals(
            lcalc.Abs('x', lcalc.App(lcalc.Abs('z', lcalc.Val('z', 0)), lcalc.Val('x', 0))),
            lcalc.try_parse('λx.(λz.z) x')
        )


class CloneTestCase(unittest.TestCase):
    def test0(self):
        expr = lcalc.try_parse('\\b.b')
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
            lcalc.try_parse('\\x.x \\z.z').shift(1),
            lcalc.try_parse('\\a.\\x.x a')._body.substitute(lcalc.try_parse('\\z.z'))
        )

    def test4(self):
        self.assertEquals(
            lcalc.try_parse('\\z.z').shift(3),
            lcalc.try_parse('\\a.\\b.\\c.c')._body._body._body.substitute(lcalc.try_parse('\\z.z'))
        )


class BetaTestCase(unittest.TestCase):
    def test(self):
        self.assertEquals(
            lcalc.try_parse('λy.λz.z'),
            lcalc.try_parse('(λx.λy.x) λz.z').beta()
        )

    def test2(self):
        self.assertEquals(
            lcalc.try_parse('λa.λa.λa.λy.λz.z'),
            lcalc.try_parse('λa.λa.λa.(λx.λy.x) λz.z').beta()
        )

    def test3(self):
        self.assertEquals(
            lcalc.try_parse('λf.f'),
            lcalc.try_parse('(λn.λf.f) λf.λx.x').beta()
        )
        self.assertEquals(
            lcalc.try_parse('λf.λx.f'),
            lcalc.try_parse('(λn.λf.λx.f) λf.λx.x').beta()
        )

    def test_beta_4(self):
        self.assertEquals(
            lcalc.try_parse('λf.(λx.((λx.{<-0}x) {<-0}f) (((λx.{<-0}x) {<-0}f) {<-0}x))'),
            lcalc.try_parse('λf.(λf.λx.{<-1}f ({<-1}f {<-0}x)) ((λx.{<-0}x) {<-0}f)').beta()
        )


class EvaluateTestCase(unittest.TestCase):
    def test(self):
        expr = lcalc.evaluate(lcalc.try_parse('{SUCC:=}(λn.λf.λx.f (n f x)) {ZERO:=}(λf.λx.x)'))
        self.assertEquals(
            lcalc.church_numerals[1],
            expr
        )

    def test2(self):
        expr = lcalc.evaluate(lcalc.try_parse('{SUCC:=}(λn.λf.λx.f (n f x)) {ONE:=}(λf.λx.f x)'))
        print(expr)
        self.assertEquals(
            lcalc.try_parse('λf.λx.f (f x)'),
            expr
        )

    def test3(self):
        SUCC_ZERO = lcalc.evaluate(lcalc.try_parse('{SUCC:=}(λn.λf.λx.f (n f x)) {ZERO:=}(λf.λx.x)'))
        SUCC_SUCC_ZERO = lcalc.evaluate(lcalc.try_parse('{SUCC:=}(λn.λf.λx.f (n f x)) {ONE:=}(%s)' % SUCC_ZERO))
        self.assertEquals(
            lcalc.try_parse('λf.λx.f (f x)'),
            SUCC_SUCC_ZERO
        )

    def test4(self):
        SUCC = lcalc.try_parse('λn.λf.λx.f (n f x)')
        self.assertEquals(
            lcalc.church_numerals[1],
            lcalc.evaluate(lcalc.App(SUCC, lcalc.church_numerals[0]))
        )

    def test_plus(self):
        PLUS = lcalc.try_parse('λm.λn.λf.λx.m f (n f x)')
        self.assertEquals(
            lcalc.church_numerals[135],
            lcalc.evaluate(lcalc.App(lcalc.App(PLUS, lcalc.church_numerals[61]), lcalc.church_numerals[74]))
        )

    def test_mult_1_1(self):
        MULT = lcalc.try_parse('λm.λn.λf.m (n f)')
        self.assertEquals(
            lcalc.church_numerals[1],
            lcalc.evaluate(lcalc.App(lcalc.App(MULT, lcalc.church_numerals[1]), lcalc.church_numerals[1]))
        )

    def test_mult_2_1(self):
        MULT = lcalc.try_parse('λm.λn.λf.m (n f)')
        self.assertEquals(
            lcalc.church_numerals[2],
            lcalc.evaluate(lcalc.App(lcalc.App(MULT, lcalc.church_numerals[2]), lcalc.church_numerals[1]))
        )

    def test_mult_2_3(self):
        MULT = lcalc.try_parse('λm.λn.λf.m (n f)')
        self.assertEquals(
            lcalc.church_numerals[6],
            lcalc.evaluate(lcalc.App(lcalc.App(MULT, lcalc.church_numerals[2]), lcalc.church_numerals[3]))
        )

    def test_eval_one(self):
        self.assertEquals(
            lcalc.church_numerals[1],
            lcalc.evaluate(lcalc.church_numerals[1])
        )

    def test_eval_two(self):
        self.assertEquals(
            lcalc.church_numerals[2],
            lcalc.evaluate(lcalc.church_numerals[2])
        )

    def test_pow(self):
        POW = lcalc.try_parse('λb.λe.e b')
        self.assertEquals(
            lcalc.church_numerals[32],
            lcalc.evaluate(lcalc.App(lcalc.App(POW, lcalc.church_numerals[2]), lcalc.church_numerals[5]))
        )


class ChurchEncoding(unittest.TestCase):
    def test(self):
        ZERO = lcalc.Abs('f', lcalc.Abs('x', lcalc.Val('x', 0)))
        SUCC = lcalc.try_parse('λn.λf.λx.f (n f x)')
        x = ZERO
        for t in range(10):
            actual = lcalc.evaluate(lcalc.church_numerals[t])
            expected = lcalc.evaluate(x)
            self.assertEquals(
                expected,
                actual,
                'Error for %d: %s != %s' % (t, expected, actual)
            )
            x = lcalc.evaluate(lcalc.App(SUCC, x))


class ProgramTest(unittest.TestCase):
    def test2(self):
        x = lcalc.try_parse(source='''
        succ = λx.x;
        succ 0
        ''')
        a = lcalc.evaluate(x)
        self.assertEquals(lcalc.evaluate(lcalc.parse('0')), a)

    def test_order_insignificance(self):
        a = lcalc.try_parse(source='''
        (λzero.
        (λsucc.
          succ zero
        ) λn.λf.λx.f (n f x)
        ) λf.λx.x
        ''')

        b = lcalc.try_parse(source='''
        succ = λn.λf.λx.f (n f x);
        zero = λf.λx.x;
        succ zero
        ''')
        self.assertEquals(
            lcalc.evaluate(a),
            lcalc.evaluate(b),
        )

    def test_boolean(self):
        a = lcalc.evaluate(lcalc.parse(source='''
        TRUE = λx.λy.x;
        FALSE = λx.λy.x;
        AND = λp.λq.p q p;
        OR = λp.λq.p p q;
        NOT = λp.p FALSE TRUE;
        IFTHENELSE = λp.λa.λb.p a b;
        
        AND TRUE FALSE
        '''))
        self.assertEqual(
            a,
            lcalc.parse('λx.λy.x')
        )

    def test_numbers(self):
        a = lcalc.evaluate(lcalc.parse(source='''
        SUCC = λn.λf.λx.f (n f x);
        SUCC 1
        '''))
        self.assertEqual(
            a,
            lcalc.evaluate(lcalc.parse('2'))
        )

    @unittest.skip('takes 50 seconds to complete')
    def test_recursion(self):
        a = lcalc.evaluate(lcalc.parse(source='''
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
        
        G 2
        '''))
        self.assertEqual(lcalc.evaluate(lcalc.parse('3')), a)
