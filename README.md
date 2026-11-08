# Olist: auditoría y reconstrucción de cuatro depósitos

Fase 1: cohorte histórica entregada con eventos verificables; sin simulación.
El ZIP original permanece intacto en la raíz. Se lee directamente; data/raw se reserva para futuras fuentes originales.

## Ejecución (PowerShell, Python 3.12)

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/analizar_dataset.py
.venv/Scripts/python.exe -m pytest -q
```

Alternativa si se utiliza uv: `uv venv .venv --python 3.12` y `uv pip install --python .venv/Scripts/python.exe -r requirements.txt`.
Para otro archivo use `--zip RUTA`. No se descarga ni sustituye el dataset.

## Estructura

- `src/data_processing.py`: lectura, auditoría, selección, reconstrucción vectorizada y validaciones.
- `scripts/analizar_dataset.py`: ejecución, exportaciones, informe y gráficos.
- `tests/test_data_processing.py`: cronología, conservación, transferencias, reproducibilidad y límites horarios.
- `data/raw/`: reservado; el ZIP original se conserva en la raíz.
- `data/processed/`: CSV regenerables.
- `reports/`: informe de auditoría, resultados de pruebas y dos gráficos PNG.

Los cortes horarios incluyen eventos con fecha menor o igual al corte. Los flujos cuentan (t−1h,t]. Las fechas originales no se redondean. Tasas en pedidos/hora son observadas, no calibradas. X4 es entrega terminal acumulada.

Véase `reports/auditoria_dataset.md` para cifras, exclusiones, duraciones y limitaciones. Esta cohorte no representa el inventario operativo completo: omite pedidos no entregados, fechas incompletas e inconsistencias. Antes de las EDO hay que definir censura, cancelaciones, población, condiciones iniciales y calibración.

## Fase 2: formulación matemática (sin implementación numérica)

- [Modelo matemático](docs/modelo_matematico.md): balances, unidades, condiciones iniciales, entrada horaria y especificación de RK4.
- [Plan de calibración y validación](docs/plan_calibracion_validacion.md): corte temporal 70/30, mínimos cuadrados restringidos, métricas y control de filtración futura.
- [Escenarios propuestos](docs/escenarios_propuestos.md): base, incremento hipotético de β e incremento hipotético de γ.

No se han calibrado parámetros ni ejecutado EDO o escenarios. La formulación queda pendiente de revisión antes de implementar la siguiente fase.

## Fase 3: motor continuo RK4 y cuatro agentes

Se añadió un motor NumPy independiente de AgentPy y un modelo AgentPy con cuatro depósitos agregados. Comparten la misma integración vectorial y permiten variar los coeficientes y subpasos por hora. Se verifican conservación, estabilidad y positividad sin recortar estados.

- `src/rk4_solver.py`: ecuaciones y RK4.
- `src/simulation_engine.py`: trayectoria pura y selección de ventanas históricas.
- `src/agent_model.py`: cuatro agentes y coordinación del motor.
- `tests/test_rk4_solver.py`, `tests/test_agent_model.py`, `tests/test_simulation_engine.py`: pruebas nuevas junto con las de fase 1.
- [Implementación y comandos](docs/implementacion_rk4_agentpy.md).
- [Informe ejecutado](reports/pruebas_motor_simulacion.txt).

Entorno comprobado: Python 3.12.13 y AgentPy 0.1.5, versiones exactas en requirements.txt.

```powershell
.venv/Scripts/python.exe scripts/probar_simulacion.py
```

Para una medición opcional con 18.291 intervalos exclusivamente artificiales:

```powershell
.venv/Scripts/python.exe scripts/probar_simulacion.py --benchmark
```

La demostración no ejecuta una simulación completa sobre Olist. Sus coeficientes son ejemplos matemáticos, sin calibración ni interpretación operativa. La lectura del corte reservado comprueba únicamente condiciones iniciales y alineación. Calibración, validación estadística, escenarios e interfaz siguen pendientes.

## Fase 4A: calibración y diagnóstico sólo en entrenamiento

Se añadieron `src/calibration.py`, `src/calibration_metrics.py`, `scripts/calibrar_modelo.py` y `tests/test_calibration.py`. El lector de calibración carga únicamente las primeras 12.804 filas horarias, hasta el 2 de marzo de 2018 a las 22:00. Las exposiciones preliminares se censuran en ese corte. La reserva final no se evalúa.

```powershell
.venv/Scripts/python.exe scripts/calibrar_modelo.py
.venv/Scripts/python.exe -m pytest -q
```

No se necesitan dependencias adicionales. El ajuste usa mínimos cuadrados restringidos y un propagador auxiliar por exponencial matricial de las mismas EDO. La reproducción definitiva y las métricas emplean RK4; los cuatro agentes producen resultados exactamente equivalentes. La evaluación cronológica interna usa el 80/20 del entrenamiento y después se reajusta el modelo con todo ese entrenamiento, sin utilizar el 30 % reservado.

- [Informe de calibración y diagnóstico](reports/calibracion_modelo.md).
- [Parámetros, configuraciones y metadatos](reports/parametros_calibrados.json).
- [Métricas de entrenamiento](reports/metricas_entrenamiento.csv).
- [Evaluación interna](reports/metricas_evaluacion_interna.csv).
- [Pruebas ejecutadas](reports/pruebas_calibracion.txt).

Las seis gráficas están en `reports/graficas_calibracion/`; incluyen niveles, entregas incrementales, pendientes totales y ampliación semanal. Las tasas son coeficientes efectivos del modelo agregado, no capacidades físicas demostradas de Olist. Hay limitaciones de ajuste, especialmente en X1 y en estabilidad temporal; la convergencia del optimizador no acredita precisión predictiva. La validación final, los escenarios y la interfaz continúan pendientes.

## Fase 5: una variante con aprobación rápida

Se conserva el modelo base y se añadió únicamente la fracción efectiva p de compras que entra directamente en T2. Ambos modelos usan cuatro estados, los mismos cuatro agentes y un motor RK4 compartido. El parámetro p se selecciona explícitamente mediante `RapidParameters`; con `Parameters` se mantiene el modelo base.

```python
from src.rk4_solver import Parameters, RapidParameters
from src.simulation_engine import simulate
from src.agent_model import simulate_agentpy

