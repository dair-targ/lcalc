import unittest
from ..identifiers import AbsoluteIdentifier, NamespaceIdentifier, RelativeIdentifier
from ..model import GlobalRef


class GlobalRefTest(unittest.TestCase):
    def test_str(self):
        namespace_identifier = 'test'
        relative_name = 'test-global-ref'
        global_ref = GlobalRef(AbsoluteIdentifier(
            NamespaceIdentifier(namespace_identifier),
            RelativeIdentifier(relative_name))
        )
        self.assertEquals(
            f'{namespace_identifier}/{relative_name}',
            global_ref.__str__(comment=False)
        )
