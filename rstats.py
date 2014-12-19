from rpy2 import robjects
import rpy2.robjects.numpy2ri
rpy2.robjects.numpy2ri.activate()
import numpy as np

r = robjects.r


def speed(data):
    return (data[:,1:,:] - data[:,:1,:])

def pca(trajdata):
    data = trajdata.toArray()
    
