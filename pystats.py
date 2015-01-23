from analysis import preprocessPosition
from scipy import linalg as la
import numpy as np
import pylab as pl
from plotdialog import PlotDialog
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def fitPca(data, project=False):
    "Variables in different rows"

    print (np.shape(data))
    data -= data.mean(axis=0)
    R = np.cov(data, rowvar=0)
    print (np.shape(R))
    eval, evec = la.eigh(R)
    idx = np.argsort(eval)[::-1]
    evec = evec[:,idx]
    eval = eval[idx]
    if project:
        projected = np.dot(evec, eval).T
        return evec, eval, projected
    else:
        return evec, eval


def screePlot(trajdata, plotDialog):
    data, names = preprocessPosition(trajdata)
    pca = [fitPca(m) for m in data]
    plotDialog.figure.clear()
    ax = plotDialog.figure.add_subplot(1,1,1)
    subj = 1
    style = ['ko-', 'k+-', 'kx-', 'k*-', 'k<-', 'k>-', 'k^-', 'kv-']
    for evec, eval in pca:
        ax.plot(eval, style[(subj-1)%len(style)], label="Subj. %d" % subj)
        subj += 1
    ax.legend()
    ax.set_title("Scree plot of marker position")
    ax.set_xlabel("Factor number")
    ax.set_ylabel("Eigenvalue")
    plotDialog.display()


def int3dPlot(trajdata, plotDialog):
    data, names = preprocessPosition(trajdata)
    pca = [fitPca(m, True) for m in data]
    plotDialog.figure.clear()
    ax = plotDialog.figure.add_subplot(111, projection='3d')
    subj = 1
    for evec, eval, projected in pca:
        print(np.shape(projected))
