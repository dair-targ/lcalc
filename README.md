# lcalc
[Lambda calculus](https://en.wikipedia.org/wiki/Lambda_calculus) implementation.

Use `lcalc.parse(source:str) -> Def` (or `lcalc.try_parse(source) -> (Def | None)`)
to parse your expression and `lcalc.evaluate(expr:Def) -> Def` to evaluate it. See `lcalc/test/test_lcalc.py` for tests.

Use `python3 setup.py test` to run tests.

This package uses Jet Brains'
[PyCharm legacy type hinting](https://www.jetbrains.com/help/pycharm/2016.1/type-hinting-in-pycharm.html).
However, [PEP-484](https://www.python.org/dev/peps/pep-0484/) is welcome and desired.

I'd like to thank to Acar and Ahmed of Chicago University for
[their lecture](http://ttic.uchicago.edu/~pl/classes/CMSC336-Winter08/lectures/lec5.pdf)
with clear description of how to implement β-reduction in de Brujin indicies.
