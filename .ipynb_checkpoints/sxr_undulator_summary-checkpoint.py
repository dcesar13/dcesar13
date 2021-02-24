import time
from os import path
from pydm import Display
from pydm.widgets import channel
#from qtpy.QtUiTools import QUiLoader
from qtpy.QtWidgets import QCheckBox, QWidget, QVBoxLayout
from qtpy.QtCore import Signal, Slot, Property, QTimer
#import epics
import time
import numpy as np
#import h5py as h5py


class xleap_dashboard(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(xleap_dashboard, self).__init__(parent=parent, args=args, macros=None)

        self.specSumCurve=self.ui.PyDMTimePlot.addYChannel(y_channel=None, name='Sum spec', color='#000', lineStyle=1, lineWidth=1, symbol=None, symbolSize=None)
        self.specRmsCurve=self.ui.PyDMTimePlot.addYChannel(y_channel=None, name='FWHM spec', color='#f59042', lineStyle=0, lineWidth=1, symbol=1, symbolSize=1)
        
        #epics.camonitor('TMO:VLS:CAM:01:IMAGE2:ArrayData',callback=sumSpecCallback)
        #mypv=epics.PV('BPMS:UNDS:4090:X')
        #mypv.add_callback(self.sumSpecCallback)
        mypv = channel.PyDMChannel(address='TMO:VLS:CAM:01:IMAGE2:ArrayData', value_slot=self.newSpecCallback)
        mypv.connect()
        self.sumScale=10000
        self.rmsScale=1;
        self.PyDMTimePlot.maxRedrawRate=1
        self.PyDMWaveformPlot.maxRedrawRate=1
        self.RefreshRateTimechart.returnPressed.connect(self.setRefreshRateTimechart)
        self.RefreshRateWaveform.returnPressed.connect(self.setRefreshRateWaveform)
        
        
        self.timeYmin.returnPressed.connect(self.setTimechartYRange)
        self.timeYmax.returnPressed.connect(self.setTimechartYRange)
        self.timeSumScale.returnPressed.connect(self.setTimeSumScale)
        self.timeRmsScale.returnPressed.connect(self.setTimeRmsScale)
        
        self.specXmin.returnPressed.connect(self.setWaveformXRange)
        self.specXmax.returnPressed.connect(self.setWaveformXRange)

        
    def ui_filename(self):
        # Point to our UI file
        return 'xleap_dashboard.ui'

    def ui_filepath(self):
        # Return the full path to the UI file
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())
    
    @Slot(float)
    @Slot(int)
    @Slot(np.ndarray)
    def newSpecCallback(self,values):
        if int(self.PyDMWaveformPlot.minXRange)<int(self.PyDMWaveformPlot.maxXRange):
            values=values[int(self.PyDMWaveformPlot.minXRange):int(self.PyDMWaveformPlot.maxXRange)]
        lowmask=values<np.percentile(values,25)
        bg=np.median(values[lowmask])
        values=values-bg
        self.specSumCurve.receiveNewValue(sum(values)/self.sumScale)
        idx=np.argmax(values)
        idx1=np.clip(idx-5,0,len(values))
        idx2=np.clip(idx+5,0,len(values))
        if np.mean(values[idx1:idx2])>(2*np.std(values[lowmask])+np.mean(values[lowmask])):
            fwhm=np.abs(np.diff(peak_fwhm(idx,values,outfrompeak=True,interp=True)))
            self.specRmsCurve.receiveNewValue(fwhm/self.rmsScale)
        return None
        
    def setRefreshRateTimechart(self):
        try:
            self.PyDMTimePlot.maxRedrawRate=float(self.RefreshRateTimechart.text())
        except:
            pass
    def setRefreshRateWaveform(self):
        try:
            self.PyDMWaveformPlot.maxRedrawRate=float(self.RefreshRateWaveform.text())
        except:
            pass
    def setTimechartYRange(self):
        self.PyDMTimePlot.autoRangeY=False
        if len(self.timeYmin.text())>0:
            try:
                self.PyDMTimePlot.minYRange=float(self.timeYmin.text())
            except:
                pass
        if len(self.timeYmax.text())>0:
            try:
                self.PyDMTimePlot.maxYRange=float(self.timeYmax.text())
            except:
                pass
    def setTimeSumScale(self):
        try:
            self.sumScale=float(self.timeSumScale.text())*10000
        except:
            pass
    def setTimeRmsScale(self):
        try:
            self.rmsScale=float(self.timeRmsScale.text())
        except:
            pass
    def setWaveformXRange(self):
        self.PyDMWaveformPlot.autoRangeX=False
        if len(self.specXmin.text())>0:
            try:
                self.PyDMWaveformPlot.minXRange=float(self.specXmin.text())
            except:
                pass
        if len(self.specXmax.text())>0:
            try:
                self.PyDMWaveformPlot.maxXRange=float(self.specXmax.text())
            except:
                pass
#def receiveNewValue(self, new_value):
def peak_fwhm(pk_idx,lis,thresh=None,outfrompeak=True,interp=False):
    """
    pk_idx: integer index of the peak in list
    lis: the list of values
    thresh: the value of the threshold. An absolute number. Default is max(list)/2 which would give FWM
    outfrompeak: bool choice whether to search starting from peak, or from edges of list
    interp: bool choice whether to interpolate value between last two points.
    
    Note search is exclusice: so values found will be at or lower than Thresh (rather than last "Good" point)
    returns: pt1,pt2
    """
    m=lis[pk_idx]
    if thresh==None:
        thresh=m/2
    pt1=pk_idx;pt2=pk_idx;
    if outfrompeak:
        try:
            for idx,l in enumerate(np.flip(lis[0:pk_idx],0)):
                if l<=thresh:
                    pt1=pk_idx-idx-1;
                    break
        except:
            pt1=0
        try:
            for idx,l in enumerate(lis[pk_idx:]):
                if l<=thresh:
                    pt2=pk_idx+idx;
                    break
        except:
            pt2=len(lis)
    else:
        try:
            for idx,l in enumerate(lis[0:pk_idx]):
                if l>=thresh:
                    pt1=idx-1;
                    break
        except:
            pt1=0
        try:
            for idx,l in enumerate(np.flip(lis[pk_idx:],0)):
                if l>=thresh:
                    pt2=len(lis)-idx;
                    break
        except:
            pt2=len(lis)
        pt1=np.clip(pt1,1,len(lis)-2)
        pt2=np.clip(pt2,1,len(lis)-2)
    #print(lis[pt1],lis[pt2])
    if interp:
        try:
            invweights=np.abs(np.array(lis[pt1:pt1+2])-thresh)
            invweights[invweights==0]=1e5;
            weights=1/invweights
            pt1=np.sum(np.array([pt1,pt1+1]*weights)/np.sum(weights))
        except:
            pt1=pt1
        try:
            invweights=np.abs(np.array(lis[pt2-1:pt2+1])-thresh)
            invweights[invweights==0]=1e-5;
            weights=1/invweights
            pt2=np.sum(np.array([pt2-1,pt2]*weights)/np.sum(weights))
        except:
            pt2=pt2
        pt1=np.clip(pt1,0,len(lis)-2)
        pt2=np.clip(pt2,0,len(lis)-2)
    return pt1,pt2