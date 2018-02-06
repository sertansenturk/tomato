import Levenshtein
import networkx as nx
from numpy import matrix


class GraphOperations(object):
    _metrics = ['norm_levenshtein']
    """

    """
    @staticmethod
    def norm_levenshtein(str1, str2):
        max_len = float(max([len(str1), len(str2)]))

        try:
            return Levenshtein.distance(str1, str2) / max_len
        except ZeroDivisionError:  # both sections are instrumental
            return 0

    @classmethod
    def get_dist_matrix(cls, stream1, stream2=None, metric='norm_levenshtein'):
        if metric not in cls._metrics:
            raise ValueError("The distance metric can be: {0!s}".
                             format(', '.join(cls._metrics)))
        dist_metric = getattr(GraphOperations, metric)

        if stream2 is None:  # return self distance matrix
            stream2 = stream1

        return matrix([[dist_metric(a, b) for a in stream1] for b in stream2])

    @classmethod
    def get_cliques(cls, dists, sim_thres):
        # convert the similarity threshold to distance threshold
        dist_thres = 1 - sim_thres

        # cliques of similar nodes
        g_similar = nx.from_numpy_matrix(dists <= dist_thres)
        c_similar = nx.find_cliques(g_similar)

        # cliques of exact nodes
        g_exact = nx.from_numpy_matrix(dists <= 0.001)  # inexact matching
        c_exact = nx.find_cliques(g_exact)

        # convert the cliques to list of sets
        c_similar = cls._sort_cliques([set(s) for s in list(c_similar)])
        c_exact = cls._sort_cliques([set(s) for s in list(c_exact)])

        return {'exact': c_exact, 'similar': c_similar}

    @staticmethod
    def _sort_cliques(cliques):
        min_idx = [min(c) for c in cliques]  # get the minimum in each clique

        # sort minimum indices to get the actual sort indices for the clique
        # list
        return GraphOperations.sort_by_idx(cliques, min_idx)

    @staticmethod
    def sort_by_idx(cliques, min_idx):
        sort_key = [i[0] for i in
                    sorted(enumerate(min_idx), key=lambda x: x[1])]
        return [cliques[k] for k in sort_key]
