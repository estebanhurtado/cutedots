# Copyright 2012 Esteban Hurtado
#
# This file is part of Cutedots.
#
# Cutedots is distributed under the terms of the Reciprocal Public License 1.5.
#
# Cutedots is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the Reciprocal Public License 1.5 for more details.
#
# You should have received a copy of the Reciprocal Public License along with
# Cutedots. If not, see <http://opensource.org/licenses/rpl-1.5>.

from trajdata import RawFrame, RawData, Traj, TrajData
import h5py
import numpy as np
import traceback
import trajectorization as tz
import modelops as mops
import sys

# C3D
#####

def rawDataFromC3D(c3d, progress):
    numFrames = c3d.numFrames
    print("Num. frames: %d" % numFrames)
    rd = RawData()
    rd.filename = c3d.filename
    rd.frameRate = c3d.header.frameRate

    for i in range(numFrames):
        if i % 1000 == 0:
            progress.setValue( int(100.0*i / numFrames) )
            if progress.wasCanceled():
                return
        try:
            rd.frames.append( RawFrame(c3d.data[i,:,:]) )
        except:
            e = sys.exc_info()[1]
            print('Error appending frame %d of %d' % (i, numFrames))
            print(str(e))
            traceback.print_exc()
            break
    progress.setValue(100)
    return rd

# CSV
#####

def rawDataFromCSV(filename, progress):
    with open(filename) as pointsfile:
        framecount = 100
        rd = RawData()
        rd.filename = filename
        rd.frameRate = 100.0

        for line in pointsfile:
            line_array = line.split(',')
            if (line_array[0] == 'info'):
                if (line_array[1] == 'framecount'):
                    framecount = int(line_array[2])
            if (line_array[0] == 'frame'):
                i = len(rd.frames)
                if i % 1000 == 0:
                    progress.setValue( int(100.0*i / framecount) )
                if progress.wasCanceled():
                    return
                try:
                    rd.frames.append(readFrameFromArray(line_array, i))
                except:
                   print('Error appending frame %d of %d' % (i, framecount))
                   break
        progress.setValue(100)
    
    if (not framecount):
        print ('Error frame count not found!')

    return rd
    
def readFrameFromArray(line, line_number):
    # This won't be used
    frame_id = int(line[1])
    frame_timestamp = float(line[2])
    rigidbody_count = int(line[3])
    counter = 4
    # read rigid bodies
    # for counter in range(rigidbody_count):
    counter = counter + rigidbody_count

    # This will
    frame_scale = 800
    marker_count = int(line[counter])
    if (marker_count == 0):
        print ('Warning, markers not found in the frame')
    data = np.zeros((marker_count, 4), dtype = np.float32)
    counter = counter + 1

    for i in range(marker_count):
        # 5 is the index for x in the first marker, and the other 5 is for the
        # number of variables (x, y, z, id, name) 
        #x
        data[i, 0] = np.float32(line[counter]) * frame_scale
        #y
        data[i, 2] = np.float32(line[counter + 1]) * frame_scale
        #z
        data[i, 1] = np.float32(line[counter + 2]) * -1 * frame_scale
        counter = counter + 5
    # if line_number == 0:
        # print (data)
    rf = RawFrame(data)
    return rf

# CSV 2
#######

def rawDataFromCSV2(filename, progress):
    with open(filename) as pointsfile:
        framecount = 100
        rd = RawData()
        rd.filename = filename
        rd.frameRate = 100.0
        counter = 0

        for line in pointsfile:
            counter = counter + 1
            # Line with the information
            if (counter == 1):
                line_array = line.split(',')
                framecount = int(line_array[11])
            # Line containing a frame
            if (counter > 7):
                line_array = line.split(',')
                i = len(rd.frames)
                if i % 1000 == 0:
                    progress.setValue( int(100.0*i / framecount) )
                if progress.wasCanceled():
                    return
                rd.frames.append(readFrameFromArray2(line_array, i))
        progress.setValue(100)
    
    if (not framecount):
        print ('Error frame count not found!')

    return rd
    
