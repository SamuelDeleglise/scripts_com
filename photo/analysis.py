from pyinstruments.curvestore import models
from scripts_com.analysis.processing import cor_vs_freq, SingleRun
from pandas import  *
from scipy.optimize import curve_fit

def analyze(parent_id, av_freq=1e4):
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
    for i in range(0,df[df.columns[0]].size):
        freqs.append(df.ix[i].name)
        pshot.append( fitPower(df.ix[i]) )
    c_shot=Series(data=pshot,index=freqs)
    return c_shot,df

def fitFunc(t,lbd):
    return lbd*t/(lbd*t+2)

def fitPower(s):
    ind=np.array(s.index,dtype=float)
    fitparams,fitcov=curve_fit(fitFunc,ind,s.values)
    return 1/fitparams[0]