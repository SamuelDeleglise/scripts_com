from pandas import DataFrame,read_csv
from scipy.signal import welch

def psd(name, average):
    """
    Return the psd using welsh method
    """
    z=read_csv(str(name), sep='\t',header=5,index_col=0,dtype=float)
    fe=1/(z.index[1]-z.index[0])#sampling frequency
    psds=[]
    for c in z.columns:
        f,p=welch(z[c],fe,nperseg=average)
        psds.append(p)
    df=DataFrame(index=f)
    for c,i in zip(psds,range(len(psds))):
        df[str(i)]=c
    return df.mean(axis=1)

