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
# Cutedots. If not, see <http://http://opensource.org/licenses/rpl-1.5>.

from __future__ import print_function
import struct
from numpy import fromstring, reshape, dtype, float32
import numpy as np

def printStruct(s):
    for key, code in s.structList:
        value = s.__dict__[key]
        print( key, ":", value )

# Binary structure for reading file data blocks.
class BinStruct:
    def __init__(self, structList, storageDict=None):
        self.structList = structList
        self.setFmtStr()
        self.storageDict = storageDict
        if storageDict is None:
            self.storageDict = self.__dict__
    def setFmtStr(self):
        self.fmtStr = ""
        for name, type in self.structList:
            self.fmtStr += type
    def parseStr(self, string):
        data = struct.unpack(self.fmtStr, string)
        i = 0
        for name, type in self.structList:
            self.storageDict[name] = data[i]
            i += 1
    def __str__(self):
        s = ""
        for name, type in self.structList:
            s += "%s = %s\n" % (name, str(self.storageDict[name]))
        return s

# Data header structure
class C3dHeader(BinStruct):
    def __init__(self, string):
        structList = [
            ( "firstParamBlock", "B"),
            ( "ADTechTag", "B" ),
            ( "numPoints", "h" ),
            ( "numMeasurements", "h" ),
            ( "firstFrameNum", "H" ),
            ( "lastFrameNum", "H" ),
            ( "maxGap", "h" ),
            ( "scaleFactor", "f" ),
            ( "dataStart", "h" ),
            ( "numSamples", "h" ),
            ( "frameRate", "f" ),
            ( "na", "270s" ),
            ( "lrPresentKey", "h" ),
            ( "lrFirstBlock", "h" ),
            ( "fourCharKey", "h" ),
            ( "numTimeEvents", "h" ),
            ( "na2", "h" ),
            ( "eventTimes", "72s" ),
            ( "eventFlags", "18s" ),
            ( "na3", "h" ),
            ( "eventLabels", "72s" ),
            ( "na", "44s" )
        ]
        BinStruct.__init__(self, structList)
        self.parseStr(string)
    @property
    def numFrames(self):
        return self.lastFrameNum - self.firstFrameNum + 1

class ParamHeader(BinStruct):
    def __init__(self, string):
        structList = [
            ( "reserved1", "B" ),
            ( "reserved2", "B" ),
            ( "numBlocks", "B" ),
            ( "procType", "B" )
        ]
        BinStruct.__init__(self, structList)
        self.parseStr(string)

class GroupDesc(BinStruct):
    def __init__(self, string, storageDict):
        structList = [ ( "descLen", "b" ) ]
        BinStruct.__init__(self, structList, storageDict)
        self.parseStr(string[:1])
        storageDict["desc"] = string[1:1+storageDict["descLen"]]

class ParamData(BinStruct):
    def __init__(self, string, storageDict):
        structList = [
            ( "elemLen", "b" ),
            ( "numDims", "b" )
        ]
        BinStruct.__init__(self, structList, storageDict)
        self.parseStr(string[:2])
        storageDict["dims"] = []
        D = storageDict["numDims"]
        for d in range(D):
            storageDict["dims"].append(struct.unpack("b",string[(2+d):(3+d)])[0])
        # Compute number of elements
        T = 1  # Zero dimensions means scalar ==> one element
        dims = storageDict["dims"]
        for d in range(D):
            T *= dims[d]
        # Compute element type
        elemLen = storageDict["elemLen"]
        if elemLen == 1: type = "b"
        elif elemLen == 2: type = "h"
        elif elemLen == 4: type = "f"
        elif elemLen == -1: type = "s"
        else: type = "None"
        data = "-"
        if type != "None":
            eLen = elemLen
            if eLen < 0:
                eLen = -eLen
            data = struct.unpack("%d"%T+type, string[2+D:2+D+T*eLen])
            if len(data) == 1:
                data = data[0]
        storageDict["data"] = data

