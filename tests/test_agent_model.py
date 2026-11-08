import numpy as np
import agentpy as ap
from src.rk4_solver import Parameters
from src.simulation_engine import simulate
from src.agent_model import simulate_agentpy, DepositAgent, FourDepositModel


def test_agentpy_exact_equivalence_and_four_agents():
    arrivals=np.array([0,10,0,30,5,0]*10)
    p=Parameters(.4,.2,.1)
    pure=simulate([100,40,20,1000],arrivals,p)
    agents,model=simulate_agentpy([100,40,20,1000],arrivals,p)
    assert isinstance(model,ap.Model) and isinstance(model,FourDepositModel)
    assert len(model.deposits)==4
    assert all(isinstance(a,ap.Agent) and isinstance(a,DepositAgent) for a in model.deposits)
    assert len({a.id for a in model.deposits})==4
    np.testing.assert_array_equal(pure.states,agents.states)
    np.testing.assert_array_equal(pure.transfers,agents.transfers)
    np.testing.assert_array_equal(pure.conservation_errors,agents.conservation_errors)
    np.testing.assert_array_equal([a.level for a in model.deposits],agents.states[-1])
    assert model.completed==len(arrivals) and model.t==len(arrivals)
    assert len(model.output.variables.DepositAgent)==4*(len(arrivals)+1)
    recorded = model.output.variables.FourDepositModel
    np.testing.assert_array_equal(recorded[['q12_integrated','q23_integrated','q34_integrated']].to_numpy()[1:], agents.transfers)
    np.testing.assert_array_equal(recorded.purchases.to_numpy()[1:], arrivals)
    assert model.deposits[3].outgoing_flow(p)==0
    assert model.deposits[0].outgoing_flow(p)==p.alpha*model.deposits[0].level


def test_agent_transfers_without_creation_or_loss():
    r,_=simulate_agentpy([100,30,10,2],[0,0,0,0],Parameters(.5,.3,.2))
    np.testing.assert_allclose(r.states.sum(axis=1),142,atol=1e-12)
    assert (r.transfers>=0).all()
    assert r.states[-1,3] > r.states[0,3]


def test_agent_empty_window_and_reproducibility():
    args=([1,2,3,4],[],Parameters(0,0,0))
    r,m=simulate_agentpy(*args)
    repeated,_=simulate_agentpy(*args)
    np.testing.assert_array_equal(r.states,[[1,2,3,4]])
    np.testing.assert_array_equal(r.states,repeated.states)
    assert m.completed==0 and m.t==0
