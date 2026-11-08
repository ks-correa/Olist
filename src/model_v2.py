"""Conservative phase chains; hourly piecewise rates, classical RK4 propagators."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.linalg import solve_banded


@dataclass(frozen=True)
class ModelSpec:
    name: str
    theta: tuple
    phases: tuple = (1, 1, 1)

    def __post_init__(self):
        if self.name not in ('A', 'B', 'C', 'D'):
            raise ValueError('Modelo desconocido')
        expected = 12 if self.name in ('B', 'D') else 3
        if len(self.theta) != expected or not np.isfinite(self.theta).all():
            raise ValueError('Parámetros inválidos')
        if self.phases != ((2, 2, 2) if self.name in ('C', 'D') else (1, 1, 1)):
            raise ValueError('Fases incompatibles')


def rates(spec, cuts):
    dates = pd.DatetimeIndex(cuts)
    if spec.name in ('B', 'D'):
        z = np.column_stack([np.ones(len(dates)), np.sin(2*np.pi*dates.hour/24),
                             np.cos(2*np.pi*dates.hour/24), (dates.dayofweek >= 5)])
        return np.exp(z @ np.asarray(spec.theta).reshape(3, 4).T)
    return np.broadcast_to(np.exp(spec.theta), (len(dates), 3)).copy()


def propagators(spec, cuts, substeps=4):
    if isinstance(substeps, bool) or not isinstance(substeps, (int, np.integer)) or substeps < 1:
        raise ValueError('Subpasos inválidos')
    r = rates(spec, cuts)
    if (r/substeps > 1).any():
        raise ValueError('Paso no positivo en etapas RK4; reducir h')
    n, m = len(r), sum(spec.phases)+1
    # Extra state is a constant forcing: u=purchases/h, not an order deposit.
    a = np.zeros((n, m+1, m+1))
    k = np.repeat(r, spec.phases, axis=1)
    for j in range(m-1):
        a[:, j, j] = -k[:, j]
        a[:, j+1, j] = k[:, j]
    a[:, 0, m] = 1
    eye = np.broadcast_to(np.eye(m+1), a.shape)
    z = a/substeps
    z2 = z @ z
    step = eye + z + z2/2 + (z2 @ z)/6 + (z2 @ z2)/24
    f = eye.copy()
    for _ in range(substeps):
        f = step @ f
    if (f < -1e-14).any() or not np.isfinite(f).all():
        raise ValueError('Propagador no físico')
    return f[:, :m, :m], f[:, :m, m]


def initial_internal(initial, phases):
    initial = np.asarray(initial, float)
    if initial.shape != (4,) or not np.isfinite(initial).all() or (initial < 0).any():
        raise ValueError('Estado inicial inválido')
    return np.r_[np.repeat(initial[:3]/np.asarray(phases), phases), initial[3]]


def aggregate(internal, phases):
    ends = np.r_[0, np.cumsum(phases)]
    return np.column_stack([internal[:, ends[j]:ends[j+1]].sum(axis=1)
                            for j in range(3)] + [internal[:, -1]])


def simulate_v2(initial, arrivals, cuts, spec, substeps=4, internal_initial=None):
    """Only initial, arrivals and calendar enter the free trajectory.

    Triangular band solves evaluate the RK4 recurrence without time-loop Python.
    No observation assimilation, clipping or mass corrections.
    """
    dates = pd.DatetimeIndex(cuts)
    u = np.asarray(arrivals, float)
    if (u.ndim != 1 or len(dates) != len(u)+1 or not len(u)
            or not np.isfinite(u).all() or (u < 0).any() or dates.hasnans
            or not ((dates[1:]-dates[:-1]) == pd.Timedelta(hours=1)).all()):
        raise ValueError('Entrada/malla inválida')
    x0 = initial_internal(initial, spec.phases)
    if internal_initial is not None:
        proposed = np.asarray(internal_initial, float)
        if proposed.shape != x0.shape or not np.isfinite(proposed).all() or (proposed < 0).any():
            raise ValueError('Subestados iniciales inválidos')
        if not np.allclose(aggregate(proposed[None, :], spec.phases)[0], initial, rtol=0, atol=1e-10):
            raise ValueError('Subestados no suman niveles iniciales')
        x0 = proposed.copy()
    f, g = propagators(spec, dates[:-1], substeps)
    n, m = len(u), len(x0)
    x = np.empty((n+1, m)); x[0] = x0
    for i in range(m):
        forcing = g[:, i]*u
        for j in range(i):
            forcing = forcing + f[:, i, j]*x[:-1, j]
        forcing[0] += f[0, i, i]*x0[i]
        band = np.zeros((2, n)); band[0] = 1
        band[1, :-1] = -f[1:, i, i]
        x[1:, i] = solve_banded((1, 0), band, forcing, check_finite=False)
    states = aggregate(x, spec.phases)
    error = states.sum(axis=1) - (sum(initial) + np.r_[0, np.cumsum(u)])
    delta = np.diff(states, axis=0)
    transfers = np.column_stack([u-delta[:, 0], u-delta[:, :2].sum(axis=1), delta[:, 3]])
    if (not np.isfinite(x).all() or (x < 0).any() or (transfers < -1e-8).any()
            or (delta[:, 3] < 0).any() or np.max(np.abs(error)) > 1e-7*max(1, states.sum(axis=1).max())):
        raise ValueError('Trayectoria no física')
    return states, x, transfers, error


def simulate_agentpy_v2(initial, arrivals, cuts, spec, substeps=4):
    """Four agents publish aggregates from the same precomputed RK4 trajectory."""
    import agentpy as ap
    from .agent_model import DepositAgent

    class PhaseModel(ap.Model):
        def setup(self):
            self.result = simulate_v2(initial, arrivals, cuts, spec, substeps)
            self.deposits = ap.AgentList(self, [DepositAgent(self, position=i, name=f'X{i+1}', level=initial[i]) for i in range(4)])
            self.published = [np.asarray(initial, float)]

        def step(self):
            for agent, value in zip(self.deposits, self.result[0][self.t]):
                agent.receive_state(value)
            self.published.append(np.array([a.level for a in self.deposits]))

    model = PhaseModel({'steps': len(arrivals), 'seed': 0})
    model.run(display=False)
    return np.asarray(model.published), model
