"""Lectura verificada de artefactos; no recalcula escenarios oficiales."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from .rk4_solver import Parameters
from .simulation_engine import simulate
from .agent_model import simulate_agentpy
from .scenario_metrics import cumulative_areas,horizon_indicators

WINDOWS={'principal':'Principal · marzo–octubre 2018','sensibilidad_enero':'Sensibilidad · enero 2018'}
LABELS={'E0':'E0 · Base','E1':'E1 · Despacho +20 %','E2':'E2 · Entrega +20 %'}
WARNING='Modelo de simulación académica. Validación categoría C: los resultados de escenarios son hipotéticos y no constituyen mejoras operativas comprobadas para Olist'
FILES=['reports/comparacion_escenarios.json','reports/trayectorias_escenarios.csv',
       'reports/transferencias_escenarios.csv','reports/indicadores_horizontes.csv',
       'reports/diferencias_escenarios.csv','reports/metricas_validacion.csv',
       'reports/resumen_validacion.json','reports/parametros_calibrados.json',
       'data/processed/niveles_reales_4_tanques.csv']


@dataclass
class ScenarioSeries:
    window: str
    code: str
    dates: np.ndarray
    states: np.ndarray
    flows: np.ndarray
    purchases: np.ndarray
    area: np.ndarray
    parameters: tuple
    custom: bool=False

    @property
    def duration(self):
        return len(self.states)-1

    @property
    def cumulative_purchases(self):
        return np.r_[0.,np.cumsum(self.purchases)]

    def frame(self):
        frame=pd.DataFrame(self.states,columns=['X1','X2','X3','X4'])
        frame.insert(0,'corte_horario',self.dates)
        frame.insert(0,'escenario',self.code)
        frame.insert(0,'ventana',self.window)
        frame['horas_desde_inicio']=np.arange(len(frame))
        frame['X4_incremental']=self.states[:,3]-self.states[0,3]
        frame['P']=self.states[:,:3].sum(axis=1)
        frame['area_acumulada_P']=self.area
        frame['compras_intervalo']=np.r_[np.nan,self.purchases]
        for i,name in enumerate(['q12_integrado','q23_integrado','q34_integrado']):
            frame[name]=np.r_[np.nan,self.flows[:,i]]
        frame['error_conservacion']=self.states.sum(axis=1)-self.states[0].sum()-self.cumulative_purchases
        return frame


@dataclass
class DashboardData:
    series: dict
    indicators: pd.DataFrame
    differences: pd.DataFrame
    validation: pd.DataFrame
    validation_summary: dict
    historical: pd.DataFrame
    parameters: tuple
    metadata: dict

    def get(self,window,scenario):
        if (window,scenario) not in self.series:
            raise ValueError('Ventana o escenario oficial no disponible')
        return self.series[window,scenario]

    def horizons(self,window):
        return sorted(self.indicators.loc[self.indicators.ventana==window,'horizonte_horas'].unique().astype(int).tolist())

    def visual_maxima(self,window):
        values=np.stack([self.get(window,code).states[:,:3].max(axis=0) for code in LABELS])
        return np.maximum(1.,values.max(axis=0))


def file_signature(root):
    root=Path(root)
    return tuple((name,(root/name).stat().st_mtime_ns,(root/name).stat().st_size) for name in FILES)


def read_numeric_csv(path,text_columns=()):
    frame=pd.read_csv(path,dtype=str)
    for column in frame:
        if column not in text_columns:
            frame[column]=frame[column].astype(float)
    return frame


def load_dashboard(root):
    root=Path(root);reports=root/'reports'
    metadata=json.loads((reports/'comparacion_escenarios.json').read_text(encoding='utf-8'))
    summary=json.loads((reports/'resumen_validacion.json').read_text(encoding='utf-8'))
    base=json.loads((reports/'parametros_calibrados.json').read_text(encoding='utf-8'))
    if metadata['base_validation_category']!='C' or summary['decision']!='C':
        raise ValueError('Falta el antecedente científico de categoría C')
    trajectories=read_numeric_csv(reports/'trayectorias_escenarios.csv',('ventana','escenario','corte_horario'))
    flows=read_numeric_csv(reports/'transferencias_escenarios.csv',('ventana','escenario','corte_horario'))
    parameters=tuple(base[key] for key in ['alpha','beta','gamma'])
    series={}
    for window in WINDOWS:
        for code in LABELS:
            t=trajectories.loc[(trajectories.ventana==window)&(trajectories.escenario==code)]
            f=flows.loc[(flows.ventana==window)&(flows.escenario==code)]
            if t.empty or f.empty:
                raise ValueError('Faltan escenarios: ejecute scripts/ejecutar_escenarios.py --sensibilidad')
            dates=pd.DatetimeIndex(pd.to_datetime(t.corte_horario)).to_numpy(dtype='datetime64[ns]')
            fd=pd.DatetimeIndex(pd.to_datetime(f.corte_horario)).to_numpy(dtype='datetime64[ns]')
            if len(np.unique(dates))!=len(dates) or not (np.diff(dates)==np.timedelta64(1,'h')).all() or not np.array_equal(fd,dates[1:]):
                raise ValueError('Fechas de niveles y flujos desalineadas')
            states=t[['X1','X2','X3','X4']].to_numpy(dtype=float)
            moved=f[['q12_integrado','q23_integrado','q34_integrado']].to_numpy(dtype=float)
            purchases=f.compras.to_numpy(dtype=float)
            n=5488 if window=='principal' else 744
            if len(states)!=n+1 or moved.shape!=(n,3) or not np.array_equal(t.horas_desde_inicio,np.arange(n+1)):
                raise ValueError('Dimensiones de escenario incorrectas')
            for array in (states,moved,purchases):
                if not np.isfinite(array).all() or (array<0).any():
                    raise ValueError('Datos de simulación no físicos')
            expected=states[0].sum()+np.r_[0,np.cumsum(purchases)]
            if (np.abs(states.sum(axis=1)-expected)>1e-8*np.maximum(1,expected)).any():
                raise ValueError('Artefactos no conservan pedidos')
            delta=np.column_stack([purchases-moved[:,0],moved[:,0]-moved[:,1],moved[:,1]-moved[:,2],moved[:,2]])
            if not np.allclose(np.diff(states,axis=0),delta,rtol=0,atol=1e-7) or (np.diff(states[:,3])<0).any():
                raise ValueError('Niveles y transferencias incompatibles')
            record=next(r for r in metadata['runs'] if r['window']==window and r['code']==code)
            if hashlib.sha256(states.tobytes()).hexdigest()!=record['states_sha256']:
                raise ValueError('La trayectoria no coincide con su huella de escenarios')
            coefficients=tuple(record['parameters'][key] for key in ['alpha','beta','gamma'])
            series[window,code]=ScenarioSeries(window,code,dates,states,moved,purchases,t.area_acumulada_P.to_numpy(),coefficients)
    indicators=pd.read_csv(reports/'indicadores_horizontes.csv')
    for window in WINDOWS:
        for code in LABELS:
            s=series[window,code]
            rows=indicators.loc[(indicators.ventana==window)&(indicators.escenario==code)]
            if rows.empty:
                raise ValueError('Faltan indicadores oficiales')
            for row in rows.itertuples():
                h=int(row.horizonte_horas)
                if h>s.duration or not np.isclose(row.P_area_pedidos_hora,s.area[h],rtol=1e-12):
                    raise ValueError('Indicadores y trayectoria no coinciden')
    actual=indicators.loc[(indicators.ventana=='principal')&(indicators.horizonte_horas==5488)].set_index('escenario')
    np.testing.assert_allclose(actual.loc[['E0','E1','E2'],'P_area_pedidos_hora'],[13339474.306616245,12860070.715045635,11660143.579588065],rtol=0,atol=.01)
    history=pd.read_csv(root/'data/processed/niveles_reales_4_tanques.csv',parse_dates=['corte_horario'])
    return DashboardData(series,indicators,pd.read_csv(reports/'diferencias_escenarios.csv'),
        pd.read_csv(reports/'metricas_validacion.csv'),summary,history,parameters,metadata)


def export_csv(frame):
    return frame.to_csv(index=False,date_format='%Y-%m-%d %H:%M:%S').encode('utf-8-sig')


def custom_experiment(reference,coefficients):
    """Ejecución explícita en memoria; no escribe ni sustituye escenarios oficiales."""
    parameters=Parameters(*coefficients)
    pure=simulate(reference.states[0],reference.purchases,parameters,4)
    agents,model=simulate_agentpy(reference.states[0],reference.purchases,parameters,4)
    np.testing.assert_array_equal(pure.states,agents.states)
    np.testing.assert_array_equal(pure.transfers,agents.transfers)
    if len(model.deposits)!=4:
        raise ValueError('Se requieren cuatro agentes')
    area=cumulative_areas(pure.times,pure.states[:,:3].sum(axis=1)[:,None])[:,0]
    return ScenarioSeries(reference.window,'Personalizado',reference.dates.copy(),pure.states,pure.transfers,
                          pure.arrivals,area,tuple(coefficients),True)


def custom_indicators(series,horizons):
    from .simulation_engine import SimulationResult
    error=series.states.sum(axis=1)-series.states[0].sum()-series.cumulative_purchases
    result=SimulationResult(np.arange(series.duration+1),series.states,series.flows,series.purchases,error,np.zeros(series.duration))
    return horizon_indicators(pd.DatetimeIndex(series.dates),result,horizons)
