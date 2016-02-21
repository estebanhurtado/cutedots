import numpy as np
import scipy.stats as st

def average(rows):
    n = rows.shape[0]
    factors = np.ones(n, dtype=float) / n
    for i in range(10):
        scaled = np.multiply(rows, factors.reshape((n,1)))
        avg = np.sum(scaled, 0)
        r = np.array([np.sum(x*avg) for x in rows])
        factors = r / np.sum(r)
    return np.sum(scaled, 0)
