"""Demostración técnica artificial y pruebas; nunca calibra ni simula Olist completo."""
from pathlib import Path
import argparse
import platform
import subprocess
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import scipy
from scipy.linalg import expm
import agentpy
import pandas as pd
from src.rk4_solver import Parameters
from src.simulation_engine import simulate, load_window
from src.agent_model import simulate_agentpy


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark',action='store_true',help='Medir 18.291 intervalos artificiales; no usa llegadas de Olist')
    args=parser.parse_args()
    lines=[]
    def log(message):
        lines.append(str(message))
        print(message)
    log('FASE 3: PRUEBAS MATEMÁTICAS ARTIFICIALES; SIN CALIBRACIÓN NI MÉTRICAS PREDICTIVAS')
    log(f'Python {platform.python_version()}; AgentPy {agentpy.__version__}; NumPy {np.__version__}; SciPy {scipy.__version__}; pandas {pd.__version__}')
    suite=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    log(suite.stdout)
    if suite.stderr: log(suite.stderr)
    if suite.returncode:
        (ROOT/'reports/pruebas_motor_simulacion.txt').write_text('\n'.join(lines),encoding='utf-8')
        raise SystemExit(suite.returncode)
    w=load_window(ROOT/'data/processed','2018-03-02 22:00:00','2018-03-03 02:00:00')
    log(f'Lectura real (sin simular): inicio={w.cuts[0]}, X0={w.initial.tolist()}, total={w.initial.sum()}, intervalos seleccionados={len(w.arrivals)}')
    p=Parameters(.4,.2,.1)  # Sólo prueba matemática: no son parámetros de Olist.
    x0=np.array([100.,50.,30.,5.])
    arrivals=np.array([0,20,3,0,15,7,1,0],dtype=float)
    matrix=np.array([[-.4,0,0,0],[.4,-.2,0,0],[0,.2,-.1,0],[0,0,.1,0]])
    reference=[x0]
    for purchase in arrivals:
        augmented=np.zeros((5,5)); augmented[:4,:4]=matrix; augmented[0,4]=purchase
        reference.append((expm(augmented) @ np.r_[reference[-1],1])[:4])
    reference=np.array(reference)
    runs=[]; errors=[]
    log('Convergencia en caso artificial: h(horas), máximo error absoluto frente a expm (pedidos)')
    for steps in (4,8,16):
        r=simulate(x0,arrivals,p,steps); runs.append(r)
        error=float(np.max(np.abs(r.states-reference))); errors.append(error)
        log(f'h={1/steps:.4f}: {error:.12g}; error máximo conservación={r.max_conservation_error:.12g}')
    diff=runs[1].states-runs[2].states
    scales=np.maximum(1,reference.mean(axis=0))
    normalized=np.sqrt(np.mean(diff**2,axis=0))/scales
    log(f'Diferencia entre mallas finas: max={np.max(np.abs(diff)):.12g}; NRMSE numérico por estado={normalized.tolist()}')
    log(f'Factores de reducción de error: {errors[0]/errors[1]:.6f}, {errors[1]/errors[2]:.6f}')
    assert np.max(np.abs(diff)) <= .1 and (normalized<=.001).all()
    agent_result,model=simulate_agentpy(x0,arrivals,p)
    np.testing.assert_array_equal(agent_result.states,runs[0].states)
    np.testing.assert_array_equal(agent_result.transfers,runs[0].transfers)
    log(f'AgentPy: {len(model.deposits)} agentes; diferencia máxima estados=0; diferencia máxima transferencias=0 (igualdad exacta).')
    log('Los casos inestable y estable con etapa interna negativa se rechazan en las pruebas; un paso menor permite avanzar.')
    if args.benchmark:
        synthetic=np.tile([0.,10.,3.,0.,7.,2.],3049)[:18291]
        start=time.perf_counter(); r=simulate(x0,synthetic,p); elapsed=time.perf_counter()-start
        log(f'Rendimiento artificial: {len(synthetic)} intervalos, {len(r.states)} estados, motor puro {elapsed:.3f} s; error máximo conservación={r.max_conservation_error:.12g}')
        start=time.perf_counter(); a,m=simulate_agentpy(x0,synthetic,p); elapsed=time.perf_counter()-start
        np.testing.assert_array_equal(r.states,a.states)
        np.testing.assert_array_equal(r.transfers,a.transfers)
        log(f'Rendimiento artificial AgentPy: {elapsed:.3f} s; cuatro agentes; equivalencia exacta también en 18.291 intervalos.')
    log('No se ejecutaron simulaciones históricas completas, calibración, validación estadística ni escenarios.')
    (ROOT/'reports/pruebas_motor_simulacion.txt').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':
    main()
