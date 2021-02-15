import time
from os import path
from pydm import Display
#from qtpy.QtUiTools import QUiLoader
from qtpy.QtWidgets import QCheckBox, QWidget, QVBoxLayout


class read_write_tweak_device(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(read_write_tweak_device, self).__init__(parent=parent, args=args, macros=macros)
        # Compression board
        self.ui.tweakVal.textChanged.connect(self.tweakVal_change)

    def ui_filename(self):
        # Point to our UI file
        return 'read_write_tweak_device.ui'

    def ui_filepath(self):
        # Return the full path to the UI file
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    def tweakVal_change(self, int):
        buttons=[self.ui.tweakDown,self.ui.tweakUp]
        try:
            self.tweakDown.updatePressValue(-1*float(self.ui.tweakVal.text()))
            self.tweakUp.updatePressValue(float(self.ui.tweakVal.text()))
            self.tweakDown.setToolTip('- '+self.ui.tweakVal.text())
            self.tweakUp.setToolTip('+ '+self.ui.tweakVal.text())
        except:
            pass
