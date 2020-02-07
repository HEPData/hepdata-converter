import abc
import unittest
from hepdata_converter.common import GetConcreteSubclassMixin
from future.utils import with_metaclass


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

        class AAB(with_metaclass(abc.ABCMeta, AB)):
            @abc.abstractmethod
            def abstract(self):
                pass

        self.assertEqual(set([AB, AC]), set(A.get_all_subclasses()))

        self.assertEqual(set([AB, AC, AAB]), set(A.get_all_subclasses(include_abstract=True)))