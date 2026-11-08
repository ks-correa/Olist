"""Two parallel exponential dwell paths per logistic stage, seven ODEs."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.linalg import expm
from scipy.signal import lfilter
from scipy.special import expit


@dataclass(frozen=True)
class MixtureSpec:
    theta: tuple

    def __post_init__(self):
        if len(self.theta)!=9 or not np.isfinite(self.theta).all():
            raise ValueError('Mezcla: nueve parámetros finitos')

    @property
    def coefficients(self):
        t=np.asarray(self.theta).reshape(3,3)
        return np.exp(t[:,:2]), expit(t[:,2])


def mixture_matrix(spec):
    k,p=spec.coefficients
    a=np.zeros((8,8))
    for stage in range(3):
        for path in range(2):
            i=2*stage+path
            a[i,i]=-k[stage,path]
            if stage<2:
                a[2*(stage+1),i]=p[stage+1]*k[stage,path]
                a[2*(stage+1)+1,i]=(1-p[stage+1])*k[stage,path]
            else:a[6,i]=k[stage,path]
    a[0,7]=p[0];a[1,7]=1-p[0]
    return a


def simulate_mixture(initial,arrivals,cuts,spec,substeps=4,analytical=False):
    initial=np.asarray(initial,float);u=np.asarray(arrivals,float);dates=pd.DatetimeIndex(cuts)
    if initial.shape!=(4,) or u.ndim!=1 or not len(u) or len(dates)!=len(u)+1 or dates.hasnans or not ((dates[1:]-dates[:-1])==pd.Timedelta(hours=1)).all():
        raise ValueError('Malla/estado incompatible')
    if not np.isfinite(initial).all() or (initial<0).any() or not np.isfinite(u).all() or (u<0).any():raise ValueError('Entrada no física')
    if isinstance(substeps,bool) or not isinstance(substeps,(int,np.integer)) or substeps<1:raise ValueError('Paso inválido')
    a=mixture_matrix(spec)
    if np.max(-np.diag(a))/substeps>1:raise ValueError('Etapas RK4 no positivas: reducir h')
    if analytical:f=expm(a)
    else:
        z=a/substeps;z2=z@z
        f=np.linalg.matrix_power(np.eye(8)+z+z2/2+z2@z/6+z2@z2/24,substeps)
    k,p=spec.coefficients
    weights=np.column_stack([p,1-p])/k
    weights/=weights.sum(axis=1)[:,None]
    x0=np.r_[(initial[:3,None]*weights).ravel(),initial[3]]
    x=np.empty((len(u)+1,7));x[0]=x0
    for i in range(7):
        forcing=f[i,7]*u
        for j in range(i):forcing=forcing+f[i,j]*x[:-1,j]
        x[1:,i],_=lfilter([1.],[1.,-f[i,i]],forcing,zi=[f[i,i]*x0[i]])
    states=np.column_stack([x[:,0:2].sum(axis=1),x[:,2:4].sum(axis=1),x[:,4:6].sum(axis=1),x[:,6]])
    err=states.sum(axis=1)-(sum(initial)+np.r_[0,np.cumsum(u)])
    delta=np.diff(states,axis=0)
    flows=np.column_stack([u-delta[:,0],u-delta[:,:2].sum(axis=1),delta[:,3]])
    if not np.isfinite(x).all() or x.min()<0 or flows.min() < -1e-8 or (delta[:,3]<0).any() or abs(err).max()>1e-7*max(1,states.sum(axis=1).max()):raise ValueError('Trayectoria de mezcla no física')
    return states,x,flows,err


def simulate_mixture_agentpy(initial,arrivals,cuts,spec):
    import agentpy as ap
    from .agent_model import DepositAgent
    class MixedModel(ap.Model):
        def setup(self):
            self.result=simulate_mixture(initial,arrivals,cuts,spec)
            self.deposits=ap.AgentList(self,[DepositAgent(self,position=i,name=f'X{i+1}',level=initial[i]) for i in range(4)])
            self.published=[np.array(initial,float)]
        def step(self):
            for agent,value in zip(self.deposits,self.result[0][self.t]):agent.receive_state(value)
            self.published.append(np.array([a.level for a in self.deposits]))
    model=MixedModel({'steps':len(arrivals),'seed':0});model.run(display=False)
    return np.asarray(model.published),model
