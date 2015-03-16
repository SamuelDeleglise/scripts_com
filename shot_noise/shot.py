from pyinstruments.pyhardwaredb import instrument
from pyinstruments.curvestore import models

from PyQt4 import QtCore, QtGui

vsa = instrument("vsa")

label_pd1='A'
label_pd2='B'
label_cs='C'
label_iq='D'

class Shot(QtGui.QWidget):
    def __init__(self, type="debug", comment='', parent=None):
        self.type=str(type)
        self.tags = [self.get_current_tag()]
        self.comment=comment
        self.get_parent(parent)
        super(Shot, self).__init__()
        
        self.button_data = QtGui.QPushButton("Take data")
        self.button_data.clicked.connect(self.button_data_clicked)
        
        self.power_label = QtGui.QLabel('input power (mW)')
        self.power_box = QtGui.QDoubleSpinBox()
        self.power_box.setMinimum(0.)
        self.power_box.setMaximum(30.)
        self.power_box.setSingleStep(0.1)

        self.v_lay = QtGui.QVBoxLayout()
        self.hlay = QtGui.QHBoxLayout()
        self.hlay.addWidget(self.button_data)
        self.hlay.addStretch(1)
        self.hlay.addWidget(self.power_label)
        self.hlay.addWidget(self.power_box)
        
        self.v_lay.addLayout(self.hlay)                            
        self.setWindowTitle("Shot")
        self.setLayout(self.v_lay)
        self.show()
        
    @property
    def power(self):
        return float(self.power_box.value())
    @power.setter
    def power(self, val):
        val=float(val)
        self.power_box.setValue(val)
        
    def take_curve(self, label):
        vsa.active_label = label
        curve = vsa.get_curve()
        curve.tags+= self.tags
        curve.params["name"] = curve.params["data_name"] + "_" +\
                                str(curve.params["current_average"])
        curve.params["comment"]=self.comment
        curve.params["power"]=self.power
        curve.move(self.power_crv)
        curve.save()
        
    def take_one_point(self):
        print 'taking_one_point'
        prt=models.CurveDB()
        prt.name='power_'+str(self.power)+'mW'
        prt.params["comment"]=self.comment
        prt.tags+=[self.type]
        prt.move(self.parent_crv)
        self.power_crv=prt
        prt.save()
        vsa.pause()
        self.take_curve(label_pd1)
        self.take_curve(label_pd2)
        self.take_curve(label_cs)
        self.take_curve(label_iq)
        
    
    def get_current_tag(self):
        existing = models.Tag.objects.filter(name__startswith=self.type)
        num_max = 0
        for tag in existing:
            num_str = tag.name.split("/")[-1]
            try:
                num = int(num_str)
            except ValueError:
                pass
            else:
                num_max = max(num_max, num)
        return self.type+"/%04i"%(num_max+1)
      
    def button_data_clicked(self):
        self.take_one_point()
        
    def get_parent(self,parent):
        if parent is None:
            prt=models.CurveDB()
            prt.name='shot'
            prt.params["comment"]=self.comment
            prt.tags+=[self.type]
            prt.save()
            self.parent_crv=prt
        else:
            self.parent_crv=models.CurveDB.objects.get(id=parent)
        