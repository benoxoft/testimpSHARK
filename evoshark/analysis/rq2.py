import os
import csv

import seaborn
import matplotlib.pyplot as plt
import collections
import numpy
from pandas import DataFrame

fieldnames = ['all', 'dev', 'istqb', 'ieee', 'use_mock', 'without_mock_istqb', 'without_mock_ieee', 'mock_cutoff_istqb',
              'mock_cutoff_ieee', 'istqb_dev', 'ieee_dev', 'without_mock_istqb_dev', 'without_mock_ieee_dev',
              'mock_cutoff_istqb_dev', 'mock_cutoff_ieee_dev', 'revision_hash']




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
    }


    revision_hashes = []
    print(f)
    with open(f) as csvfile:
        project = f.split('_')[0]
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        next(reader, None)  # skip the headers
        for row in reader:
            revision_hashes.append(row['revision_hash'])
            for field in results.keys():
                results[field].append(int(row[field]))
            for field in ['all', 'istqb', 'ieee']:
                boxplot_results['type'].append(field)
                boxplot_results['value'].append(int(row[field]))
                boxplot_results['project'].append(project)

        all_considered_states.extend(revision_hashes)

        # matplotlib
        seaborn.set_style("darkgrid")
        fig = plt.figure(figsize=(15, 10), dpi=100)
        ax = plt.subplot(111)

        results = collections.OrderedDict(sorted(results.items()))

        for res_name, values in results.items():
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

        # Put an event on it
        def onpick3(event):
            ind = event.ind
            print('onpick3 scatter:', ind, numpy.take(revision_hashes, ind))

        # matplotlib
        fig.canvas.mpl_connect('pick_event', onpick3)
        plt.show()

# Boxplot
data_frame = DataFrame(data=boxplot_results)
fig = plt.figure(1, figsize=(9, 6))

# Create an axes instance
ax = seaborn.boxplot(x="project", y="value", hue="type", data=data_frame)

# Create the boxplot
plt.show()
