"""Predetermined candidates and expanding-origin fitting, development only."""
import numpy as np
from scipy.optimize import least_squares
from .calibration import TRAIN_END
from .model_v2 import ModelSpec, simulate_v2

BASE = np.array([.10202378368368686, .013240792867426554, .004071911987908591])
ORIGINS = (5123, 7043, 8963, 10883)
HORIZON = 1920


def make_spec(name, theta):
    return ModelSpec(name, tuple(theta), (2, 2, 2) if name in ('C', 'D') else (1, 1, 1))


def fit_v2(name, data):
    if data.cuts[-1] > TRAIN_END:
        raise ValueError('Calibración fuera de desarrollo prohibida')
    calendar = name in ('B', 'D')
    low = np.log(np.full(3, .0001)); high = np.log(np.ones(3))
    if calendar:
        high = np.log(np.full(3, .15))
        low = np.column_stack([low, np.full((3, 3), -1.)]).ravel()
        high = np.column_stack([high, np.ones((3, 3))]).ravel()
    scales = data.scales.copy()
    def objective(theta):
        spec = make_spec(name, theta)
        pred = simulate_v2(data.observed[0], data.arrivals, data.cuts, spec)[0]
        res = ((pred[1:, :3]-data.observed[1:, :3])/scales).ravel()/np.sqrt(3*len(data.arrivals))
        if calendar:
            res = np.r_[res, np.sqrt(.01)*theta.reshape(3, 4)[:, 1:].ravel()]
        return res
    runs = []
    for factor in (.5, 1.5):
        initial = np.log(BASE*factor*(2 if name in ('C', 'D') else 1))
        if calendar:
            initial = np.column_stack([initial, np.zeros((3, 3))]).ravel()
        initial = np.minimum(np.maximum(initial, low+1e-8), high-1e-8)
        result = least_squares(objective, initial, bounds=(low, high), max_nfev=100,
                               ftol=1e-7, xtol=1e-7, gtol=1e-7)
        s = np.linalg.svd(result.jac, compute_uv=False)
        runs.append(dict(theta=result.x.tolist(), success=bool(result.success),
                         cost=float(result.cost), nfev=int(result.nfev), message=result.message,
                         optimality=float(result.optimality), singular_values=s.tolist(),
                         condition=float(s[0]/s[-1]) if s[-1] else None,
                         initial_factor=factor, scales=scales.tolist(), end=str(data.cuts[-1])))
    ok = [r for r in runs if r['success']]
    if not ok:
        raise RuntimeError(f'Sin convergencia {name}')
    best = min(ok, key=lambda r:r['cost'])
    return make_spec(name, best['theta']), runs
