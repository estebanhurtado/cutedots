import errors
import numpy as np
from analysis import  preprocessPosition

class RPlotException(errors.Warning):
    pass

try:
    from rpy2 import robjects
    from rpy2.robjects.numpy2ri import numpy2ri
    robjects.numpy2ri.activate()
    from rpy2.interactive import process_revents
    r = robjects.r
    rpyAvailable = True
except:
    rpyAvailable = False
    rpyError = RPlotException("R plots and analysis disabled. Install rpy2 " +\
                              "extension for Python in order to enable.")

def checkRpy(func):
    if not rpyAvailable:
        raise rpyError
    return func

@checkRpy
def rProcessEvents():
    process_revents.start()

@checkRpy
def rLibrary(name, msg):
    try:
        r("library(rgl)")
    except:
        raise RPlotException(msg)

def rotate180(data):
    data[:,:,:2] *= -1

def scalarSpeed(data):
    s = (data[:,1:,:] - data[:,:1,:])
    s = np.sqrt(np.sum(s**2,2))
    return s.T

@checkRpy
def fitPca(trajdata):
    "Appends data as if subject 2 were more observations of subject 1"
    data, names = preprocessPosition(trajdata)
    data = np.vstack((data[0], data[1]))
    robj = numpy2ri(data)
    r.assign("f", robj)
    r("f <- as.data.frame(f)")
    robj = numpy2ri(np.array(names))
    r.assign("nm", robj)
    r("names(f) <- nm")
    r("fit <- princomp(f)")
    r("print(loadings(fit))")

@checkRpy
def fitPca2(trajdata):
    "Makes two separate fits, one for each subject"
    data, names = preprocessPosition(trajdata)

    def speed(d):
        return d[1:,...] - d[:-1,...]

    data = [speed(d) for d in data]
    s1 = numpy2ri(data[0])
    s2 = numpy2ri(data[1])
    r.assign("s1", s1)
    r.assign("s2", s2)
    r("f1 <- as.data.frame(s1)")
    r("f2 <- as.data.frame(s2)")
    robj = numpy2ri(np.array(names))
    r.assign("nm", robj)
    r("names(f1) <- nm")
    r("names(f2) <- nm")
    r("fit1 <- princomp(f1, cor=F)")
    r("fit2 <- princomp(f2, cor=F)")
    r("ccf(fit1$scores[,1], fit2$scores[,1], lag.max=200, type='correlation')")

@checkRpy
def fitPca3(trajdata):
    "Makes a single fit with different subject speeds as different variables"
    data, names = preprocessPosition(trajdata,scalarSpeed, False)
    data = np.hstack((data[0], data[1]))
    robj = numpy2ri(data)
    r.assign("f", robj)
    r("f <- as.data.frame(f)")
    names = [n + s for s in ['1', '2'] for n in names]
    robj = numpy2ri(np.array(names))
    r.assign("nm", robj)
    r("names(f) <- nm")
    r("fit <- princomp(f)")
    r("print(loadings(fit))")

@checkRpy
def pcaScreePlot(trajdata):
    fitPca(trajdata)
    r("plot(fit, type='lines', main='Scree plot for speed PCA')")
    rProcessEvents()

@checkRpy
def pcaBiplot(trajdata):
    fitPca(trajdata)
    r("biplot(fit)")

@checkRpy
def pca3dPlot(trajdata):
    rLibrary('rgl',
             "Please install  'rgl' library in R in order to " +\
             "enable 3D plotting.")
    fitPca2(trajdata)
    r("c1 <- heat.colors(NROW(f1))")
    r("c2 <- cm.colors(NROW(f2))")
    r("scores <- rbind(fit1$scores, fit2$scores)")
    r("plot3d(scores[,1:3], col=c(c1,c2))")
    rProcessEvents()

@checkRpy
def pca3dPlotTogether(trajdata):
    rLibrary('rgl',
             "Please install  'rgl' library in R in order to " +\
             "enable 3D plotting.")
    fitPca(trajdata)
    r("c1 <- heat.colors(NROW(f)/2)")
    r("c2 <- cm.colors(NROW(f)/2)")
    r("scores <- fit$scores")
    r("plot3d(scores[,1:3], col=c(c1,c2))")
    rProcessEvents()

@checkRpy
def pcaDistancePlot(trajdata):
    fitPca2(trajdata)
    r("sco1 <- fit1$scores[,1:3]")
    r("sco2 <- fit2$scores[,1:3]")
    r("dist <- rowSums((sco2 - sco1)**2)**0.5")
    r("plot(dist, type='lines', main='PCA distance vs time')")
    rProcessEvents()

@checkRpy
def pcaLoadings(trajdata):
    fitPca3(trajdata)