# Valores artificiales de ejemplo, sin interpretación como capacidades de Olist.
base = Parameters(0.1, 0.01, 0.004)
candidate = RapidParameters(0.1, 0.01, 0.004, p=0.25)
result = simulate([10, 20, 30, 40], [5, 10, 0], candidate)
agent_result, model = simulate_agentpy([10, 20, 30, 40], [5, 10, 0], candidate)
```

`result.transfers[:,0]` sigue siendo la transferencia convencional T1→T2; `result.rapid_arrivals` es la entrada directa en T2. Las aprobaciones totales simuladas suman ambas, sin duplicar compras.

Para reproducir la comparación, los ajustes y todas las pruebas:

```powershell
.venv/Scripts/python.exe scripts/comparar_modelos.py
```

El script usa exclusivamente el 70 % de desarrollo, cuatro ventanas expansivas con evaluación interna de 1.920 horas cada una y escalas iguales para ambos modelos calculadas sólo en cada período de ajuste. Conserva `reports/parametros_calibrados.json` y los resultados de fases anteriores. No requiere dependencias nuevas.

- [Hipótesis y protocolo fijado antes del cálculo](docs/modelo_aprobacion_rapida.md).
- [Informe comparativo y decisión](reports/comparacion_modelos.md).
- [Métricas completas por modelo, período y ventana](reports/comparacion_modelos.csv).
- [Parámetros y metadatos del candidato](reports/parametros_aprobacion_rapida.json).
- [Modelo seleccionado y recalibrado con todo el desarrollo](reports/modelo_seleccionado_desarrollo.json).
- [Pruebas de comparación](reports/pruebas_comparacion_modelos.txt).

Los gráficos están en `reports/graficas_comparacion/`. La decisión conserva el modelo base: la mejora mediana interna de X1 del candidato no alcanza el 15 % requerido. La evaluación de desarrollo reutilizada no constituye validación independiente; el 30 % final, los escenarios y Streamlit permanecen sin ejecutar.

## Fase 4B: validación final del modelo base congelado

Se añadieron `src/validation.py`, `scripts/validar_modelo.py` y `tests/test_validation.py`. La evaluación utiliza el período 2018-03-02 22:00 a 2018-10-17 14:00: 5.488 intervalos y 5.489 estados. Parte una sola vez del estado observado (113,586,3005,53963), con parámetros y escalas de entrenamiento congelados. No recalibra, no evalúa el candidato rápido y no modifica las ecuaciones.

```powershell
.venv/Scripts/python.exe scripts/validar_modelo.py
```

El script ejecuta RK4 y AgentPy, verifica conservación y equivalencia, comprueba convergencia sin cambiar parámetros, genera diez gráficas y ejecuta las pruebas anteriores y nuevas. No requiere dependencias adicionales. Las métricas por cuatro bloques de 1.372 horas son cortes de una trayectoria continua, sin reinicializaciones.

- [Informe de validación final](reports/validacion_final.md).
- [Métricas finales](reports/metricas_validacion.csv).
- [Métricas por bloque](reports/metricas_por_bloque.csv).
- [Trayectoria observada y simulada](reports/trayectoria_validacion.csv).
- [Resumen y huellas SHA-256](reports/resumen_validacion.json).
- [Pruebas ejecutadas](reports/pruebas_validacion.txt).

Los resultados corresponden a la categoría C: el motor es matemáticamente correcto, pero las tres etapas pendientes incumplen NMAE/NRMSE y no sustentan recomendaciones operativas confiables. La reserva final ya fue evaluada; repetir el comando reproduce la misma evaluación y no crea una prueba independiente nueva. Todo desarrollo posterior motivado por estos errores necesitará otra reserva para evaluación independiente. Las referencias a una reserva intacta en informes de fases anteriores describen su situación histórica. Se conservan esos archivos sin sobrescribirlos. No se ejecutaron escenarios ni Streamlit.

## Escenarios hipotéticos del modelo base — fase 5

La validación previa sigue siendo categoría C. Se implementaron exactamente E0 (base), E1 (beta ×1,20) y E2 (gamma ×1,20), sin recalibrar ni modificar el motor, las llegadas o las condiciones iniciales dentro de cada ventana. Son experimentos del modelo, sin evidencia de mejoras operativas reales para Olist.

```powershell
.venv/Scripts/python.exe scripts/ejecutar_escenarios.py
.venv/Scripts/python.exe scripts/ejecutar_escenarios.py --sensibilidad
```

El primer comando compara tres trayectorias principales, del 2 de marzo al 17 de octubre de 2018, en horizontes de 168, 720, 1440 y 5488 horas. El segundo añade las mismas tres configuraciones en enero de 2018 (744 horas): seis trayectorias comparadas, cada una ejecutada con RK4 y AgentPy para comprobar equivalencia. Cada horizonte es una lectura de la misma trayectoria; no reinicializa estados. Las pruebas automáticas se ejecutan y registran al finalizar.

- `src/scenarios.py`: definiciones, carga, ejecución y controles de los tres escenarios.
- `src/scenario_metrics.py`: áreas trapezoidales horarias, medias temporales, indicadores y diferencias.
- [Informe de escenarios](reports/escenarios_resultados.md).
- [Indicadores por horizonte](reports/indicadores_horizontes.csv).
- [Resumen de ventanas completas](reports/indicadores_escenarios.csv).
- [Trayectorias](reports/trayectorias_escenarios.csv).
- [Metadatos y huellas](reports/comparacion_escenarios.json).
- [Pruebas ejecutadas](reports/pruebas_escenarios.txt).

Los PNG están en `reports/graficas_escenarios/`, con colores fijos por configuración. Las áreas se calculan sobre todos los cortes horarios mediante trapecios (pedidos·hora); las medias son área/duración. Las diferencias porcentuales usan 100·(escenario−base)/base, sin porcentaje si el denominador es cero. X4 se presenta como incremento desde el inicio.

La API reutilizable para una futura interfaz permite obtener niveles, flujos, entradas y metadatos sin depender de gráficos ni Streamlit:

```python
from src.scenarios import load_base_parameters, load_scenario_window, run_official_scenarios

