import numpy as np
import pytest
from pathlib import Path
import pandas as pd
from src.rk4_solver import Parameters
from src.simulation_engine import simulate, load_window

ROOT = Path(__file__).resolve().parents[1]


def test_conservation_transfers_and_reproducibility():
    initial = [100,40,20,1000]
    arrivals = np.random.default_rng(42).integers(0,30,240)
    p = Parameters(.4,.2,.1)
    r = simulate(initial,arrivals,p)
    repeated = simulate(initial,arrivals,p)
    np.testing.assert_array_equal(r.states,repeated.states)
    np.testing.assert_array_equal(r.transfers,repeated.transfers)
    expected = sum(initial)+np.r_[0,np.cumsum(arrivals)]
    assert (np.abs(r.conservation_errors) <= 1e-8*np.maximum(1,expected)).all()
    np.testing.assert_allclose(r.states.sum(axis=1),expected,rtol=0,atol=1e-9)
    f = r.transfers
    changes = np.column_stack([arrivals-f[:,0],f[:,0]-f[:,1],f[:,1]-f[:,2],f[:,2]])
    np.testing.assert_allclose(np.diff(r.states,axis=0),changes,rtol=0,atol=1e-10)
    assert np.isfinite(r.states).all() and (r.states>=0).all()
    assert (np.diff(r.states[:,3]) >= 0).all()
    assert (r.transfers>=0).all()
    assert len(r.times)==len(arrivals)+1


def test_real_initial_and_right_endpoint_alignment():
    w = load_window(ROOT/'data/processed','2018-03-02 22:00:00','2018-03-03 02:00:00')
    np.testing.assert_array_equal(w.initial,[113,586,3005,53963])
    assert w.initial.sum() == 57667
    f = pd.read_csv(ROOT/'data/processed/eventos_por_hora.csv',parse_dates=['corte_horario'])
    selected = f.loc[(f.corte_horario>w.cuts[0])&(f.corte_horario<=w.cuts[-1]),'compras']
    np.testing.assert_array_equal(w.arrivals, selected.to_numpy())
    assert len(w.cuts) == 5 and len(w.arrivals) == 4
    # Sólo lectura histórica; no se simula ni evalúa la ventana de validación.


def test_different_windows_and_empty_simulation():
    w = load_window(ROOT/'data/processed','2016-09-15 12:00:00','2016-09-15 14:00:00')
    np.testing.assert_array_equal(w.arrivals,[1,0])
    w0 = load_window(ROOT/'data/processed',w.cuts[-1],w.cuts[-1])
    r = simulate(w0.initial,w0.arrivals,Parameters(0,0,0))
    assert r.states.shape == (1,4) and r.transfers.shape == (0,3)


@pytest.mark.parametrize('start,end',[('2018-03-02 22:30','2018-03-03'),('1900-01-01','2018-03-03'),('2018-03-03','2018-03-02')])
def test_invalid_window(start,end):
    with pytest.raises(ValueError):
        load_window(ROOT/'data/processed',start,end)


@pytest.mark.parametrize('fault',['duplicate','gap','unsorted','mismatch','missing_column','wrong_purchases','invalid_state'])
def test_corrupt_hourly_data(tmp_path,fault):
    directory=ROOT/'data/processed'
    f=pd.read_csv(directory/'eventos_por_hora.csv').head(5)
    l=pd.read_csv(directory/'niveles_reales_4_tanques.csv').head(5)
    if fault=='duplicate': f.loc[1,'corte_horario']=f.loc[0,'corte_horario']
    elif fault=='gap': f=f.drop(index=2); l=l.drop(index=2)
    elif fault=='unsorted': f=f.iloc[::-1]
    elif fault=='mismatch': f['corte_horario']=pd.to_datetime(f.corte_horario)+pd.Timedelta(hours=1)
    elif fault=='missing_column': f=f.drop(columns='compras')
    elif fault=='wrong_purchases': f.loc[1,'compras']=42
    elif fault=='invalid_state': l.loc[1,'X1']=-1
    f.to_csv(tmp_path/'eventos_por_hora.csv',index=False)
    l.to_csv(tmp_path/'niveles_reales_4_tanques.csv',index=False)
    with pytest.raises(ValueError):
        load_window(tmp_path,'2016-09-15 11:00','2016-09-15 15:00')
