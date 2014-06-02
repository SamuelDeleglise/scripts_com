import pandas as pd
import numpy as np
from pyinstruments.curvestore import models
import gc
import math
from matplotlib.pyplot import figure,scatter
from matplotlib.cm import cool
from curve import Curve

from scripts_com.common import *
	

class Run:
	def __init__(self,idmin, idmax, type="runCOM"):
		runs=range(idmin,idmax+1)
		curves = models.CurveDB.objects.filter_tag(type).filter(id__in=runs)#filter_param("id", value__in=runs)
		self.curves_pha = curves.filter_param("trace_label",value=label_pha)
		self.curves_int = curves.filter_param("trace_label",value=label_int)
		self.curves_cs = curves.filter_param("trace_label",value=label_cs)
		self.curves_iq = curves.filter_param("trace_label",value=label_iq)
		self.get_cs_iq()
		
	def get_cs_iq(self):
		c_cs_iq=[]
		for c1,c2 in zip( self.curves_iq, self.curves_pha ):
			c_cs_iq.append( convert_IQ(c1, c2) )
		self.curves_cs_iq = c_cs_iq
		
class SingleRun(Run):
	def __init__(self,id_pha, id_int, id_iq):
		self.curves_pha = [models.CurveDB.objects.get(id=id_pha)]
		self.curves_int = [models.CurveDB.objects.get(id=id_int)]
		self.curves_iq = [models.CurveDB.objects.get(id=id_iq)]
		self.get_cs_iq()

def conv(Curves, exclude=None,cplx=False):
	mean=[]
	rms=[]
	m=mask(Curves[0], exclude)
	if not cplx:
		for c in Curves:
			mean.append( c.data[m].mean() )
			rms.append( c.params["current_average"] )
		data=pd.Series(mean,index=rms)
		return data
	else:
		for c in Curves:
			mean.append( c.data[m].real.mean()+1j*c.data[m].imag.mean() )
			rms.append( c.params["current_average"] )
		data=pd.Series(mean,index=rms)
		return data

def conv_cs(Run, exclude=None):
	return conv(Run.curves_cs, exclude)

def conv_cs_iq(Run, exclude=None):
	return conv(Run.curves_cs_iq, exclude, cplx=True)

def conv_pha(Run, exclude=None):
	return conv(Run.curves_pha, exclude)

def conv_int(Run, exclude=None):
	return conv(Run.curves_int, exclude)

def conv_lock(Run):
	lock_point=[]
	rms=[]
	angles=[]
	for c1,c2 in zip( Run.curves_cs_iq, Run.curves_pha):
		freq = get_mmode_freq(c2)
		test = test_mod_freq(freq,c2)
		rms.append(c1.params["current_average"])
		lock_point.append(c1.data[freq])
		angles.append(float(c1.params["angle"]))
	lock=pd.Series(lock_point,index=rms)
	angles=pd.Series(angles,index=rms)
	return np.cos(np.radians(angles))*lock.real + np.sin(np.radians(angles))*lock.imag

def conv_cor(Run, exclude=None):
	mean_cs=[]
	mean_pha=[]
	mean_int=[]
	rms=[]
	m=mask(Run.curves_pha[0], exclude)
	for c in Run.curves_cs:
		cs=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_cs.append(cs)
		rms.append(cur_rms)
	data_cs=pd.Series(mean_cs,index=rms)
	rms=[]
	for c in Run.curves_pha:
		pha=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_pha.append(pha)
		rms.append(cur_rms)
	data_pha=pd.Series(mean_pha,index=rms)
	rms=[]
	for c in Run.curves_int:
		int=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_int.append(int)
		rms.append(cur_rms)
	data_int=pd.Series(mean_int,index=rms)
	data=data_cs/np.sqrt(data_pha*data_int)
	return data

def conv_cor_iq(Run, exclude=None):
	data_cs_iq=conv_cs_iq(Run, exclude)
	data_pha=conv_pha(Run, exclude)
	data_int=conv_int(Run, exclude)
	data=data_cs_iq/np.sqrt(data_pha*data_int)
	return data

def conv_cor_huge(idmin, idmax,exclude=None):
	runs=range(idmin,idmax+1)
	curves = models.CurveDB.objects.filter_tag("runCOM").filter_param("id", value__in=runs)
	curves_pha = curves.filter_param("trace_label",value='A')
	del curves
	m=mask(curves_pha[0], exclude)
	gc.collect()
	mean_cs=[]
	mean_pha=[]
	mean_int=[]
	rms=[]
	for c in curves_pha:
		pha=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_pha.append(pha)
		rms.append(cur_rms)
	data_pha=pd.Series(mean_pha,index=rms)
	data_pha.sort_index()
	rms=[]
	del curves_pha
	del mean_pha
	gc.collect()
	curves = models.CurveDB.objects.filter_tag("runCOM").filter_param("id", value__in=runs)
	curves_int = curves.filter_param("trace_label",value='B')
	del curves
	gc.collect()
	for c in curves_int:
		inte=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_int.append(inte)
		rms.append(cur_rms)
	data_int=pd.Series(mean_int,index=rms)
	data_int.sort_index()
	rms=[]
	del curves_int
	del mean_int
	gc.collect()
	prod=data_pha*data_int
	del data_pha
	del data_int
	gc.collect()
	prod=np.sqrt(prod)
	curves = models.CurveDB.objects.filter_tag("runCOM").filter_param("id", value__in=runs)
	curves_cs = curves.filter_param("trace_label",value='C')
	del curves
	gc.collect()
	for c in curves_cs:
		cs=c.data[m].mean()
		cur_rms=c.params["current_average"]
		mean_cs.append(cs)
		rms.append(cur_rms)
	data_cs=pd.Series(mean_cs,index=rms)
	del rms
	del mean_cs
	gc.collect()
	return data_cs/prod

