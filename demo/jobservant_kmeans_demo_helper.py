import numpy
import pandas

import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs
from io import StringIO


def get_points_and_labels(**kwargs):
    if kwargs.get('initialize_seed'):
        numpy.random.seed(1337)

    centers = [[-10, -10], [-10, 13], [8, -1]]
    blobs, cluster_labels = make_blobs(n_samples=1000, n_features=2,
                                       centers=centers, cluster_std=5.0)
    return blobs, cluster_labels


def plot_clusters(title, xy_points, labels=None):
    plt.figure()
    plt.title(title)
    xy_points_df = pandas.DataFrame(xy_points, columns=['x', 'y'])

    if labels is None:
        plt.scatter(xy_points_df.x, xy_points_df.y, c="grey")
    else:
        xy_points_df['labels'] = pandas.Series(labels)
        colours = ["red", "blue", "green"]
        clusters = [0, 1, 2]
        for cluster_id in clusters:
            cluster_data = \
                xy_points_df.loc[xy_points_df["labels"] == cluster_id,
                                 ["x", "y"]]
            plt.scatter(cluster_data.x, cluster_data.y,
                        c=colours[cluster_id-1])

    plt.show()


def numpy_to_csv(array):
    csv = ''
    for row in array:
        if type(row).__name__ == 'ndarray':
            csv += ','.join([str(i) for i in row])
        else:
            csv += str(row)
        csv += '\n'
    return csv


def output_to_numpy(out):
    return numpy.genfromtxt(StringIO(out), delimiter=',')
