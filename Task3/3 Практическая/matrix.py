import numpy as np


def create_matrix(arr):
    max_len = len(format(len(arr)+1, "b"))

    bin_indices = [bin(i)[2:].zfill(max_len) for i in range(1, len(arr) + 1)]

    matrix = np.array([list(b) for b in bin_indices])

    return matrix