"""Validación final: congelación, aislamiento de entradas y métricas reproducibles."""
from pathlib import Path
import json
import inspect
import numpy as np
import pandas as pd
import pytest
import scipy.optimize
import src.validation as validation
from src.validation import (load_validation,load_frozen,run_frozen,level_arrays,scored_levels,
    block_slices,acceptance,ValidationData,START,END,INTERVALS,FROZEN_THETA,FROZEN_SCALES,audit_trajectory,sha256)
from src.rk4_solver import Parameters,RapidParameters,NumericalError
from src.simulation_engine import simulate

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def data():
    return load_validation(ROOT/'data/processed')


@pytest.fixture(scope='module')
def frozen():
    return load_frozen(ROOT/'reports')


@pytest.fixture(scope='module')
def validated(data,frozen):
    return run_frozen(data,frozen[0])


def test_exact_reserved_window_alignment(data):
    assert len(data.arrivals)==5488 and len(data.cuts)==5489
    assert data.cuts[0]==START and data.cuts[-1]==END
    assert not data.cuts.has_duplicates
    np.testing.assert_array_equal(data.initial,[113,586,3005,53963])
    assert data.initial.sum()==57667
    assert data.arrivals.sum()==37415
    f=pd.read_csv(ROOT/'data/processed/eventos_por_hora.csv',parse_dates=['corte_horario'])
    selected=f.loc[(f.corte_horario>START)&(f.corte_horario<=END),'compras'].to_numpy()
    np.testing.assert_array_equal(data.arrivals,selected)


def test_parameters_and_scales_frozen(frozen):
    parameters,scales,_=frozen
    assert type(parameters) is Parameters
    np.testing.assert_array_equal(parameters.array(),FROZEN_THETA)
    np.testing.assert_array_equal(scales[:3],FROZEN_SCALES)
    assert scales[4]==1378.890650628759
    assert scales[3]==15774.909318128564


@pytest.mark.parametrize('fault',['parameter','scale','selected_model'])
def test_frozen_configuration_change_rejected(tmp_path,fault):
    for filename in ['parametros_calibrados.json','modelo_seleccionado_desarrollo.json',
                     'metricas_entrenamiento.csv','metricas_transferencias_entrenamiento.csv']:
        (tmp_path/filename).write_bytes((ROOT/'reports'/filename).read_bytes())
    filename='modelo_seleccionado_desarrollo.json' if fault=='selected_model' else 'parametros_calibrados.json'
    path=tmp_path/filename;j=json.loads(path.read_text(encoding='utf-8'))
    if fault=='parameter': j['alpha']*=1.01
    elif fault=='scale': j['scales_pending'][0]*=2
    else: j['model']='candidate'
    path.write_text(json.dumps(j),encoding='utf-8')
    with pytest.raises(ValueError): load_frozen(tmp_path)


def test_no_optimization_and_no_future_observed_inputs(monkeypatch,data,frozen):
    def forbidden(*args,**kwargs):
        raise AssertionError('Se intentó optimizar durante validación')
    monkeypatch.setattr(scipy.optimize,'least_squares',forbidden)
    n=48
    original=ValidationData(data.cuts[:n+1],data.initial,data.arrivals[:n],data.observed[:n+1],data.flows[:n])
    observed=original.observed.copy();observed[1:]+=1000
    altered=ValidationData(original.cuts,original.initial,original.arrivals,observed,original.flows+100)
    a,_=run_frozen(original,frozen[0]);b,_=run_frozen(altered,frozen[0])
    np.testing.assert_array_equal(a.states,b.states)
    np.testing.assert_array_equal(a.transfers,b.transfers)
    source=inspect.getsource(validation)
    assert 'from .calibration import' not in source and 'from .rapid_calibration import' not in source


def test_single_initialization_and_no_block_restarts(monkeypatch,data,frozen):
    calls=[]
    def tracked(initial,arrivals,parameters,substeps):
        calls.append((np.array(initial).copy(),len(arrivals),substeps))
        return simulate(initial,arrivals,parameters,substeps)
    monkeypatch.setattr(validation,'simulate',tracked)
    result,_=run_frozen(data,frozen[0])
    assert len(calls)==1 and calls[0][1:]==(5488,4)
    np.testing.assert_array_equal(calls[0][0],data.initial)
    expected=simulate(data.initial,data.arrivals,frozen[0],4)
    np.testing.assert_array_equal(result.states,expected.states)


