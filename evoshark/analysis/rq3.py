import os
import csv

import seaborn
import matplotlib.pyplot as plt
import collections
import statsmodels.api as sm
import numpy
from pandas import DataFrame
from scipy.misc import factorial
from scipy.optimize import curve_fit
import scipy.stats as stats
fieldnames = ['all', 'dev', 'istqb', 'ieee', 'use_mock', 'without_mock_istqb', 'without_mock_ieee', 'mock_cutoff_istqb',
              'mock_cutoff_ieee', 'istqb_dev', 'ieee_dev', 'without_mock_istqb_dev', 'without_mock_ieee_dev',
              'mock_cutoff_istqb_dev', 'mock_cutoff_ieee_dev', 'revision_hash']


def cohens_d(x, y):
    return (numpy.mean(x) - numpy.mean(y)) / (numpy.sqrt((numpy.std(x) ** 2 + numpy.std(y) ** 2) / 2))

best = []
second_best = []
dev = []
use_mock = []
mock_strict = []
without_mock = []
dev_unit_all = []
dev_unit_dev = []


# To get the complete number of states, we need to get the whole number of states that we are considering
all_considered_states = []

files = [f for f in os.listdir(os.path.join(os.path.dirname(__file__), 'data')) if os.path.isfile(f) and f.endswith('raw_data.csv')]
boxplot_results = {
        'type': [],
        'value': [],
        'project': []
}
for f in files:
    results = {
        'all': [],
        'istqb': [],
        'ieee': [],
        'without_mock_istqb': [],
        'mock_cutoff_istqb': [],
        'without_mock_ieee': [],
        'mock_cutoff_ieee': [],
    }


    revision_hashes = []
    print(f)
    with open(f) as csvfile:
        project = f.split('_')[0]
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        next(reader, None)  # skip the headers
        i = 0
        for row in reader:
            # ignore commits where # unit tests in developer's eyes is 0
            if int(row['use_mock']) > 0:
                revision_hashes.append(row['revision_hash'])
                for field in results.keys():
                    results[field].append(int(row[field]))
                for field in ['all', 'istqb','ieee', 'without_mock_istqb', 'mock_cutoff_istqb', 'without_mock_ieee', 'mock_cutoff_ieee']:
                    boxplot_results['type'].append(field)
                    boxplot_results['value'].append(int(row[field]))
                    boxplot_results['project'].append(project)
                i+=1
        all_considered_states.extend(revision_hashes)

        print(cohens_d(results['ieee'], results['without_mock_ieee']))
        print(cohens_d(results['ieee'], results['mock_cutoff_ieee']))
        print(cohens_d(results['istqb'], results['without_mock_istqb']))
        print(cohens_d(results['istqb'], results['mock_cutoff_istqb']))
        '''
        print(numpy.var(results['ieee']))
        print(numpy.mean(results['ieee']))

        print(stats.wilcoxon(results['ieee'], results['without_mock_ieee']))
        print(stats.wilcoxon(results['ieee'], results['mock_cutoff_ieee']))
        print(stats.wilcoxon(results['istqb'], results['without_mock_istqb']))
        print(stats.wilcoxon(results['istqb'], results['mock_cutoff_istqb']))

        print(stats.normaltest()
        print(stats.normaltest(results['ieee']))
        print(stats.normaltest(results['without_mock_istqb']))
        print(stats.normaltest(results['mock_cutoff_istqb']))
        print(stats.normaltest(results['without_mock_ieee']))
        print(stats.normaltest(results['mock_cutoff_ieee']))
        '''

        # matplotlib
        seaborn.set_style("darkgrid")
        fig = plt.figure(figsize=(15, 10), dpi=100)
        ax = plt.subplot(111)

        results = collections.OrderedDict(sorted(results.items()))

        for res_name, values in results.items():
            if res_name in ['all', 'ieee', 'without_mock_ieee', 'mock_cutoff_ieee']:
                ax.plot(list(range(0, len(next(iter(results.values()))))), values, '-o', label=res_name, picker=True)

        plt.xlim(0)
        plt.xlabel('Commit')
        plt.ylabel('#Tests')

        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.05,
                         box.width, box.height * 0.95])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                  fancybox=True, shadow=True, ncol=5)

        # matplotlib
        plt.show()

        # matplotlib
        seaborn.set_style("darkgrid")
        fig = plt.figure(figsize=(15, 10), dpi=100)
        ax = plt.subplot(111)

        results = collections.OrderedDict(sorted(results.items()))

        for res_name, values in results.items():
            if res_name in ['all', 'istqb', 'without_mock_istqb', 'mock_cutoff_istqb']:
                ax.plot(list(range(0, len(next(iter(results.values()))))), values, '-o', label=res_name, picker=True)

        plt.xlim(0)
        plt.xlabel('Commit')
        plt.ylabel('#Tests')

        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.05,
                         box.width, box.height * 0.95])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),
                  fancybox=True, shadow=True, ncol=5)

        # matplotlib
        plt.show()


# Boxplot
data_frame = DataFrame(data=boxplot_results)
fig = plt.figure(1, figsize=(9, 6))

# Create an axes instance
ax = seaborn.boxplot(x="project", y="value", hue="type", data=data_frame)

# Create the boxplot
plt.show()
