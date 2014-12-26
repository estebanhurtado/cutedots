from rpy2 import robjects
from rpy2.robjects.numpy2ri import numpy2ri
robjects.numpy2ri.activate()
import numpy as np
from rpy2.interactive import process_revents
import errors

r = robjects.r


class RPlotException(errors.Warning):
    pass

def rProcessEvents():
    process_revents.start()

def rLibrary(name, msg):
    try:
        r("library(rgl)")
    except:
        raise RPlotException(msg)

def scalarSpeed(data):
    return (data[:,1:,:] - data[:,:1,:])


def fitPca(trajdata):
    data = trajdata.toArray()
    s = scalarSpeed(data)
    s = np.sqrt(np.sum(s**2,2))
    robj = numpy2ri(s.T)
    r.assign("f", robj)
    r("f <- as.data.frame(f)")
    r("fit <- princomp(f)")

def pcaScreePlot(trajdata):
    fitPca(trajdata)
    r("plot(fit, type='lines', main='Scree plot for speed PCA')")
    rProcessEvents()

def pcaBiplot(trajdata):
    fitPca(trajdata)
    r("biplot(fit)")

def pca3dPlot(trajdata):
    rLibrary('rgl',
             "Please install  'rgl' library in R in order to " +\
             "enable 3D plotting.")
    fitPca(trajdata)
    r("plot3d(fit$scores[,1:3], col=heat.colors(NROW(f)))")
    rProcessEvents()
