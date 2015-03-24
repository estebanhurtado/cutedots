from analysis import preprocessPosition
from scipy import linalg as la
from numpy.linalg import svd
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


def varimax(Phi, gamma = 1.0, q = 20, tol = 1e-6):
    p,k = Phi.shape
    R = np.eye(k)
    d=0
    for i in range(q):
        d_old = d
        Lambda = np.dot(Phi, R)
        u,s,vh = svd(np.dot(Phi.T,np.asarray(Lambda)**3 - (gamma/p) * np.dot(Lambda, np.diag(np.diag(np.dot(Lambda.T,Lambda))))))
        R = np.dot(u,vh)
        d = np.sum(s)
        if d_old!=0 and d/d_old < 1 + tol: break
    return R

def printMat(mat):
    sym = [' ', '.', 'o', 'O', '#']
    for i in range(mat.shape[0]):
        print(i, '\t:', end='')
        for j in range(mat.shape[1]):
            k = int(mat[i,j] * 5 - 0.00000001)
            print(sym[k], end='')
        print('')

def pcaVarimax(trajdata, transform=None):
    data, names = preprocessPosition(trajdata)
    pca = [fitPca(m, False, transform) for m in data]
    evec, eval = pca[0]
    printMat(evec)
    print ("===================")
    printMat(np.dot(evec,varimax(evec)))


def fitPcaRotation(data, project=False, transform=None, rotation=varimax):
    "Variables in different rows"

    result = fitPca(data, project, transform)
    if rotation is None:
        return result
    R = rotation(result[0])
    if project:
        return (np.dot(result[0],R), result[1], np.dot(result[2],R))
    else:
        return (np.dot(result[0],R), result[1])

