import sys

from modulegraph.modulegraph import ModuleGraph, SourceModule
from mongoengine import DoesNotExist, connect
import os
from evoshark.mongomodel import TestState, File, Commit, Project
from trace import Trace
import unittest
from evoshark.common import get_all_immidiate_folders

connect('unit_integration', host='localhost', port=27017, authentication_source='admin', username='root',
        password='balla1234$')

proj = Project.objects(url="https://github.com/numenta/nupic").get()
commits = Commit.objects(projectId=proj.id).order_by('+revisionHash').only('id', 'revisionHash').all()
#commits = [commit.id for commit in commits]
for commit in commits:
    states = TestState.objects(commit_id=commit.id).count()
    print(commit.revisionHash)
    print(states)
    if states == 0:
        print(commit.revisionHash)
        sys.exit(1)
#test_states = TestState.objects(commit_id__in=commits)
#print(len(test_states))

'''
connect('smartshark_hpc_speed', host='141.5.100.156', port=27017, authentication_source='admin',
                username='root', password='balla1234$')

pip_proj = Project.objects(url="https://github.com/pybuilder/pybuilder").get()
commits = Commit.objects(projectId=pip_proj.id)
commit_ids = [commit.id for commit in commits]
print(len(commits))
states = FileState.objects(commit_id__in=commit_ids).only('commit_id')
state_set = set()

for state in states:
    state_set.add(state.commit_id)

print(len(state_set))

for state in set(commit_ids) - state_set:
    print(state)
'''
'''
if __name__ == '__main__':
    test_loader = nose.loader.TestLoader(workingDir="/home/ftrauts/Arbeit/projects/picard")
    #test_loader.loadTestsFromFile('/home/ftrauts/Arbeit/projects/awesome-aws/tests/test_awesome_cli.py')
    nose.main(plugins=[HelloWorld()], testLoader=test_loader)
'''

'''
sys.path[0] = os.path.split('/home/ftrauts/Arbeit/projects/awesome-aws/tests/test_awesome_cli.py')[0]
suite = unittest.TestSuite()
suite.addTest(AwesomeCliTest("test_nothing"))
runner = unittest.TextTestRunner()
runner.run(suite)
'''
'''

t = Trace(countfuncs=1)
path_for_search = ['/home/ftrauts/Arbeit/projects/output/pip/rev/9d3ad30cd4b13024bb433ff19e2d7721491bc9b0_testrev']
sys.path.append('/home/ftrauts/Arbeit/projects/output/pip/rev/9d3ad30cd4b13024bb433ff19e2d7721491bc9b0_testrev')
for folder in get_all_immidiate_folders('/home/ftrauts/Arbeit/projects/output/pip/rev/9d3ad30cd4b13024bb433ff19e2d7721491bc9b0_testrev'):
    sys.path.append(os.path.join('/home/ftrauts/Arbeit/projects/output/pip/rev/9d3ad30cd4b13024bb433ff19e2d7721491bc9b0_testrev', folder))
    path_for_search.append(os.path.join('/home/ftrauts/Arbeit/projects/output/pip/rev/9d3ad30cd4b13024bb433ff19e2d7721491bc9b0_testrev', folder))

sys.path[0] = os.path.split('/home/ftrauts/Arbeit/projects/output/pip/rev/9d3ad30cd4b13024bb433ff19e2d7721491bc9b0_testrev/tests/test_proxy.py')[0]

graph = ModuleGraph(path_for_search)
graph.run_script('/home/ftrauts/Arbeit/projects/output/pip/rev/9d3ad30cd4b13024bb433ff19e2d7721491bc9b0_testrev/tests/test_proxy.py')
node = graph.findNode('/home/ftrauts/Arbeit/projects/output/pip/rev/9d3ad30cd4b13024bb433ff19e2d7721491bc9b0_testrev/tests/test_proxy.py')

for ref in graph.getReferences(node):
    if isinstance(ref, SourceModule):
        print(ref)
'''
'''
connect('unit_integration', host='localhost', port=27017, authentication_source='admin',
                username='root', password='balla1234$')

cnt = 0
pip_proj = Project.objects(url="https://github.com/pypa/pip").get()
commits = Commit.objects(projectId=pip_proj.id)
commit_ids = [commit.id for commit in commits]
print(len(commits))
states = FileState.objects(commit_id__in=commit_ids).only('commit_id')
state_set = set()

for state in states:
    state_set.add(state.commit_id)

print(len(state_set))
sys.exit(1)
for file_state in FileState.objects():
    proj = Commit.objects(id=file_state.commit_id).get().projectId

    if proj == pip_proj.id:
        cnt += 1

print(cnt)
'''
