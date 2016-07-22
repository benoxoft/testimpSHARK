# Connect to mongodb
from __future__ import print_function

import sys
import timeit
import copy
from bson import ObjectId
from bson.son import SON
from mongoengine import connect, Q
import plotly
from plotly.graph_objs import Scatter, Layout
import os
from evoshark.mongomodel import Project, Commit, File, TestState, FileAction, Result
from datetime import datetime
import csv


import matplotlib.pyplot as plt
from matplotlib.image import AxesImage
import numpy as np
from numpy.random import rand

path_to_plots_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'plots')


def commits_per_day(project):
    pipeline = [
        {'$match': {'projectId': project.id}},
        {
            '$group': {'_id': {
                'year': {'$year': "$committerDate"},
                'month': {'$month': "$committerDate"},
                'day': {'$dayOfMonth': "$committerDate"}
            },
            'count': {'$sum': 1},
            }
        },
        {'$sort': SON([('_id.year', 1), ("_id.month", 1), ("_id.day", 1) ])}
    ]
    commits = list(Commit.objects().aggregate(*pipeline))
    dates = []
    counts = []

    for commit in commits:
        dates.append(datetime(year=commit['_id']['year'], month=commit['_id']['month'], day=commit['_id']['day']))
        counts.append(commit['count'])

    # matplotlib
    fig, ax = plt.subplots()
    ax.plot(dates, counts, marker="o", picker=True)
    plt.show()

    # plotly

    plotly.offline.plot({
        "data": [Scatter(x=dates, y=counts)],
        "layout": Layout(title="Commits per Day")
    }, filename=os.path.join(path_to_plots_dir, project.name+'overview.html'))


def changes_per_commit(commits):
    #commits = Commit.objects(projectId=project.id).order_by('+committerDate').only('id', 'committerDate', 'revisionHash',
    #                                                                               'fileActionIds')
    changes = []
    text = []
    for commit in commits:
        number_of_changes = len(commit.fileActionIds)
        changes.append(number_of_changes)
        text.append(commit.revisionHash)


    def onpick3(event):
        ind = event.ind
        print('onpick3 scatter:', ind, np.take(text, ind), np.take(changes, ind))

    # matplotlib
    fig, ax = plt.subplots()
    col = ax.scatter(list(range(0, len(commits))), changes, picker=True)
    fig.canvas.mpl_connect('pick_event', onpick3)
    plt.show()

def testchanges_per_commit(project, commits):
    #commits = Commit.objects(projectId=project.id).order_by('+committerDate').only('id', 'committerDate', 'revisionHash',
    #                                                                               'fileActionIds')
    changes = []
    text = []
    for commit in commits:
        text.append(commit.revisionHash)

        file_actions = FileAction.objects(id__in=commit.fileActionIds).only('fileId')
        changed_file_ids = [action.fileId for action in file_actions]

        names = []
        for file_id in changed_file_ids:
            file_name = File.objects(id=file_id).only('name').get().name
            if (file_name.startswith('test') or file_name.startswith('tests') or file_name.endswith('test.py') or \
                    file_name.endswith('tests.py')) and file_name.endswith('.py'):
                names.append(file_name)
        changes.append(len(names))

    def onpick3(event):
        ind = event.ind
        print('onpick3 scatter:', ind, np.take(text, ind), np.take(changes, ind))

    # matplotlib
    fig, ax = plt.subplots()
    col = ax.scatter(list(range(0, len(commits))), changes, picker=True)
    fig.canvas.mpl_connect('pick_event', onpick3)
    plt.show()

    plotly.offline.plot({
        "data": [Scatter(x=list(range(0, len(commits))), y=changes)],
        "layout": Layout(title="Test changes per Commit")
    }, filename=os.path.join(path_to_plots_dir, project.name+'test_changes.html'))



def tests_per_commit(commits):
    # for ansible
    #commits = Commit.objects(projectId=proj.id, branches='refs/remotes/origin/HEAD').order_by('+committerDate')\
    #.only('id', 'committerDate', 'revisionHash')
    #commits = Commit.objects(projectId=project.id).order_by('+committerDate').only('id', 'committerDate', 'revisionHash')

    text = []
    tests = []
    for commit in commits:
        commit_id = commit.id
        states = TestState.objects(commit_id=commit_id).count()
        tests.append(states)
        text.append(commit.revisionHash)

    def onpick3(event):
        ind = event.ind
        print('onpick3 scatter:', ind, np.take(text, ind), np.take(tests, ind))

    # matplotlib
    fig, ax = plt.subplots()
    col = ax.scatter(list(range(0, len(commits))), tests, picker=True)
    fig.canvas.mpl_connect('pick_event', onpick3)
    plt.show()

    # plotly
    '''
    plotly.offline.plot({
    "data": [
        Scatter(
            x=commits,
            y=tests,
            mode='markers+lines',
            text=text,
        )
    ],
    "layout": Layout(title="#Tests per commit")
    }, filename=os.path.join(path_to_plots_dir, 'tests.html'))

    print(dependend_modules)
    '''
