import os
import csv

import seaborn
import matplotlib.pyplot as plt
import collections
import scipy
import numpy
from pandas import DataFrame

def calculate_error_mean(dev_list, definition_list):
    # Calculate error over all revisions
    substracted_values = [a_i - b_i for a_i, b_i in zip(dev_list, definition_list)]

    # Add them up
    sum = 0
    for value in substracted_values:
        sum += value

    # Calculate mean
    return sum/float(len(dev_list))

fieldnames = ['all', 'dev', 'istqb', 'ieee', 'use_mock', 'without_mock_istqb', 'without_mock_ieee', 'mock_cutoff_istqb',
              'mock_cutoff_ieee', 'istqb_dev', 'ieee_dev', 'revision_hash']


best = []
second_best = []
dev = []
use_mock = []
mock_strict = []
without_mock = []
dev_unit_all = []
dev_unit_dev = []


path_to_data_folder = os.path.join(os.path.dirname(__file__), 'data')

files = [os.path.join(path_to_data_folder, f) for f in os.listdir(path_to_data_folder)
         if os.path.isfile(os.path.join(path_to_data_folder, f)) and
         os.path.join(path_to_data_folder, f).endswith('raw_data.csv')]

boxplot_results = {
        'Type': [],
        '#Tests': [],
        'Project': []
}

for f in files:
    results = {
        'all': [],
        'dev': [],
        'istqb': [],
        'ieee': [],
        'istqb_dev': [],
        'ieee_dev': [],
    }


    revision_hashes = []
    print(f)

    with open(f) as csvfile:
        print(f)
        project = f.split('/')[-1].split('_')[0]
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        next(reader, None)  # skip the headers
        for row in reader:
            # ignore commits where # unit tests in developer's eyes is 0
            if int(row['dev']) > 0:
                revision_hashes.append(row['revision_hash'])
                for field in results.keys():
                    results[field].append(int(row[field]))
                for field in ['dev', 'istqb_dev', 'ieee_dev']:
                    if field == 'istqb_dev':
                        boxplot_results['Type'].append('istqb')
                    elif field == 'ieee_dev':
                        boxplot_results['Type'].append('ieee')
                    else:
                        boxplot_results['Type'].append(field)

                    boxplot_results['#Tests'].append(int(row[field]))
                    boxplot_results['Project'].append(project)
        print(calculate_error_mean(results['dev'], results['istqb_dev']))
        print(calculate_error_mean(results['dev'], results['ieee_dev']))

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
ax = seaborn.boxplot(x="Project", y="#Tests", hue="Type", data=data_frame)

# Create the boxplot
plt.show()
