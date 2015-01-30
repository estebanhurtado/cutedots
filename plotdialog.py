# Copyright 2014 Esteban Hurtado
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
# Cutedots. If not, see &lt;http://opensource.org/licenses/rpl-1.5&gt;.

import os
os.environ['QT_API'] = 'pyside' 
from PySide import QtGui
import matplotlib.pyplot as pl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as PLCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as PLToolbar
import matplotlib as mpl
import modelstate
import analysis
import numpy as np

mpl.rcParams['backend.qt4'] = 'PySide'

class PlotDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(PlotDialog, self).__init__(parent)

        self.figure = pl.figure()
        self.canvas = PLCanvas(self.figure)
        self.toolbar = PLToolbar(self.canvas, self)


        # layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

    def display(self):
        self.canvas.draw()
        self.show()


class DataPlot(PlotDialog):
    def __init__(self, parent=None):
        super(DataPlot, self).__init__(parent)

    def clear(self):
        self.figure.clear()

    def subplot(self, rows=1, cols=1, num=1):
        return self.figure.add_subplot(rows, cols, num)

    def warnIfNoDataLoaded(method):
        "Decorator that throws a warning if no data is already loaded."
        def deco(self, *args, **kargs):
            if self.parent().data is None:
                QtGui.QMessageBox.warning(self.parent(), 'Warning', 'No data loaded yet.')
                return
            method(self, *args, **kargs)
        return deco





