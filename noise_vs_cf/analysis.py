from pyinstruments.curvestore import models
from pandas import  *
from scipy.optimize import curve_fit
from pylab import show, figure, plot, legend
from numpy  import log10

def analyze( parent_id, min_freq=8e5, max_freq=1e8, exclude=None ):
    """Gives the maximum noise versus the carrier frquency in the given BW"""
    cp=models.CurveDB.objects.get(id=parent_id)
    f_childs=cp.childs.filter_param("name", value__contains="V")
    voltage=[]
    noise=[]
    power=[]
    if exclude is not None:
        exclude.sort()
        intrv=[]
        temp=min_freq
        for e in exclude:
            intrv.append( [ temp, e[0] ] )
            temp=e[1]
        intrv.append( [temp,max_freq] )
    else:
        intrv=[ [min_freq,max_freq] ]
    for c in f_childs:
        c_noise=c.childs.filter_param("name", value__contains="Noise")[0]
        c_int=c.childs.filter_param("name", value__contains="Int")[0]
        v=c_int.params["volt"]
        voltage.append(v)
        p=c_int.data.mean()
        power.append(p)
        n=-1
        for i in intrv:
            n_new=c_noise.data[i[0]:i[1]].max()
            if n_new>n:
                n=n_new
        noise.append(n)
    print "Calibrations"
    c_calib=cp.childs.filter_param("name", value__contains="calib")[0]
    voltage=Series(voltage)
    freq=calib_freq(c_calib)(voltage)
#    print len(noise)
#    print freq
#    print voltage
    noise=Series(data=noise,index=freq.values)
    power=Series(data=power,index=freq.values)
    noise_norm=noise/(power**2) #classical noise measured
    noise_norm=10*log10(noise_norm/noise_norm.max())
    return noise_norm, noise, power, freq, voltage
    
def calib_freq(c):
    max=c.data.ix[100e6:].max()
    w,=np.where(c.data>max-10)
    w2=np.where(c.data.index[w]>100e6)
    f_min=c.data.index[w[w2][0]]
    f_max=c.data.index[w[w2][-1]]
    return lambda x: x*(f_max-f_min)/10.+f_min
