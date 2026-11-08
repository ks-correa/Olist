"""Sistema vectorial y RK4 puro. Estados: pedidos; tiempo: horas."""
from dataclasses import dataclass
import numpy as np


class NumericalError(ValueError):
    """Paso inestable o resultado no físico; reducir h, sin recortar estados."""


def vector(value, size, name):
    array = np.array(value, dtype=float, copy=True)
    if array.shape != (size,) or not np.isfinite(array).all() or (array < 0).any():
        raise ValueError(f'{name}: se requieren {size} valores finitos no negativos')
    return array


@dataclass(frozen=True)
class Parameters:
    alpha: float
    beta: float
    gamma: float

    def __post_init__(self):
        vector([self.alpha, self.beta, self.gamma], 3, 'Parámetros')

    def array(self):
        return np.array([self.alpha, self.beta, self.gamma], dtype=float)


@dataclass(frozen=True)
class RapidParameters(Parameters):
    """Variante con aprobación rápida efectiva; array() conserva las tres tasas."""
    p: float

    def __post_init__(self):
        super().__post_init__()
        value = vector([self.p], 1, 'Fracción rápida p')[0]
        if value > 1:
            raise ValueError('p debe pertenecer a [0,1]')

    def full_array(self):
        return np.r_[self.array(), self.p]


def split_arrival(arrival_rate, parameters):
    """Entradas externas a T1 y T2; no son dos compras diferentes."""
    p = parameters.p if isinstance(parameters, RapidParameters) else 0.0
    return (1-p)*arrival_rate, p*arrival_rate


def check_substeps(substeps):
    if isinstance(substeps, (bool, np.bool_)) or not isinstance(substeps, (int, np.integer)) or substeps < 1:
        raise ValueError('substeps debe ser entero positivo')
    return int(substeps)


def check_stability(parameters, h):
    if not np.isfinite(h) or h <= 0:
        raise ValueError('h debe ser finito y positivo')
    with np.errstate(over='ignore', invalid='ignore'):
        z = -h * parameters.array()
        r = 1 + z + z*z/2 + z**3/6 + z**4/24
    if not np.isfinite(r).all() or (np.abs(r) > 1 + 1e-14).any():
        raise NumericalError('RK4 fuera de estabilidad lineal; reduzca h o aumente substeps')


def transfer_rates(state, parameters):
    """Única definición de los tres flujos, en pedidos/hora."""
    return parameters.array() * np.asarray(state, dtype=float)[:3]


def rhs(t, state, arrival_rate, parameters):
    """Las cuatro derivadas simultáneas; t es hora local de simulación."""
    q12, q23, q34 = transfer_rates(state, parameters)
    slow, rapid = split_arrival(arrival_rate, parameters)
    return np.array([slow-q12, rapid+q12-q23, q23-q34, q34])


def _physical(state):
    if not np.isfinite(state).all() or (state < 0).any():
        raise NumericalError('Estado RK4 no finito o negativo (incluidas etapas internas); reduzca h')


def _rk4_step(state, arrival_rate, parameters, h, t):
    # Entrada escalar congelada también para K4 en la frontera final de la hora.
    k1 = rhs(t, state, arrival_rate, parameters)
    s2 = state + h*k1/2
    _physical(s2)
    k2 = rhs(t+h/2, s2, arrival_rate, parameters)
    s3 = state + h*k2/2
    _physical(s3)
    k3 = rhs(t+h/2, s3, arrival_rate, parameters)
    s4 = state + h*k3
    _physical(s4)
    k4 = rhs(t+h, s4, arrival_rate, parameters)
    new = state + h*(k1+2*k2+2*k3+k4)/6
    _physical(new)
    # Cuadratura RK4 de q: transferencias integradas, no flujos del extremo.
    moved = h*(transfer_rates(state, parameters) + 2*transfer_rates(s2, parameters)
               + 2*transfer_rates(s3, parameters) + transfer_rates(s4, parameters))/6
    if not np.isfinite(moved).all() or (moved < 0).any() or new[3] < state[3]:
        raise NumericalError('Flujos no físicos o X4 decreciente; reduzca h')
    return new, moved


def rk4_step(state, arrival_rate, parameters, h=0.25, t=0.0):
    """Un paso: devuelve (nuevo vector, transferencias integradas). No muta entrada."""
    state = vector(state, 4, 'Estado')
    vector([arrival_rate], 1, 'Entrada')
    if not np.isfinite(t):
        raise ValueError('t debe ser finito')
    check_stability(parameters, h)
    return _rk4_step(state, float(arrival_rate), parameters, h, t)


def integrate_hour(state, purchases, parameters, substeps=4):
    """Integra exactamente una hora con compras constantes, sin pandas."""
    state = vector(state, 4, 'Estado')
    vector([purchases], 1, 'Compras')
    substeps = check_substeps(substeps)
    h = 1/substeps
    check_stability(parameters, h)
    moved = np.zeros(3)
    for j in range(substeps):
        state, transfer = _rk4_step(state, float(purchases), parameters, h, j*h)
        moved += transfer
    return state, moved
