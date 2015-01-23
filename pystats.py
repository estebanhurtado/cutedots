from analysis import preprocessPosition
from scipy import linalg as la
import numpy as np
import pylab as pl
from plotdialog import PlotDialog

def fitPca(data):
    "Variables in different rows"

    print (np.shape(data))
    data -= data.mean(axis=0)
    R = np.cov(data, rowvar=0)
    print (np.shape(R))
    eval, evec = la.eigh(R)
    idx = np.argsort(eval)[::-1]
    evec = evec[:,idx]
    eval = eval[idx]
    return evec, eval

def screePlot(trajdata, plotDialog):
    data, names = preprocessPosition(trajdata)
    pca = [fitPca(m) for m in data]
    plotDialog.figure.clear()
    ax = plotDialog.figure.add_subplot(1,1,1)
    subj = 1
    for evec, eval in pca:
        ax.plot(eval, 'o', label="Subj. %d" % subj)
        subj += 1
    ax.legend()
    ax.title("Scree plot of marker position")
    ax.
    plotDialog.display()