def readFrameFromArray2(line_array, line_number):
    '''
    - line_array is an array that in each cell stores a string float or an empty
     string.
    - points is an int array that stores the indices in line_array that are 
    floats.
    '''
    # This won't be used
    frame_id = int(line_array[0])
    frame_timestamp = float(line_array[1])

    # This will
    marker_count = 0
    points = []
    frame_scale = 800
    start = 2
    # read the indices in the array of the markers present in this frame
    for i in range(start, len(line_array)):
        if (line_array[i] and line_array[i] != "\r\n"):
            points.append(i)
    data = np.zeros((len(points)/3, 4), dtype = np.float32)
    # print ("frame number: " + str(line_number))
    # print ("line_array: " + str(line_array))
    # print ("points: " +  str(points))
    # divided by three because each marker has x, y, z
    # iteration on triples (x, y, z) of every marker
    for i in range(0, len(points), 3):
        # read the next 3 elements
        # if (line_number == 44352):
        # print ("i: " + str(i))
        # print ("line_array[i]: " + line_array[points[i]])
        # print ("marker_count: " + str(marker_count))
        #x
        data[marker_count, 0] = np.float32(line_array[points[i]]) * frame_scale
        #y
        data[marker_count, 2] = np.float32(line_array[points[i + 1]]) * frame_scale
        #z
        data[marker_count, 1] = np.float32(line_array[points[i + 2]]) * -1 * frame_scale
        marker_count = marker_count + 1
    # print ("data: " + str(data))
    rf = RawFrame(data)
    return rf

# HDF5
######

def trajDataFromH5(filename, progress=None):
    """Read data from hdf5 file"""
    td = TrajData()
    td.filename = filename
    source = h5py.File(filename, 'r')
    group = source['trajectories']
    if not 'frame_rate' in group.attrs:
        print("Warning, no framerate specified. Setting to 100 FPS.")
        td.frameRate = 100.0
        td.changed = True
    else:
        td.frameRate = group.attrs['frame_rate']
    if not 'format_version' in group.attrs:
        print("Warning, no format version specified. Save to correct.")
        td.changed = True
    totalTrajs = len(list(group))        # Find number of trajectories
    for dsetName in list(group):
        dset = group[dsetName]
        tr = Traj(int(dset.attrs['begin_frame']), str(dset.attrs['name']))
        if tr.name.startswith("b'") and tr.name.endswith("'"):
            tr.name = tr.name[2:-1]
        tr.pointData = [np.array(p) + np.array([0, 0, 0]) for p in  dset.value.tolist()]
        td.trajs.append(tr)
        if progress is not None:
            progress.setValue( int(100.0*td.numTrajs / totalTrajs) )
    source.close()
    del source
    if progress is not None:
        progress.setValue(100)
    return td

def trajToH5Dataset(h5group, idx, traj):
    shape = (traj.numFrames, 3)
    dset = h5group.create_dataset(
        'traj%d' % idx, shape, 'f', compression='gzip', data=traj.pointData)
    dset.attrs["name"] = traj.name
    dset.attrs["begin_frame"] = traj.beginFrame

def trajDataSaveH5(trajData, progress=None):
    f = h5py.File(trajData.filename, 'w')
    trajgroup = f.create_group('trajectories')
    trajgroup.attrs['format_version'] = 'dots 0'
    trajgroup.attrs['frame_rate'] = trajData.framerate
    idx = 0
    numTrajs = trajData.numTrajs
    for traj in trajData.trajs:
        idx += 1
        trajToH5Dataset(trajgroup, idx, traj)
        if progress is not None:
            progress.setValue( int(100.0 * idx / numTrajs) )
    f.flush()
    f.close()
    del f
    if progress is not None:
        progress.setValue(100)


# Raw to trajectorized data
###########################

def trajDataFromRawData(rdata, progress):
    t = tz.Trajectorizer(rdata, progress)
    t.trajectorize()
    td = TrajData()
    td.frameRate = rdata.frameRate
    td.filename = rdata.filename + '.qtd'
    td.trajs.extend(t.trajs)
    td.rename()
    mops.guessSideAndSubject(td)
    mops.sortTrajs(td)
    return td
