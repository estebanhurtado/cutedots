import numpy as np

class FragmentData(object):

    def __init__(self):
        self.zc_left = []
        self.zc_right = [] 
        self.segment_length = []
        self.speaker = []
        self.framerate = 100.0
        self.condition1 = []
        self.condition2 = []
        self.condition3 = []
        self.idx_cond1 = []
        self.idx_cond2 = []
        self.idx_cond3 = []
        self.n_idx1 = 0
        self.n_idx2 = 0
        self.n_idx3 = 0


    def getSegmentLength(self):
        self.segment_length = (self.zc_right - self.zc_left)+1


    def joinNeighbour(self,idx_cond,x,condition_label):
        self.zc_right[idx_cond[x-1]-1] = self.zc_right[idx_cond[x-1]]
        self.zc_right[idx_cond[x-1]] = -1
        self.zc_left[idx_cond[x-1]] = 0
        self.speaker[idx_cond[x-1]] = False
        self.selectCondition(idx_cond,x,condition_label)   
 

    def suicideSpeaker(self,idx_cond,x,condition_label,min_frames):
        self.getSegmentLength()
        if (self.segment_length[idx_cond[x-1]] < min_frames):        
            self.zc_right[idx_cond[x-1]] = -1
            self.zc_left[idx_cond[x-1]] = 0
            self.speaker[idx_cond[x-1]] = False
            self.selectCondition(idx_cond,x,condition_label)
                        

    def killNeighbour(self,idx_cond,x,condition_label):
        self.zc_right[idx_cond[x-1]-1] = -1
        self.zc_left[idx_cond[x-1]-1] = 0
        self.speaker[idx_cond[x-1]-1] = False
        self.selectCondition(idx_cond,x,condition_label)
        

    def selectCondition(self,idx_cond,x,condition_label):
        if (condition_label == 3):
            self.condition3[idx_cond[x-1]] = False
        elif (condition_label == 2):
            self.condition2[idx_cond[x-1]] = False
        else:
            self.condition1[idx_cond[x-1]] = False   
 

    def getConditions(self, min_frames, threshold_speaker):
        self.getSegmentLength()
        self.condition1 = (self.segment_length >= min_frames) # SEGMENTOS
        self.condition2 = (self.segment_length >= threshold_speaker) & (self.segment_length < min_frames) # TURNOS
        self.condition3 = (self.segment_length < threshold_speaker) # INTERVENCIONES
      

    def getIdxConditions(self):
        self.idx_cond1 = np.where(self.condition1)[0]
        self.idx_cond2 = np.where(self.condition2)[0]
        self.idx_cond3 = np.where(self.condition3)[0]
        self.n_idx1 = len(self.idx_cond1)
        self.n_idx2 = len(self.idx_cond2)
        self.n_idx3 = len(self.idx_cond3)  

    
    def updateFields(self,min_frames, threshold_speaker):
        self.zc_left = self.zc_left[np.where(self.speaker > 0)]
        self.zc_right = self.zc_right[np.where(self.speaker > 0)]
        self.speaker = self.speaker[np.where(self.speaker > 0)]
        self.segment_length = self.getSegmentLength()
        self.getConditions(min_frames, threshold_speaker)
        self.getIdxConditions()

