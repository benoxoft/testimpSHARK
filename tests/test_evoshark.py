import unittest
import json
import os
from modulefinder import ModuleFinder, Module

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from evoshark.evoshark import EvoSHARK


class EvoSHARKTest(unittest.TestCase):
    @staticmethod
    def prepare_database(url, db, hostname, port, auth, user, password):
        try:
            client = MongoClient('%s:%s' % (hostname, port))
            client[auth].authenticate(user, password)
            client[db].get_collection('project').insert_one({'url': url})
        except DuplicateKeyError:
            pass


    @classmethod
    def setUpClass(cls):
        with open(os.path.dirname(os.path.realpath(__file__))+"/config.json", 'r') as data_file:
            read_config = json.load(data_file)

        output_dir = os.path.realpath(__file__)+read_config['output_dir']

        cls.prepare_database(read_config['url'], read_config['db_database'], read_config['db_hostname'],
                              read_config['db_port'], read_config['db_auth'], read_config['db_user'],
                              read_config['db_password'])

        cls.evo_shark = EvoSHARK(output_dir, read_config['url'], read_config['db_database'],
                                  read_config['db_hostname'], read_config['db_port'], read_config['db_auth'],
                                  read_config['db_user'], read_config['db_password'])
        cls.project1_path = os.path.dirname(os.path.realpath(__file__))+"/../tests/data/project1"
        cls.project2_path = os.path.dirname(os.path.realpath(__file__))+"/../tests/data/project2"

        cls.path_to_main_program_root = os.path.dirname(os.path.realpath(__file__))+"/../"
        cls.path_to_module_of_project2 = os.path.join(cls.project2_path, 'module')

        cls.path_to_tests_of_project_1 = os.path.join(cls.project1_path, 'test')
        cls.path_to_tests_of_project_2 = os.path.join(cls.project2_path, 'tests')

    def test_get_tests_path(self):
        self.assertEqual(self.evo_shark.get_tests_path(self.project1_path), self.path_to_tests_of_project_1)
        self.assertEqual(self.evo_shark.get_tests_path(self.project2_path), self.path_to_tests_of_project_2)

    def test_is_unit_test(self):
        finder = ModuleFinder([self.path_to_main_program_root])
        file = os.path.join(self.path_to_tests_of_project_2, "test_unit.py")

        modules = [
            Module('tests.data.project2', os.path.join(self.project2_path, '__init__.py')),
            Module('tests.data.project2.module', os.path.join(self.path_to_module_of_project2, '__init__.py')),
            Module('tests.data.project2.module.module6', os.path.join(self.path_to_module_of_project2, 'module6.py')),
            Module('tests.data.project2.tests', os.path.join(self.path_to_tests_of_project_2, '__init__.py')),
            Module('tests.data.project2.tests.data', os.path.join(self.path_to_tests_of_project_2, 'data', '__init__.py')),
            Module('tests.data.project2.tests.data.some_data', os.path.join(self.path_to_tests_of_project_2, 'data', 'some_data.py')),
        ]

        result, detected_modules = self.evo_shark.is_unit_test2(finder, file, self.project2_path,
                                                                self.path_to_tests_of_project_2)
        detected_modules.sort(key=lambda x: x.__name__)
        self.assertTrue(result)
        self.assertTrue(self.checkModulesListEqual(modules, detected_modules))

    def checkModulesListEqual(self, mod_list1, mod_list2):
        if len(mod_list1) != len(mod_list2):
            return False

        for i in range(0, len(mod_list1)):
            if mod_list1[i].__name__ != mod_list2[i].__name__ or mod_list1[i].__file__ != mod_list2[i].__file__:
                return False

        return True

    def test_is_unit_test_negative_1(self):
        finder = ModuleFinder([self.path_to_main_program_root])
        file = os.path.join(self.path_to_tests_of_project_2, "test_non_unit.py")

        modules = [
            Module('tests.data.project2', os.path.join(self.project2_path, '__init__.py')),
            Module('tests.data.project2.module', os.path.join(self.path_to_module_of_project2, '__init__.py')),
            Module('tests.data.project2.module.module1', os.path.join(self.path_to_module_of_project2, 'module1.py')),
            Module('tests.data.project2.module.module2', os.path.join(self.path_to_module_of_project2, 'module2.py')),
            Module('tests.data.project2.tests', os.path.join(self.path_to_tests_of_project_2, '__init__.py')),
            Module('tests.data.project2.tests.data', os.path.join(self.path_to_tests_of_project_2,
                                                                  'data', '__init__.py')),
            Module('tests.data.project2.tests.data.some_data', os.path.join(self.path_to_tests_of_project_2, 'data',
                                                                            'some_data.py')),
        ]

        result, detected_modules = self.evo_shark.is_unit_test2(finder, file, self.project2_path,
                                                                self.path_to_tests_of_project_2)

        detected_modules.sort(key=lambda x: x.__name__)
        self.assertFalse(result)
        self.assertTrue(self.checkModulesListEqual(modules, detected_modules))

    def test_is_unit_test_negative_2(self):
        finder = ModuleFinder([self.path_to_main_program_root])
        file = os.path.join(self.path_to_tests_of_project_2, "test_non_unit2.py")

        modules = [
            Module('tests.data.project2', os.path.join(self.project2_path, '__init__.py')),
            Module('tests.data.project2.module', os.path.join(self.path_to_module_of_project2, '__init__.py')),
            Module('tests.data.project2.module.module1', os.path.join(self.path_to_module_of_project2, 'module1.py')),
            Module('tests.data.project2.module.module2', os.path.join(self.path_to_module_of_project2, 'module2.py')),
            Module('tests.data.project2.module.module3', os.path.join(self.path_to_module_of_project2, 'module3.py')),
            Module('tests.data.project2.module.module4', os.path.join(self.path_to_module_of_project2, 'module4.py')),
            Module('tests.data.project2.module.module5', os.path.join(self.path_to_module_of_project2, 'module5.py')),
            Module('tests.data.project2.module.module6', os.path.join(self.path_to_module_of_project2, 'module6.py')),
            Module('tests.data.project2.tests', os.path.join(self.path_to_tests_of_project_2, '__init__.py')),
            Module('tests.data.project2.tests.data', os.path.join(self.path_to_tests_of_project_2, 'data', '__init__.py')),
            Module('tests.data.project2.tests.data.data_that_imports_other_module',
                   os.path.join(self.path_to_tests_of_project_2, 'data', 'data_that_imports_other_module.py')),
        ]

        result, detected_modules = self.evo_shark.is_unit_test2(finder, file, self.project2_path,
                                                                self.path_to_tests_of_project_2)

        detected_modules.sort(key=lambda x: x.__name__)
        self.assertFalse(result)
        self.assertTrue(self.checkModulesListEqual(modules, detected_modules))

    '''
    deprecated

    def test_sanitize_references(self):
        first_node = Node('unittest.loader')
        second_node = MissingModule('tests.data.readme_expected')
        second_node = SourceModule('tests.data.readme_expected2')

        references = [first_node, second_node]
        folders = ['tests', 'module', 'module2', 'some_value']

        sanitized_references = self.evo_shark.sanitize_references(references, folders)

        self.assertEqual(sanitized_references, [SourceModule('tests.data.readme_expected2')])

    def test_is_ref_in_folders(self):
        folders = ['test', 'module', 'module2', 'some_value']
        first_node = Node('unittest.loader')
        second_node = Node('tests.data.readme_expected')
        third_node = Node('test.data.readme_expected')
        missing_module = MissingModule('test.missing.module')

        self.assertFalse(self.evo_shark.is_ref_in_folders(first_node, folders))
        self.assertFalse(self.evo_shark.is_ref_in_folders(second_node, folders))
        self.assertTrue(self.evo_shark.is_ref_in_folders(third_node, folders))
        self.assertTrue(self.evo_shark.is_ref_in_folders(missing_module, folders))

    def test_is_unit_test(self):
        graph = ModuleGraph([self.path_to_main_program_root])
        folders = ['module', 'tests']
        file = os.path.join(self.path_to_tests_of_project_2, "test_unit.py")
        tests_path = self.path_to_tests_of_project_2

        self.assertTrue(self.evo_shark.is_unit_test(graph, file, folders, tests_path))

    def test_is_unit_test_negative_1(self):
        graph = ModuleGraph([self.path_to_main_program_root])
        folders = ['module', 'tests']
        file = os.path.join(self.path_to_tests_of_project_2, "test_non_unit.py")
        tests_path = self.path_to_tests_of_project_2

        self.assertTrue(self.evo_shark.is_unit_test(graph, file, folders, tests_path))

    def test_is_unit_test_negative_2(self):
        graph = ModuleGraph([self.path_to_main_program_root])
        folders = ['module', 'tests']
        file = os.path.join(self.path_to_tests_of_project_2, "test_non_unit2.py")
        tests_path = self.path_to_tests_of_project_2

        self.assertTrue(self.evo_shark.is_unit_test(graph, file, folders, tests_path))

    def test_get_all_node_references(self):
        graph = ModuleGraph([self.path_to_main_program_root])
        node = graph.run_script(os.path.join(self.path_to_module_of_project2, "module3.py"))
        references = []
        self.evo_shark.get_all_node_references(graph, node, references)

        module4 = SourceModule('tests.data.project2.module.module4',
                               os.path.join(self.path_to_module_of_project2, 'module4.py'))
        module5 = SourceModule('tests.data.project2.module.module5',
                               os.path.join(self.path_to_module_of_project2, 'module5.py'))
        module6 = SourceModule('tests.data.project2.module.module6',
                               os.path.join(self.path_to_module_of_project2, 'module6.py'))
        data_package = Package('tests.data.project2.module',
                               os.path.join(self.path_to_module_of_project2, '__init__.py'), [self.path_to_module_of_project2])

        tests_package = Package('tests', os.path.join(self.path_to_main_program_root, 'tests', '__init__.py'),
                                [os.path.join(self.path_to_main_program_root, 'tests')])
        data_namespace = NamespacePackage('tests.data.project2', '-',
                                          [os.path.join(self.path_to_main_program_root, 'tests', 'data', 'project2')])
        data2_namespace = NamespacePackage('tests.data', '-',
                                           [os.path.join(self.path_to_main_program_root, 'tests', 'data')])



        expected_references=[module4, module5, module6, data_package, tests_package, data_namespace, data2_namespace]

        self.assertTrue(self.checkEqual(references, expected_references))


    def checkEqual(self, L1, L2):
        return len(L1) == len(L2) and sorted(L1) == sorted(L2)
    '''


if __name__ == '__main__':
    unittest.main()
