import fnmatch
import logging
import sys
import os
import timeit
from modulefinder import ModuleFinder

from modulegraph.modulegraph import ModuleGraph, SourceModule, Package
from mongoengine import connect, DoesNotExist, NotUniqueError
import logging.config
from pymongo.errors import DuplicateKeyError
import re

if sys.version_info < (3, 0):
    from .newmodulefinder.newmodulefinder_python2 import NewModuleFinder, Module
else:
    from .newmodulefinder.newmodulefinder_python35 import NewModuleFinder, Module

from .mongomodel import File, Project, Commit, TestState
from .common import get_all_immidiate_folders, setup_logging


class EvoSHARK(object):

    def __init__(self, output, url, db_database, db_hostname, db_port, db_auth, db_user, db_password, mock_paths):
        """
        Main runner of the mecoshark app

        """
        setup_logging()

        # connect to mongodb
        connect(db_database, host=db_hostname, port=db_port, authentication_source=db_auth,
                username=db_user, password=db_password, connect=False)

        self.url = url
        self.logger = logging.getLogger("evoshark")
        self.project_id = self.get_project_id(url)
        self.mock_paths = mock_paths

        self.regex_for_class_mock_detection = re.compile('\s*(?:@patch\.object|patch\.object)\s*\(\s*([\w\.]*)\s*\,')
        self.regex_for_patch_mock_detection = re.compile("\s*(?:@patch|mock\.patch|patch)\s*\(\s*(?:\'|\")\s*([\w\.]*)")
        self.regex_for_import_detection = re.compile('^from ([\w\.]*) import \(*([\w, \\_]*)')
        self.regex_for_import_detection2 = re.compile('^import ([\w\.]*) as \(*([\w, \\_]*)')


    @staticmethod
    def sanitize_path(path):
        home_folder = os.path.expanduser('~')+"/"

        if path.endswith('/'):
            path = path[:-1]

        return path.replace("~", home_folder)

    @staticmethod
    def sanitize_name(path, input_path):
        return path.replace(input_path+"/", "")

    def get_project_id(self, url):
        """
        Gets the project id for the given url
        :param url: url of the project
        :return: project id (ObjectId)
        """
        # find projectid
        try:
            return Project.objects(url=url).get().id
        except DoesNotExist:
            self.logger.error("Project with the url %s does not exist in the database! Execute vcsSHARK first!" % url)
            sys.exit(1)

    def get_commit_id(self, project_id, revision_hash):
        """
        Gets the commit id for the corresponding projectid and revision
        :param project_id: id of the project
        :param revision_hash: revision hash that is analyzed
        :return: commit id (ObjectId)
        """
        try:
            return Commit.objects(projectId=project_id, revisionHash=revision_hash).get().id
        except DoesNotExist:
            self.logger.error("Commit with project_id %s and revision %s does not exist" % (project_id, revision_hash))
            sys.exit(1)

    def find_stored_files(self, input_path):
        # get all stored files of the project
        stored_files = {}
        for file in File.objects(projectId=self.project_id):
            stored_files[file.path] = file.id

        return stored_files

    def get_all_files_in_current_revision(self, input_path):
        input_files = []
        for root, dirs, files in os.walk(input_path, topdown=True):
            for name in files:
                full_file_path = os.path.join(root, name).replace(input_path, "")

                # Filter out git directory
                if not full_file_path.startswith("/.git/"):
                    input_files.append(full_file_path.lstrip('/'))

        return input_files



    def filter_files_list(self, files):
        starting_with_test = fnmatch.filter(files, 'test*')
        starting_with_Test = fnmatch.filter(files, 'Test*')

        starting_list = fnmatch.filter(starting_with_test+starting_with_Test, '*.py')

        ending_with_test = fnmatch.filter(files, '*test.py')
        ending_with_tests = fnmatch.filter(files, '*tests.py')
        ending_with_Test = fnmatch.filter(files, '*Test.py')

        return starting_list+ending_with_test+ending_with_tests+ending_with_Test

    def process_revision(self, revision, input_path):
        self.logger.info("Processing revision %s" % revision)

        commit_id = self.get_commit_id(self.project_id, revision)
        input_path = self.sanitize_path(input_path)
        stored_files = self.find_stored_files(input_path)
        folders = get_all_immidiate_folders(input_path)
        current_files = self.get_all_files_in_current_revision(input_path)

        path_for_search = [input_path]
        path_for_search.extend(self.mock_paths)

        for folder in folders:
            path_for_search.append(os.path.join(input_path, folder))


        # Measure execution time
        start_time = timeit.default_timer()
        python_version_error = False
        for root, dirs, files in os.walk(input_path):
            for file_name in self.filter_files_list(files):
                test_file = os.path.join(root, file_name)
                path_parts = root.split('/')

                # dont look into folders that have build, external, or bin in their name
                if 'build' in path_parts or 'external' in path_parts or 'bin' in path_parts or \
                                'build_system' in path_parts:
                    continue

                dep_modules = []
                direct_imports = []
                mock_cutoff_dependencies = []
                error = False
                mocked_modules = []
                uses_mock = False

                self.logger.info("Found test %s" % self.sanitize_name(test_file, input_path))
                finder = ModuleFinder(path_for_search)

                new_finder = NewModuleFinder(path_for_search)
                try:
                    dep_modules, direct_imports, uses_mock, mocked_modules = self.get_dep_modules(finder, new_finder,
                                                                                                  test_file,
                                                                                                  input_path, current_files)
                except SyntaxError as e:
                    self.logger.error("Syntax error. Wrong python version?")
                    error = True
                    python_version_error = True
                except ImportError:
                    self.logger.error("Import path too deep for file %s" % file_name)
                    error = True

                if len(mocked_modules) > 0:
                    try:
                        graph = ModuleGraph(path_for_search)
                        mocked_modules_identifier = [mod.__name__ for mod in mocked_modules]
                        mock_cutoff_dependencies = self.get_dependencies_with_mock_cutoff(graph,
                                                                                          test_file,
                                                                                          input_path,
                                                                                          mocked_modules_identifier)
                    except SyntaxError as e:
                        self.logger.error("Syntax error. Wrong python version?")
                        error = True
                        python_version_error = True
                    except ImportError:
                        self.logger.error("Import path too deep for file %s" % file_name)
                        error = True

                self.store_data_in_mongodb(test_file, stored_files, input_path, commit_id,
                                           dep_modules, direct_imports, error, uses_mock, mocked_modules,
                                           mock_cutoff_dependencies)

        elapsed = timeit.default_timer() - start_time
        self.logger.info("Execution time: %0.5f s" % elapsed)

        if python_version_error:
            sys.exit(1)

    def get_dependencies_with_mock_cutoff(self, graph, file, input_path, mocked_modules):
        graph.run_script(file)
        node = graph.findNode(file)
        references = []
        self.get_all_node_references(graph, node, references, mocked_modules, input_path)
        self.logger.debug("Dependencies with mock cutoff: %s" % [ref.identifier for ref in references])
        return references

    def get_all_node_references(self, graph, node, references, mocked_modules, input_path):
        if node is None:
            return

        for ref in graph.getReferences(node):
            if ref not in references and (isinstance(ref, SourceModule) or isinstance(ref, Package)) \
                    and ref.filename.startswith(input_path) and ref.identifier not in mocked_modules:
                references.append(ref)
                self.get_all_node_references(graph, ref, references, mocked_modules, input_path)

    def store_data_in_mongodb(self, file, stored_files, input_path, commit_id, dep_modules, direct_imports, error,
                              uses_mock, mocked_modules, mock_cutoff_dependencies):
        file = self.sanitize_name(file, input_path)

        depends_on = []
        for module in dep_modules:
            depends_on.append(stored_files[self.sanitize_name(module.__file__, input_path)])

        import_direct = []
        for module in direct_imports:
            import_direct.append(stored_files[self.sanitize_name(module.__file__, input_path)])

        new_mocked_modules = []
        for module in mocked_modules:
            new_mocked_modules.append(stored_files[self.sanitize_name(module.__file__, input_path)])

        new_mock_cutoff_dep = []
        for module in mock_cutoff_dependencies:
            new_mock_cutoff_dep.append(stored_files[self.sanitize_name(module.filename, input_path)])

        file_state = TestState(file_id=stored_files[file], commit_id=commit_id, depends_on=depends_on,
                               direct_imp=import_direct, file_type='file', long_name=file, error=error,
                               uses_mock=uses_mock, mocked_modules=new_mocked_modules,
                               mock_cut_dep=new_mock_cutoff_dep)

        try:
            file_state.save()
        except (DuplicateKeyError, NotUniqueError):
            state = TestState.objects(file_id=stored_files[file], commit_id=commit_id, long_name=file)
            # Regardless of the error state of the saved state -> skip if the current execution has thrown an error
            # If the state before is also error, we do not need to change anything, and if it wasnt an error, we do not
            # WANT to change anything.

            if error is False and state.get().error is True:
                state.update_one(depends_on=depends_on, direct_imp=import_direct, error=error, uses_mock=uses_mock,
                                 mocked_modules=new_mocked_modules, mock_cut_dep=new_mock_cutoff_dep)

    def get_dep_modules(self, finder, graph, file, input_path, current_files):
        """
        We make several assumptions:
        1) We exclude the __init__.py of the different packages for calculating if it is a unit test or not

        :param graph:
        :param file:
        :param folders:
        :param tests_path:
        :return:
        """

        direct_imports = self.get_direct_imports(graph, file, input_path)
        direct_imports_files = [mod.__file__ for mod in direct_imports]

        finder.run_script(file)

        modules = []
        uses_mock = False
        mocked_modules = []
        for name, mod in finder.modules.items():
            if 'mock' in name or 'unittest.mock' in name:
                uses_mock = True
                mocked_modules = self.get_what_is_mocked(file, input_path, current_files)

            if mod.__file__ is not None and mod.__file__.startswith(input_path) and mod.__file__ != file \
                    and mod.__file__ not in direct_imports_files:
                modules.append(mod)

        self.logger.debug("The following modules are imported: %s" % ','.join([ref.__name__ for ref in modules]))
        self.logger.debug("Uses mock: %s" % uses_mock)
        self.logger.debug("Mocks modules: %s" % ', '.join([mod.__name__ for mod in mocked_modules]))

        return modules, direct_imports, uses_mock, mocked_modules

    def get_what_is_mocked(self, file, input_path, current_files):
        mocked_modules = set()
        mocked_classes = set()

        with open(file, 'r') as f:
            contents = f.read()
        contents = contents.replace('\n', ' ')

        # Find mocks of the form @patch.objects(ClassName, 'method')
        m = re.findall(self.regex_for_class_mock_detection, contents)
        if m is not None and len(m) > 0:
            for match in m:
                # we can have matches like "@patch.object(decorators.logging, ...)
                if '.' in match:
                    mocked_classes.add(match.split('.')[0])
                mocked_classes.add(match)

        # find mocks of the form @patch('module.module2.method', ...)
        m = re.findall(self.regex_for_patch_mock_detection, contents)
        if m is not None and len(m) > 0:
            for found_module_mock in m:
                mocked_module = self.get_correct_module(found_module_mock, file, input_path, current_files)
                # It can happen, that people mock other libraries like os. But we are only interested in mocks
                # which mock things from the project
                if mocked_module is not None:
                    mocked_modules.add(mocked_module)

        if len(mocked_classes) > 0:
            import_dict = {}
            with open(file, 'r') as f:
                lines = f.readlines()

            # We need to preprocess the file, as we have imports over multiple lines, which are hard to find with regex
            lines = self.preprocess_file_for_import_detection(lines)

            # Create a dictionary: "class: module"
            for line in lines:
                line = line.replace('\\', ' ')
                imports = re.search(self.regex_for_import_detection, line.strip())
                if imports is not None:
                    for found_class in imports.group(2).split(','):
                        import_dict[found_class.strip()] = imports.group(1)

                imports = re.search(self.regex_for_import_detection2, line.strip())
                if imports is not None:
                    for found_class in imports.group(2).split(','):
                        import_dict[found_class.strip()] = imports.group(1)

            # Go through all found mocked classes and check if they are in the import dict, if yes: get the module
            for mocked_class in mocked_classes:
                if mocked_class in import_dict:
                    mocked_module = self.get_correct_module(import_dict[mocked_class]+"."+mocked_class, file, input_path, current_files)
                    if mocked_module is not None:
                        mocked_modules.add(mocked_module)

        return mocked_modules

    def preprocess_file_for_import_detection(self, contents):
        new_contents = []
        for i in range(len(contents)):
            new_line = ""
            line = contents[i]

            if line.startswith('from') or line.startswith('import'):
                new_line += line.strip()+' '
                for next_line in contents[i+1:len(contents)]:
                    if next_line.startswith('from') or next_line.startswith('import'):
                        break
                    elif not next_line.strip():
                        break
                    else:
                        new_line += next_line.strip()+' '
                new_contents.append(new_line)
        return new_contents

    def get_correct_module(self, module_string, file, input_path, current_files):
        parts = module_string.split('.')

        # Filter empty strings from list
        parts = list(filter(None, parts))

        file_dir = os.path.dirname(file)
        file_module = os.path.dirname(self.sanitize_name(file, input_path)).replace('/', '.')

        # If the import is of the form .user or user, we assume that a module, which is in the same package is imported
        if len(parts) == 1:
            folders = get_all_immidiate_folders(file_dir)
            if parts[0] in folders:
                module_identifier = "%s.%s" % (file_module, parts[0])
                module_path = os.path.join(file_dir, parts[0]+'.py')
                return Module(name=module_identifier, file=module_path)

        module = ''
        for i in range(len(parts), 0, -1):
            part_path = os.path.join('/'.join(parts[0:i])+'.py')
            part_path_init = os.path.join('/'.join(parts[0:i]), '__init__.py')

            for item in current_files:
                item_parts = item.split('/')
                part_path_parts = part_path.split('/')
                if item.endswith(part_path) and item_parts[-1] == part_path_parts[-1]:
                    module_identifier = '.'.join(parts[0:i])
                    return Module(name=module_identifier, file=item)

                if item.endswith(part_path_init):
                    module_identifier = '.'.join(parts[0:i])
                    return Module(name=module_identifier, file=item)

    def get_direct_imports(self, graph, file, input_path):
        modules = []
        graph.run_script(file)
        for name, mod in graph.modules.items():
            if mod.__file__ is not None and mod.__file__.startswith(input_path) and mod.__file__ != file:
                modules.append(mod)

        self.logger.debug("Direct imports for module: %s" % ','.join([ref.__name__ for ref in modules]))
        return modules

