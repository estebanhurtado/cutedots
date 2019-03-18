from __future__ import print_function
#from numba import jit
from scipy import linalg as la
import scipy.signal as sig
from numpy.linalg import svd
import numpy as np
import transform
import analysis
import pylab as pl


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

def pcaVarimax(trajdata, transform=None, rotation=varimax):
    data, names = analysis.preprocessPosition(trajdata)
    pca = [fitPcaRotation(m, False, transform, rotation) for m in data]
    out = r'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml/DTD/xhtml-transitional.dtd">'
    out += r'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">'
    out += '<head></head>'
    out += '<body>'
    subject = 1
    for evec, eval in pca:
        out += "<h2>Subject %d</h2>" % subject
        subject += 1
        out += "<h3>Eigenvectors</h3><table><tr><th></th>"
        for i in range(evec.shape[0]):
            out += "<th>Comp %d</th>" % (i+1)
        out += "</tr>"
        for i in range(evec.shape[1]):
            out += "<tr><th>%s</th>" % names[i]
            for j in range(evec.shape[0]):
                w = evec[j,i]
                out += ("<td>%.3f</td>" % w) if w >= 0.3 else "<td></td>"
            out += "</tr>"
        out += "</table>\n<br/><h3>Eigenvalues</h3><table>"
        out += "<tr><th>Component</th><th>Value</th><th>Cum. exp. variance</th></tr>"
        cumvar = 100.0 * np.cumsum(np.array(eval) / np.sum(eval))
        for i in range(len(eval)):
            out += "<tr><th>%d</th><td>%.3f</td><td>%.3f</td></tr>" % ((i+1), eval[i], cumvar[i])
        out += "</table>"
    out += "</body></html>"
    return out

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


def pad(s):
    N = len(s)
    return np.pad(s, (0, N), 'constant', constant_values=(0,0))

def fftCorr(a, b, randomize=False):
#    cb, ca = sig.butter(2, (0.02, 0.1), 'bandpass')
#    a, b = [sig.filtfilt(cb, ca, x, padtype=None) for x in [a, b]]
#    za = ((a - a.mean()) / a.std())
#    zb = ((b - b.mean()) / b.std())
#    if randomize:
 #       zb = np.roll(zb, np.random.randint(1, len(zb)))

    na, nb = [x / np.sum(x) for x in [a,b]]
    c = sig.fftconvolve(nb, na[::-1], 'valid')
#    return c / (sig.triang(len(c)) * (len(za)-1.0))
    return c


def dcFilter(x, n):
    dc = np.correlate(x, np.ones(n,float)/n, 'same')
    return x - dc

def fftCorrPair(a, b, timespan, framerate, randomize=False):
    trim = int(framerate * 2 * timespan + 0.5)
    a = a[trim/2:-trim/2]
    c = fftCorr(a,b,randomize)
    N = len(c)
    mid = int(N/2)
    span = int(framerate * timespan)
    x = c[mid-span:mid+span]
    t = np.arange(-span, span) / framerate
    return x #, t

#@jit
def corrDeviations(da, db, d2a, d2b):
    return np.sum(da*db) / (np.sum(d2a)**0.5 * np.sum(d2b)**0.5)

#@jit
def statCorr(a, b, timespan, framerate, randomize):
    da = a - a.mean()
    db = b - b.mean()
    d2a = da**2
    d2b = db**2
    center = len(a) // 2
    framespan = int(framerate * timespan)
    corr = np.zeros(2 * framespan + 1)
    corr[framespan] = corrDeviations(da, db, d2a, d2b)
    for i in range(1,(framespan+1)):
        corr[framespan+i] = corrDeviations(da[i:], db[:-i], d2a[i:], d2b[:-i])
        corr[framespan-i] = corrDeviations(da[:-i], db[i:], d2a[:-i], d2b[i:])
    return corr


def allCorr(a, b, timespan, framerate, randomize):
    ca = np.hstack(([0], np.cumsum(a)))
    cb = np.hstack(([0], np.cumsum(b)))
    N = len(a)
    M = int(framerate * timespan + 0.5)

    corr = np.zeros(2 * M + 1)
    count = np.zeros(2 * M + 1, int)

    for i in range(0, N - M + 1, 100):
        xa = a[i:i+M]
        sa = ca[i+M] - ca[i]
        for j in range(max(0,i-M), min(N-M, i+M)):
            xb = b[j:j+M]
            sb = cb[i+M] - cb[i]

            idx = M+j-i
            corr[idx] += np.sum(xa * xb) / (sa * sb)
            count[idx] += 1

    return corr / count

def allCorr2(a, b, timespan, framerate, randomize):
    ca = np.hstack(([0], np.cumsum(a)))
    cb = np.hstack(([0], np.cumsum(b)))
    N = len(a)
    M = int(framerate * timespan + 0.5)

    corr = np.zeros(2 * M + 1)
    count = np.zeros(2 * M + 1, int)

    for i in range(N - M + 1):
        xa = a[i:i+M]
        sa = ca[i+M] - ca[i]
        for j in range(max(0,i-M), min(N-M, i+M)):
            xb = b[j:j+M]
            sb = cb[i+M] - cb[i]

            idx = M+j-i
            corr[idx] += np.sum(xa * xb) / (sa * sb)
            count[idx] += 1

    return corr / count

def pcaCorrTrajData(td, timespan, framerate, randomize=False):
    # Low pass filter 
    newTd = td.clone()
    transform.LpFilterTrajData(newTd, 10.0)
    data, names = analysis.preprocessPosition(newTd)
#    pcaMain = [fitPcaRotation(np.transpose(m), True, None)[2][:,0] for m in data][:2]
    e = [sum((x[:, 1:] - x[:, :-1]) ** 2,0) for x in data]
#    speeds = [(x[1:] - x[:-1])*framerate  for x in pcaMain]
#    e = [x**2 for x in speeds]
    c = allCorr(e[0], e[1], timespan, framerate, randomize)
    t = np.linspace(-timespan, timespan, len(c))
    return c, t

#@jit
def windowedSum(x, winsize):
    numwin = len(x) - winsize
    s = np.zeros(numwin)
    s[0] = np.sum(x[:winsize])
    for i in range(1, numwin):
        s[i] = s[i-1] - x[i-1] + x[i-1+winsize]
    return s

#@jit
def windowedCorrPair(x1, x2, window, timespan, framerate, randomize):
    framespan = int(timespan * framerate)
    winsize = int(window * framerate)

    N = len(x1)
    if N < (winsize + 2 * framespan):
        return None

    numwin = N - winsize
    d1 = x1 - x1.mean()
    d2 = x2 - x2.mean()
    sd1 = d1**2
    sd2 = d2**2
    s1 = windowedSum(sd1, winsize) ** 0.5
    s2 = windowedSum(sd2, winsize) ** 0.5

    result = np.zeros(framespan * 2 + 1)
    counts = np.zeros(framespan * 2 + 1, dtype=int)

    for off in range(-framespan, framespan+1):
        off1, off2 = (off, 0) if off >= 0 else (0, -off)
        M = N - winsize - max(off1, off2)
        for i in range(M):
            start1, start2 = off1 + i, off2 + i
            end1, end2 = start1 + winsize, start2 + winsize
            num = np.sum(d1[start1:end1] * d2[start2:end2])
            den = s1[off1] * s2[off2]
            result[off + framespan] += num / den
            counts[off + framespan] += 1

    t = np.linspace(-timespan, timespan, len(result))
    return result[::-1]/counts, t
