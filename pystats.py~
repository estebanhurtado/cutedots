from analysis import preprocessPosition
from scipy import linalg as la
import numpy as np

def fitPca(data, project=False, transform=None):
    "Variables in different rows"

    if not transform is None:
        data = transform(data)
    cdata = data - data.mean(axis=0)
    R = np.cov(cdata, rowvar=0)
    eval, evec = la.eigh(R)
    idx = np.argsort(eval)[::-1]
    evec = evec[:,idx]
    eval = eval[idx]
    if project:
        projected = np.dot(evec.T, cdata.T).T
        return evec, eval, projected
    else:
        return evec, eval

