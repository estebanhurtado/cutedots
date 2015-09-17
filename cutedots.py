#!/usr/bin/env python

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


import traceback
import errors
from PySide import QtGui
from mainwindow import CuteDotsMainWindow
import sys
import mpl_toolkits

def main():
    app = QtGui.QApplication(sys.argv)
    cd = CuteDotsMainWindow()

    def excepthook(extype, exval, tb):
        message = str(exval)
        if isinstance(exval, errors.Warning):
            QtGui.QMessageBox.warning(cd, "Warning", message)
        else:
            ex = traceback.format_exception(extype, exval, tb, 10)
            message = "Unknown error:\n\n" + message + \
                      "\n\n" + "Technical details:\n\n" + ''.join(ex)
            QtGui.QMessageBox.critical(cd, "Error", message)

    sys.excepthook = excepthook

    cd.show()
    sys.exit(app.exec_())    

#import cProfile
#cProfile.run('main()', sort='cumulative')

#from OpenGL.GLUT import glutInit

main()
