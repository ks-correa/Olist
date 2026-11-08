"""Calibración restringida exclusivamente al desarrollo; no evalúa reserva final."""
from dataclasses import dataclass
from pathlib import Path
import time
import numpy as np
import pandas as pd
from scipy.linalg import expm
from scipy.signal import lfilter
from scipy.optimize import least_squares
from .rk4_solver import Parameters, vector, rhs
from .data_processing import DATES

TRAIN_START = pd.Timestamp('2016-09-15 11:00:00')
TRAIN_END = pd.Timestamp('2018-03-02 22:00:00')
N_TRAIN = 12803


@dataclass
class TrainingData:
    cuts: pd.DatetimeIndex
    arrivals: np.ndarray
    observed: np.ndarray
    flows: np.ndarray

    def __post_init__(self):
        self.cuts = pd.DatetimeIndex(self.cuts)
        self.arrivals = np.array(self.arrivals,dtype=float,copy=True)
        self.observed = np.array(self.observed,dtype=float,copy=True)
        self.flows = np.array(self.flows,dtype=float,copy=True)
        n = len(self.arrivals)
        if n < 1 or self.arrivals.shape != (n,) or self.observed.shape != (n+1,4) or self.flows.shape != (n,3):
            raise ValueError('Dimensiones incompatibles de entrenamiento')
        if len(self.cuts)!=n+1 or self.cuts.hasnans or self.cuts.has_duplicates:
            raise ValueError('Cortes inválidos')
        if not ((self.cuts[1:]-self.cuts[:-1])==pd.Timedelta(hours=1)).all():
            raise ValueError('Cortes desalineados: se exige una hora')
        if self.cuts[-1]>TRAIN_END:
            raise ValueError('Prohibido incorporar período reservado a calibración')
        for array in (self.arrivals,self.observed,self.flows):
            if not np.isfinite(array).all() or (array<0).any():
                raise ValueError('Entrenamiento corrupto: valores no finitos o negativos')

    @property
    def scales(self):
        # Excluye el corte inicial, como la pérdida; mismos N objetivos por etapa.
        return np.maximum(1., self.observed[1:,:3].mean(axis=0))

    def section(self, begin, end):
        if not 0<=begin<end<=len(self.arrivals):
            raise ValueError('Subventana inválida')
        return TrainingData(self.cuts[begin:end+1],self.arrivals[begin:end],
                            self.observed[begin:end+1],self.flows[begin:end])


def load_training(directory):
    """Lee sólo las primeras 12.804 filas: ninguna fila horaria reservada."""
    directory=Path(directory)
    levels=pd.read_csv(directory/'niveles_reales_4_tanques.csv',nrows=N_TRAIN+1)
    flows=pd.read_csv(directory/'eventos_por_hora.csv',nrows=N_TRAIN+1)
    required_l=['corte_horario','A','B','C','D','X1','X2','X3','X4']
    required_f=['corte_horario','compras','compras_por_hora','aprobaciones','despachos','entregas']
    if not set(required_l)<=set(levels) or not set(required_f)<=set(flows):
        raise ValueError('Columnas requeridas ausentes')
    cuts=pd.DatetimeIndex(pd.to_datetime(levels.corte_horario,errors='raise'))
    fc=pd.DatetimeIndex(pd.to_datetime(flows.corte_horario,errors='raise'))
    expected=pd.date_range(TRAIN_START,TRAIN_END,freq='h')
    if not cuts.equals(expected) or not fc.equals(expected):
        raise ValueError('Mallas de entrenamiento diferentes o ventana incompleta')
    cumulative=levels[['A','B','C','D']].to_numpy(dtype=float)
    observed=levels[['X1','X2','X3','X4']].to_numpy(dtype=float)
    purchases=flows.compras.to_numpy(dtype=float)
    transfers=flows[['aprobaciones','despachos','entregas']].to_numpy(dtype=float)
    for arr in (cumulative,observed,purchases,transfers):
        if not np.isfinite(arr).all() or (arr<0).any() or not (arr==np.floor(arr)).all():
            raise ValueError('Conteos históricos inválidos')
    a,b,c,d=cumulative.T
    if not np.array_equal(observed,np.column_stack([a-b,b-c,c-d,d])):
        raise ValueError('Niveles incompatibles con acumulados')
    if not np.array_equal(np.diff(cumulative,axis=0), np.column_stack([purchases[1:],transfers[1:]])):
        raise ValueError('Flujos desalineados o incompatibles con acumulados')
    if not np.array_equal(purchases,flows.compras_por_hora.to_numpy(dtype=float)):
        raise ValueError('Compras y tasa incompatibles')
    return TrainingData(cuts,purchases[1:],observed,transfers[1:])