class ParamRecord(BinStruct):
    def __init__(self, string):
        structList = [
            ( "nameLen", "b" ),
            ( "groupID", "b" ),
        ]
        BinStruct.__init__(self, structList)
        self.parseStr(string[:2])
        self.name = string[2:2+self.nameLen]
        self.nextRecStart = struct.unpack("h", string[2+self.nameLen:4+self.nameLen])[0]
        if self.isGroup():
            self.groupDescStruct = GroupDesc(string[4+self.nameLen:], self.__dict__)
        else:
            self.paramDataStruct = ParamData(string[4+self.nameLen:], self.__dict__)
    def isGroup(self):
        return self.groupID < 0
    def __str__(self):
        s = ""
        if self.isGroup():
            names = ["nameLen","groupID","name","nextRecStart","descLen","desc"]
        else:
            names = ["nameLen","groupID","name","nextRecStart","elemLen","numDims","dims","data"]
        for name in names:
            s += "%s = %s\n" % (name, str(self.__dict__[name]))
        return s

class P3df:
    structLen = 16
    def __init__(self, string):
        self.x, self.y, self.z, self.camResids = struct.unpack("ffff", string[:16])
    @property
    def isValid(self):
        return self.camResids >= 0.0


class P3di:
    structLen = 8
    def __init__(self, string):
        self.x, self.y, self.z, self.camResids = struct.unpack("hhhh", string[:8])
    @property
    def isValid(self):
        return self.camResids >= 0

class P3dFrame:
    def __init__(self, string, numPoints, pointClass):
        self.points = []
        for i in range(numPoints):
            self.points.append(pointClass(string[i*pointClass.structLen:(i+1)*pointClass.structLen]))

class C3d:
    def __init__(self, filename):
        fin = open(filename, 'rb')
        self.filename = filename
        self.data = None
        self.read(fin)
    @property
    def numFrames(self):
        if self.data is None:
            return 0
        else:
            return np.shape(self.data)[0]
    def read(self, fin):
        # Read header
        data = fin.read(512)
        self.header = C3dHeader(data)
        printStruct(self.header)
        # Read parameter header
        parBlock = self.header.firstParamBlock - 1
        fin.seek(parBlock*512)
        data = fin.read(4)
        self.paramHeader = ParamHeader(data)
        printStruct(self.paramHeader)
        # Read parameter section
        fin.seek(parBlock*512+4)
        data = fin.read(self.paramHeader.numBlocks * 512-4)
        start = 0
        self.paramRecords = []
        while True:
            rec = ParamRecord(data[start:])
            printStruct(rec)
            self.paramRecords.append(rec)
            if rec.nextRecStart == 0:
                break
            start += 2 + rec.nameLen + rec.nextRecStart
        # Organize groups
        self.groups = dict()
        for rec in self.paramRecords:
            if rec.isGroup():
                self.groups[-rec.groupID] = rec.name
        # Make parameter dictionary
        self.paramDict = {}
        for rec in self.paramRecords:
            if not rec.isGroup():
                try:
                    parName = "%s:%s" % (self.groups[rec.groupID], rec.name)
                    self.paramDict[parName] = rec.data
                except:
                    pass
        # Point labels
        self.pointLabels = []

        try:
            print("Names", [x.name for x in self.paramRecords])
            print("Groups", [x.groupID for x in self.paramRecords])
        except:
            pass

        labelsParam = [ x for x in self.paramRecords if x.name.decode() == "LABELS" and self.groups[x.groupID].decode() == "POINT"][0]
        labelLen = labelsParam.dims[0]
        text = labelsParam.data
        for i in range(self.header.numPoints):
            self.pointLabels.append(text.decode()[i*labelLen:(i+1)*labelLen].strip(" "))
        # Read data section
        numFrames = self.header.numFrames
        numPoints = self.header.numPoints
        totalNumbers = numFrames * numPoints * 4
        fin.seek(512 * (self.header.dataStart - 1))
        data = fin.read(totalNumbers * 4)
        numberData = fromstring(data, dtype(float32))
        numFrames = len(numberData) / (numPoints*4)
        numberData = numberData[:(numFrames*numPoints*4)]
        self.data = reshape(numberData, (numFrames,numPoints,4))
    def printParams(self):
        for key,value in self.paramDict.iteritems():
            print(key.ljust(20), "=", value)
        print(self.pointLabels)
    def printParamDetails(self):
        for rec in self.paramRecords:
            print(str(rec))
    def __str__(self):
        s = ""
        s += str(self.header)
        s += str(self.paramHeader)
        return s
