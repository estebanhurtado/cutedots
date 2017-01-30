import sys
sys.path.append('..')
import dotsio as dio
import trajdata
import numpy as np
import scipy.signal as sig
import xcorr
import pylab as pl

gauss = sig.gaussian(200, 20)
#ang = np.linspace(0, 8*np.pi, 200)
#sinu = np.sin(ang) * gauss

def synthTraj(name, size, position, sign, feat=gauss):
    t = trajdata.Traj(0, name)
    data = np.zeros((size, 3))
    end = position + len(feat)
    data[position:end, 0] = sign * feat * 50
#    data[position:-1, 0 ] = 1
    t.pointData = data.tolist()
    return t


def synthesize(t1, t2, sig=1, length=800):
    td = trajdata.TrajData()
    td.trajs.append( synthTraj('UBL1', length, t1, 1) )
    td.trajs.append( synthTraj('UBL2', length, t2, sig) )
    td.filename = 'test.qtd'
    dio.trajDataSaveH5(td)
    curves = xcorr.corrFile('test.qtd', ['UB'], [1.0, 1.0, 1.0], 100)

    x1 = np.array(td.trajs[0].pointData)[:,0]
    x2 = np.array(td.trajs[1].pointData)[:,0]
    pl.figure(figsize=(5,6))
    pl.subplot(3,1,1)
    pl.plot(x1, 'r', linewidth=2)
    pl.ylim(np.min(x1) - np.max(x1)*0.1, np.max(x1) * 1.1)
    pl.ylabel("position of\nparticipant A (mm)")
    pl.xlabel("time (msec)")
    pl.subplot(3,1,2)
    pl.plot(x2, 'b', linewidth=2)
    if sig == 1:
        pl.ylim(np.min(x2) - np.max(x2)*0.1, np.max(x2) * 1.1)
    else:
        pl.ylim(np.min(x2)*1.1, np.max(x2) - np.min(x2)*0.1)
    pl.ylabel("position of\nparticipant B (mm)")
    pl.xlabel("time (msec)")
    pl.subplot(3,1,3)
    curves.plot(10)
    if sig == 1:
        pl.ylim(-0.6, 1.2)
    else:
        pl.ylim(-1.2, 0.6)
    pl.ylabel("cross-correlation\nof speed")
    pl.xlabel("delay (msec)")
    pl.xlim(-200, 200)
    pl.tight_layout()


ext = '.eps'
synthesize(400, 500)
pl.savefig('plotp100p1' + ext)
pl.close()
synthesize(500, 400)
pl.savefig('plotn100p1' + ext)
pl.close()
synthesize(400, 500, -1)
pl.savefig('plotp100n1' + ext)
pl.close()
synthesize(500, 400, -1)
pl.savefig('plotn100n1' + ext)
pl.close()
