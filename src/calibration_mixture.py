"""Adaptive second-round candidate; only the historical development prefix fits."""
import numpy as np
from scipy.optimize import least_squares
from scipy.special import logit
from .model_mixture import MixtureSpec, simulate_mixture
from .calibration import TRAIN_END
from .calibration_v2 import BASE


def fit_mixture(data):
    if data.cuts[-1]>TRAIN_END:raise ValueError('No se ajusta fuera de desarrollo')
    low=np.tile([np.log(.0001),np.log(.0001),logit(.01)],3)
    high=np.tile([0.,0.,logit(.99)],3)
    scale=data.scales.copy()
    def objective(theta):
        x=simulate_mixture(data.observed[0],data.arrivals,data.cuts,MixtureSpec(tuple(theta)))[0]
        return ((x[1:,:3]-data.observed[1:,:3])/scale).ravel()/np.sqrt(3*len(data.arrivals))
    runs=[]
    for fast,slow,p in [(2,.5,.5),(5,.2,.8)]:
        initial=np.column_stack([np.log(BASE*fast),np.log(BASE*slow),np.full(3,logit(p))]).ravel()
        result=least_squares(objective,initial,bounds=(low,high),max_nfev=200,ftol=1e-7,xtol=1e-7,gtol=1e-7)
        s=np.linalg.svd(result.jac,compute_uv=False)
        theta=result.x.reshape(3,3).copy()
        for row in theta:
            if row[0]<row[1]:row[:2]=row[:2][::-1];row[2]*=-1
        runs.append(dict(theta=theta.ravel().tolist(),success=bool(result.success),cost=float(result.cost),nfev=int(result.nfev),
                         message=result.message,condition=float(s[0]/s[-1]) if s[-1] else None,singular_values=s.tolist(),
                         optimality=float(result.optimality),active_mask=result.active_mask.tolist(),scales=scale.tolist(),end=str(data.cuts[-1])))
    ok=[r for r in runs if r['success']]
    if not ok:raise RuntimeError('Sin convergencia de mezcla')
    return MixtureSpec(tuple(min(ok,key=lambda r:r['cost'])['theta'])),runs
