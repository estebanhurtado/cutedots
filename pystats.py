from __future__ import print_function
from analysis import preprocessPosition
from scipy import linalg as la
import scipy.signal as sig
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

def pcaVarimax(trajdata, transform=None, rotation=varimax):
    data, names = preprocessPosition(trajdata)
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
    za = pad((a - a.mean()) / a.std())
    zb = pad((b - b.mean()) / b.std())
    if randomize:
        zb = np.roll(zb, np.random.randint(1, len(zb)))
    c = sig.fftconvolve(za, zb[::-1])
    return c / (sig.triang(len(c)) * (len(za)-1.0))


def fftCorrPair(a, b, timespan, framerate, randomize=False):
    c = fftCorr(a,b,randomize)
    N = len(c)
    mid = int(N/2)
    span = int(framerate * timespan)
    x = c[mid-span:mid+span]
    t = np.arange(-span, span) / framerate
    return x, t

def corrDeviations(da, db):
    return np.corrcoef(da, db)[0,1]

def statCorr(a, b, timespan, framerate, randomize=False):
    da = a - a.mean()
    db = b - b.mean()
    center = len(a) // 2
    framespan = int(framerate * timespan)
    corr = np.zeros(2 * framespan + 1)
    corr[framespan] = corrDeviations(da, db)
    for i in range(1,(framespan+1)):
        corr[framespan+i] = corrDeviations(da[i:], db[:-i])
        corr[framespan-i] = corrDeviations(da[:-i], db[i:])
    return corr

def pcaCorrTrajData(td, timespan, framerate, randomize=False):
    data,names = preprocessPosition(td)
    pca = [fitPcaRotation(m, True, None)[2] for m in data][:2]
    corrFunc = statCorr
    corr = [np.abs(corrFunc(pca[0][:,i], pca[1][:,i], timespan, framerate, randomize)) for i in range(pca[0].shape[1])]
    c = np.mean(corr,0)
    t = np.linspace(-timespan, timespan, len(c))
    return c, t

