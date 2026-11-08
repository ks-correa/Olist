"""Independent mathematical and statistical checks for experimental models."""
from dataclasses import replace
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from scipy.linalg import expm
from src.model_v2 import ModelSpec, simulate_v2, simulate_agentpy_v2, rates
from src.calibration_v2 import make_spec, fit_v2, BASE, ORIGINS, HORIZON
from src.calibration import load_training
from src.goodness_of_fit import goodness, residual_diagnostics, kaplan_meier, grouped_errors
from src.rk4_solver import Parameters
from src.simulation_engine import simulate

ROOT=Path(__file__).resolve().parents[1]


def fixture(name='A'):
    theta=np.log(BASE)
    if name in ('B','D'):
        theta=np.column_stack([theta,np.zeros((3,3))]).ravel()
    return make_spec(name,theta), pd.date_range('2017-01-01',periods=241,freq='h')


@pytest.mark.parametrize('name',['A','B','C','D'])
def test_conservation_positive_and_agents(name):
    spec,cuts=fixture(name)
    u=np.random.default_rng(3).poisson(10,240)
    initial=np.array([30,100,400,1000.])
    states,internal,flows,errors=simulate_v2(initial,u,cuts,spec)
    np.testing.assert_allclose(states.sum(axis=1),sum(initial)+np.r_[0,np.cumsum(u)],atol=1e-8)
    assert internal.min()>=0 and flows.min()>=-1e-10
    assert (np.diff(states[:,3])>=0).all()
    np.testing.assert_array_equal(simulate_v2(initial,u,cuts,spec)[0],states)
    agents,_=simulate_agentpy_v2(initial,u,cuts,spec)
    np.testing.assert_array_equal(agents,states)


def test_v1_and_calendar_zero_equivalence():
    a,cuts=fixture(); b,_=fixture('B'); u=np.arange(240)%20
    initial=[10,30,100,500]
    old=simulate(initial,u,Parameters(*BASE)).states
    new=simulate_v2(initial,u,cuts,a)[0]
    np.testing.assert_allclose(old,new,rtol=1e-12,atol=1e-8)
    np.testing.assert_array_equal(simulate_v2(initial,u,cuts,b)[0],new)


def test_rk4_against_independent_exponential_and_order():
    spec,cuts=fixture('C'); initial=[40,60,100,0]; u=np.ones(240)*10
    # Independent continuous chain matrix, constant forcing.
    m=np.zeros((8,8)); k=np.repeat(BASE,2)
    for i in range(6):m[i,i]=-k[i];m[i+1,i]=k[i]
    m[0,7]=10
    x=np.r_[np.repeat(np.asarray(initial[:3])/2,2),0.,1.]
    exact=np.array([(expm(t*m)@x)[:7] for t in range(241)])
    errors=[]
    for sub in (4,8,16):
        internal=simulate_v2(initial,u,cuts,spec,sub)[1]
        errors.append(np.max(abs(internal-exact)))
    assert errors[0]>errors[1]>errors[2]
    assert errors[0]/errors[1]>10


def test_metrics_independent_and_negative_r2():
    y=np.tile(np.arange(1.,11)[:,None],(1,3)); x=y+10; scale=np.array([2,4,5])
    t=goodness(y,x,scale)
    np.testing.assert_allclose(t.MAE,[10]*3);np.testing.assert_allclose(t.RMSE,[10]*3)
    np.testing.assert_allclose(t.NRMSE,10/scale);np.testing.assert_allclose(t.NMAE,10/scale)
    np.testing.assert_allclose(t.R2,1-1000/np.sum((np.arange(1.,11)-5.5)**2))
    assert (t.R2<0).all() and not t.cumple.any()
    assert goodness(np.ones((10,3)),np.ones((10,3)),scale).R2.isna().all()


def test_km_censoring_ties():
    km=kaplan_meier([1,1,2,3],[True,False,True,False])
    np.testing.assert_allclose(km.supervivencia,[.75,.375,.375])
    assert km.censuras.sum()==2 and km.eventos.sum()==2


def test_autocorrelation_reference():
    e=np.tile(np.arange(200.)[:,None],(1,3))
    table,acf=residual_diagnostics(e)
    v=e[:,0]-e[:,0].mean()
    assert acf[0,0]==pytest.approx(v[1:]@v[:-1]/(v@v))
    assert (table.p_descriptivo<.001).all()
    zero,zero_acf=residual_diagnostics(np.zeros((200,3)))
    assert zero.p_descriptivo.isna().all() and np.isnan(zero_acf).all()


def test_split_and_training_normalization():
    d=load_training(ROOT/'data/processed')
    for origin in ORIGINS:
        tr,ev=d.section(0,origin),d.section(origin,origin+HORIZON)
        assert tr.cuts[-1]==ev.cuts[0] and tr.cuts[-2]<ev.cuts[1]
        np.testing.assert_array_equal(tr.scales,np.maximum(1,tr.observed[1:,:3].mean(axis=0)))
    with pytest.raises(ValueError):
        replace(d,cuts=d.cuts+pd.Timedelta(days=1000))


def test_future_observations_not_input():
    spec,cuts=fixture('B'); u=np.ones(240)
    x=simulate_v2([10,20,30,40],u,cuts,spec)[0]
    changed=u.copy();changed[120:]=100
    x2=simulate_v2([10,20,30,40],changed,cuts,spec)[0]
    np.testing.assert_array_equal(x[:121],x2[:121])


@pytest.mark.parametrize('bad',[-1,0,True,1.5])
def test_invalid_steps(bad):
    spec,cuts=fixture()
    with pytest.raises(ValueError):simulate_v2([0]*4,np.ones(240),cuts,spec,bad)


def test_calendar_and_group_scales():
    spec,cuts=fixture('B'); theta=np.array(spec.theta).reshape(3,4); theta[:,3]=np.log(2)
    spec=make_spec('B',theta.ravel())
    rr=rates(spec,cuts)
    np.testing.assert_allclose(rr[0],2*BASE); np.testing.assert_allclose(rr[24],BASE)
    y=np.ones((240,3));table=grouped_errors(cuts[1:],y,2*y,[2,3,4])
    np.testing.assert_allclose(table.groupby('variable').escala.first(),[2,3,4])


def test_frozen_artifact_and_original_integrity():
    folder=ROOT/'reports/modelo_v2'
    if not (folder/'congelado.json').exists():pytest.skip('Ejecutar experimento completo primero')
    import hashlib
    frozen=json.loads((folder/'congelado.json').read_text(encoding='utf8'))
    from src.validation_v2 import load_frozen_v2
    spec,record=load_frozen_v2(ROOT)
    assert spec.name=='B' and record['theta']==frozen['theta']
    assert frozen['protocolo_sha256']==hashlib.sha256((folder/'protocolo.md').read_bytes()).hexdigest()
    audit=json.loads((folder/'auditoria_previa.json').read_text(encoding='utf8'))
    for path,digest in audit['files'].items():
        if path.startswith(('src','data','reports','tests','docs')):
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
