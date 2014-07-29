from pyinstruments.curvestore import models
import pandas as p
import numpy as np

from pyinstruments.pyhardwaredb import instrument

#diff_eff return the diffraction efficiency, not simple pass efficiency a long as the power on
#both photodiodes is the same

def diff_eff(name, comment='', oscl='WS', spect='averell'):
    osc=instrument(oscl)
    spec=instrument(spect)
    name=str(name)
    f_min,f_max,c_freq_id=f_min_max()
    i_min,i_max,c_ramp_id=i_min_max()
    #getting ref curve
    osc.channel_idx=2
    c_ref=osc.get_curve()
    c_ref.name="ref"
    c_ref.save()
    #getting 0 order curve
    osc.channel_idx=1
    c_0=osc.get_curve()
    c_0.name="0 order"
    c_0.save()
    osc.channel_idx=4
    c_1=osc.get_curve()
    c_1.name="1 order"
    c_1.save()
    diff=c_1.data/(c_0.data+c_1.data)
    diff=diff[i_min:i_max]
    ind=np.linspace(f_min,f_max,diff.size)
    diff_data=p.Series(data=diff.values,index=ind)
    c_diff=models.CurveDB.create(diff_data,**{'comment':comment,'name':'diffraction efficiency'})
    c_diff.save()
    sgl_pass=c_1.data/c_ref.data
    sgl_pass=sgl_pass[i_min:i_max]
    sgl_pass_data=p.Series(data=sgl_pass.values,index=ind)
    c_sngl=models.CurveDB.create(sgl_pass_data,**{'comment':comment,'name':'single pass  efficiency'})
    c_sngl.save()
    prt=models.CurveDB()
    prt.name=name
    prt.params["comment"]=comment
    prt.tags+=['AOM']
    prt.save()
    give_birth(prt,*[c_diff.id, c_sngl.id,c_freq_id,c_ramp_id,c_ref.id, c_0.id, c_1.id])
    return c_sngl, c_diff
    
    
def f_min_max(spec):
    c=spec.get_curve()
    c.name="freq_scan"
    c.save()
    max=c.data.ix[100e6:].max()
    w,=np.where(c.data>max-10)
    w2=np.where(c.data.index[w]>100e6)
    f_min=c.data.index[w[w2][0]]
    f_max=c.data.index[w[w2][-1]]
    return f_min, f_max, c.id

def i_min_max(osc,chan=3):
    #getting the ramp
    osc.channel_idx=chan
    c=osc.get_curve()
    c.name="ramp"
    c.save()
    i_min=c.data.values.argmin()
    i_max=c.data.values.argmax()
    return i_min,i_max, c.id

def give_birth(p, *args):
    for id in args:
        c=models.CurveDB.objects.get(id=id)
        c.move(p)
        
def normalize(c_id, val, freq):
    c=models.CurveDB.objects.get(id=c_id)
    inc=c.data.index[1]-c.data.index[0]+1.
    range=c.data[freq-inc/2.:freq+inc/2.]
    ind=range.index[0]
    norm=val/c.data.ix[ind]
    d_values=c.data.values*norm
    d=models.CurveDB.create(c.data.index,d_values,**c.params)
    d.name='single_pass_calibrated'
    d.save()
    d.move(c.parent)
    return d

def dbl_pass_fbr_cpl(name='coupling', comment='', oscl='Atchoum'):
    osc2=instrument(oscl)
    osc2.channel_idx=1
    c_1=osc2.get_curve()
    c_1.name='before'
    c_1.save()
    imin, imax, c_ramp_id = i_min_max(osc2, chan=2)
    osc2.channel_idx=4
    c_2=osc2.get_curve()
    c_2.name='after'
    c_2.save()
    cpl_data=c_2.data/c_1.data
    cpl_data=cpl_data[imin:imax]
    cpl_data=cpl_data/cpl_data.max()
    c_cpl=models.CurveDB.create(cpl_data,**{'comment':comment,'name':'coupling  efficiency'})
    c_cpl.save()
    prt=models.CurveDB()
    prt.name=name
    prt.params["comment"]=comment
    prt.tags+=['AOM','coupling']
    prt.save()
    give_birth(prt,c_ramp_id, c_1.id, c_2.id, c_cpl.id)
    return c_cpl