def get_all_file_ids_where_commit_message_contains_unit_tests(project):
    commits = Commit.objects(Q(message__icontains='unit test') &
                             Q(message__not__icontains='functional') &
                             Q(message__not__icontains='integration') &
                             Q(message__not__icontains='pass') &
                             Q(projectId=project.id)).only('fileActionIds', 'message').all()
    all_file_ids = set([])
    for commit in commits:
        #print(commit.message)
        file_actions = FileAction.objects(id__in=commit.fileActionIds).only('fileId').all()
        file_ids = set([file_action.fileId for file_action in file_actions])
        dep_files_unit = File.objects(Q(id__in=file_ids) & Q(path__not__icontains='__init__.py') &
                                  Q(name__icontains='test') & Q(path__endswith='.py')).only('id', 'path').all()
        #print(', '.join([file.path for file in dep_files_unit]))
        all_file_ids = all_file_ids | set([file.id for file in dep_files_unit])

    return all_file_ids


def get_unit_test_developer_think_are_unit(project):
    unit_by_commit_message = get_all_file_ids_where_commit_message_contains_unit_tests(project)

    dep_files_unit = File.objects(Q(projectId=project.id) &
                                  Q(path__not__contains='__init__.py') &
                                  Q(name__icontains='test') & Q(path__endswith='.py') &
                                  Q(path__icontains='unit')).only('id', 'path').all()
    unit_by_path = set([file.id for file in dep_files_unit])
    return unit_by_commit_message | unit_by_path


def all_dep_have_same_package(all_dependencies, file_dict):
    # Filter the depdendencies in a way, that we only look at dependencies, that do not have __init__.py in it and
    # we also exclude "test"
    paths = [file_dict[dep_id] for dep_id in all_dependencies if file_dict[dep_id].endswith('.py')]
    if not paths:
        return False, ''

    sanitized_paths = []

    # We delete the last part of the path here, as we are only interested in the pacakges
    for path in paths:
        parts = path.split('/')[:-1]
        sanitized_paths.append('/'.join(parts))

    if len(sanitized_paths) == 0:
        return False, ''

    # Sort by the length of the path, so that the longest is in the start
    sorted_paths = sorted(sanitized_paths, key=lambda item: len(item.split('/')), reverse=True)

    # Now we check if all dependencies are from the same package, as we have sorted the paths, we can just take
    # the first one (e.g., "pre_commit/clientlib") and check if all other dependencies have the same package
    # if not: return false
    item = sorted_paths[0]
    for path in sorted_paths:
        if path != item:
            return False, ''

    return True, item

def condense_results_for_plot(condensed_plot, results):
    if condensed_plot:
        best_line_name = ''
        best_line_average = 0
        second_best_line_name = ''
        second_best_line_average = 0

        for result_name, result_list in results.items():
            average = sum(result_list)/float(len(result_list))
            if average > best_line_average and result_name not in ['all', 'dev', 'use_mock']:
                second_best_line_average = best_line_average
                second_best_line_name = best_line_name
                best_line_name = result_name
                best_line_average = average
            elif average > second_best_line_average and result_name not in ['all', 'dev', 'use_mock']:
                second_best_line_name = result_name
                second_best_line_average = average

        new_results = copy.deepcopy(results)
        result_names = ['all', 'dev', 'use_mock', best_line_name, second_best_line_name]
        for result_name, values in new_results.items():
            if result_name not in result_names:
                del results[result_name]

