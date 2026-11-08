"""Indicadores temporales de escenarios: pedidos, horas y pedidos·hora."""
import numpy as np
import pandas as pd


def cumulative_areas(times,states):
    """Regla trapezoidal sobre cortes horarios; no usa etapas RK4 ocultas."""
    t=np.asarray(times,dtype=float);x=np.asarray(states,dtype=float)
    if t.ndim!=1 or x.ndim!=2 or len(t)!=len(x) or len(t)<2:
        raise ValueError('Dimensiones inválidas para cuadratura')
    if not np.isfinite(t).all() or not np.isfinite(x).all() or (x<0).any() or (np.diff(t)<=0).any():
        raise ValueError('Cuadratura requiere estados finitos no negativos y tiempos crecientes')
    increments=.5*(x[1:]+x[:-1])*np.diff(t)[:,None]
    return np.vstack([np.zeros(x.shape[1]),np.cumsum(increments,axis=0)])


def percent_change(value,reference):
    """100*(escenario−base)/base; cero no tiene porcentaje definido."""
    if not np.isfinite(value) or not np.isfinite(reference) or value<0 or reference<0:
        raise ValueError('Comparación requiere magnitudes finitas no negativas')
    return None if reference==0 else float(100*(value-reference)/reference)


def horizon_indicators(cuts,result,horizons):
    cuts=pd.DatetimeIndex(cuts)
    if len(cuts)!=len(result.states) or len(cuts)<2 or cuts.hasnans or cuts.has_duplicates:
        raise ValueError('Fechas y trayectoria desalineadas')
    if not ((cuts[1:]-cuts[:-1])==pd.Timedelta(hours=1)).all() or not np.array_equal(result.times,np.arange(len(cuts))):
        raise ValueError('Se requieren cortes horarios alineados al tiempo del motor')
    horizons=list(horizons)
    if len(set(horizons))!=len(horizons) or not horizons:
        raise ValueError('Horizontes vacíos o duplicados')
    for h in horizons:
        if isinstance(h,(bool,np.bool_)) or not isinstance(h,(int,np.integer)) or h<1 or h>=len(cuts):
            raise ValueError('Horizonte fuera de la trayectoria o no entero')
    pending=np.column_stack([result.states[:,:3],result.states[:,:3].sum(axis=1)])
    areas=cumulative_areas(result.times,pending)
    rows=[]
    for h in horizons:
        levels=pending[:h+1]
        delivered=float(result.states[h,3]-result.states[0,3])
        cumulative_flows=result.transfers[:h].sum(axis=0)
        row={'horizonte_horas':h,'fecha_horizonte':str(cuts[h]),'compras_acumuladas':float(result.arrivals[:h].sum()),
             'entregas_incrementales':delivered}
        for i,name in enumerate(['X1','X2','X3','P']):
            row[name+'_inicial']=float(levels[0,i]);row[name+'_final']=float(levels[-1,i])
            row[name+'_maximo']=float(levels[:,i].max())
            row[name+'_fecha_maximo']=str(cuts[int(np.argmax(levels[:,i]))])
            row[name+'_area_pedidos_hora']=float(areas[h,i])
            row[name+'_promedio']=float(areas[h,i]/h)
        for i,name in enumerate(['q12','q23','q34']):
            row[name+'_acumulado']=float(cumulative_flows[i])
            row[name+'_media_por_hora']=float(cumulative_flows[i]/h)
        rows.append(row)
    return pd.DataFrame(rows)


def comparisons(indicators):
    """Diferencias para todos los niveles/áreas/medias/flujos, con fórmula única."""
    rows=[]
    for window,group in indicators.groupby('ventana',sort=False):
        base=group.loc[group.escenario=='E0'].set_index('horizonte_horas')
        columns=[c for c in group.columns if c not in ['ventana','escenario','horizonte_horas','fecha_horizonte']
                 and pd.api.types.is_numeric_dtype(group[c])]
        for _,row in group.iterrows():
            h=int(row.horizonte_horas)
            if h not in base.index:
                raise ValueError('Falta referencia base para el horizonte')
            for col in columns:
                reference=float(base.loc[h,col]);value=float(row[col])
                rows.append({'ventana':window,'escenario':row.escenario,'horizonte_horas':h,
                    'indicador':col,'valor_base':reference,'valor_escenario':value,
                    'diferencia_absoluta':value-reference,'variacion_porcentual':percent_change(value,reference)})
    return pd.DataFrame(rows)