base = load_base_parameters('reports')
window = load_scenario_window('data/processed')
runs = run_official_scenarios(window, base)
# Cada elemento contiene definition, window, result, indicators y checks.
```

La comparación calculada favorece E2 en los horizontes definidos para estas ventanas; no se extrapola a otras operaciones o a efectos causales reales. Se preservaron parámetros, datos, validación y resultados anteriores mediante SHA-256. La interfaz y sus dependencias se incorporan en la fase 6 descrita a continuacion.


## Aplicación interactiva — fase 6

```powershell
.venv/Scripts/python.exe -m streamlit run app.py
```

Cinco pantallas: vista general, simulación, escenarios, datos y validación, y metodología. Reproductor con pausa, reinicio, navegación horaria y cinco velocidades; dos ventanas y seis trayectorias oficiales verificadas. Las tarjetas de los cuatro agentes, flujos y marcador comparten un índice. El modo personalizado ejecuta RK4 y cuatro agentes AgentPy sólo al enviar el formulario, en memoria y sin sobrescribir resultados.

Streamlit 1.67.0 y Plotly 7.1.0; AgentPy 0.1.5 y Python 3.12.13. Dependencias fijadas en requirements.txt. Instalación, interpretación, limitaciones y revisión visual: [guía de uso](docs/guia_uso_streamlit.md). Pruebas: `.venv/Scripts/python.exe -m pytest -q`; registro: [pruebas del dashboard](reports/pruebas_dashboard.txt).

La validación sigue siendo categoría C. Los escenarios son hipotéticos; no acreditan mejoras operativas reales. No se modifican la calibración ni los artefactos científicos anteriores. La animación requiere revisión visual manual: no hubo navegador disponible en esta sesión.

## Cuatro tanques virtuales conectados — rediseño visual

Simulación ahora presenta cuatro tanques SVG persistentes con bloques agregados, llenado proporcional y conexiones animadas según las transferencias horarias verificadas. Las escalas se mantienen entre E0/E1/E2; T4 muestra altura incremental y total acumulado separado. Se conservan controles, RK4, AgentPy y artefactos originales. Se compactó el encabezado y se mejoraron terminología, avisos y formato español de tablas y cifras, sin redondear datos exportados.

Detalles, archivos e instrucciones para las capturas y grabación de revisión visual: [rediseño de tanques](docs/redisenio_tanques.md). Pruebas de esta iteración: [registro](reports/pruebas_tanques.txt). No hay dependencias adicionales.

## Refinamiento temporal y comunicación académica — Prompt 10

Se conserva el diseño de los tanques. Los datos del instante actual se publican juntos dentro del componente, con una revisión que descarta actualizaciones atrasadas. Esto evita mezclar la fecha de un SVG anterior con indicadores nativos más recientes. La gráfica móvil de Simulación se incluye en esa misma actualización; las gráficas y tablas de Escenarios se conservan. Se retira el recuadro lateral, se simplifican los mensajes y se mantienen intactas las métricas originales y la clasificación C en el detalle técnico.

Investigación, límites de la verificación y archivos: [refinamiento de interfaz](docs/refinamiento_interfaz.md). Resultado de las pruebas: [registro](reports/pruebas_refinamiento.txt). No cambia el comando de inicio ni se añaden dependencias de la aplicación.
