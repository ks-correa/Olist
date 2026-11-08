"""Errors and serial diagnostics; normalization must be supplied by training."""
import numpy as np
import pandas as pd
from scipy.stats import chi2
from .calibration_metrics import metrics


def goodness(observed, simulated, scales):
    y, x = np.asarray(observed, float), np.asarray(simulated, float)
    table = metrics(y, x, ['X1', 'X2', 'X3'], scales)
    sse = ((x-y)**2).sum(axis=0)
    sst = ((y-y.mean(axis=0))**2).sum(axis=0)
    table['R2'] = np.divide(sse, sst, out=np.full(3, np.nan), where=sst>0)*-1+1
    table['n'] = len(y)
    table['error_final_absoluto'] = np.abs(x[-1]-y[-1])
    table['pico_limite'] = np.maximum(1, .2*y.max(axis=0))
    table['final_limite'] = np.maximum(1, .2*np.asarray(scales))
    table['cumple'] = ((table.NRMSE <= .30) & (table.NMAE <= .20)
                        & (table.error_nivel_maximo_absoluto <= table.pico_limite)
                        & (table.error_final_absoluto <= table.final_limite))
    table['fraccion_sobreestimacion'] = ((x-y)>0).mean(axis=0)
    return table


def residual_diagnostics(errors, lags=(24, 168)):
    e = np.asarray(errors, float)
    if e.ndim != 2 or e.shape[1] != 3 or not np.isfinite(e).all() or len(e)<2:
        raise ValueError('Residuos inválidos')
    rows, acfs = [], []
    for j in range(3):
        v = e[:, j]-e[:, j].mean(); denom = v@v
        maxlag = min(max(lags), len(v)-1)
        acf = np.array([v[k:]@v[:-k]/denom if denom else np.nan for k in range(1, maxlag+1)])
        acfs.append(acf)
        for lag in lags:
            if lag > maxlag:
                continue
            q = len(v)*(len(v)+2)*np.sum(acf[:lag]**2/(len(v)-np.arange(1,lag+1)))
            rows.append(dict(variable=f'X{j+1}',lag=lag,Q=q,p_descriptivo=chi2.sf(q,lag),n=len(v)))
    return pd.DataFrame(rows), np.asarray(acfs)


def grouped_errors(cuts, observed, simulated, scales):
    dates = pd.DatetimeIndex(cuts)
    groups = {'mes': dates.strftime('%Y-%m'), 'hora': dates.hour,
              'dia_semana': dates.dayofweek, 'bloque_168h': np.arange(len(dates))//168}
    tables = []
    for kind, labels in groups.items():
        for value in np.unique(labels):
            mask = labels == value
            t = goodness(observed[mask], simulated[mask], scales)
            t['grupo'] = kind; t['valor'] = str(value)
            tables.append(t)
    return pd.concat(tables, ignore_index=True)


def kaplan_meier(durations, completed):
    """Right censoring, ties process events before censoring; no p-value."""
    t, d = np.asarray(durations, float), np.asarray(completed, bool)
    if t.shape != d.shape or t.ndim != 1 or not len(t) or not np.isfinite(t).all() or (t<0).any():
        raise ValueError('Duraciones inválidas')
    unique, inv = np.unique(t, return_inverse=True)
    events = np.bincount(inv, weights=d, minlength=len(unique))
    counts = np.bincount(inv, minlength=len(unique))
    risk = len(t)-np.r_[0, np.cumsum(counts)[:-1]]
    survival = np.cumprod(1-events/risk)
    return pd.DataFrame(dict(horas=unique, en_riesgo=risk, eventos=events,
                             censuras=counts-events, supervivencia=survival))
