"""Auditoría y reconstrucción vectorizada de una cohorte histórica entregada."""
from pathlib import Path
import hashlib
import zipfile
import numpy as np
import pandas as pd

DATES = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date', 'order_delivered_customer_date']
ALL_DATES = DATES + ['order_estimated_delivery_date']
FLOWS = ['compras', 'aprobaciones', 'despachos', 'entregas']


def read_orders(archive):
    """Lee directamente del ZIP; no modifica ni extrae los datos originales."""
    with zipfile.ZipFile(archive) as z:
        members = z.namelist()
        matches = [n for n in members if Path(n).name == 'olist_orders_dataset.csv']
        if len(matches) != 1:
            raise ValueError('Se requiere exactamente un CSV de pedidos')
        with z.open(matches[0]) as f:
            raw = pd.read_csv(f, dtype=str)
    return raw, members


def audit_and_clean(raw):
    df = raw.copy()
    quality = []
    for col in ALL_DATES:
        missing = raw[col].isna() | raw[col].str.strip().eq('')
        df[col] = pd.to_datetime(raw[col], errors='coerce', format='%Y-%m-%d %H:%M:%S')
        quality.append({'columna': col, 'faltantes': int(missing.sum()), 'invalidas_no_vacias': int((~missing & df[col].isna()).sum()), 'minimo': df[col].min(), 'maximo': df[col].max()})
    chronology = pd.DataFrame({f'{a} > {b}': df[a].gt(df[b]) for a, b in zip(DATES[:-1], DATES[1:])})
    # Exclusiones mutuamente excluyentes, aplicadas en este orden.
    criteria = [('identificador_faltante', df.order_id.isna() | df.order_id.str.strip().eq('')),
                ('identificador_duplicado_posterior', df.order_id.duplicated()),
                ('estado_distinto_delivered', df.order_status.ne('delivered')),
                ('fecha_principal_faltante_o_invalida', df[DATES].isna().any(axis=1)),
                ('cronologia_invalida', chronology.any(axis=1))]
    remaining = pd.Series(True, index=df.index)
    excluded = []
    for reason, mask in criteria:
        excluded.append({'criterio': reason, 'detectados_independientes': int(mask.sum()), 'excluidos_secuenciales': int((remaining & mask).sum())})
        remaining &= ~mask
    clean = df.loc[remaining].sort_values(['order_purchase_timestamp', 'order_id']).reset_index(drop=True)
    durations = pd.DataFrame({name: (clean[b] - clean[a]).dt.total_seconds()/3600 for name, a, b in zip(['compra_aprobacion', 'aprobacion_despacho', 'despacho_entrega'], DATES[:-1], DATES[1:])})
    stats = durations.describe(percentiles=[.05, .25, .5, .75, .90, .95, .99]).T
    return df, clean, pd.DataFrame(quality), pd.DataFrame(excluded), chronology, stats


def reconstruct(clean):
    """Cortes t cada hora; acumulados incluyen evento <= t, flujos en (t-1h,t].

    Se añade un corte inicial vacío y uno final que incluye el último evento.
    Las marcas de eventos no se redondean: searchsorted opera sobre originales.
    """
    if clean.empty:
        raise ValueError('Cohorte vacía')
    start = clean[DATES].min().min().floor('h') - pd.Timedelta(hours=1)
    end = clean[DATES].max().max().ceil('h')
    grid = pd.date_range(start, end, freq='h')
    cumulative = pd.DataFrame(index=grid)
    for name, col in zip(FLOWS, DATES):
        events = clean[col].to_numpy(dtype='datetime64[ns]')
        cumulative[name] = np.searchsorted(np.sort(events), grid.to_numpy(dtype='datetime64[ns]'), side='right')
    flows = cumulative.diff().fillna(cumulative).astype('int64')
    for name in FLOWS:
        flows[name + '_por_hora'] = flows[name].astype(float)  # intervalos de exactamente 1 h
    levels = pd.DataFrame({'A': cumulative.compras, 'B': cumulative.aprobaciones, 'C': cumulative.despachos, 'D': cumulative.entregas})
    levels['X1'] = levels.A - levels.B
    levels['X2'] = levels.B - levels.C
    levels['X3'] = levels.C - levels.D
    levels['X4'] = levels.D
    for table in (flows, levels):
        table.index.name = 'corte_horario'
    validate(flows, levels, len(clean))
    return flows, levels


def validate(flows, levels, n):
    x = levels[['X1', 'X2', 'X3', 'X4']]
    assert (x >= 0).all().all(), 'Niveles negativos'
    assert x.sum(axis=1).eq(levels.A).all(), 'No se conserva la población'
    delta = x.diff().fillna(x)
    expected = pd.DataFrame({'X1': flows.compras-flows.aprobaciones, 'X2': flows.aprobaciones-flows.despachos, 'X3': flows.despachos-flows.entregas, 'X4': flows.entregas})
    assert np.array_equal(delta.to_numpy(), expected.to_numpy()), 'Transferencias incoherentes'
    assert levels.iloc[-1][['A','B','C','D']].eq(n).all()
    assert levels.iloc[-1][['X1','X2','X3']].eq(0).all()


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()
