from tests.data.project2.module.module1 import Module1
from .wrong_placed_module import *
from tests.data.project2.tests.data.data_that_imports_other_module import data

import unittest
from re import match

class Module1Test(unittest.TestCase):
    def setUp(self):
        self.data = data

    def test_something(self):
        module1 = Module1()
