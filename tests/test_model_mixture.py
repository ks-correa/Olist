import numpy as np
import pandas as pd
from scipy.special import logit
from src.model_mixture import MixtureSpec,mixture_matrix,simulate_mixture,simulate_mixture_agentpy
from src.calibration_v2 import BASE


def test_mixture_balance_and_exact_comparison():
    theta=np.column_stack([np.log(BASE*4),np.log(BASE*.3),np.full(3,logit(.7))]).ravel()
    spec=MixtureSpec(tuple(theta));a=mixture_matrix(spec)
    np.testing.assert_allclose(a[:7,:7].sum(axis=0),0,atol=1e-16)
    assert a[:7,7].sum()==1
    dates=pd.date_range('2017-01-01',periods=401,freq='h');u=np.arange(400)%13
    initial=[100.,300.,500.,1000.]
    x,internal,q,e=simulate_mixture(initial,u,dates,spec)
    assert internal.min()>=0 and q.min()>=-1e-10 and (np.diff(x[:,3])>=0).all()
    np.testing.assert_allclose(x.sum(axis=1),sum(initial)+np.r_[0,np.cumsum(u)],atol=1e-8)
    exact=simulate_mixture(initial,u,dates,spec,analytical=True)[0]
    fine=simulate_mixture(initial,u,dates,spec,substeps=8)[0]
    assert abs(x-exact).max()/abs(fine-exact).max()>10
    agents,_=simulate_mixture_agentpy(initial,u,dates,spec)
    np.testing.assert_array_equal(x,agents)


def test_mixture_symmetry():
    theta=np.column_stack([np.log(BASE*2),np.log(BASE*.3),np.full(3,logit(.7))])
    swapped=theta.copy();swapped[:,:2]=swapped[:,:2][:,::-1];swapped[:,2]*=-1
    dates=pd.date_range('2017-01-01',periods=101,freq='h')
    x=simulate_mixture([10,20,30,40],np.ones(100),dates,MixtureSpec(tuple(theta.ravel())))[0]
    y=simulate_mixture([10,20,30,40],np.ones(100),dates,MixtureSpec(tuple(swapped.ravel())))[0]
    np.testing.assert_allclose(x,y,atol=1e-10)
