from tests.data.project2.module.module1 import Module1
from tests.data.project2.module.module2 import Module2
from tests.data.project2.tests.data.some_data import data

import unittest


class Module2Test(unittest.TestCase):
    def setUp(self):
        pass

    def test_something(self):
        module1 = Module1()
        module2 = Module2()