def get_overview_data(proj):
    commits = Commit.objects(projectId=proj.id).order_by('+committerDate').only('id', 'committerDate', 'revisionHash',
                                                                            'message', 'fileActionIds').all()
    commit_ids = [commit.id for commit in commits]
    test_states = TestState.objects(commit_id__in=commit_ids).count()
    file_actions = FileAction.objects(projectId=proj.id).count()
    print('#Commits: %d' % len(commits))
    print('#Test States: %d' % test_states)
    print('#File Actions: %d' % file_actions)
    from_date = Commit.objects(projectId=proj.id).order_by('+committerDate').limit(-1).first().committerDate
    to_date = Commit.objects(projectId=proj.id).order_by('-committerDate').limit(-1).first().committerDate
    print('Lifetime: %s - %s' % (from_date, to_date))

#proj = Project.objects(url="https://github.com/numenta/nupic").get()
#connect('unit_integration', host='localhost', port=27017, authentication_source='admin', username='root',
#        password='balla1234$')

# Measure execution time
start_time = timeit.default_timer()
connect('smartshark_hpc_speed', host='141.5.100.156', port=27017, authentication_source='admin', username='root',
        password='balla1234$')

#proj = Project.objects(url="https://github.com/pypa/pip").get()
#proj = Project.objects(url="https://github.com/donnemartin/awesome-aws").get()
#proj = Project.objects(url="https://github.com/pre-commit/pre-commit").get()
proj = Project.objects(url="https://github.com/numenta/nupic").get()
#proj = Project.objects(url="https://github.com/ansible/ansible").get()
#proj = Project.objects(url="https://github.com/cuckoosandbox/cuckoo").get()
#proj = Project.objects(url="https://github.com/clips/pattern").get()
#proj = Project.objects(url="https://github.com/overviewer/Minecraft-Overviewer").get()
#proj = Project.objects(url="https://github.com/fchollet/keras").get()
#proj = Project.objects(url="https://github.com/fabric/fabric").get()


condensed_plot = False


# For ansible
#commits = Commit.objects(projectId=proj.id, branches='refs/remotes/origin/HEAD').order_by('+committerDate')\
#    .only('id', 'committerDate', 'revisionHash', 'message', 'fileActionIds')

# For cuckoo
#commits = Commit.objects(projectId=proj.id, branches='refs/heads/master').order_by('+committerDate')\
#    .only('id', 'committerDate', 'revisionHash', 'message', 'fileActionIds')

commits = Commit.objects(projectId=proj.id).order_by('+committerDate').only('id', 'committerDate', 'revisionHash',
                                                                            'message', 'fileActionIds')

get_overview_data(proj)

#changes_per_commit(commits)
#commits_per_day(proj)
#testchanges_per_commit(proj, commits)
tests_per_commit(commits)
#sys.exit(1)
#package_depth(None)

#print(get_unit_test_developer_think_are_unit())

file_ids_of_unit_tests = get_unit_test_developer_think_are_unit(proj)
i=0





text = []
results = {
    'all': [],
    'dev': [],
    'strict': [],
    'without_test': [],
    'without_test_const': [],
    'without_test_util': [],
    'without_test_util_const': [],
    'without_special': [],
    'use_mock': [],
    'without_mock': [],
    'mock_strict': [],
    'package': []
}


files_without_init = File.objects(projectId=proj.id, path__not__contains='__init__.py').only('path', 'id').all()
files_without_init_id = set([file.id for file in files_without_init])


files_without_init_and_test = File.objects(Q(projectId=proj.id) & Q(path__not__contains='__init__.py') &
                                           Q(path__not__contains='test')).only('path', 'id').all()
files_without_init_and_test_ids = set([file.id for file in files_without_init_and_test])
files_without_init_and_test_dict = {}
for file in files_without_init_and_test:
    files_without_init_and_test_dict[file.id] = file.path


files_without_init_and_test_and_const = File.objects(Q(projectId=proj.id) & Q(path__not__contains='__init__.py') &
                                                    Q(path__not__contains='test') &
                                                    Q(path__not__contains='const')).only('path', 'id').all()
files_without_init_and_test_and_const_ids = set([file.id for file in files_without_init_and_test_and_const])


files_without_init_and_test_and_util = File.objects(Q(projectId=proj.id) & Q(path__not__contains='__init__.py') &
                                                    Q(path__not__contains='test') &
                                                    Q(path__not__contains='util')).only('path', 'id').all()
files_without_init_and_test_and_util_ids = set([file.id for file in files_without_init_and_test_and_util])


files_without_init_and_test_and_const_and_util = File.objects(Q(projectId=proj.id) &
                                                              Q(path__not__contains='__init__.py') &
                                                              Q(path__not__contains='test') &
                                                              Q(path__not__contains='util') &
                                                              Q(path__not__contains='const')).only('path', 'id').all()
