"""Estimación y protocolo de desarrollo para la única variante de aprobación rápida."""
import time
import numpy as np
from scipy.optimize import least_squares
from .rk4_solver import RapidParameters, vector
from .calibration import analytical_trajectory


P_STARTS = (0., .5, .9)
RATE_FACTORS = (.5, 1., 2.)
PROFILE_P = (0., .25, .5, .75, .9, .99, 1.)


def development_windows(data):
    """Cuatro evaluaciones consecutivas con prefijos expansivos; sólo desarrollo."""
    n=len(data.arrivals)
    horizon=int(.15*n)
    if horizon<1:
        raise ValueError('Información insuficiente para ventanas de desarrollo')
    first=n-4*horizon
    return [(f'V{k+1}', data.section(0,first+k*horizon),
             data.section(first+k*horizon,first+(k+1)*horizon)) for k in range(4)]


def candidate_residual(theta,data,scales=None):
    parameters=RapidParameters(*vector(theta,4,'Parámetros candidato'))
    scale=data.scales if scales is None else vector(scales,3,'Escalas')
    if (scale<=0).any():
        raise ValueError('Escalas deben ser positivas')
    states=analytical_trajectory(data.observed[0],data.arrivals,parameters)
    return ((states[1:,:3]-data.observed[1:,:3])/scale).ravel()


def fit_candidate(data, initial, max_nfev=200, fixed_p=None):
    initial=vector(initial,4,'Inicial candidato')
    RapidParameters(*initial)
    scale=data.scales.copy()
    calls=0
    if fixed_p is not None:
        RapidParameters(*initial[:3],fixed_p)
    def objective(theta):
        nonlocal calls
        calls+=1
        full=theta if fixed_p is None else np.r_[theta,fixed_p]
        return candidate_residual(full,data,scale)
    x0=initial if fixed_p is None else initial[:3]
    upper=np.r_[np.full(3,np.inf),1.] if fixed_p is None else np.full(3,np.inf)
    start=time.perf_counter()
    r=least_squares(objective,x0,bounds=(np.zeros(len(x0)),upper),method='trf',
        jac='3-point',x_scale='jac',loss='linear',ftol=1e-10,xtol=1e-10,gtol=1e-10,max_nfev=max_nfev)
    full=r.x if fixed_p is None else np.r_[r.x,fixed_p]
    # Escalas relativas para tasas, escala absoluta unitaria para p, incluso p=0.
    sensitivity=r.jac*np.r_[full[:3],1.][:len(x0)][None,:]
    singular=np.linalg.svd(sensitivity,compute_uv=False)
    norms=np.linalg.norm(sensitivity,axis=0)
    corr=None
    if fixed_p is None and norms[0]>0 and norms[3]>0:
        corr=float(sensitivity[:,0]@sensitivity[:,3]/(norms[0]*norms[3]))
    info={'initial':initial.tolist(),'parameters':full.tolist(),'fixed_p':fixed_p,
          'cost_half_sse':float(r.cost),'mean_normalized_squared_error':float(np.mean(r.fun**2)),
          'success':bool(r.success),'status':int(r.status),'message':r.message,
          'nfev':int(r.nfev),'njev':int(r.njev),'actual_residual_calls':calls,
          'optimality':float(r.optimality),'active_mask':r.active_mask.tolist(),
          'seconds':time.perf_counter()-start,'jacobian_singular_values':singular.tolist(),
          'jacobian_condition':float(singular[0]/singular[-1]) if singular[-1]>0 else None,
          'sensitivity_cosine_alpha_p':corr}
    return RapidParameters(*full),info


def candidate_multistart(data,preliminary):
    runs=[]
    for factor in RATE_FACTORS:
        for fraction in P_STARTS:
            p,info=fit_candidate(data,np.r_[np.asarray(preliminary)*factor,fraction])
            info['initial_rate_factor']=factor
            info['initial_p']=fraction
            runs.append((p,info))
    ok=[pair for pair in runs if pair[1]['success']]
    if not ok:
        raise RuntimeError('Ningún inicio del candidato convergió')
    return min(ok,key=lambda pair:pair[1]['cost_half_sse']),runs


def percent_improvement(base,candidate):
    if base==0:
        return 0. if candidate==0 else None
    return 100*(1-candidate/base)


def assess_selection(improvements, candidate_infos, numeric_passed):
    """Aplica criterios fijados sin reescalar ni volver a elegir umbrales."""
    values=np.asarray(improvements,dtype=float)
    if values.shape!=(4,3) or not np.isfinite(values).all():
        raise ValueError('Se requieren cuatro ventanas y tres mejoras finitas')
    theta=np.array([info['parameters'] for info in candidate_infos])
    if theta.shape!=(4,4):
        raise ValueError('Se requieren parámetros de las cuatro ventanas')
    rate_ratios=np.divide(theta[:,:3].max(axis=0),theta[:,:3].min(axis=0),
                          out=np.full(3,np.inf),where=theta[:,:3].min(axis=0)>0)
    checks={'median_X1_improvement_at_least_15':bool(np.median(values[:,0])>=15),
        'no_X2_X3_deterioration_above_10_any_window':bool((values[:,1:]>=-10).all()),
        'numerical_checks':bool(numeric_passed),
        'optimizers_converged':all(i['success'] for i in candidate_infos),
        'p_range_at_most_020':bool(np.ptp(theta[:,3])<=.20),
        'rate_ratios_at_most_2':bool((rate_ratios<=2).all()),
        'no_p_near_one':bool((theta[:,3]<.99).all()),
        'local_condition_below_1000':all(i['jacobian_condition'] is not None and i['jacobian_condition']<1000 for i in candidate_infos),
        'alpha_p_sensitivity_cosine_below_098':all(i['sensitivity_cosine_alpha_p'] is not None and abs(i['sensitivity_cosine_alpha_p'])<.98 for i in candidate_infos)}
    return {'checks':checks,'selected_model':'candidate' if all(checks.values()) else 'base',
        'median_X1_improvement_percent':float(np.median(values[:,0])),
        'minimum_X2_X3_improvement_percent':values[:,1:].min(axis=0).tolist(),
        'p_range':float(np.ptp(theta[:,3])),'rate_max_min_ratios':rate_ratios.tolist()}