def exposure_estimates(path, start, end):
    """Salidas/eventos y exposición exacta censurada antes de convertir fechas futuras.

    Se lee la membresía retrospectiva ya fijada. Fechas mayores que end se
    sustituyen por ausencia antes de conversión y de cualquier resta temporal.
    """
    start,end=pd.Timestamp(start),pd.Timestamp(end)
    if pd.isna(start) or pd.isna(end) or end>TRAIN_END or end<=start:
        raise ValueError('Ventana de exposición inválida o fuera de entrenamiento')
    raw=pd.read_csv(path,usecols=DATES,dtype=str)
    cutoff=end.strftime('%Y-%m-%d %H:%M:%S')
    censored={}
    for col in DATES:
        values=raw[col]
        # Sólo importa si el evento ya ocurrió; su marca futura no se usa.
        observed=values.where(values.le(cutoff))
        dates=pd.to_datetime(observed,format='%Y-%m-%d %H:%M:%S',errors='raise')
        censored[col]=dates
    rows=[]
    for name,a,b in zip(['alpha','beta','gamma'],DATES[:-1],DATES[1:]):
        entry,exit=censored[a],censored[b]
        valid=entry.notna()
        if ((exit.notna() & ~valid) | (exit.lt(entry))).any():
            raise ValueError('Eventos observados incoherentes')
        left=entry.clip(lower=start)
        right=exit.fillna(end)
        durations=(right-left).dt.total_seconds()/3600
        exposure=float(durations.where(valid,0).clip(lower=0).sum())
        count=int((exit.gt(start)&exit.le(end)).sum())
        pending=int((valid & (entry.le(end)) & exit.isna()).sum())
        if exposure<=0:
            raise ValueError(f'Sin exposición suficiente para {name}; no se inventa tasa')
        rows.append({'parametro':name,'transferencias':count,'exposicion_pedidos_hora':exposure,
                     'pendientes_al_corte':pending,'tasa_inicial':count/exposure})
    return pd.DataFrame(rows)


def analytical_trajectory(initial, arrivals, parameters):
    """Mismas EDO, expm una vez por θ, recurrencia causal triangular con lfilter.

    No es suavizado: lfilter ejecuta x[k+1]=F*x[k]+g*u[k] exactamente en cada
    corte (salvo redondeo), conservando todos los intervalos de entrada.
    """
    initial=vector(initial,4,'Estado inicial')
    arrivals=np.array(arrivals,dtype=float,copy=True)
    if arrivals.ndim!=1 or not np.isfinite(arrivals).all() or (arrivals<0).any():
        raise ValueError('Llegadas inválidas')
    augmented=np.zeros((5,5))
    for i in range(4):
        augmented[:4,i]=rhs(0,np.eye(4)[i],0,parameters)
    augmented[:4,4]=rhs(0,np.zeros(4),1,parameters)
    propagator=expm(augmented)
    f,g=propagator[:4,:4],propagator[:4,4]
    states=np.empty((len(arrivals)+1,4)); states[0]=initial
    if len(arrivals):
        for i in range(4):
            forcing=g[i]*arrivals
            for j in range(i):
                forcing=forcing+f[i,j]*states[:-1,j]
            states[1:,i],_=lfilter([1.],[1.,-f[i,i]],forcing,zi=[f[i,i]*initial[i]])
    if not np.isfinite(states).all() or (states<0).any():
        raise ValueError('Propagador produjo estados no físicos')
    return states


def residual_vector(theta, data, scales=None):
    p=Parameters(*vector(theta,3,'Parámetros'))
    scale=data.scales if scales is None else vector(scales,3,'Escalas')
    if (scale<=0).any():
        raise ValueError('Escalas deben ser positivas')
    simulated=analytical_trajectory(data.observed[0],data.arrivals,p)
    return ((simulated[1:,:3]-data.observed[1:,:3])/scale).ravel()


def fit_parameters(data, initial, max_nfev=200):
    """TRF en coeficientes, cotas [0,+inf); no impone capacidades arbitrarias."""
    initial=vector(initial,3,'Parámetros iniciales')
    scale=data.scales.copy()
    calls=0
    def objective(theta):
        nonlocal calls
        calls+=1
        return residual_vector(theta,data,scale)
    start=time.perf_counter()
    result=least_squares(objective,initial,bounds=(np.zeros(3),np.full(3,np.inf)),
                         method='trf',jac='3-point',x_scale='jac',loss='linear',
                         ftol=1e-10,xtol=1e-10,gtol=1e-10,max_nfev=max_nfev)
    elapsed=time.perf_counter()-start
    singular=np.linalg.svd(result.jac*result.x[None,:],compute_uv=False)
    info={'initial':initial.tolist(),'parameters':result.x.tolist(),'units':'1/hora',
          'cost_half_sse':float(result.cost),'mean_normalized_squared_error':float(np.mean(result.fun**2)),
          'nfev':int(result.nfev),'njev':int(result.njev),'actual_residual_calls':calls,
          'success':bool(result.success),'status':int(result.status),'message':result.message,
          'optimality':float(result.optimality),'active_mask':result.active_mask.tolist(),
          'seconds':elapsed,'scaled_jacobian_singular_values':singular.tolist(),
          'scaled_jacobian_condition':float(singular[0]/singular[-1]) if singular[-1]>0 else None}
    return Parameters(*result.x),info


def multistart_fit(data, preliminary):
    """Factores prefijados 0,5/1/2 de tasas de exposición, sin mirar reserva."""
    runs=[]
    for factor in (.5,1.,2.):
        p,info=fit_parameters(data,np.asarray(preliminary)*factor)
        info['initial_factor']=factor
        runs.append((p,info))
    successful=[pair for pair in runs if pair[1]['success']]
    if not successful:
        raise RuntimeError('Ninguna inicialización convergió')
    return min(successful,key=lambda pair:pair[1]['cost_half_sse']),runs
