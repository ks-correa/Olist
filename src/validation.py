"""Validación final del modelo base congelado; no importa optimizadores."""
from dataclasses import dataclass
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from .rk4_solver import Parameters
from .simulation_engine import load_window,simulate,verify_interval
from .agent_model import simulate_agentpy
from .calibration_metrics import metrics

START=pd.Timestamp('2018-03-02 22:00:00')
END=pd.Timestamp('2018-10-17 14:00:00')
INTERVALS=5488
BLOCK_HOURS=1372
FROZEN_THETA=np.array([.10202378368368686,.013240792867426554,.004071911987908591])
FROZEN_SCALES=np.array([44.39279856283684,330.3622588455831,1004.1355932203389])
INITIAL=np.array([113.,586.,3005.,53963.])
NAMES=['X1','X2','X3','X4_incremental','P']


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def load_frozen(reports):
    reports=Path(reports)
    raw=json.loads((reports/'parametros_calibrados.json').read_text(encoding='utf-8'))
    theta=np.array([raw[key] for key in ['alpha','beta','gamma']],dtype=float)
    if not np.array_equal(theta,FROZEN_THETA) or not np.array_equal(raw['scales_pending'],FROZEN_SCALES):
        raise ValueError('Parámetros o escalas no coinciden con los valores congelados')
    selected=reports/'modelo_seleccionado_desarrollo.json'
    if selected.exists():
        record=json.loads(selected.read_text(encoding='utf-8'))
        if record['model']!='base' or not np.array_equal(record['parameters'],theta):
            raise ValueError('El modelo seleccionado no es el base congelado')
    train=pd.read_csv(reports/'metricas_entrenamiento.csv').set_index('variable')
    if not np.array_equal(train.loc[['X1','X2','X3'],'escala'].to_numpy(),FROZEN_SCALES):
        raise ValueError('Las escalas del informe original no coinciden')
    scales=train.loc[NAMES,'escala'].to_numpy(dtype=float)
    flow_train=pd.read_csv(reports/'metricas_transferencias_entrenamiento.csv').set_index('variable')
    flow_scales=flow_train.loc[['aprobaciones','despachos','entregas'],'escala'].to_numpy(dtype=float)
    if not np.isfinite(scales).all() or (scales<=0).any() or not np.isfinite(flow_scales).all() or (flow_scales<=0).any():
        raise ValueError('Escalas originales inválidas')
    return Parameters(*theta),scales,flow_scales


@dataclass
class ValidationData:
    cuts: pd.DatetimeIndex
    initial: np.ndarray
    arrivals: np.ndarray
    observed: np.ndarray
    flows: np.ndarray

    def __post_init__(self):
        self.cuts=pd.DatetimeIndex(self.cuts)
        for name in ('initial','arrivals','observed','flows'):
            setattr(self,name,np.array(getattr(self,name),dtype=float,copy=True))
        n=len(self.arrivals)
        if n<1 or self.initial.shape!=(4,) or self.arrivals.shape!=(n,) or self.observed.shape!=(n+1,4) or self.flows.shape!=(n,3) or len(self.cuts)!=n+1:
            raise ValueError('Ventana de validación desalineada')
        if self.cuts.hasnans or self.cuts.has_duplicates or not ((self.cuts[1:]-self.cuts[:-1])==pd.Timedelta(hours=1)).all():
            raise ValueError('Fechas duplicadas, inválidas o no horarias')
        for a in (self.initial,self.arrivals,self.observed,self.flows):
            if not np.isfinite(a).all() or (a<0).any():
                raise ValueError('Validación con valores no finitos o negativos')
        if not np.array_equal(self.initial,self.observed[0]):
            raise ValueError('Estado inicial distinto del observado al inicio')


def load_validation(directory):
    directory=Path(directory)
    # Reutiliza controles existentes de malla y acumulados sin cambiar el motor.
    window=load_window(directory,START,END)
    expected=pd.date_range(START,END,freq='h')
    if not window.cuts.equals(expected) or len(window.arrivals)!=INTERVALS or not np.array_equal(window.initial,INITIAL):
        raise ValueError('Ventana reservada, duración o condición inicial incorrecta')
    l=pd.read_csv(directory/'niveles_reales_4_tanques.csv',parse_dates=['corte_horario']).set_index('corte_horario')
    f=pd.read_csv(directory/'eventos_por_hora.csv',parse_dates=['corte_horario']).set_index('corte_horario')
    if not {'aprobaciones','despachos','entregas'}<=set(f.columns):
        raise ValueError('Faltan transferencias observadas para evaluación')
    observed=l.loc[expected,['X1','X2','X3','X4']].to_numpy(dtype=float)
    flows=f.loc[expected[1:],['aprobaciones','despachos','entregas']].to_numpy(dtype=float)
    data=ValidationData(expected,window.initial,window.arrivals,observed,flows)
    changes=np.column_stack([data.arrivals-flows[:,0],flows[:,0]-flows[:,1],flows[:,1]-flows[:,2],flows[:,2]])
    if not np.array_equal(np.diff(observed,axis=0),changes):
        raise ValueError('Transferencias observadas incompatibles con niveles')
    if not np.array_equal(observed.sum(axis=1),data.initial.sum()+np.r_[0,np.cumsum(data.arrivals)]):
        raise ValueError('No se conserva la población histórica')
    return data


