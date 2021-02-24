import time
from os import path
from pydm import Display
from pydm.widgets import channel
from qtpy.QtWidgets import QCheckBox, QWidget, QVBoxLayout
from qtpy.QtCore import Signal, Slot, Property, QTimer
import pyqtgraph as pg
import time
from functools import partial
import numpy as np
import meme.names


kact=meme.names.list_pvs('USEG:UNDS:%:KAct')#('BPMS:CLTH:%:X')
taperact=meme.names.list_pvs('USEG:UNDS:%:TaperAct')
#taperact=kact;

class SxrUndulatorSummary(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(SxrUndulatorSummary, self).__init__(parent=parent, args=args, macros=None)
        
#Add graph        
        #self.graphWidget=pg.PlotWidget()
        #self.ui.verticalLayout.addWidget(self.graphWidget,0)  
        self.graphWidget.setBackground('w')
        # Add Axis Labels
        styles = {"color": "k", "font-size": "12x"}
        self.graphWidget.setLabel("left", "K", **styles)
        #self.graphWidget.setLabel("bottom", "Und #", **styles)
#Set und_k_curve X axis. Interleave to make rectangular plot from data.
        cell_frac=3.4/4.4
        cell_starts=np.arange(0,len(kact))
        cell_ends=cell_starts+cell_frac
        self.x=np.zeros(len(kact)*4)
        self.x[0::4]=cell_starts
        self.x[1::4]=cell_starts
        self.x[2::4]=cell_ends
        self.x[3::4]=cell_ends
        self.y=np.zeros(len(self.x))
        pen = pg.mkPen(color='k',width=2)
        self.und_k_curve=self.graphWidget.plot(self.x, self.y,pen=pen)
        #self.und_k_curve.receiveXValue(x)
#Use timer to update graph
        self.timer = QTimer()
        self.timer.setInterval(150)
        self.timer.timeout.connect(self.draw_k)
        self.timer.start()
#K Channels        
        kact_channels =[channel.PyDMChannel(address=x, value_slot=partial(self.new_kact_callback, x)) for x in kact]
        self.kact_values=np.zeros(len(kact))
        taper_channels =[channel.PyDMChannel(address=x, value_slot=partial(self.new_taper_Callback, x)) for x in taperact]
        self.taper_values=np.zeros(len(taper_channels))
        [x.connect() for x in kact_channels] 
        [x.connect() for x in taper_channels]        
#Plot settings              
        self.x_min.returnPressed.connect(self.set_x_range)
        self.x_max.returnPressed.connect(self.set_x_range)
        self.y_min.returnPressed.connect(self.set_y_range)
        self.y_max.returnPressed.connect(self.set_y_range)
        self.graphWidget.disableAutoRange()
        self.custom_range=True
        self.y_range=[4,6]
        self.graphWidget.setXRange(min(self.x),max(self.x), padding=0)
        
    def ui_filename(self):
        # Point to our UI file
        return 'sxr_undulator_summary.ui'

    def ui_filepath(self):
        # Return the full path to the UI file
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())
    
    @Slot(float)
    def new_kact_callback(self,pvname,value):
        idx=kact.index(pvname)
        self.kact_values[idx]=value
        #self.draw_k() #called by timer
        return None
    
    @Slot(float)
    def new_taper_Callback(self,pvname,value):
        idx=taperact.index(pvname)
        self.taper_values[idx]=value
        #self.draw_k() #called by timer
        return None
    
    def draw_k(self):
#Y axis
        zero_pad=np.zeros(len(kact))
        self.y[0::4]=zero_pad
        self.y[1::4]=self.kact_values
        self.y[2::4]=self.kact_values+self.taper_values
        self.y[3::4]=zero_pad
        #self.und_k_curve.receiveYValue(y)
        self.und_k_curve.setData(self.x, self.y)
        self.set_custom_range()
        return None
        
    def set_x_range(self):
        curr_range=self.graphWidget.viewRange()[0]
        self.custom_range=False
        if (len(self.x_min.text())>0):
            try:
                self.graphWidget.setXRange(float(self.x_min.text()),
                                           curr_range[1], padding=0)
            except:
                self.graphWidget.setXRange(min(self.x),max(self.x), padding=0)
        curr_range=self.graphWidget.viewRange()[0]
        if len(self.x_max.text())>0:
            try:
                self.graphWidget.setXRange(curr_range[0],float(self.x_max.text()), padding=0)
            except:
                self.graphWidget.setXRange(min(self.x),max(self.x), padding=0)
    def set_custom_range(self):
        if self.custom_range:
            y_range=np.round(np.array([min(self.kact_values[-6:-2]),
                               max(self.kact_values[-6:-2])+2e-3])*500,
                             )/500
            if any(y_range!=self.y_range):
                self.y_range=y_range
                self.graphWidget.setYRange(y_range[0],y_range[1],
                    padding=0.2)
                
    def set_y_range(self):
        curr_range=self.graphWidget.viewRange()[1]
        self.custom_range=False
        if (len(self.y_min.text())>0):
            try:
                self.y_range=[float(self.y_min.text()),curr_range[1]]
                self.graphWidget.setYRange(self.y_range[0],self.y_range[1], padding=0)
                
            except:
                pass
        else:
            self.custom_range=True
            self.set_custom_range()
        curr_range=self.graphWidget.viewRange()[1]
        if len(self.y_max.text())>0:
            try:
                self.y_range=[curr_range[0],float(self.y_max.text())]
                self.graphWidget.setYRange(self.y_range[0],self.y_range[1],padding=0)
            except:
                pass
        else:
            self.custom_range=True
            self.set_custom_range()