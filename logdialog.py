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

from PySide import QtGui, QtCore
import sys

class TextStream(QtCore.QObject):
    textWritten = QtCore.Signal(str)
    def write(self, text):
        self.textWritten.emit(str(text))


class LogDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(LogDialog, self).__init__(parent)
        self.textEdit = QtGui.QTextEdit(self)

        # layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.textEdit)
        self.setLayout(layout)
        self.resize(800, 600)


        self.stdout = sys.stdout
        sys.stdout = TextStream()
        self.connect(sys.stdout, QtCore.SIGNAL('textWritten(QString)'),self.appendText)

    def __del__(self):
        sys.stdout = self.stdout

    def appendText(self, text):
#        sys.stderr.write("Append %s\n" % text)

        cursor = self.textEdit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.textEdit.ensureCursorVisible()
        QtGui.QApplication.instance().processEvents()