def run_frozen(data,parameters):
    """Sólo consulta initial y arrivals: ningún nivel posterior alimenta al motor."""
    if type(parameters) is not Parameters or not np.array_equal(parameters.array(),FROZEN_THETA):
        raise ValueError('Sólo se permite el modelo base con los parámetros congelados')
    result=simulate(data.initial,data.arrivals,parameters,4)
    agents,model=simulate_agentpy(data.initial,data.arrivals,parameters,4)
    np.testing.assert_array_equal(result.states,agents.states)
    np.testing.assert_array_equal(result.transfers,agents.transfers)
    if model.completed!=len(data.arrivals) or model.t!=len(data.arrivals):
        raise ValueError('Se perdieron o duplicaron intervalos AgentPy')
    audit_trajectory(result,data.initial,data.arrivals)
    return result,agents


def audit_trajectory(result,initial,arrivals):
    n=len(arrivals)
    if result.states.shape!=(n+1,4) or result.transfers.shape!=(n,3) or not np.array_equal(result.times,np.arange(n+1)):
        raise ValueError('Trayectoria incompleta o desalineada')
    if not np.array_equal(result.states[0],initial):
        raise ValueError('Inicialización incorrecta')
    expected=np.sum(initial)+np.r_[0,np.cumsum(arrivals)]
    for i in range(n):
        verify_interval(result.states[i],result.states[i+1],result.transfers[i],arrivals[i],expected[i+1])
    if result.rapid_arrivals is None or not (result.rapid_arrivals==0).all():
        raise ValueError('No se permite aprobación rápida en validación final')
    return float(np.max(np.abs(result.states.sum(axis=1)-expected)))


def level_arrays(data,result):
    observed=data.observed.copy();simulated=result.states.copy()
    observed[:,3]-=data.initial[3];simulated[:,3]-=data.initial[3]
    return (np.column_stack([observed,observed[:,:3].sum(axis=1)]),
            np.column_stack([simulated,simulated[:,:3].sum(axis=1)]))


def scored_levels(cuts,observed,simulated,scales):
    """Sólo cortes objetivo: no incluye la fila inicial gratis en métricas."""
    cuts=pd.DatetimeIndex(cuts)
    if len(cuts)!=len(observed):
        raise ValueError('Fechas de métricas desalineadas')
    table=metrics(observed,simulated,NAMES,scales)
    table['fecha_maximo_observado']=[str(cuts[np.argmax(observed[:,i])]) for i in range(5)]
    table['fecha_maximo_simulado']=[str(cuts[np.argmax(simulated[:,i])]) for i in range(5)]
    return table


def block_slices(n=INTERVALS):
    if n!=4*BLOCK_HOURS:
        raise ValueError('Se requieren exactamente cuatro bloques de 1372 intervalos')
    # Índices de estados: 1..1372,1373..2744,... sin duplicar fronteras.
    return [(f'B{i+1}',slice(1+i*BLOCK_HOURS,1+(i+1)*BLOCK_HOURS)) for i in range(4)]


def acceptance(table,blocks):
    rows=[]
    for row in table.iloc[:3].itertuples(index=False):
        biases=blocks.loc[blocks.variable==row.variable,'sesgo_medio'].to_numpy()
        persistent=bool((biases>0).all() or (biases<0).all())
        numeric={'NMAE_cumple':row.NMAE<=.20,'NRMSE_cumple':row.NRMSE<=.30,
                 'error_pico_cumple':row.error_nivel_maximo_absoluto<=max(1,.2*row.maximo_observado),
                 'error_final_cumple':abs(row.error_final)<=max(1,.2*row.escala)}
        rows.append({'variable':row.variable,**numeric,'sesgo_mismo_signo_4_bloques':persistent,
            'cumple_criterios_cuantitativos':all(numeric.values())})
    return pd.DataFrame(rows)
