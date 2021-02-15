import time
from os import path
from pydm import Display
#from qtpy.QtUiTools import QUiLoader
from qtpy.QtWidgets import QCheckBox, QWidget, QVBoxLayout


class compression(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(compression, self).__init__(parent=parent, args=args, macros=macros)
        # Compression board
        self.ui.enabler.stateChanged.connect(self.compression_enabler_change)

    def ui_filename(self):
        # Point to our UI file
        return 'compression.ui'

    def ui_filepath(self):
        # Return the full path to the UI file
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    def compression_enabler_change(self, int):
        displays=[self.ui.PyDMEmbeddedDisplay,self.ui.PyDMEmbeddedDisplay_2, \
                 self.ui.PyDMEmbeddedDisplay_3,self.ui.PyDMEmbeddedDisplay_4]
        if self.ui.enabler.isChecked():
            [x.setEnabled(True) for x in displays]
        else:
            [x.setEnabled(False) for x in displays]
