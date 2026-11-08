"""Pruebas de la única variante; los ejemplos artificiales no son datos de Olist."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.rk4_solver import Parameters,RapidParameters,split_arrival,rhs,NumericalError,rk4_step
from src.simulation_engine import simulate,verify_interval
from src.agent_model import simulate_agentpy
from src.calibration import (analytical_trajectory,TrainingData,load_training,residual_vector,
                             TRAIN_END,N_TRAIN)
from src.rapid_calibration import (candidate_residual,fit_candidate,development_windows,
                                  assess_selection,percent_improvement)
from src.calibration_metrics import level_metrics

ROOT=Path(__file__).resolve().parents[1]


def test_p0_exact_base_rhs_rk4_analytical_and_agents():
    bp=Parameters(.2,.07,.02);cp=RapidParameters(*bp.array(),0)
    initial=[30,50,100,10];arrivals=[0,10,23,0,30,0,0]
    np.testing.assert_array_equal(rhs(0,initial,10,bp),rhs(0,initial,10,cp))
    b=simulate(initial,arrivals,bp);c=simulate(initial,arrivals,cp)
    np.testing.assert_array_equal(b.states,c.states)
    np.testing.assert_array_equal(b.transfers,c.transfers)
    np.testing.assert_array_equal(b.conservation_errors,c.conservation_errors)
    np.testing.assert_array_equal(analytical_trajectory(initial,arrivals,bp),analytical_trajectory(initial,arrivals,cp))
    a,m=simulate_agentpy(initial,arrivals,cp)
    np.testing.assert_array_equal(a.states,b.states)
    assert len(m.deposits)==4


@pytest.mark.parametrize('p',[-.1,1.00001,np.inf,np.nan,[.5]])
def test_invalid_p(p):
    with pytest.raises(ValueError): RapidParameters(.1,.1,.1,p)


@pytest.mark.parametrize('p',[0.,.35,1.])
def test_split_and_hour_boundary_conservation(p):
    initial=[0,0,0,0];arrivals=np.array([0.,12.,0.,20.])
    parameters=RapidParameters(0,0,0,p)
    slow,rapid=split_arrival(arrivals,parameters)
    np.testing.assert_allclose(slow+rapid,arrivals,rtol=0,atol=1e-14)
    r=simulate(initial,arrivals,parameters)
    np.testing.assert_allclose(r.states[:,0],np.r_[0,np.cumsum(slow)],atol=1e-13)
    np.testing.assert_allclose(r.states[:,1],np.r_[0,np.cumsum(rapid)],atol=1e-13)
    np.testing.assert_array_equal(r.transfers,np.zeros((4,3)))
    np.testing.assert_allclose(r.states.sum(axis=1),np.r_[0,np.cumsum(arrivals)],atol=1e-13)
    # Ninguna aprobación rápida vuelve a contarse en q12 convencional.
    np.testing.assert_array_equal(r.rapid_arrivals,rapid)


def test_four_agents_same_transfers_conventional_and_rapid():
    parameters=RapidParameters(.2,.07,.02,.6)
    arrivals=np.random.default_rng(7).integers(0,50,100)
    initial=[30,50,100,1000]
    r=simulate(initial,arrivals,parameters)
    a,m=simulate_agentpy(initial,arrivals,parameters)
    np.testing.assert_array_equal(a.states,r.states)
    np.testing.assert_array_equal(a.transfers,r.transfers)
    np.testing.assert_array_equal(a.rapid_arrivals,r.rapid_arrivals)
    moved=r.transfers;rapid=r.rapid_arrivals
    changes=np.column_stack([arrivals-rapid-moved[:,0],rapid+moved[:,0]-moved[:,1],
                              moved[:,1]-moved[:,2],moved[:,2]])
    np.testing.assert_allclose(np.diff(r.states,axis=0),changes,rtol=0,atol=1e-11)
    np.testing.assert_array_equal(m.output.variables.FourDepositModel.rapid_purchases.to_numpy()[1:],rapid)
    assert r.max_conservation_error<1e-8*(sum(initial)+arrivals.sum())
    assert (r.states>=0).all() and (np.diff(r.states[:,3])>=0).all()


def test_p1_transfers_and_analytical_solution():
    p=RapidParameters(.5,.1,.02,1)
    initial=[100,10,20,30];arrivals=[2,5,10,0,0]
    r=simulate(initial,arrivals,p,16)
    np.testing.assert_allclose(r.states[:,0],100*np.exp(-.5*r.times),atol=1e-6,rtol=0)
    np.testing.assert_allclose(r.states,analytical_trajectory(initial,arrivals,p),atol=1e-6,rtol=0)
    assert r.max_conservation_error<1e-10


def test_p1_alpha_unidentifiable_if_initial_X1_zero():
    arrivals=np.arange(20,dtype=float)
    a=analytical_trajectory([0,10,20,30],arrivals,RapidParameters(.01,.1,.02,1))
    b=analytical_trajectory([0,10,20,30],arrivals,RapidParameters(.5,.1,.02,1))
    # expm changes roundoff when the unused alpha block changes (observed 2.84e-14).
    # Use a floating-point bound here; p=0 and AgentPy equivalence remain exact.
    np.testing.assert_allclose(a,b,rtol=0,atol=8*np.finfo(float).eps*np.max(a))
    rk_a=simulate([0,10,20,30],arrivals,RapidParameters(.01,.1,.02,1))
    rk_b=simulate([0,10,20,30],arrivals,RapidParameters(.5,.1,.02,1))
    np.testing.assert_array_equal(rk_a.states,rk_b.states)


@pytest.fixture
def controlled():
    known=RapidParameters(.16,.06,.02,.55)
    arrivals=np.random.default_rng(8).integers(0,50,180).astype(float)
    states=simulate([30,50,100,10],arrivals,known,32).states
    data=TrainingData(pd.date_range('2017-01-01',periods=181,freq='h'),arrivals,states,np.zeros((180,3)))
    return data,known


def test_recover_candidate_parameters_and_reproducibility(controlled):
    data,known=controlled
    initial=[.12,.08,.03,.3]
    p,info=fit_candidate(data,initial)
    q,again=fit_candidate(data,initial)
    assert info['success'] and again['success']
    np.testing.assert_allclose(p.full_array(),known.full_array(),rtol=1e-5,atol=1e-8)
    np.testing.assert_array_equal(p.full_array(),q.full_array())
    assert info['cost_half_sse']==again['cost_half_sse']
    assert candidate_residual(p.full_array(),data).shape==(540,)
    with pytest.raises(ValueError): candidate_residual([.1,.1,.1,2],data)


def test_p0_same_normalized_residuals_and_identical_windows(controlled):
    data,_=controlled
    np.testing.assert_array_equal(residual_vector([.1,.02,.005],data),candidate_residual([.1,.02,.005,0],data))
    windows=development_windows(data)
    assert len(windows)==4
    for _,fit,evaluate in windows:
        assert fit.cuts[0]==data.cuts[0]
        assert fit.cuts[-1]==evaluate.cuts[0]
        assert evaluate.cuts[-1]<=TRAIN_END
        assert len(evaluate.arrivals)==int(.15*len(data.arrivals))
        for parameters in [Parameters(.1,.02,.005),RapidParameters(.1,.02,.005,.3)]:
            states=simulate(evaluate.observed[0],evaluate.arrivals,parameters).states
            table=level_metrics(evaluate,states,np.r_[fit.scales,1,1])
            np.testing.assert_array_equal(table.escala.to_numpy()[:3],fit.scales)
    assert windows[-1][2].cuts[-1]==data.cuts[-1]


def test_candidate_cannot_use_reserved_data(tmp_path):
    source=ROOT/'data/processed'
    for filename in ['eventos_por_hora.csv','niveles_reales_4_tanques.csv']:
        with (source/filename).open(encoding='utf-8') as f:
            prefix=''.join(next(f) for _ in range(N_TRAIN+2))
        (tmp_path/filename).write_text(prefix+'2019-01-01,INVALID,RESERVED,UNUSED\n',encoding='utf-8')
    a=load_training(source);b=load_training(tmp_path)
    theta=[.1,.01,.004,.3]
    np.testing.assert_array_equal(candidate_residual(theta,a),candidate_residual(theta,b))
    p,_=fit_candidate(a,theta);q,_=fit_candidate(b,theta)
    np.testing.assert_array_equal(p.full_array(),q.full_array())
    assert all(test.cuts[-1]<=TRAIN_END for _,fit,test in development_windows(a))


def test_numerical_convergence_and_unstable_candidate(controlled):
    data,p=controlled
    reference=analytical_trajectory(data.observed[0],data.arrivals,p)
    results=[simulate(data.observed[0],data.arrivals,p,n) for n in (4,8,16)]
    errors=[np.max(np.abs(result.states-reference)) for result in results]
    assert errors[0]>errors[1]>errors[2]
    difference=results[1].states-results[2].states
    assert np.max(np.abs(difference))<=.1
    assert (np.sqrt(np.mean(difference[1:,:3]**2,axis=0))/data.scales<=.001).all()
    with pytest.raises(NumericalError): rk4_step([100,0,0,0],0,RapidParameters(12,0,0,.5),.25)
    with pytest.raises(NumericalError): verify_interval(np.ones(4),np.ones(4),np.zeros(3),1,4,2)


def test_selection_is_not_training_loss():
    infos=[{'parameters':[.1,.01,.004,.3],'success':True,'jacobian_condition':10,
             'sensitivity_cosine_alpha_p':.9} for _ in range(4)]
    enough=np.array([[20,0,0]]*4)
    assert assess_selection(enough,infos,True)['selected_model']=='candidate'
    assert assess_selection(np.zeros((4,3)),infos,True)['selected_model']=='base'
    enough[0,2]=-11
    assert assess_selection(enough,infos,True)['selected_model']=='base'
    assert percent_improvement(0,0)==0 and percent_improvement(0,1) is None
    assert percent_improvement(1,.8)==pytest.approx(20)


def test_base_parameters_file_preserved():
    j=json.loads((ROOT/'reports/parametros_calibrados.json').read_text(encoding='utf-8'))
    assert j['alpha']==.10202378368368686
    assert j['beta']==.013240792867426554 and j['gamma']==.004071911987908591
    import hashlib
    other=ROOT/'reports/parametros_aprobacion_rapida.json'
    if other.exists():
        rapid=json.loads(other.read_text(encoding='utf-8'))
        assert hashlib.sha256((ROOT/'reports/parametros_calibrados.json').read_bytes()).hexdigest()==rapid['base_parameters_file_sha256']
        assert rapid['final_validation_evaluated'] is False
