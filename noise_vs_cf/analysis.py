from pyinstruments.curvestore import models
from pandas import  *
from scipy.optimize import curve_fit
from pylab import show, figure, plot, legend

def analyze( parent_id, min_freq=8e5, max_freq=1e8 ):
    """Gives the maximum noise versus the carrier frquency in the given BW"""
    cp=models.CurveDB.objects.get(id=parent_id)
    f_childs=cp.childs.filter_param("name", value__contains="V")
    voltage=[]
    noise=[]
    power=[]
    for c in f_childs:
        c_noise=c.childs.filter_param("name", value__contains="Noise")[0]
        c_int=c.childs.filter_param("name", value__contains="Int")[0]
        v=c_int.params["volt"]
        voltage.append(v)
        p=c_int.data.mean()
        power.append(p)
        n=c_noise.data[min_freq:max_freq].max()
        noise.append(n)
    c_calib=cp.childs.filter_param("name", value__contains="calib")[0]
    f_min, f_max=calib(c_calib)
    
def calib(c_calib):
    max=c.data.ix[100e6:].max()
    w,=np.where(c.data>max-10)
    w2=np.where(c.data.index[w]>100e6)
    f_min=c.data.index[w[w2][0]]
    f_max=c.data.index[w[w2][-1]]
    return f_min, f_max