def test_conservation_and_exact_agentpy_equivalence(data,validated):
    result,agents=validated
    np.testing.assert_array_equal(result.states,agents.states)
    np.testing.assert_array_equal(result.transfers,agents.transfers)
    total=data.initial.sum()+np.r_[0,np.cumsum(data.arrivals)]
    assert (np.abs(result.states.sum(axis=1)-total)<=1e-8*np.maximum(1,total)).all()
    assert audit_trajectory(result,data.initial,data.arrivals)<1e-7
    assert np.isfinite(result.states).all() and (result.states>=0).all()
    assert (result.transfers>=0).all() and (np.diff(result.states[:,3])>=0).all()
    assert result.states.shape==(5489,4) and result.transfers.shape==(5488,3)


def test_correct_segmentation_without_duplicated_targets(data):
    segments=block_slices()
    indices=np.concatenate([np.arange(INTERVALS+1)[segment] for _,segment in segments])
    np.testing.assert_array_equal(indices,np.arange(1,5489))
    assert all(len(data.cuts[segment])==1372 for _,segment in segments)
    assert len(np.unique(indices))==5488
    with pytest.raises(ValueError): block_slices(5487)


def test_metrics_and_incremental_terminal(data,frozen,validated):
    y,x=level_arrays(data,validated[0])
    assert y[0,3]==x[0,3]==0
    assert y[-1,3]==41119
    result=scored_levels(data.cuts[1:],y[1:],x[1:],frozen[1])
    np.testing.assert_array_equal(result.escala.to_numpy(),frozen[1])
    errors=x[1:,:3]-y[1:,:3]
    np.testing.assert_allclose(result.RMSE.to_numpy()[:3],np.sqrt(np.mean(errors**2,axis=0)))
    np.testing.assert_allclose(result.NMAE.to_numpy()[:3],np.mean(np.abs(errors),axis=0)/FROZEN_SCALES)
    assert result.loc[0,'fecha_maximo_observado']=='2018-04-24 17:00:00'
    assert len(result)==5
    for row in result.itertuples():
        assert START<pd.Timestamp(row.fecha_maximo_observado)<=END
        assert START<pd.Timestamp(row.fecha_maximo_simulado)<=END


def test_blocks_are_slices_of_single_trajectory(data,frozen,validated):
    y,x=level_arrays(data,validated[0]);tables=[]
    for name,segment in block_slices():
        table=scored_levels(data.cuts[segment],y[segment],x[segment],frozen[1]);table['bloque']=name
        tables.append(table)
    combined=pd.concat(tables)
    overall=scored_levels(data.cuts[1:],y[1:],x[1:],frozen[1])
    # Longitudes iguales: la media de MSE de los bloques reproduce el MSE global.
    for var in ['X1','X2','X3','X4_incremental','P']:
        rmse=combined.loc[combined.variable==var,'RMSE'].to_numpy()
        expected=overall.loc[overall.variable==var,'RMSE'].iloc[0]
        assert np.sqrt(np.mean(rmse**2))==pytest.approx(expected,rel=1e-14)
    verdict=acceptance(overall,combined)
    assert not verdict.cumple_criterios_cuantitativos.any()


def test_reproducible_trajectory_and_metrics(data,frozen,validated):
    repeated=simulate(data.initial,data.arrivals,frozen[0],4)
    np.testing.assert_array_equal(repeated.states,validated[0].states)
    np.testing.assert_array_equal(repeated.transfers,validated[0].transfers)
    y,a=level_arrays(data,repeated);_,b=level_arrays(data,validated[0])
    pd.testing.assert_frame_equal(scored_levels(data.cuts[1:],y[1:],a[1:],frozen[1]),
                                  scored_levels(data.cuts[1:],y[1:],b[1:],frozen[1]))


def test_reject_alternative_or_changed_parameters(data):
    with pytest.raises(ValueError): run_frozen(data,RapidParameters(*FROZEN_THETA,.2))
    with pytest.raises(ValueError): run_frozen(data,Parameters(.1,.01,.004))


def test_corrupt_validation_rejected(data):
    observed=data.observed[:3].copy();observed[1,0]=np.nan
    with pytest.raises(ValueError):
        ValidationData(data.cuts[:3],data.initial,data.arrivals[:2],observed,data.flows[:2])
    with pytest.raises(ValueError):
        ValidationData(data.cuts[:3],data.initial,data.arrivals[:1],data.observed[:3],data.flows[:2])


def test_final_summary_preserves_inputs():
    path=ROOT/'reports/resumen_validacion.json'
    if path.exists():
        j=json.loads(path.read_text(encoding='utf-8'))
        assert j['parameters_recalibrated'] is False and j['alternative_model_evaluated'] is False
        for name,expected in j['sha256_protected_inputs'].items():
            assert sha256(ROOT/name)==expected
