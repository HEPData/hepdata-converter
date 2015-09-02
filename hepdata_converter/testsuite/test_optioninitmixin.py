import unittest
from hepdata_converter.common import OptionInitMixin, Option


class OptionInitMixinTestSuite(unittest.TestCase):
    def test_dir(self):
        class TestClass(OptionInitMixin):
            @classmethod
            def options(cls):
                return {
                'testoption': Option('testoption')
                }

            def __init__(self, *args, **kwargs):
                OptionInitMixin.__init__(self, options=kwargs)

        test_value = 1
        a = TestClass(testoption=test_value)
        self.assertEqual(a.testoption, test_value)
        self.assertIn('testoption', dir(a))

