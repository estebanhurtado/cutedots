import numpy as np
import pylab as pl
import scipy.signal as sig

randSig = lambda: np.random.randn(10000)
norm = lambda x: (x - x.mean()) / x.std()
corrTime = lambda a, b: np.correlate(a, b, 'same') / len(a)
corrFreq = lambda a,b : sig.fftconvolve(a, b[::-1], 'same') / len(a)


s1 = norm(randSig())
s2 = norm(randSig())

ct = corrTime(s1, s2)
cts = corrTime(s1, s1)

cf = corrFreq(s1, s2)
cfs = corrFreq(s1, s1)

pl.subplot(3,2,1)
pl.plot(ct)
pl.ylim(-.1,.1)
pl.subplot(3,2,2)
pl.plot(cts)
pl.ylim(-.1,.1)
pl.subplot(3,2,3)
pl.plot(cf)
pl.ylim(-.1,.1)
pl.subplot(3,2,4)
pl.plot(cfs)
pl.ylim(-.1,.1)
pl.subplot(3,2,5)
pl.plot(cf - ct)
pl.ylim(-.1,.1)
pl.subplot(3,2,6)
pl.plot(cfs - cts)
pl.ylim(-.1,.1)
pl.show()

