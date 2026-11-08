from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from src.data_processing import read_orders, audit_and_clean, reconstruct, DATES, FLOWS

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def result():
    raw, _ = read_orders(ROOT/'Brazilian_E-Commerce_Public_Dataset_by_Olist.zip')
    clean = audit_and_clean(raw)[1]
    flows, levels = reconstruct(clean)
    return raw, clean, flows, levels

def test_cohort_chronology(result):
    raw, clean, _, _ = result
    assert len(raw) == 99441
    assert len(clean) == 95082
    assert clean.order_id.is_unique
    assert clean[DATES].notna().all().all()
    assert clean.order_status.eq('delivered').all()
    for a,b in zip(DATES[:-1], DATES[1:]):
        assert clean[a].le(clean[b]).all()

def test_nonnegative_and_terminal(result):
    _, clean, _, levels = result
    assert levels[['X1','X2','X3','X4']].ge(0).all().all()
    assert levels.X4.diff().dropna().ge(0).all()
    assert levels.iloc[-1][['X1','X2','X3','X4']].tolist() == [0,0,0,len(clean)]

def test_conservation(result):
    levels = result[3]
    assert levels[['X1','X2','X3','X4']].sum(axis=1).eq(levels.A).all()

def test_transfers(result):
    flows, levels = result[2:]
    dx = levels[['X1','X2','X3','X4']].diff().fillna(0)
    expected = np.column_stack([flows.compras-flows.aprobaciones,flows.aprobaciones-flows.despachos,flows.despachos-flows.entregas,flows.entregas])
    np.testing.assert_array_equal(dx, expected)
    np.testing.assert_array_equal(flows[FLOWS].cumsum(), levels[['A','B','C','D']])

def test_reproducibility(result):
    raw, clean, flows, levels = result
    repeated = audit_and_clean(raw)[1]
    pd.testing.assert_frame_equal(clean, repeated)
    f2, l2 = reconstruct(repeated)
    pd.testing.assert_frame_equal(flows, f2)
    pd.testing.assert_frame_equal(levels, l2)

def test_hour_boundary_exact_events():
    # Eventos verificables de prueba; no se incorporan al dataset ni a sus resultados.
    clean = pd.DataFrame({DATES[0]: pd.to_datetime(['2020-01-01 10:00:00','2020-01-01 10:00:01']), DATES[1]: pd.to_datetime(['2020-01-01 10:00:00','2020-01-01 10:59:59']), DATES[2]: pd.to_datetime(['2020-01-01 11:00:00','2020-01-01 11:00:01']), DATES[3]: pd.to_datetime(['2020-01-01 11:00:00','2020-01-01 12:00:00'])})
    flows, levels = reconstruct(clean)
    assert levels.loc['2020-01-01 10:00:00', ['A','B','C','D']].tolist() == [1,1,0,0]
    assert flows.loc['2020-01-01 11:00:00', FLOWS].tolist() == [1,1,1,1]
    assert levels.iloc[-1].X4 == 2
