"""AgentPy administra cuatro depósitos; el motor común realiza toda integración."""
import agentpy as ap
import numpy as np
from .rk4_solver import integrate_hour, transfer_rates, split_arrival
from .simulation_engine import prepare, verify_interval, SimulationResult


class DepositAgent(ap.Agent):
    def setup(self, position, name, level):
        self.position = position
        self.name = name
        self.level = float(level)

    def outgoing_flow(self, parameters):
        """Flujo instantáneo diagnóstico; X4 no tiene salida."""
        if self.position == 3:
            return 0.0
        vector = np.zeros(4)
        vector[self.position] = self.level
        return float(transfer_rates(vector, parameters)[self.position])

    def receive_state(self, level):
        """Recibe el resultado ya calculado; no integra ni transfiere por su cuenta."""
        self.level = float(level)


class FourDepositModel(ap.Model):
    def setup(self):
        initial, arrivals, substeps, expected = prepare(
            self.p.initial, self.p.arrivals, self.p.coefficients, self.p.substeps)
        self.arrivals, self.substeps, self.expected = arrivals, substeps, expected
        self.coefficients = self.p.coefficients
        names = ['aprobacion', 'despacho', 'transporte', 'entregas_acumuladas']
        self.deposits = ap.AgentList(self, [DepositAgent(self, position=i, name=name, level=initial[i])
                                          for i,name in enumerate(names)])
        n = len(arrivals)
        self.states = np.empty((n+1,4))
        self.transfers = np.empty((n,3))
        self.errors = np.zeros(n+1)
        self.states[0] = initial
        self.completed = 0
        _, self.rapid_arrivals = split_arrival(arrivals, self.coefficients)
        self.rapid_purchases = 0.0
        self.purchases = self.q12_integrated = self.q23_integrated = self.q34_integrated = 0.0
        if n == 0:
            self.stop()

    def step(self):
        j = self.completed
        previous = np.array([agent.level for agent in self.deposits])
        new, moved = integrate_hour(previous, self.arrivals[j], self.coefficients, self.substeps)
        error = verify_interval(previous, new, moved, self.arrivals[j], self.expected[j+1], self.rapid_arrivals[j])
        # El vector completo está calculado y validado antes de publicar cualquier nivel.
        for agent, level in zip(self.deposits, new):
            agent.receive_state(level)
        self.purchases = float(self.arrivals[j])
        self.rapid_purchases = float(self.rapid_arrivals[j])
        self.q12_integrated, self.q23_integrated, self.q34_integrated = map(float, moved)
        self.completed += 1
        self.states[j+1], self.transfers[j], self.errors[j+1] = new, moved, error
        if self.completed == len(self.arrivals):
            self.stop()

    def update(self):
        # Fila inicial con flujos cero; cada fila posterior corresponde a una hora.
        self.record(['purchases', 'rapid_purchases', 'q12_integrated', 'q23_integrated', 'q34_integrated'])
        for agent in self.deposits:
            agent.record('level')

    def end(self):
        n = self.completed
        self.result = SimulationResult(np.arange(n+1,dtype=float), self.states[:n+1].copy(),
                                       self.transfers[:n].copy(), self.arrivals[:n].copy(), self.errors[:n+1].copy(), self.rapid_arrivals[:n].copy())
        self.report('max_conservation_error', self.result.max_conservation_error)


def simulate_agentpy(initial, arrivals, parameters, substeps=4):
    """Devuelve resultado y modelo; semilla fija, sin decisiones aleatorias."""
    initial, arrivals, substeps, _ = prepare(initial, arrivals, parameters, substeps)
    model = FourDepositModel({'initial': initial, 'arrivals': arrivals,
                              'coefficients': parameters, 'substeps': substeps,
                              'steps': len(arrivals), 'seed': 0})
    model.run(display=False)
    return model.result, model
