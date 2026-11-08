# Implementación del motor RK4 y AgentPy — fase 3

## Alcance y entorno comprobado

Se implementó el motor continuo y la coordinación de cuatro depósitos agregados. No se ajustaron coeficientes, no se calcularon métricas predictivas contra niveles históricos y no se ejecutaron escenarios de mejora ni interfaz.

Se inspeccionaron los tres documentos de fase 2, el procesamiento, las pruebas anteriores y las formas y columnas de los ocho CSV procesados. Se mantiene su estructura. El archivo histórico de flujos y el de niveles tienen 18.292 filas, incluidas la inicial y las correspondientes a 18.291 intervalos.

Entorno utilizado: Python 3.12.13 y AgentPy 0.1.5, con versiones exactas de todas las dependencias en `requirements.txt`. AgentPy se instaló e importó sin errores de compatibilidad; se inspeccionó el código de la versión instalada, incluidas las firmas de AgentList y los métodos públicos Model.run y sim_step. Se utilizan Agent.setup, Agent.record, AgentList, Model.setup/step/update/end, Model.run, Model.stop y Model.report. Referencia pública: [API de agentes de AgentPy](https://agentpy.readthedocs.io/en/latest/reference_agents.html); para el comportamiento exacto se verificó la versión instalada 0.1.5, pues la documentación latest se identifica como desarrollo 0.1.6.

La primera ejecución de pruebas encontró un error propio en el lector: se comparaba DatetimeIndex.asi8 con una constante en nanosegundos, aunque pandas 3 puede almacenar otra resolución temporal. Se corrigió usando diferencias de timestamps y Timedelta(hours=1); no se cambiaron fechas, datos ni dependencias para ocultar el fallo. Los resultados finales de las pruebas se conservan en el informe.

## Arquitectura

- `src/rk4_solver.py`: parámetros, flujos, derivada vectorial, estabilidad, paso RK4 e integración de una hora. No importa AgentPy ni pandas.
- `src/simulation_engine.py`: función pura `simulate`, validaciones por intervalo, estructura `SimulationResult` y lector de ventanas `load_window`. Sólo el lector utiliza pandas; no hay operaciones de pandas dentro de subpasos.
- `src/agent_model.py`: `DepositAgent` representa cada depósito, `FourDepositModel` administra cuatro instancias y `simulate_agentpy` ejecuta una ventana completa.
- `scripts/probar_simulacion.py`: ejecuta pruebas y una demostración matemática controlada, genera el informe y permite una medición opcional de rendimiento artificial.

Las ecuaciones se definen una sola vez en `rhs(t,state,arrival_rate,parameters)` y los flujos en `transfer_rates`. Tanto el motor independiente como el modelo AgentPy llaman a la misma `integrate_hour`. No hay un agente por pedido.

Cada agente tiene su `id` de AgentPy, posición, nombre y nivel flotante. `outgoing_flow` calcula un diagnóstico instantáneo mediante la función común de flujos, con salida cero para X4. `receive_state` recibe un nivel ya calculado; no integra ni mueve pedidos. El modelo lee los cuatro niveles antes de resolver, calcula y valida un nuevo vector completo y después publica sus componentes. Aunque las cuatro asignaciones se realizan en un bucle, ninguna asignación alimenta otro cálculo: la actualización matemática es simultánea.

Un paso de AgentPy corresponde a una hora del proceso, no a un subpaso RK4. `update` registra niveles iniciales y posteriores mediante Agent.record. Model.record guarda purchases y q12_integrated/q23_integrated/q34_integrated, con una fila inicial de referencia de flujos cero. Los arreglos del modelo guardan estados y transferencias por hora, y el resultado incluye el error de conservación. `end` publica el error máximo mediante Model.report. No se duplican registros de todas las etapas RK4.

## Uso del motor

```python
from src.rk4_solver import Parameters
from src.simulation_engine import simulate, load_window
from src.agent_model import simulate_agentpy

# Ejemplo matemático artificial: estos valores NO están calibrados para Olist.
parameters = Parameters(alpha=0.4, beta=0.2, gamma=0.1)
result = simulate([100, 50, 30, 5], [0, 20, 3, 0], parameters, substeps=4)
agent_result, model = simulate_agentpy(
    [100, 50, 30, 5], [0, 20, 3, 0], parameters, substeps=4
)

# Lectura histórica solamente: no ejecuta ni evalúa una simulación histórica.
window = load_window(
    'data/processed', '2018-03-02 22:00:00', '2018-03-03 02:00:00'
)
```

`simulate(initial, arrivals, parameters, substeps=4)` recibe N llegadas horarias y retorna:

| Campo | Forma y unidad |
|---|---|
| times | N+1 tiempos relativos, horas, desde cero |
| states | (N+1,4), pedidos, incluida condición inicial |
| transfers | (N,3), integrales de q12, q23, q34 por hora, pedidos |
| arrivals | (N,), compras por intervalo, pedidos |
| conservation_errors | N+1 errores firmados, pedidos |
| max_conservation_error | Máximo error absoluto, pedidos |

Al durar exactamente una hora cada intervalo, las transferencias integradas tienen el mismo valor numérico que las tasas medias por hora, pero no son el flujo instantáneo del extremo. Las transferencias se integran con los mismos pesos y estados intermedios de RK4, preservando su correspondencia con los cambios de nivel. Una ventana sin intervalos retorna sólo el estado inicial y transferencias de forma (0,3).

`simulate_agentpy` recibe los mismos argumentos y retorna `(SimulationResult, FourDepositModel)`. La semilla del envoltorio se fija en cero y no hay decisiones aleatorias. Se prueba igualdad exacta de niveles y transferencias, sin ampliar tolerancias para ocultar diferencias.

## Entrada histórica y condiciones iniciales

`load_window(directory,start,end)` comprueba columnas, fechas válidas, cortes únicos ordenados, separación de una hora y coincidencia de mallas. Rechaza huecos, duplicados, ventanas invertidas o fuera de cortes disponibles. Comprueba compras enteras no negativas, equivalencia con compras_por_hora, relaciones de niveles con A,B,C,D y diferencias de A con compras. Las verificaciones completas del archivo son controles de integridad, no un ajuste a observaciones futuras.

La selección retorna los cortes inclusivos [start,end], únicamente el estado inicial y compras con fechas en (start,end]. No retorna transferencias reales como entradas. Las columnas reales `aprobaciones`, `despachos` y `entregas` no se consumen por el integrador. En start=2018-03-02 22:00:00 se lee (113,586,3005,53963), total 57667. La prueba de este corte es exclusivamente de lectura/alineación; no simula la ventana reservada para validación.

Cada fila s_k aporta compras de (s_{k−1},s_k]. Ese conteo dividido por una hora se mantiene constante durante todos los subpasos de esa hora, incluidos K1–K4. El último K4 no toma compras de la hora siguiente. No se interpola, extrapola ni incorpora la fila inicial como intervalo adicional. Las condiciones iniciales provienen de start, y no se corrigen con estados posteriores.

## Método y controles físicos

El estado es un vector NumPy de cuatro valores flotantes. RK4 calcula K1, K2, K3, K4 a partir de vectores completos y retorna otro arreglo, sin modificar el inicial por referencia. `rk4_step` permite h explícito; `simulate` e `integrate_hour` usan `substeps` entero positivo, con h=1/substeps para que ningún paso cruce una hora. El candidato es substeps=4, h=0,25 h.

Los parámetros, estados iniciales, entradas y pasos deben ser finitos y físicamente admisibles. Se rechazan coeficientes negativos y substeps no enteros, booleanos o no positivos. Se comprueba |R(−hk)|≤1 con R(z)=1+z+z²/2+z³/6+z⁴/24 para cada coeficiente. La tolerancia 1e−14 de esa comprobación sólo absorbe redondeo del polinomio de estabilidad.

Además se exige positividad estricta de estados finales e intermedios de RK4: no se toleran valores negativos ni se recortan. Es una decisión conservadora que puede rechazar un paso linealmente estable si sus etapas intermedias no son físicas. Se levanta `NumericalError` con indicación de reducir h. El usuario puede aumentar substeps; no hay adaptación silenciosa ni cambio automático de parámetros.

Se verifican finitud, flujos no negativos y X4 no decreciente. Después de cada hora se verifica:

`sum(X)=sum(X_inicial)+sum(compras_integradas)`

con tolerancia `1e-8*max(1,total_esperado)`, en pedidos. Esta tolerancia propuesta en fase 2 cubre acumulación de errores de redondeo; no permite corregir el estado. También se comprueba que el incremento de cada nivel coincide con compras y transferencias integradas. La conservación puede cumplirse con parámetros predictivamente incorrectos: no constituye validación del modelo logístico.

## Verificación numérica

Las pruebas controladas cubren equilibrio sin flujos, sólo compras, decaimiento exponencial con transferencia a la etapa siguiente, balance de cuatro estados y agentes, discontinuidades horarias, mutabilidad, entradas inválidas, ventanas corruptas y reproducibilidad. También prueban rechazo de un caso inestable y de otro linealmente estable que genera una etapa interna negativa; un paso menor permite integrar el primero.

La convergencia se evalúa con substeps=4,8,16 (h=0,25; 0,125; 0,0625 h), comparando los mismos cortes horarios. Una solución analítica exponencial verifica el orden de error; una matriz aumentada de 5×5 y `scipy.linalg.expm` proporciona una referencia independiente del sistema completo con entrada constante por hora, incluso cuando hay coeficientes cero sin requerir invertir la matriz singular del sistema.

En el caso artificial de referencia se exige error decreciente y reducción superior a un factor 14 al dividir h por dos, consistente con el orden cuatro. Además se verifican los criterios de fase 2 entre las dos mallas más finas: máximo ≤0,1 pedido y NRMSE numérico ≤0,001 por estado. Las escalas de esta comprobación provienen exclusivamente del caso matemático artificial, con mínimo un pedido. No son escalas estimadas de Olist ni métricas predictivas. Los parámetros futuros deberán repetir convergencia con sus escalas de entrenamiento, porque estas pruebas no garantizan precisión para todos los coeficientes.

## Ejecución y reproducción (PowerShell)

Desde la raíz del proyecto, con Python 3.12:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe scripts/probar_simulacion.py
```

Alternativa con uv si python no está disponible en PATH:

```powershell
uv venv .venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe scripts/probar_simulacion.py --benchmark
```

El script guarda versiones, salida real de pytest, errores de referencia/conservación y comparación con AgentPy en `reports/pruebas_motor_simulacion.txt`. Sale con código no cero si falla la suite. `--benchmark` añade 18.291 intervalos de llegadas artificiales para medir tiempo de ejecución y equivalencia; no ejecuta todo el dataset con parámetros arbitrarios. El tiempo medido depende del equipo y no representa duración del proceso logístico. Los arreglos de salida son O(N); sólo se retienen datos horarios relevantes y cuatro agentes.

## Límites y siguiente fase

Los coeficientes .4, .2, .1 y los demás valores de las pruebas son exclusivamente ejemplos matemáticos. No son estimaciones de Olist. La implementación no afirma precisión frente a niveles históricos y no elimina el sesgo de selección de pedidos entregados completos. La siguiente fase requerirá estimación con entrenamiento, repetición de controles numéricos con esos parámetros y evaluación reservada según el plan. Las fases 1 y 2 y sus resultados se mantienen como antecedentes; sus referencias a RK4 como trabajo futuro describen su alcance en aquel momento.
