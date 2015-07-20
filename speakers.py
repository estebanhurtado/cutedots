import os
import numpy as np
import dotsio as dio
import analysis as an
import trajdata as td
import copy
import modelops as mops
from fragdata import FragmentData


#2015-07-08 05:00:05 
#TO DO: Factorizar checkLength y crear log de conversiones, incluyendo: nombre de archivo de entrada, archivo de salida, zc_left,zc_right,speaker originales y finales

def makeSegmentation(indir,outdir,min_seconds,min_seconds_speaker,window_width):
    indir = checkDirs(indir)
    outdir = checkDirs(outdir)
    for dirpath, dirnames, filenames in os.walk(indir):
        for fn in filenames:
            if fn.endswith('.qtd'):
                key = dirpath[len(indir):]
                fullfn = os.path.join(dirpath, fn)
                directory = '{}{}{}'.format(outdir,key,os.path.sep)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                td = dio.trajDataFromH5(fullfn, progress=None)
                e1 = movAvgFilter(td,window_width,1)
                e2 = movAvgFilter(td,window_width,2)
                td_aux = td
                findSpeaker(e1,e2,min_seconds,min_seconds_speaker,td_aux,fn,directory)
                

def movAvgFilter(trajData,window_width,subject_id):
    window_vec = np.ones(window_width,'d')
    window_filt = window_vec/window_vec.sum()
    if (subject_id == 2):
        subj = [t for t in trajData.trajs if t.subject == 2]
    else:
        subj = [t for t in trajData.trajs if t.subject == 1]
    e = an.energy(subj, transform=lambda x: x)
    e_filt = np.convolve(window_filt,e,mode='valid')
    return e_filt


def findSpeaker(e1,e2,min_seconds,min_seconds_speaker,trajData,fn,directory):
    zero_crossings = np.where(np.absolute(np.diff(np.sign(e1-e2)))>=2)[0]
    #valid_segments = np.where(np.diff(zero_crossings)>2000)[0]
    spkr_frame1 = np.where(e1[0]-e2[0] > 0,1,2)
    speaker = np.concatenate((spkr_frame1*np.ones(1),np.where(e1[zero_crossings+1]-e2[zero_crossings+1] > 0,1,2)),axis=0)
    zc_left = np.concatenate((np.zeros(1),zero_crossings[:]+1),axis=1)
    zc_right = np.concatenate((zero_crossings[:],len(e1)*np.ones(1)),axis=1)
    min_frames = min_seconds*trajData.framerate
    threshold_speaker = min_seconds_speaker*trajData.framerate
    zc_left_1, zc_right_1, speaker_1 = checkLength(zc_left,zc_right,speaker,min_frames,threshold_speaker,trajData.framerate)
    theSegmentator(zc_left_1,zc_right_1,speaker_1,trajData,fn,directory)    

