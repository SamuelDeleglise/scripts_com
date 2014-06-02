from pyinstruments.pyhardwaredb import instrument
from pyinstruments.curvestore import models

import time
from PyQt4 import QtCore, QtGui

vsa = instrument("vsa")

class Acquisition(QtGui.QWidget):
    def __init__(self, default_sleep=500, resume=True, auto=True):
        self.tags = [self.get_current_tag()]
        super(Acquisition, self).__init__()
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(default_sleep)
        self.timer.timeout.connect(self.take_one_point)
        
        self.button_start = QtGui.QPushButton("Start")
        self.button_start.clicked.connect(self.button_start_clicked)
        
        self.button_stop = QtGui.QPushButton("Stop")
        self.button_stop.clicked.connect(self.button_stop_clicked)
        
        self.label = QtGui.QLabel('sleep time (ms)')
        self.sleep_time_box = QtGui.QSpinBox() 
        self.sleep_time_box.setMaximum(int(1e9))
        
        self.checkbox_resume = QtGui.QCheckBox("Resume ?")
        
        self.checkbox_auto = QtGui.QCheckBox("Auto ?")
        
        self.v_lay = QtGui.QVBoxLayout()
        self.lay = QtGui.QHBoxLayout()
        self.lay.addWidget(self.button_start)
        self.lay.addWidget(self.button_stop)
        self.lay.addWidget(self.label)
        self.lay.addWidget(self.sleep_time_box)
        self.lay.addWidget(self.checkbox_auto)
        
        self.v_lay.addLayout(self.lay)
        self.hlay2 = QtGui.QHBoxLayout()
        self.hlay2.addWidget(self.checkbox_resume)
        self.v_lay.addLayout(self.hlay2)
                            
        
        self.setLayout(self.v_lay)
        
        self.sleep_time = default_sleep
        self.is_resume=resume
        self.isAuto=auto
        self.show()
        
    def take_curve(self, label):
        vsa.active_label = label
        curve = vsa.get_curve()
        curve.tags+= self.tags
        curve.params["name"] = curve.params["data_name"] + "_" +\
                                str(curve.params["current_average"])
        curve.save()
        
    def take_one_point(self):
        print 'taking_one_point'
        vsa.pause()
        self.take_curve('A')
        self.take_curve('B')
        self.take_curve('C')
        if self.isAuto:
            self.sleep_time=2*self.sleep_time
        self.timer.setInterval(self.sleep_time)
        vsa.resume()
        self.timer.start()
    
    @property
    def sleep_time(self):
        return self.sleep_time_box.value()
    
    @sleep_time.setter
    def sleep_time(self, val):
        self.sleep_time_box.setValue(val)
    
    @property
    def is_resume(self):
        return self.checkbox_resume.checkState()==2

    @is_resume.setter
    def is_resume(self, val):
        return self.checkbox_resume.setCheckState(val*2)
    
    @property
    def isAuto(self):
        return bool(self.checkbox_auto.checkState())

    @isAuto.setter
    def isAuto(self, val):
        return self.checkbox_auto.setCheckState(2*val)
    
    def get_current_tag(self):
        existing = models.Tag.objects.filter(name__startswith="average_coss")
        num_max = 0
        for tag in existing:
            num_str = tag.name.split("/")[-1]
            try:
                num = int(num_str)
            except ValueError:
                pass
            else:
                num_max = max(num_max, num)
        return "average_coss/%04i"%(num_max+1)
    
    def change_interval(self, val):
        self.timer.setInterval(val)
      
    def button_start_clicked(self):
        if self.is_resume:
            vsa.resume()
        else:
            vsa.restart()
        self.timer.start()
        
    def button_stop_clicked(self):
        self.timer.stop()
        
class Analysis:
    def __init__(self, num):
        curves = models.CurveDB.objects.filter_tag("average_coss/%04i"%(num)).filter_param("data_name", value="Cross Spectrum")
        for curve in curves:
            pass
        