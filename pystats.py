from analysis import preprocessPosition
from scipy import linalg as la
import numpy as np
import pylab as pl
from plotdialog import PlotDialog
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

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

def screePlot(trajdata, plotDialog, title, transform=None):
    data, names = preprocessPosition(trajdata)
    pca = [fitPca(m, False, transform) for m in data]
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
    ax.set_title(title)
    plotDialog.display()


def speedFunc(samplerate):
    def func(data):
        print("Computing speed")
        return (data[1:,...] - data[:-1,...])*samplerate
    return func

def int3dPlot(trajdata, plotDialog, title, transform=None):
    data, names = preprocessPosition(trajdata)
    pca = [fitPca(m, True, transform) for m in data]
    plotDialog.figure.clear()
    ax = plotDialog.figure.add_subplot(111, projection='3d')
    subj = 1
    for evec, eval, projected in pca:
        ax.plot(projected[:,0], projected[:,1], projected[:,2])
    ax.set_xlabel("First dimension")
    ax.set_ylabel("Second dimension")
    ax.set_zlabel("Third dimension")
    ax.set_title(title)
    plotDialog.display()
