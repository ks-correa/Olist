"""Calibración: datos artificiales controlados y aislamiento de entrenamiento real."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest
from src.calibration import (TrainingData,load_training,exposure_estimates,analytical_trajectory,
    residual_vector,fit_parameters,TRAIN_START,TRAIN_END,N_TRAIN)
from src.rk4_solver import Parameters
from src.simulation_engine import simulate
from src.agent_model import simulate_agentpy
from src.calibration_metrics import metrics,level_metrics,calendar_diagnostics

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def synthetic():
    arrivals=np.random.default_rng(123).integers(0,50,160).astype(float)
    initial=np.array([30.,20.,10.,1.])
    known=Parameters(.2,.07,.02)
    # Datos matemáticos generados por RK4 fino, no eventos ni resultados de Olist.
    states=simulate(initial,arrivals,known,32).states
    cuts=pd.date_range('2017-01-01',periods=len(arrivals)+1,freq='h')
    return TrainingData(cuts,arrivals,states,np.zeros((len(arrivals),3))),known


def test_residual_dimensions_alignment_and_scales(synthetic):
    data,p=synthetic
    assert analytical_trajectory(data.observed[0],data.arrivals,p).shape==data.observed.shape
    residual=residual_vector(p.array(),data)
    expected=((analytical_trajectory(data.observed[0],data.arrivals,p)[1:,:3]-data.observed[1:,:3])/data.scales).ravel()
    np.testing.assert_array_equal(residual,expected)
    assert residual.shape==(3*len(data.arrivals),)
    changed=data.observed.copy();changed[1:,3]+=1e6
    altered=TrainingData(data.cuts,data.arrivals,changed,data.flows)
    np.testing.assert_array_equal(residual,residual_vector(p.array(),altered))
    with pytest.raises(ValueError):
        residual_vector(p.array(),data,[1,0,1])


def test_recovery_and_reproducible_calibration(synthetic):
    data,known=synthetic
    p,info=fit_parameters(data,known.array()*1.5)
    second,info2=fit_parameters(data,known.array()*1.5)
    assert info['success'] and info2['success']
    np.testing.assert_allclose(p.array(),known.array(),rtol=2e-6,atol=1e-9)
    np.testing.assert_array_equal(p.array(),second.array())
    assert info['cost_half_sse']==info2['cost_half_sse']
    assert info['actual_residual_calls']>=info['nfev']


@pytest.mark.parametrize('theta',[[-1,.1,.1],[np.nan,.1,.1],[.1,np.inf,.1],[1,2]])
def test_reject_invalid_calibration_parameters(synthetic,theta):
    data,_=synthetic
    with pytest.raises(ValueError): residual_vector(theta,data)


@pytest.mark.parametrize('kind',['nan','negative','wrong_shape','duplicate','gap','reserved'])
def test_reject_corrupt_training(kind):
    cuts=pd.date_range('2017-01-01',periods=4,freq='h')
    arrivals=np.ones(3);observed=np.ones((4,4));flows=np.ones((3,3))
    if kind=='nan': observed[1,0]=np.nan
    elif kind=='negative': arrivals[0]=-1
    elif kind=='wrong_shape': observed=observed[:-1]
    elif kind=='duplicate': cuts=pd.DatetimeIndex([cuts[0],cuts[0],cuts[2],cuts[3]])
    elif kind=='gap': cuts=pd.date_range('2017-01-01',periods=4,freq='2h')
    elif kind=='reserved': cuts=pd.date_range(TRAIN_END,periods=4,freq='h')
    with pytest.raises(ValueError): TrainingData(cuts,arrivals,observed,flows)


def test_training_loader_and_no_future_rows(tmp_path):
    original=load_training(ROOT/'data/processed')
    assert len(original.arrivals)==N_TRAIN
    assert original.cuts[0]==TRAIN_START and original.cuts[-1]==TRAIN_END
    np.testing.assert_array_equal(original.observed[0],[0,0,0,0])
    assert original.arrivals.sum()==57667
    # Incluso filas reservadas corruptas no son leídas ni verificadas por calibración.
    for filename in ['eventos_por_hora.csv','niveles_reales_4_tanques.csv']:
        with (ROOT/'data/processed'/filename).open(encoding='utf-8') as f:
            prefix=''.join(next(f) for _ in range(N_TRAIN+2))
        (tmp_path/filename).write_text(prefix+'FUTURO,NO,DEBE,USARSE\n',encoding='utf-8')
    isolated=load_training(tmp_path)
    np.testing.assert_array_equal(original.arrivals,isolated.arrivals)
    np.testing.assert_array_equal(original.observed,isolated.observed)
    p=Parameters(.1,.01,.004)
    np.testing.assert_array_equal(residual_vector(p.array(),original),residual_vector(p.array(),isolated))


def test_preliminary_exact_exposure_censoring_and_future_independence(tmp_path):
    cols=['order_purchase_timestamp','order_approved_at','order_delivered_carrier_date','order_delivered_customer_date']
    raw=pd.DataFrame([
        ['2017-01-01 00:10:00','2017-01-01 00:20:00','2017-01-01 00:30:00','2017-01-01 00:40:00'],
        ['2017-01-01 00:00:00','2017-01-01 02:00:00','2017-01-01 03:00:00','2017-01-01 04:00:00']
    ],columns=cols)
    path=tmp_path/'orders.csv';raw.to_csv(path,index=False)
    a=exposure_estimates(path,'2017-01-01','2017-01-01 01:00:00')
    np.testing.assert_allclose(a.exposicion_pedidos_hora,[1+1/6,1/6,1/6])
    np.testing.assert_array_equal(a.transferencias,[1,1,1])
    np.testing.assert_array_equal(a.pendientes_al_corte,[1,0,0])
    for col in cols:
        raw.loc[raw[col]>'2017-01-01 01:00:00',col]='2099-12-31 23:59:59'
    raw.to_csv(path,index=False)
    b=exposure_estimates(path,'2017-01-01','2017-01-01 01:00:00')
    pd.testing.assert_frame_equal(a,b)
    with pytest.raises(ValueError): exposure_estimates(path,'2017-01-01','2019-01-01')


def test_no_information_exposure_rejected(tmp_path):
    columns=['order_purchase_timestamp','order_approved_at','order_delivered_carrier_date','order_delivered_customer_date']
    path=tmp_path/'orders.csv'
    pd.DataFrame([['2019-01-01 00:00:00']*4],columns=columns).to_csv(path,index=False)
    with pytest.raises(ValueError,match='Sin exposición'):
        exposure_estimates(path,'2017-01-01','2017-01-02')


def test_analytical_zero_coefficients_and_causal_recurrence():
    p=Parameters(0,0,0)
    states=analytical_trajectory([1,2,3,4],[0,10,0,20],p)
    np.testing.assert_array_equal(states[:,0],[1,1,11,11,31])
    np.testing.assert_array_equal(states[:,1:],np.tile([2,3,4],(5,1)))
    near=analytical_trajectory([100,0,0,0],np.zeros(8),Parameters(1e-8,0,0))
    np.testing.assert_allclose(near[:,0],100*np.exp(-1e-8*np.arange(9)),atol=1e-12)
    zero=analytical_trajectory([100,0,0,0],np.zeros(8),Parameters(.4,0,0))
    np.testing.assert_allclose(zero[:,0],100*np.exp(-.4*np.arange(9)),atol=1e-12)


def test_metrics_exact_values_and_invalid_data():
    table=metrics(np.array([[1],[3]]),np.array([[2],[1]]),['x'],[2])
    row=table.iloc[0]
    assert row.MAE==1.5 and row.RMSE==np.sqrt(2.5)
    assert row.NMAE==.75 and row.error_nivel_maximo==-1 and row.error_final==-2
    assert row.sesgo_medio==-.5 and row.error_absoluto_maximo==2
    with pytest.raises(ValueError): metrics([[np.nan]],[[1]],['x'])
    with pytest.raises(ValueError): metrics([[1]],[[1],[2]],['x'])


def test_calibrated_parameters_conservation_convergence_and_engine_equivalence():
    metadata=json.loads((ROOT/'reports/parametros_calibrados.json').read_text(encoding='utf-8'))
    assert metadata['final_validation_evaluated'] is False
    p=Parameters(*(metadata[key] for key in ['alpha','beta','gamma']))
    arrivals=np.random.default_rng(2).integers(0,40,80)
    initial=[30,100,300,400]
    exact=analytical_trajectory(initial,arrivals,p)
    runs=[simulate(initial,arrivals,p,n) for n in (4,8,16)]
    errors=[np.max(np.abs(r.states-exact)) for r in runs]
    assert errors[0]>errors[1]>errors[2]
    for r in runs:
        assert r.max_conservation_error<=1e-8*(sum(initial)+arrivals.sum())
    diff=runs[1].states-runs[2].states
    assert np.max(np.abs(diff))<=.1
    scale=np.r_[metadata['scales_pending'],1]
    assert (np.sqrt(np.mean(diff**2,axis=0))/scale<=.001).all()
    agents,_=simulate_agentpy(initial,arrivals,p,4)
    np.testing.assert_array_equal(agents.states,runs[0].states)
    np.testing.assert_array_equal(agents.transfers,runs[0].transfers)


def test_sections_and_calendar_alignment(synthetic):
    data,p=synthetic
    block=data.section(100,160)
    np.testing.assert_array_equal(block.observed[0],data.observed[100])
    np.testing.assert_array_equal(block.arrivals,data.arrivals[100:160])
    sim=analytical_trajectory(block.observed[0],block.arrivals,p)
    assert len(level_metrics(block,sim))==5
    assert not calendar_diagnostics(block.cuts[1:],block.observed[1:,:3],sim[1:,:3]).empty
    with pytest.raises(ValueError): level_metrics(block,sim[:-1])
    with pytest.raises(ValueError): calendar_diagnostics(block.cuts,block.observed[:-1,:3],sim[:,:3])
