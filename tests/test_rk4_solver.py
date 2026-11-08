"""Pruebas matemáticas artificiales: no representan parámetros de Olist."""
import numpy as np
import pytest
from scipy.linalg import expm
from src.rk4_solver import Parameters, NumericalError, rk4_step, check_stability
from src.simulation_engine import simulate


def test_constant_without_flows():
    x = np.array([3.,4.,5.,6.])
    r = simulate(x, np.zeros(5), Parameters(0,0,0))
    np.testing.assert_array_equal(r.states, np.tile(x,(6,1)))
    np.testing.assert_array_equal(x, [3,4,5,6])


def test_only_purchases_and_boundaries():
    r = simulate([1,2,3,4], [0,7,0,19], Parameters(0,0,0))
    np.testing.assert_array_equal(r.states[:,0], [1,1,8,8,27])
    np.testing.assert_array_equal(r.states[:,1:], np.tile([2,3,4],(5,1)))
    assert r.max_conservation_error == 0


def test_isolated_exponential_convergence():
    errors = []
    for n in (4,8,16):
        r = simulate([100,0,0,0], np.zeros(8), Parameters(.7,0,0), n)
        exact = 100*np.exp(-.7*r.times)
        errors.append(np.max(np.abs(r.states[:,0]-exact)))
        np.testing.assert_allclose(r.states[:,0]+r.states[:,1], 100, atol=1e-12)
    assert errors[0]/errors[1] > 14
    assert errors[1]/errors[2] > 14


def test_expm_reference_and_convergence_thresholds():
    p = Parameters(.4,.2,.1)
    arrivals = np.array([0,20,3,0,15,7,1,0], dtype=float)
    initial = np.array([100.,50.,30.,5.])
    # Referencia independiente: matriz aumentada incluye entrada constante.
    m = np.array([[-.4,0,0,0],[.4,-.2,0,0],[0,.2,-.1,0],[0,0,.1,0]])
    reference = [initial]
    for arrival in arrivals:
        augmented = np.zeros((5,5))
        augmented[:4,:4] = m
        augmented[0,4] = arrival
        reference.append((expm(augmented) @ np.r_[reference[-1],1])[:4])
    reference = np.array(reference)
    runs = [simulate(initial, arrivals, p, n) for n in (4,8,16)]
    errors = [np.max(np.abs(r.states-reference)) for r in runs]
    assert errors[0] > errors[1] > errors[2]
    assert errors[0]/errors[1] > 14
    assert errors[1]/errors[2] > 14
    difference = runs[1].states-runs[2].states
    scales = np.maximum(1,reference.mean(axis=0))  # Escalas sólo del caso matemático.
    assert np.max(np.abs(difference)) <= .1
    assert (np.sqrt(np.mean(difference**2,axis=0))/scales <= .001).all()


@pytest.mark.parametrize('values', [(-1,0,0),(0,np.nan,0),(0,0,np.inf)])
def test_invalid_parameters(values):
    with pytest.raises(ValueError):
        Parameters(*values)


@pytest.mark.parametrize('state', [[-1,0,0,0],[0,np.nan,0,0],[0,0,np.inf,0],[1,2,3],[[1,2,3,4]]])
def test_invalid_states(state):
    with pytest.raises(ValueError):
        simulate(state, [1], Parameters(0,0,0))


@pytest.mark.parametrize('arrivals', [[-1],[np.inf],[np.nan],[[1]]])
def test_invalid_arrivals(arrivals):
    with pytest.raises(ValueError):
        simulate([0,0,0,0], arrivals, Parameters(0,0,0))


@pytest.mark.parametrize('n', [0,-1,True,4.0])
def test_invalid_substeps(n):
    with pytest.raises(ValueError):
        simulate([0,0,0,0], [1], Parameters(0,0,0), n)


@pytest.mark.parametrize('h', [0,-1,np.nan,np.inf])
def test_invalid_step(h):
    with pytest.raises(ValueError):
        rk4_step([1,0,0,0], 0, Parameters(1,0,0), h)


def test_unstable_step_and_positive_stages():
    with pytest.raises(NumericalError, match='estabilidad'):
        simulate([100,0,0,0], [0], Parameters(12,0,0), 4)
    # hk=2.5 es linealmente estable, pero genera etapa interna negativa.
    check_stability(Parameters(10,0,0), .25)
    with pytest.raises(NumericalError, match='negativo'):
        simulate([100,0,0,0], [0], Parameters(10,0,0), 4)
    r = simulate([100,0,0,0], [0], Parameters(12,0,0), 32)
    assert (r.states >= 0).all()


def test_step_does_not_mutate_input():
    x = np.array([10.,3.,2.,1.])
    saved = x.copy()
    new, moved = rk4_step(x, 7, Parameters(.2,.1,.05))
    np.testing.assert_array_equal(x,saved)
    assert not np.shares_memory(x,new)
    assert (moved >= 0).all()
