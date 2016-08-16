import os
import csv

import seaborn
import matplotlib.pyplot as plt
import collections
import numpy
from pandas import DataFrame

# Header of the CSV file
fieldnames = ['all', 'dev', 'istqb', 'ieee', 'use_mock', 'without_mock_istqb', 'without_mock_ieee', 'mock_cutoff_istqb',
              'mock_cutoff_ieee', 'revision_hash']


path_to_data_folder = os.path.join(os.path.dirname(__file__), 'data')

# Get all files
files = [os.path.join(path_to_data_folder, f) for f in os.listdir(path_to_data_folder)
         if os.path.isfile(os.path.join(path_to_data_folder, f)) and
         os.path.join(path_to_data_folder, f).endswith('raw_data.csv')]

# Initialization
boxplot_results = {
        'type': [],
        'value': [],
        'project': []
}

# Plot for each file
for f in files:
    results = {
        'all': [],
        'dev': [],
        'istqb': [],
        'ieee': [],
    }


    revision_hashes = []
    print(f)


    # Open CSV file and load data
    with open(f) as csvfile:
        project = f.split('/')[-1].split('_')[0]
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        next(reader, None)  # skip the headers
        for row in reader:
            revision_hashes.append(row['revision_hash'])
            for field in results.keys():
                results[field].append(int(row[field]))
            for field in ['all', 'dev', 'istqb', 'ieee']:
                boxplot_results['type'].append(field)
                boxplot_results['value'].append(int(row[field]))
                boxplot_results['project'].append(project)


        # Plot commits against dev, istqb, all, and ieee categories
        seaborn.set_style("darkgrid")
        seaborn.set_context("notebook", font_scale=1.5)
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