# TO DO    
def checkLength(zc_left,zc_right,speaker,min_frames,threshold_speaker,framerate):

    fd = FragmentData()
    fd.zc_left = zc_left
    fd.zc_right = zc_right
    fd.speaker = speaker
    fd.framerate = framerate
    fd.getSegmentLength()    

    fd.getConditions(min_frames, threshold_speaker)
    fd.getIdxConditions()

    for k in range(fd.n_idx3,0,-1): # ITERACIÓN PARA INTERVENCIONES
        condition_label = 3
        if (fd.idx_cond3[k-1]-1 in fd.idx_cond3):
            fd.joinNeighbour(fd.idx_cond3,k,condition_label)

        elif (fd.idx_cond3[k-1]-1 in fd.idx_cond2): #and (idx_cond3[k-1] in idx_cond3)):
            fd.joinNeighbour(fd.idx_cond3,k,condition_label)

        elif (fd.idx_cond3[k-1]-1 in fd.idx_cond1):
            fd.joinNeighbour(fd.idx_cond3,k,condition_label)
    
    print(fd.idx_cond3)
    if ((fd.idx_cond3.size != 0) and (fd.idx_cond3[0] in fd.idx_cond3)):
        fd.suicideSpeaker(fd.idx_cond3,1,condition_label,min_frames)

    fd.updateFields(min_frames, threshold_speaker)

    for j in range(fd.n_idx2,0,-1):#ITERACIÓN PARA TURNOS
        
        condition_label = 2

        if ((fd.idx_cond2[j-1]-1 in fd.idx_cond2) and (fd.speaker[fd.idx_cond2[j-1]-1] != fd.speaker[fd.idx_cond2[j-1]])):            
            fd.suicideSpeaker(fd.idx_cond2,j,condition_label,min_frames)
        
        elif ((fd.idx_cond2[j-1]-1 in fd.idx_cond1) and (fd.speaker[fd.idx_cond2[j-1]-1] != fd.speaker[fd.idx_cond2[j-1]])):
            fd.suicideSpeaker(fd.idx_cond2,j,condition_label,min_frames)
       
        elif ((fd.idx_cond2[j-1]-1 in fd.idx_cond2) and (fd.speaker[fd.idx_cond2[j-1]-1] == fd.speaker[fd.idx_cond2[j-1]])):
            fd.joinNeighbour(fd.idx_cond2,j,condition_label)

        elif ((fd.idx_cond2[j-1]-1 in fd.idx_cond1) and (fd.speaker[fd.idx_cond2[j-1]-1] == fd.speaker[fd.idx_cond2[j-1]])):
            fd.joinNeighbour(fd.idx_cond2,j,condition_label)

        elif (fd.idx_cond2[j-1]-1 in fd.idx_cond3):
            fd.killNeighbour(fd.idx_cond3,j,condition_label)
            fd.suicideSpeaker(fd.idx_cond3,j,condition_label,min_frames)

          
    fd.updateFields(min_frames, threshold_speaker)    

    for l in range(fd.n_idx1,0,-1):#ITERACIÓN PARA SEGMENTOS
        condition_label = 1        

        if (fd.idx_cond1[l-1]-1 in fd.idx_cond2): #and (fd.speaker[fd.idx_cond1[l-1]-1] != fd.speaker[fd.idx_cond1[l-1]])): 
            fd.killNeighbour(fd.idx_cond1,l,condition_label)

        elif (fd.idx_cond1[l-1]-1 in fd.idx_cond3): #and (fd.speaker[fd.idx_cond1[l-1]-1] != fd.speaker[fd.idx_cond1[l-1]])): 
            fd.killNeighbour(fd.idx_cond1,l,condition_label)    

    fd.updateFields(min_frames, threshold_speaker) 
    return fd.zc_left, fd.zc_right, fd.speaker
 
   
def theSegmentator(zc_left,zc_right,speaker,trajData,fn,directory):
    i = 0
    for zc in zc_right:
        td_aux2 = copy.deepcopy(trajData) # Creo que hay una forma más inteligente de hacer esto
        td_aux2.cutRight(int(zc_right[i]))
        td_aux2.cutLeft(int(zc_left[i]))                 
        fntemp = '{}_{}{}'.format(fn[:-4], i,'.qtd')
        td_aux2.filename = os.path.join(directory, fntemp)
        if (speaker[i] == 2):
            swapSubjectsAux(td_aux2)
        dio.trajDataSaveH5(td_aux2, progress=None) 
        i += 1


def rotate90DegAux(data):
    trajNum = 0
    numTrajs = data.numTrajs
    for traj in data.trajs:
        for i in range(traj.numFrames):
            x, y, z = traj.pointData[i]
            traj.pointData[i] = -y, x, z
        trajNum += 1
    data.changed = True
    

def swapSubjectsAux(data):
    for traj in data.trajs:
        n = traj.name
        if n[3] == '1':
            traj.name = n[:3] + '2'
        elif n[3] == '2':
            traj.name = n[:3] + '1'
    rotate90DegAux(data)
    rotate90DegAux(data)

def checkDirs(dirname):
    if (dirname[-1] == os.path.sep):
        dir_ok = dirname
    else: 
        dir_ok = '{}{}'.format(dirname,os.path.sep)           
    return dir_ok    

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--infolder')
    parser.add_argument('--outfolder')
    args = parser.parse_args()
    #formato : makeSegmentation(args.infolder, args.outfolder, duracion_minima_archivos, minimo_intervencion_sujeto, ancho_ventana)
    makeSegmentation(args.infolder, args.outfolder, 20, 2, 500)

