from tests.data.project2.module.module6 import Module6
from .wrong_placed_module import *
from tests.data.project2.tests.data.some_data import data

import unittest
from re import match


class Module1Test(unittest.TestCase):
    def setUp(self):
        self.data = data

    def test_something(self):
        module1 = Module1()