def mask(c, exclude):
	exclude_points = lambda c,min_freq,max_freq: (c.data.index<min_freq) | (c.data.index>max_freq)
	mask=pd.Series(True,index=c.data.index)
	if exclude is not None:
		for freqs in exclude:
			mask = exclude_points(c,freqs[0],freqs[1])*mask
	return mask

def growing_windows(s,numbers=100, num_strt_pt=100):
	mean=s.size/2
	num_pt=np.logspace(np.log2(num_strt_pt), np.log2(s.size), num=numbers, base=2)
	windows=[]
	for n in num_pt:
		windows.append([ [ 0, s.index[mean-n/2] ], [ s.index[mean+n/2],  np.finfo(np.float64).max] ])
	return windows

def growing(c, numbers=100, exclude=None, num_strt_pt=100):
	av=[]
	num=[]
	m=mask(c, exclude)
	windows=growing_windows(c.data[m], numbers,num_strt_pt=num_strt_pt)
	for w,n in zip( windows, range(len(windows)) ):
		if exclude is not None:
			e=list(exclude)
			e.append(w[0])
			e.append(w[1])
			m2=mask( c, exclude=e )
		else:
			m2=mask( c, w )
		av.append( c.data[m2].real.mean() + 1j*c.data[m2].imag.mean() )
		num.append(n)
	return pd.Series(av, index=num)

def growing_cs_iq(Run, numbers=100, exclude=None, num_strt_pt=100):
	data=[]
	for c in Run.curves_cs_iq:
		data.append( growing(c, numbers, exclude, num_strt_pt=num_strt_pt) )
	return data

def conv_iq(Run, numbers=100, exclude=None, num_strt_pt=100):
	data=[]
	m=mask(Run.curves_cs_iq[0], exclude)
	windows=growing_windows(Run.curves_cs_iq[0].data[m], numbers,num_strt_pt=num_strt_pt)
	for w in windows:
		if exclude is not None:
			e=list(exclude)
		else:
			e=[]
		e.append(w[0])
		e.append(w[1])
		data.append( conv_cs_iq(Run, exclude=e) )
	return data

def plot_conv_iq(Run, numbers=100, exclude=None, num_strt_pt=100):
	figure("plot_conv_iq")
	data=conv_iq(Run, numbers=numbers, exclude=exclude, num_strt_pt=num_strt_pt)
	for d,n in zip( data, range(len(data)) ):
		d.abs().plot( c=cool( float(n)/len(data)) )
	

def plot_growing_cs_iq(Run, numbers=100, exclude=None,num_strt_pt=100):
	figure()
	data=growing_cs_iq(Run, numbers=numbers, exclude=exclude, num_strt_pt=num_strt_pt)
	for d,n in zip( data, range(len(data)) ):
		d.abs().plot(c=cool( float(n)/len(data)) )
		
def cor_vs_freq(Run, av_freq=1e3):
	windows=[]
	f1=Run.curves_cs_iq[0].data.index[0]
	f2=Run.curves_cs_iq[0].data.index[-1]
	rng=f2-f1
	n_pt=int(rng/av_freq)
	for n in range(n_pt):
		a = f1+n*av_freq
		b = a+av_freq
		windows.append([a, b])
	data_iq=[]
	data_pha=[]
	data_int=[]
	freqs=[]
	for w in windows:
		print w[0]
		ex=[ [0,w[0]], [w[1],np.finfo(np.float64).max] ]
		m=mask(Run.curves_cs_iq[0], ex)
		l=len( Run.curves_pha )
		data_iq.append( Run.curves_cs_iq[l-1].data[m].real.mean() +1j*Run.curves_cs_iq[-1].data[m].imag.mean())
		data_pha.append( Run.curves_pha[l-1].data[m].mean() )
		data_int.append( Run.curves_int[l-1].data[m].mean() )
		freqs.append((w[0]+w[1])/2.)
	i=pd.Series(data_int, index=freqs)
	p=pd.Series(data_pha, index=freqs)
	iq=pd.Series(data_iq, index=freqs)
	return iq/np.sqrt(i*p)



def full_analysis(Run, numbers=100, exclude=None, num_strt_pt=100):
	cor = conv_cor(Run,exclude)
	f_cor=figure("Correlations (phaseless)")
	cor.plot()
	cs = conv_cs(Run,exclude)
	f_cs=figure("Cross Spectrum (phaseless)")
	cs.plot()
	lock = conv_lock(Run)
	f_lock=figure("Lock")
	lock.plot()
	cs_iq=conv_cs_iq(Run,exclude)
	f_cs_iq_norm=figure("Cross Spectrum IQ Norm")
	cs_iq.abs().plot()
	f_cs_iq=figure("Cross Spectrum IQ")
	scatter(cs_iq.real,cs_iq.imag,[[range(cs_iq.size)]])
	f_cor_iq_norm=figure("Correlations IQ Norm")
	cor_iq=conv_cor_iq(Run,exclude)
	cor_iq.abs().plot()
	f_cor_iq=figure("Correlations IQ")
	scatter(cor_iq.real,cor_iq.imag,[[range(cor_iq.size)]])
	plot_growing_cs_iq(Run, numbers=numbers, exclude=exclude,num_strt_pt=num_strt_pt)
	plot_conv_iq(Run, numbers=numbers, exclude=exclude,num_strt_pt=num_strt_pt)
