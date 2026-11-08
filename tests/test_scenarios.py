"""Escenarios oficiales y pruebas matemáticas de sus indicadores."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest
from src.scenarios import (load_base_parameters,official_definitions,run_official_scenarios,
    load_scenario_window,check_structural,HORIZONS)
from src.scenario_metrics import cumulative_areas,horizon_indicators,percent_change,comparisons
from src.simulation_engine import HistoricalWindow,simulate
from src.rk4_solver import Parameters,RapidParameters
from src.validation import sha256,FROZEN_THETA

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def base():
    return load_base_parameters(ROOT/'reports')


@pytest.fixture(scope='module')
def window():
    return HistoricalWindow(pd.date_range('2017-01-01',periods=49,freq='h'),
        np.array([100.,200.,300.,400.]),np.tile([10.,0.,20.,2.,0.,5.],8))


@pytest.fixture(scope='module')
def runs(window,base):
    return run_official_scenarios(window,base,(1,24,48))


def test_exactly_three_definitions_and_exclusive_interventions(base):
    scenarios=official_definitions(base)
    assert [s.code for s in scenarios]==['E0','E1','E2']
    np.testing.assert_array_equal(scenarios[0].parameters.array(),FROZEN_THETA)
    np.testing.assert_array_equal(scenarios[1].parameters.array(),[base.alpha,1.2*base.beta,base.gamma])
    np.testing.assert_array_equal(scenarios[2].parameters.array(),[base.alpha,base.beta,1.2*base.gamma])
    with pytest.raises(ValueError): official_definitions(RapidParameters(*base.array(),.1))
    with pytest.raises(ValueError): official_definitions(Parameters(.1,.01,.004))


def test_identical_inputs_initials_and_horizons(window,runs):
    for run in runs:
        np.testing.assert_array_equal(run.window.initial,window.initial)
        np.testing.assert_array_equal(run.window.arrivals,window.arrivals)
        np.testing.assert_array_equal(run.result.states[0],window.initial)
        assert run.window.cuts.equals(window.cuts)
        assert not np.shares_memory(run.window.arrivals,window.arrivals)
        assert run.indicators.horizonte_horas.tolist()==[1,24,48]
        assert run.checks['inicializaciones']==1


def test_conservation_and_pending_delivery_identity(runs,window):
    expected=window.initial.sum()+np.r_[0,np.cumsum(window.arrivals)]
    baseline=runs[0].result.states
    for run in runs:
        states=run.result.states
        np.testing.assert_allclose(states.sum(axis=1),expected,rtol=0,atol=1e-10)
        delta_deliveries=states[:,3]-baseline[:,3]
        delta_pending=states[:,:3].sum(axis=1)-baseline[:,:3].sum(axis=1)
        np.testing.assert_allclose(delta_deliveries,-delta_pending,rtol=0,atol=1e-10)
    check_structural(runs)


def test_structural_dependencies_and_relocation(runs):
    baseline=runs[0].result.states;dispatch=runs[1].result.states;delivery=runs[2].result.states
    np.testing.assert_array_equal(dispatch[:,0],baseline[:,0])
    np.testing.assert_array_equal(delivery[:,:2],baseline[:,:2])
    assert (dispatch[:,1]<=baseline[:,1]+1e-12).all()
    assert (delivery[:,2]<=baseline[:,2]+1e-12).all()
    assert (dispatch[1:,2]>baseline[1:,2]).any()  # Adelanto de carga a transporte.


def test_exact_agentpy_rk4_and_reproducibility(runs,window):
    for run in runs:
        repeated=simulate(window.initial,window.arrivals,run.definition.parameters,4)
        np.testing.assert_array_equal(repeated.states,run.result.states)
        np.testing.assert_array_equal(repeated.transfers,run.result.transfers)
        assert run.checks['AgentPy_RK4_diferencia_estados']==0
        assert run.checks['AgentPy_RK4_diferencia_transferencias']==0
        assert run.checks['agentes']==4
        assert (repeated.states>=0).all() and (repeated.transfers>=0).all()
        assert (np.diff(repeated.states[:,3])>=0).all()


def test_areas_exact_constant_and_linear_functions():
    times=np.arange(5,dtype=float)
    states=np.column_stack([np.ones(5)*7,2+3*times])
    areas=cumulative_areas(times,states)
    np.testing.assert_array_equal(areas[:,0],7*times)
    np.testing.assert_array_equal(areas[:,1],2*times+1.5*times**2)
    np.testing.assert_array_equal(areas[0],[0,0])


def test_horizon_metrics_known_values_and_incremental_deliveries():
    r=simulate([1,2,3,1000],[2,0,4,0],Parameters(0,0,0),4)
    cuts=pd.date_range('2017-01-01',periods=5,freq='h')
    table=horizon_indicators(cuts,r,[1,4]).set_index('horizonte_horas')
    assert table.loc[4,'X1_area_pedidos_hora']==17
    assert table.loc[4,'X1_promedio']==4.25
    assert table.loc[4,'P_area_pedidos_hora']==37
    assert table.loc[4,'P_promedio']==9.25
    assert table.loc[4,'P_inicial']==6 and table.loc[4,'P_final']==12
    assert table.loc[4,'entregas_incrementales']==0
    assert table.loc[4,'X1_fecha_maximo']==str(cuts[3])


def test_integrated_transfer_and_delivery_indicators(runs):
    for run in runs:
        for row in run.indicators.itertuples(index=False):
            h=row.horizonte_horas
            assert row.entregas_incrementales==pytest.approx(run.result.states[h,3]-run.result.states[0,3],abs=1e-12)
            assert row.q34_acumulado==pytest.approx(row.entregas_incrementales,abs=1e-10)
            assert row.q12_acumulado==pytest.approx(run.result.transfers[:h,0].sum(),abs=1e-12)
            assert row.q23_media_por_hora==pytest.approx(run.result.transfers[:h,1].sum()/h,abs=1e-12)
            assert row.P_area_pedidos_hora==pytest.approx(row.X1_area_pedidos_hora+row.X2_area_pedidos_hora+row.X3_area_pedidos_hora,abs=1e-9)


@pytest.mark.parametrize('values',[(1,0),(0,0)])
def test_zero_reference_percentage_is_absent(values):
    assert percent_change(*values) is None


@pytest.mark.parametrize('value,reference',[(-1,1),(1,-1),(np.nan,1),(1,np.inf)])
def test_invalid_percentage_rejected(value,reference):
    with pytest.raises(ValueError): percent_change(value,reference)


def test_consistent_comparison_sign_and_zero_reference():
    assert percent_change(80,100)==-20 and percent_change(120,100)==20
    table=pd.DataFrame({'ventana':['case','case'],'escenario':['E0','E1'],
        'horizonte_horas':[1,1],'P_final':[100.,80.],'entregas_incrementales':[0.,20.]})
    difference=comparisons(table)
    row=difference.loc[(difference.escenario=='E1')&(difference.indicador=='P_final')].iloc[0]
    assert row.diferencia_absoluta==-20 and row.variacion_porcentual==-20
    missing=difference.loc[(difference.escenario=='E1')&(difference.indicador=='entregas_incrementales')].iloc[0]
    assert pd.isna(missing.variacion_porcentual)


@pytest.mark.parametrize('horizons',[[0],[5],[1,1],[True],[1.5]])
def test_invalid_horizons_rejected(horizons):
    result=simulate([1,2,3,4],[1,1,1,1],Parameters(0,0,0))
    with pytest.raises(ValueError):
        horizon_indicators(pd.date_range('2017-01-01',periods=5,freq='h'),result,horizons)


def test_real_windows_verified_without_recalibration():
    main=load_scenario_window(ROOT/'data/processed')
    assert len(main.arrivals)==5488 and main.arrivals.sum()==37415
    np.testing.assert_array_equal(main.initial,[113,586,3005,53963])
    assert HORIZONS==(168,720,1440,5488)
    auxiliary=load_scenario_window(ROOT/'data/processed','2018-01-01','2018-02-01')
    assert len(auxiliary.arrivals)==744 and len(auxiliary.cuts)==745


def test_validation_results_preserved():
    j=json.loads((ROOT/'reports/resumen_validacion.json').read_text(encoding='utf-8'))
    assert j['decision']=='C'
    for name,fingerprint in j['sha256_protected_inputs'].items():
        assert sha256(ROOT/name)==fingerprint
    path=ROOT/'reports/comparacion_escenarios.json'
    if path.exists():
        meta=json.loads(path.read_text(encoding='utf-8'))
        assert meta['base_validation_category']=='C' and meta['parameters_recalibrated'] is False
        for name,fingerprint in meta['sha256_preserved_files'].items():
            assert sha256(ROOT/name)==fingerprint
