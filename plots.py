import pylab as pl
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from mpl_toolkits.mplot3d import Axes3D
from pystats import fitPca, fitPcaRotation, fftCorr, fftCorrPair
import analysis
import numpy as np
import scipy.signal as sig

def plotSubjectFunc(pd, func, subplot=True):
    "Makes a plot of a time function by subject"

    data = pd.parent().data
    trajs = analysis.trajsBySubj(data.trajs)
    numSubjs = len(trajs)
    subjNum = 1
    pd.clear()
    if not subplot:
        ax = pd.subplot()

    for subject, trajList in trajs.items():
        f = func(trajList)
        t = np.arange(len(f)) / data.framerate
        if subplot:
            ax = pd.subplot(numSubjs, 1, subjNum)
            ax.set_ylabel("Subject %s" % subject)
            subjNum += 1
            ax.plot(t, f)


def continuity(pd):
    data = pd.parent().data

    # Organize curves by label
    trajectories = dict()
    for traj in data.trajs:
        trajectories.setdefault(traj.name, []).append(traj)
    # Plot
    y = 0
    ticksy = []
    ticksn = []
    pd.clear()
    ax = pd.subplot()
    colors = ['b','r']
    trajectories = list(trajectories.items())

    def key(traj):
        try:
            x = traj[0]
            subj = ord(x[3]) << 24
            side = ord(x[2]) << 16
            part = modelstate.ordbpnum[x[:2]]
            return subj + side + part
        except:
            return traj

    trajectories.sort(key=key)

    for name, trajs in trajectories:
        N = len(trajs)
        y -= max(10, 2*N+2)
        ticksy.append(y)
        ticksn.append("%s (%d)" % (name, len(trajs)))
        i = 0
        for t in trajs:
            t0 = t.beginFrame / data.framerate
            t1 = (t.endFrame-1) / data.framerate
            off = 2*(i-(N/2))
            ax.plot([t0, t1], [y+off, y+off], colors[i%2], linewidth=3)
            i += 1
    ax.set_yticks(ticksy)
    ax.set_yticklabels(ticksn)
    pd.display()


def lengthHistogram(pd):
    data = pd.parent().data
    pd.clear()
    ax = pd.subplot()
    ax.hist([t.numFrames / data.framerate for t in data.trajs])
    ax.set_xlabel('length (secs)')
    pd.display()

def frequencySpectrum(pd, title, transform=None):
    trajdata = pd.parent().data
    pointData = trajdata.asMaskedArray()
    if not transform is None:
        pointData = transform(pointData)
    m = (pointData.mean(0)**2).sum(1)**0.5
    m -= np.mean(m)
    F, freq = mlab.psd(m, NFFT=256, Fs=trajdata.framerate)
    F = 10*np.log10(F)
    pd.clear()
    ax = pd.subplot()
    ax.plot(freq, F)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Log power (dB)")
    ax.set_title(title)
    pd.display()

def positionSpectrum(pd, title):
    return frequencySpectrum(pd, title)

def speedSpectrum(pd, title):
    def transform(pointData):
        return (pointData[:,1:,:] - pointData[:,:-1,:]) * pd.parent().data.framerate
    return frequencySpectrum(pd, title, transform)


def positionSpectrogram(pd):
    trajdata = pd.parent().data
    pd.clear()
    trajs, names = trajdata.posBySubj()
    flat = [np.array(analysis.separateComponents(d)) for d in trajs]
    numCols = len(flat)
    numRows = max([f.shape[1] for f in flat])
    n=1
    for subjdata in flat:
        for i in range(subjdata.shape[1]):
            ax = pd.figure.add_subplot(numRows, numCols, n)
            ax.specgram(subjdata[:,i])
            n += 1
    pd.display()

def energyVsTime(pd):
    plotSubjectFunc(pd, analysis.energy)
    pd.display()

def logEnergyVsTime(pd):
    plotSubjectFunc(pd, analysis.logEnergy)
    pd.display()

def scree(plotDialog, title, transform=None):
    trajdata = plotDialog.parent().data
    data, names = analysis.preprocessPosition(trajdata)
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

def intPca3d(plotDialog, title, transform=None, rotation=None):
    trajdata = plotDialog.parent().data
    data, names = analysis.preprocessPosition(trajdata)
    pca = [fitPcaRotation(m, True, transform, rotation) for m in data]
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

def pcaDistance(plotDialog, title, transform=None, rotation=None):
    trajdata = plotDialog.parent().data
    data, names = analysis.preprocessPosition(trajdata)
    pca = [fitPcaRotation(m, True, transform, rotation) for m in data][:2]
    plotDialog.figure.clear()
    ax = plotDialog.figure.add_subplot(111)
    proj1 = pca[0][2]
    proj2 = pca[1][2]
    distance = ((proj2 - proj1)**2).sum(1)**0.5
    fr = int(trajdata.framerate)
    ksize = fr + int(1-(fr%2))
#    distance = sig.medfilt(distance, [fr + int(1-(fr%2))])
    distance = sig.lfilter(np.ones(ksize)/ksize, [1.0], distance)
    time = np.arange(distance.shape[0]) / float(trajdata.framerate)
    ax.plot(time, distance)
    ax.set_xlabel("Time")
    ax.set_ylabel("PCA distance")
    ax.set_title(title)
    plotDialog.display()

# def pcaCorr(plotDialog, title, transform=None, rotation=None):
#     trajdata = plotDialog.parent().data
#     data, names = analysis.preprocessPosition(trajdata)
#     pca = [fitPcaRotation(m, True, transform, rotation) for m in data][:2]
#     corr = [fftCorr(pca[0][2][:,i], pca[1][2][:,i]) for i in range(pca[0][2].shape[1])]
#     ax = plotDialog.figure.add_subplot(111)
#     for c in corr:
#         N = len(c)
#         mid = int(N/2)
#         span = trajdata.framerate * 3
#         x = c[mid-span:mid+span]
#         t = np.arange(-span, span) / trajdata.framerate
#         ax.plot(t, np.abs(x))
#     ax.set_xlabel("Time (secs.)")
#     ax.set_ylabel("Correlation")
#     ax.set_title(title)
#     plotDialog.display()

    
def pcaCorr(plotDialog, title, transform=None, rotation=None):
    trajdata = plotDialog.parent().data
    data, names = analysis.preprocessPosition(trajdata)
    pca = [fitPcaRotation(m, True, transform, rotation) for m in data][:2]
    corr = [fftCorr(pca[0][2][:,i], pca[1][2][:,i]) for i in range(pca[0][2].shape[1])]
    ax = plotDialog.figure.add_subplot(111)
    c = np.mean(corr,0)
    N = len(c)
    mid = int(N/2)
    span = trajdata.framerate * 10
    x = c[mid-span:mid+span]
    t = np.arange(-span, span) / trajdata.framerate
    ax.plot(t, x)
    ax.set_xlabel("Time (secs.)")
    ax.set_ylabel("Correlation")
    ax.set_title(title)
    plotDialog.display()


def logEnergyCorr(plotDialog):
    trajdata = plotDialog.parent().data
    e1, e2 = analysis.logEnergyPairFromTrajData(trajdata)
    c = fftCorr(e1,e2)
    ax = plotDialog.figure.add_subplot(111)
    N = len(c)
    mid = int(N/2)
    span = trajdata.framerate * 10
    x = c[mid-span:mid+span]
    t = np.arange(-span, span) / trajdata.framerate
    ax.plot(t,x)
    ax.set_xlabel("Time (secs.)")
    ax.set_ylabel("Correlation")
    ax.set_title("Log-energy correlation")
    plotDialog.display()
