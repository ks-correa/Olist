"""Tres configuraciones hipotéticas del modelo base; validación previa categoría C."""
from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .rk4_solver import Parameters,check_stability
from .simulation_engine import HistoricalWindow,SimulationResult,simulate,load_window
from .agent_model import simulate_agentpy
from .validation import FROZEN_THETA,START,END,INITIAL,audit_trajectory
from .scenario_metrics import horizon_indicators

HORIZONS=(168,720,1440,5488)
COLORS={'E0':'#334155','E1':'#d56b16','E2':'#16805d'}


@dataclass(frozen=True)
class ScenarioDefinition:
    code: str
    name: str
    description: str
    parameters: Parameters


@dataclass
class ScenarioRun:
    definition: ScenarioDefinition
    window: HistoricalWindow
    result: SimulationResult
    indicators: pd.DataFrame
    checks: dict


def load_base_parameters(reports):
    reports=Path(reports)
    j=json.loads((reports/'parametros_calibrados.json').read_text(encoding='utf-8'))
    theta=np.array([j[name] for name in ['alpha','beta','gamma']],dtype=float)
    if not np.array_equal(theta,FROZEN_THETA):
        raise ValueError('Los parámetros originales no coinciden con los congelados')
    prior=json.loads((reports/'resumen_validacion.json').read_text(encoding='utf-8'))
    if prior['model']!='base' or prior['decision']!='C':
        raise ValueError('Se requiere la trazabilidad del modelo base con validación categoría C')
    return Parameters(*theta)


def official_definitions(base):
    if type(base) is not Parameters or not np.array_equal(base.array(),FROZEN_THETA):
        raise ValueError('Los escenarios oficiales requieren el modelo base congelado')
    return (
        ScenarioDefinition('E0','Base','Coeficientes históricos sin modificación',base),
        ScenarioDefinition('E1','Despacho +20 %','Sólo beta se multiplica por 1,20',Parameters(base.alpha,1.2*base.beta,base.gamma)),
        ScenarioDefinition('E2','Entrega +20 %','Sólo gamma se multiplica por 1,20',Parameters(base.alpha,base.beta,1.2*base.gamma)))


def load_scenario_window(directory,start=START,end=END):
    window=load_window(directory,start,end)
    if window.cuts[0]==START and window.cuts[-1]==END:
        if len(window.arrivals)!=5488 or not np.array_equal(window.initial,INITIAL) or window.arrivals.sum()!=37415:
            raise ValueError('Conteos o condición inicial de la ventana principal incorrectos')
    if len(window.arrivals)<1:
        raise ValueError('Escenarios requieren al menos un intervalo')
    return window


def check_structural(runs):
    """Identidades del modelo, sin convertirlas en afirmaciones operativas reales."""
    if [r.definition.code for r in runs]!=['E0','E1','E2']:
        raise ValueError('Se requieren exactamente E0,E1,E2 en orden')
    base=runs[0]
    max_totals=0.;max_identity=0.
    for run in runs:
        if not run.window.cuts.equals(base.window.cuts) or not np.array_equal(run.window.initial,base.window.initial) or not np.array_equal(run.window.arrivals,base.window.arrivals):
            raise ValueError('Las condiciones o entradas difieren entre escenarios')
        sums=run.result.states.sum(axis=1)
        expected=base.window.initial.sum()+np.r_[0,np.cumsum(base.window.arrivals)]
        tolerance=1e-8*np.maximum(1,expected)
        if (np.abs(sums-base.result.states.sum(axis=1))>tolerance).any():
            raise ValueError('Totales de escenarios diferentes')
        delta_p=run.result.states[:,:3].sum(axis=1)-base.result.states[:,:3].sum(axis=1)
        delta_d=run.result.states[:,3]-base.result.states[:,3]
        if (np.abs(delta_p+delta_d)>tolerance).any():
            raise ValueError('Delta entregas no coincide con menos delta pendientes')
        max_totals=max(max_totals,float(np.max(np.abs(sums-base.result.states.sum(axis=1)))))
        max_identity=max(max_identity,float(np.max(np.abs(delta_p+delta_d))))
    np.testing.assert_array_equal(runs[1].result.states[:,0],base.result.states[:,0])
    np.testing.assert_array_equal(runs[2].result.states[:,:2],base.result.states[:,:2])
    return {'max_diferencia_totales_entre_escenarios':max_totals,'max_error_delta_entregas_mas_delta_pendientes':max_identity,
            'X1_invariante_beta':True,'X1_X2_invariantes_gamma':True}


def run_official_scenarios(window,base,horizons=HORIZONS):
    """Tres trayectorias continuas; horizontes sólo leen prefijos, sin reinicios."""
    runs=[]
    for definition in official_definitions(base):
        check_stability(definition.parameters,.25)
        # Copias por ejecución para impedir que un consumidor altere las entradas de otra.
        same=HistoricalWindow(window.cuts.copy(),window.initial.copy(),window.arrivals.copy())
        pure=simulate(same.initial,same.arrivals,definition.parameters,4)
        agents,model=simulate_agentpy(same.initial,same.arrivals,definition.parameters,4)
        np.testing.assert_array_equal(pure.states,agents.states)
        np.testing.assert_array_equal(pure.transfers,agents.transfers)
        error=audit_trajectory(pure,same.initial,same.arrivals)
        if len(model.deposits)!=4 or model.completed!=len(same.arrivals):
            raise ValueError('AgentPy no completó la ventana con cuatro agentes')
        indicators=horizon_indicators(same.cuts,pure,horizons)
        checks={'max_error_conservacion':error,'estabilidad_RK4':True,'estados_finitos_no_negativos':True,
                'X4_no_decreciente':True,'transferencias_no_negativas':True,'agentes':4,
                'AgentPy_RK4_diferencia_estados':0.,'AgentPy_RK4_diferencia_transferencias':0.,'inicializaciones':1}
        runs.append(ScenarioRun(definition,same,pure,indicators,checks))
    check_structural(runs)
    return runs
