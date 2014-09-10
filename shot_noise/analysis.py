from pyinstruments.curvestore import models
from scripts_com.analysis.processing import cor_vs_freq, SingleRun
from pandas import  *
from scipy.optimize import curve_fit
from pylab import show, figure, plot, legend
from math import sqrt, fabs
import numpy as np

def analyze( parent_id, av_freq=1e4, keep_fit=[1e6,2e6] ):
    """return the power where classical noise equal quantum noise"""
    cp=models.CurveDB.objects.get(id=parent_id)
    childs=cp.childs.filter_param("name", value__contains="power")
    powers=[]
    correlations=[]
    lambdas=[]
    for c in childs:
        power=float(c.name.split('_')[1].split('mW')[0])
        print 'computing correlations for '+str(power)+'mw power'
        c1_id=c.childs.filter_param("trace_label", value='A')[0].id
        c2_id=c.childs.filter_param("trace_label", value='B')[0].id
        ciq_id=c.childs.filter_param("trace_label", value='D')[0].id
        srun=SingleRun(c1_id,c2_id,ciq_id)
        cvf=cor_vs_freq(srun,av_freq=av_freq)
        powers.append(power)
        correlations.append(cvf.abs())
    print 'fitting lambda'
    labels=[]
    for p in powers:
        labels.append( str(p) )
    df_dict={}
    for l,c in zip(labels,correlations):
        df_dict[l]=c
    labels.reverse()
    df=DataFrame(df_dict,index=correlations[0].index,columns=labels)
    freqs=[]
    pshot=[]
    for i in range(0, df[df.columns[0]].size ):
        freqs.append( df.ix[i].name )
        pshot.append( fitPower(df.ix[i],av_freq, *keep_fit) )
    c_shot=Series( data=pshot, index=freqs )
    return c_shot,df

def fitFunc(t,lbd):
    return lbd*t/(lbd*t+2)

def fitPower(s,av_freq=None, *args):
    '''Will plot fits for freqs in args within av_freq'''
    ind=np.array(s.index,dtype=float)
    fitparams,fitcov=curve_fit(fitFunc,ind,s.values)
    for freq in args:
#        print s.name, freq, (freq<(s.name+av_freq)), (freq>(s.name-av_freq))
        if (freq<(s.name+av_freq/2.) and freq>(s.name-av_freq/2.)):
            print "keep fit for freq "+str(freq)
            figure( str(s.name) )
            plot( ind, fitFunc(ind,fitparams[0]) ,label='fit' )
            plot( ind, s.values, label='data' )
            legend()
            show()
    return 1/fitparams[0]

def guess_correls(parent_id, pump_power, probe_power, lo_power, gain_imba=1e-3, av_freq=1e4):
    p_shot,grbg = analyze( parent_id, av_freq=av_freq)
    c_noise = pump_power/p_shot
    cors=sqrt(gain_imba)*fabs((probe_power-lo_power))/sqrt(pump_power*lo_power)
    cors=cors*c_noise/np.sqrt(1+c_noise)
    return cors

    
    
    