files_without_init_and_test_and_const_and_util_ids = set([file.id for file in files_without_init_and_test_and_const_and_util])
files_without_init_and_test_and_const_and_util_dict = {}
for file in files_without_init_and_test_and_const_and_util:
    files_without_init_and_test_and_const_and_util_dict[file.id] = file.path


files_without_special = File.objects(Q(projectId=proj.id) & Q(path__not__contains='__init__.py') &
                                     Q(path__not__contains='test') & Q(path__not__contains='util') &
                                     Q(path__not__contains='const') & Q(path__not__contains='backwardcomp') &
                                     Q(path__not__contains='log') &
                                     Q(path__not__contains='exception')).only('path', 'id').all()
files_without_special_ids = set([file.id for file in files_without_special])
files_without_special_dict = {}
for file in files_without_special:
    files_without_special_dict[file.id] = file.path

strict_text = []
commit_msg = []
for commit in commits:
    print(commit.id)
    commit_msg.append(commit.message)
    states = TestState.objects(commit_id=commit.id).only('depends_on', 'long_name', 'direct_imp', 'file_id',
                                                         'uses_mock', 'mock_cut_dep', 'mocked_modules').all()
    results['all'].append(len(states))

    all_file_ids = set()

    deps = {}
    dev = 0
    strict = 0
    without_test = 0
    without_test_const = 0
    without_test_util = 0
    without_test_util_const = 0
    without_special = 0
    use_mock = 0
    without_mock = 0
    mock_strict = 0
    package = 0

    file_paths = []
    for state in states:

        all_dependencies = set(state.depends_on + state.direct_imp)

        # unit_tests_strict
        dep_files = all_dependencies & files_without_init_id

        if len(dep_files) == 1:
            file_paths.append(state.long_name)
            strict += 1

        # dev_think_unit
        if state.file_id in file_ids_of_unit_tests:
            dev += 1

        # unit_tests_no_inits_no_tests_in_files
        dep_files = all_dependencies & files_without_init_and_test_ids
        if len(dep_files) == 1:
            without_test += 1

        (have_same_package, package_name) = all_dep_have_same_package(dep_files, files_without_init_and_test_dict)
        if have_same_package:
            package += 1


        dep_files = all_dependencies & files_without_init_and_test_and_const_ids
        if len(dep_files) == 1:
            without_test_const += 1

        dep_files = all_dependencies & files_without_init_and_test_and_util_ids
        if len(dep_files) == 1:
            without_test_util += 1

        dep_files = all_dependencies & files_without_init_and_test_and_const_and_util_ids
        if len(dep_files) == 1:
            without_test_util_const += 1

        dep_files = all_dependencies & files_without_special_ids
        if len(dep_files) == 1:
            without_special += 1

        if state.uses_mock:
            use_mock += 1

        non_mocked_dependencies = set(all_dependencies) - set(state.mocked_modules)
        dep_files = non_mocked_dependencies & files_without_init_and_test_ids
        if len(dep_files) == 1:
            without_mock += 1

        dep_files = set(state.mock_cut_dep) & files_without_init_and_test_ids
        if len(dep_files) == 1:
            mock_strict += 1

    strict_text.append('\n'.join(file_paths))
    results['dev'].append(dev)
    results['strict'].append(strict)
    results['without_test'].append(without_test)
    results['without_test_const'].append(without_test_const)
    results['without_test_util'].append(without_test_util)
    results['without_test_util_const'].append(without_test_util_const)
    results['without_special'].append(without_special)
    results['use_mock'].append(use_mock)
    results['without_mock'].append(without_mock)
    results['mock_strict'].append(mock_strict)
    results['package'].append(package)

elapsed = timeit.default_timer() - start_time
print('Needed %0.5f s' % elapsed)

condense_results_for_plot(condensed_plot, results)




# plotly
# create data for plot
data = []
for res_name, values in results.items():
    plot = Scatter(
            x=list(range(0, len(commits))),
            y=values,
            mode='markers+lines',
            name=res_name
    )

    if res_name == 'strict':
        plot.text = strict_text
    elif res_name == 'all':
        plot.text = commit_msg

    data.append(plot)

plotly.offline.plot(
    {
        "data": data,
        "layout": Layout(title="#Tests per commit", hovermode='closest')
    },
    filename=os.path.join(path_to_plots_dir, proj.name+'_tests.html')
)





