import abc
import unittest
from hepdata_converter.common import GetConcreteSubclassMixin


class ParserTestSuite(unittest.TestCase):
    """Test suite for Parser factory class
    """

    def test_get_all_subclasses(self):
        class A(GetConcreteSubclassMixin):
            pass

        class AB(A):
            pass

        class AC(A):
            pass

        class AAB(AB):
            __metaclass__ = abc.ABCMeta
            @abc.abstractmethod
            def abstract(self):
                pass

        self.assertEqual([AB, AC], A.get_all_subclasses())