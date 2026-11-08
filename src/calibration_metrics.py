"""Métricas descriptivas de ajuste/evaluación interna; nunca accede a la reserva."""
import numpy as np
import pandas as pd


def metrics(observed, simulated, names, scales=None):
    y,x=np.asarray(observed,dtype=float),np.asarray(simulated,dtype=float)
    if y.shape!=x.shape or y.ndim!=2 or len(y)==0 or y.shape[1]!=len(names):
        raise ValueError('Dimensiones de métricas incompatibles')
    if not np.isfinite(y).all() or not np.isfinite(x).all():
        raise ValueError('Métricas con datos no finitos')
    scales=np.maximum(1,y.mean(axis=0)) if scales is None else np.asarray(scales,dtype=float)
    if scales.shape!=(len(names),) or not np.isfinite(scales).all() or (scales<=0).any():
        raise ValueError('Escalas inválidas')
    error=x-y
    mae=np.mean(np.abs(error),axis=0); rmse=np.sqrt(np.mean(error**2,axis=0))
    return pd.DataFrame({'variable':names,'escala':scales,'MAE':mae,'RMSE':rmse,
        'NMAE':mae/scales,'NRMSE':rmse/scales,'error_absoluto_maximo':np.max(np.abs(error),axis=0),
        'maximo_observado':y.max(axis=0),'maximo_simulado':x.max(axis=0),
        'error_nivel_maximo':x.max(axis=0)-y.max(axis=0),
        'error_nivel_maximo_absoluto':np.abs(x.max(axis=0)-y.max(axis=0)),
        'error_final':error[-1],'sesgo_medio':error.mean(axis=0)})


def level_metrics(data, simulated, scales=None):
    y=data.observed.copy(); x=np.asarray(simulated,dtype=float).copy()
    if x.shape!=y.shape:
        raise ValueError('Trayectoria no alineada con observaciones')
    y[:,3]-=y[0,3]; x[:,3]-=x[0,3]
    y=np.column_stack([y,y[:,:3].sum(axis=1)])
    x=np.column_stack([x,x[:,:3].sum(axis=1)])
    return metrics(y[1:],x[1:],['X1','X2','X3','X4_incremental','P'],scales)


def calendar_diagnostics(cuts, observed, simulated):
    y=np.asarray(observed); x=np.asarray(simulated)
    if y.shape!=x.shape or y.shape!=(len(cuts),3) or not np.isfinite(y).all() or not np.isfinite(x).all():
        raise ValueError('Diagnóstico desalineado o no finito')
    rows=[]
    groups={'mes':pd.DatetimeIndex(cuts).strftime('%Y-%m'),
            'hora':pd.DatetimeIndex(cuts).hour,'dia_semana':pd.DatetimeIndex(cuts).day_of_week}
    for kind,values in groups.items():
        for value in np.unique(values):
            mask=values==value
            table=metrics(y[mask],x[mask],['X1','X2','X3'])
            table['grupo']=kind;table['valor']=str(value);table['n']=int(mask.sum())
            rows.append(table)
    return pd.concat(rows,ignore_index=True)
