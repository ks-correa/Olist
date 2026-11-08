"""Trayectoria pura y carga/selección temporal de datos históricos."""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from .rk4_solver import (vector, check_substeps, check_stability, integrate_hour,
                         NumericalError, split_arrival)


@dataclass
class SimulationResult:
    times: np.ndarray
    states: np.ndarray
    transfers: np.ndarray  # (N,3), pedidos por intervalo de 1 h
    arrivals: np.ndarray   # (N,), pedidos por intervalo
    conservation_errors: np.ndarray
    rapid_arrivals: np.ndarray | None = None  # Entrada directa a T2, pedidos/intervalo

    @property
    def max_conservation_error(self):
        return float(np.max(np.abs(self.conservation_errors)))


def prepare(initial, arrivals, parameters, substeps):
    initial = vector(initial, 4, 'Estado inicial')
    arrivals = np.array(arrivals, dtype=float, copy=True)
    if arrivals.ndim != 1 or not np.isfinite(arrivals).all() or (arrivals < 0).any():
        raise ValueError('Llegadas: vector finito no negativo')
    substeps = check_substeps(substeps)
    check_stability(parameters, 1/substeps)
    expected = initial.sum() + np.r_[0., np.cumsum(arrivals)]
    if not np.isfinite(expected).all():
        raise ValueError('Total acumulado no finito')
    return initial, arrivals, substeps, expected


def verify_interval(previous, new, moved, purchases, expected, rapid_purchases=0.0):
    """Comprobaciones sin correcciones ni tolerancias que oculten negativos."""
    if not np.isfinite(new).all() or (new < 0).any() or new[3] < previous[3]:
        raise NumericalError('Niveles no físicos')
    if not np.isfinite(moved).all() or (moved < 0).any():
        raise NumericalError('Transferencias no físicas')
    error = float(new.sum()-expected)
    tolerance = 1e-8*max(1., expected)
    if abs(error) > tolerance:
        raise NumericalError(f'Conservación incumplida: error={error}, tolerancia={tolerance}')
    if not np.isfinite(rapid_purchases) or not 0 <= rapid_purchases <= purchases:
        raise NumericalError('Entrada rápida incompatible con compras')
    delta = np.array([purchases-rapid_purchases-moved[0], rapid_purchases+moved[0]-moved[1], moved[1]-moved[2], moved[2]])
    if np.max(np.abs((new-previous)-delta)) > tolerance:
        raise NumericalError('Transferencias incompatibles con cambios de estado')
    return error


def simulate(initial, arrivals, parameters, substeps=4):
    """Simulación determinista independiente de AgentPy; N llegadas, N+1 estados."""
    initial, arrivals, substeps, expected = prepare(initial, arrivals, parameters, substeps)
    n = len(arrivals)
    states, transfers, errors = np.empty((n+1,4)), np.empty((n,3)), np.zeros(n+1)
    states[0] = initial
    _, rapid = split_arrival(arrivals, parameters)
    for j, purchases in enumerate(arrivals):
        states[j+1], transfers[j] = integrate_hour(states[j], purchases, parameters, substeps)
        errors[j+1] = verify_interval(states[j], states[j+1], transfers[j], purchases, expected[j+1], rapid[j])
    return SimulationResult(np.arange(n+1, dtype=float), states, transfers, arrivals, errors, rapid)


@dataclass
class HistoricalWindow:
    cuts: pd.DatetimeIndex
    initial: np.ndarray
    arrivals: np.ndarray


def load_window(directory, start, end):
    """Carga y verifica mallas completas; retorna estado de start y compras (start,end].

    No entrega transferencias reales al motor ni estados futuros para corregirlo.
    Los extremos deben existir y estar alineados a cortes horarios.
    """
    directory = Path(directory)
    flows = pd.read_csv(directory/'eventos_por_hora.csv')
    levels = pd.read_csv(directory/'niveles_reales_4_tanques.csv')
    required_f = {'corte_horario', 'compras', 'compras_por_hora'}
    required_l = {'corte_horario', 'A', 'B', 'C', 'D', 'X1', 'X2', 'X3', 'X4'}
    if not required_f.issubset(flows.columns) or not required_l.issubset(levels.columns):
        raise ValueError('Columnas históricas requeridas ausentes')
    grids = []
    for table in (flows, levels):
        grid = pd.DatetimeIndex(pd.to_datetime(table.corte_horario, errors='raise'))
        if grid.hasnans or grid.has_duplicates or len(grid) < 2 or not grid.is_monotonic_increasing:
            raise ValueError('Cortes inválidos, duplicados o desordenados')
        if not ((grid[1:] - grid[:-1]) == pd.Timedelta(hours=1)).all():
            raise ValueError('Faltan intervalos o la malla no es horaria')
        if not grid.equals(grid.floor('h')):
            raise ValueError('Cortes no alineados a la hora')
        grids.append(grid)
    if not grids[0].equals(grids[1]):
        raise ValueError('Mallas de compras y niveles diferentes')
    grid = grids[0]
    purchases = flows.compras.to_numpy(dtype=float)
    states = levels[['X1','X2','X3','X4']].to_numpy(dtype=float)
    cumulative = levels[['A','B','C','D']].to_numpy(dtype=float)
    if (not np.isfinite(purchases).all() or (purchases < 0).any()
            or not np.equal(purchases, np.floor(purchases)).all()
            or not np.array_equal(purchases, flows.compras_por_hora.to_numpy(dtype=float))):
        raise ValueError('Compras o tasas horarias inconsistentes')
    if (not np.isfinite(states).all() or (states < 0).any()
            or not np.isfinite(cumulative).all() or (cumulative < 0).any()):
        raise ValueError('Niveles o acumulados inválidos')
    a,b,c,d = cumulative.T
    if not np.array_equal(states, np.column_stack([a-b,b-c,c-d,d])):
        raise ValueError('Niveles incompatibles con acumulados')
    if not np.array_equal(np.diff(a), purchases[1:]):
        raise ValueError('Compras incompatibles con acumulados')
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if pd.isna(start) or pd.isna(end) or start not in grid or end not in grid or end < start:
        raise ValueError('Ventana fuera de cortes disponibles o invertida')
    i,j = grid.get_loc(start), grid.get_loc(end)
    return HistoricalWindow(grid[i:j+1], states[i].copy(), purchases[i+1:j+1].copy())

