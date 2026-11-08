# Calibración del modelo — fase 4A

## Objetivo y población
Estimar tres coeficientes efectivos de primer orden que reproduzcan X1–X3. Se conservan las cuatro EDO de fase 2, el motor RK4 y cuatro agentes de fase 3. Los resultados describen ajuste en entrenamiento, no validación predictiva final ni capacidades físicas de Olist.

Se usaron exclusivamente 12803 intervalos horarios desde 2016-09-15 11:00:00 hasta 2018-03-02 22:00:00, y 12804 estados incluidos los iniciales. Estado inicial leído: [0.0, 0.0, 0.0, 0.0]. Compras integradas: 57667; A final: 57667. Se verificaron mallas iguales, fechas únicas, orden horario, flujos/acumulados coherentes y extremo derecho de cada intervalo.

El lector de calibración limita nrows=12804 antes de cualquier análisis; no carga las filas horarias reservadas. No usa el lector general que verifica la malla completa. La membresía de la cohorte ya fue elegida retrospectivamente por entregas completas: se mantiene ese sesgo y no se afirma validación prospectiva. En los timestamps originales, las fechas posteriores al corte se censuran antes de convertirlas o calcular duraciones. Los pedidos aún pendientes aportan exposición hasta el corte, sin su fecha futura de salida. Las pruebas antiguas siguen comprobando integridad global, pero ningún resultado de reserva entra al ajuste o diagnóstico de esta fase.

## Estimación preliminar por exposición
Para cada etapa: k0=transferencias observadas / exposición exacta. La exposición es Σ max(0,min(salida,corte)−max(entrada,inicio)), en horas, sólo para entradas ya observadas; si no hay salida observada se usa el corte. Esto es una razón de conteos/exposición, compatible con un estimador de riesgo exponencial bajo supuestos, no el mínimo cuadrado de flujos por intervalo ni el inverso de una mediana. Eventos simultáneos pueden aportar transferencia sin duración positiva; la exposición agregada de las tres etapas es informativa.

| parametro | transferencias | exposicion_pedidos_hora | pendientes_al_corte | tasa_inicial |
|---|---|---|---|---|
| alpha | 57554 | 568847 | 113 | 0.101177 |
| beta | 56968 | 4.22952e+06 | 586 | 0.0134691 |
| gamma | 53963 | 1.28545e+07 | 3005 | 0.00419797 |

Las transferencias de esta tabla coinciden exactamente con las sumas del CSV horario de entrenamiento.

## Método y reproducibilidad
Se utilizó scipy.optimize.least_squares, método TRF, pérdida lineal de residuos (X_sim−X_obs)/s_i, con s_i=max(1,media de X_i en los N cortes objetivo de entrenamiento). Escalas: [44.39279856283684, 330.3622588455831, 1004.1355932203389]. Se excluye la fila inicial de la pérdida. Cada etapa aporta N residuos; X4 no entra. La función minimizada por SciPy es 0,5·Σr²; MSE normalizado=Σr²/(3N), proporcional al objetivo académico.

Cotas 0≤α,β,γ<∞: la no negatividad tiene justificación física y no hay cota superior arbitraria. Las exploraciones de coeficientes nulos usan el propagador bien definido sin invertir matrices. Con tasa cero se bloquea una transición y puede acumularse carga. Los valores ajustados no están en frontera (active_mask=[0, 0, 0]); el diagnóstico de cero y 1e−8 se guarda en diagnostico_frontera_cero.csv, sin modificar los otros parámetros y sin constituir perfiles reoptimizados.

Tolerancias ftol=xtol=gtol=1e−10; jacobiano por diferencias centrales, x_scale=jac, max_nfev=200. Inicializaciones prefijadas: 0,5, 1 y 2 veces tasas de exposición del subperíodo correspondiente. Se elige el menor costo entre convergencias satisfactorias. No se usaron coeficientes artificiales de pruebas.

| coeficiente | inicial_exposicion | ajustado | ajuste_interno | reajuste_bloque_posterior | cambio_bloques_pct |
|---|---|---|---|---|---|
| alpha | 0.101177 | 0.102024 | 0.105671 | 0.0999825 | -5.38288 |
| beta | 0.0134691 | 0.0132408 | 0.014631 | 0.0125491 | -14.2295 |
| gamma | 0.00419797 | 0.00407191 | 0.00475676 | 0.00365619 | -23.137 |

Todos los coeficientes están en hora⁻¹.

| initial_factor | cost_half_sse | mean_normalized_squared_error | nfev | njev | actual_residual_calls | success | status | optimality | seconds |
|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 2473.29 | 0.128787 | 7 | 7 | 49 | True | 2 | 0.00138714 | 0.0465656 |
| 1 | 2473.29 | 0.128787 | 4 | 4 | 28 | True | 2 | 0.00269104 | 0.0227925 |
| 2 | 2473.29 | 0.128787 | 5 | 5 | 35 | True | 2 | 0.000431235 | 0.0272897 |

La ejecución seleccionada terminó con: ``ftol` termination condition is satisfied.`. Costo=2473.28898; MSE normalizado=0.12878695. El criterio de parada no demuestra óptimo global. Dispersión relativa pico a pico entre soluciones de las tres inicializaciones: [3.2946428479571275e-08, 6.116825515800832e-10, 4.465145654864279e-10]. Los detalles de iniciales/finales, mensajes, versiones, tiempos, metadatos y huellas de código/arrays de entrenamiento están en parametros_calibrados.json. nfev no incluye todas las evaluaciones de diferencias finitas; se registran también llamadas reales.

## Propagador auxiliar y reproducción definitiva
La matriz lineal se construye evaluando rhs existente sobre vectores base. Se aumenta a 5×5 para la entrada constante y se calcula una exponencial por conjunto de parámetros. Se aplica causalmente x[k+1]=F x[k]+g compras[k]. lfilter ejecuta las recurrencias triangulares; no suaviza datos ni reduce intervalos. Es la solución de las mismas EDO por tramos, exacta salvo redondeo. Se contrastó con RK4 en pruebas artificiales y en todo el entrenamiento. Las trayectorias definitivas, métricas y gráficas usan RK4 con h=0,25 y AgentPy produjo exactamente los mismos niveles y transferencias. No se imponen transferencias históricas durante la simulación.

## Métricas de entrenamiento (reproducción RK4)
Errores firmados=simulado−observado. NMAE/NRMSE usan las medias observadas sólo de entrenamiento (mínimo 1); X4 usa entregas incrementales y P usa su propia escala. Error de máximo compara amplitudes máximas, mientras error absoluto máximo compara instantes iguales. Todas las métricas absolutas se expresan en pedidos.

| variable | escala | MAE | RMSE | NMAE | NRMSE | error_absoluto_maximo | maximo_observado | maximo_simulado | error_nivel_maximo | error_nivel_maximo_absoluto | error_final | sesgo_medio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| X1 | 44.3928 | 13.2255 | 22.5291 | 0.29792 | 0.507495 | 255.278 | 488 | 546.685 | 58.6847 | 58.6847 | 19.8539 | -0.341087 |
| X2 | 330.362 | 69.1095 | 99.7243 | 0.209193 | 0.301863 | 617.436 | 2011 | 1492.5 | -518.505 | 518.505 | 270.379 | 4.01017 |
| X3 | 1004.14 | 142.448 | 194.937 | 0.141861 | 0.194135 | 687.565 | 3402 | 3044.72 | -357.277 | 357.277 | -548.299 | 36.0192 |
| X4_incremental | 15774.9 | 166.47 | 229.916 | 0.0105528 | 0.0145748 | 794.198 | 53963 | 54221.1 | 258.067 | 258.067 | 258.067 | -39.6883 |
| P | 1378.89 | 166.47 | 229.916 | 0.120727 | 0.16674 | 794.198 | 4562 | 4271.41 | -290.592 | 290.592 | -258.067 | 39.6883 |

### Transferencias integradas por hora
Comparación de las cuadraturas RK4 con conteos observados de cada hora, sin imponerlos como entradas. Unidades absolutas: pedidos por intervalo de una hora (mismo valor numérico que tasa media en pedidos/hora).

| variable | escala | MAE | RMSE | NMAE | NRMSE | error_absoluto_maximo | maximo_observado | maximo_simulado | error_nivel_maximo | error_nivel_maximo_absoluto | error_final | sesgo_medio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aprobaciones | 4.49535 | 3.04841 | 6.78804 | 0.678126 | 1.51001 | 173.045 | 182 | 55.3914 | -126.609 | 126.609 | 4.58352 | -0.00155072 |
| despachos | 4.44958 | 5.63829 | 9.16401 | 1.26715 | 2.05952 | 80.1344 | 91 | 19.7631 | -71.2369 | 71.2369 | -29.6757 | -0.0226691 |
| entregas | 4.21487 | 4.91374 | 7.72447 | 1.16581 | 1.83267 | 58.3997 | 63 | 12.3979 | -50.6021 | 50.6021 | -11.9992 | 0.0201567 |

## Evaluación cronológica interna
Se fijó m=floor(0,8·12803)=10242. Ajuste inicial: 2016-09-15 11:00:00 a 2017-11-16 05:00:00, 10242 intervalos. Evaluación interna posterior: 2017-11-16 05:00:00 a 2018-03-02 22:00:00, 2561 intervalos. Se inicializó una vez desde el estado observado de ese corte, con compras conocidas; no se corrigió la trayectoria con estados posteriores. Escalas de ambos bloques fijadas en el ajuste inicial. Este experimento no es pronóstico de demanda.

| variable | escala | MAE | RMSE | NMAE | NRMSE | error_absoluto_maximo | maximo_observado | maximo_simulado | error_nivel_maximo | error_nivel_maximo_absoluto | error_final | sesgo_medio | periodo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| X1 | 31.06 | 9.4025 | 15.3015 | 0.30272 | 0.492644 | 135.954 | 190 | 104.353 | -85.6468 | 85.6468 | -20.2555 | -0.51479 | ajuste_interno_80pct |
| X2 | 224.244 | 48.5949 | 69.0364 | 0.216705 | 0.307862 | 332.115 | 821 | 509.365 | -311.635 | 311.635 | -258.152 | -7.01402 | ajuste_interno_80pct |
| X3 | 649.674 | 50.3745 | 84.0834 | 0.0775382 | 0.129424 | 389.255 | 1305 | 1336.74 | 31.7429 | 31.7429 | 142.743 | -8.95848 | ajuste_interno_80pct |
| X4_incremental | 9120.78 | 68.9016 | 108.133 | 0.00755436 | 0.0118557 | 493.598 | 31076 | 31211.7 | 135.664 | 135.664 | 135.664 | 16.4873 | ajuste_interno_80pct |
| P | 904.979 | 68.9016 | 108.133 | 0.0761362 | 0.119487 | 493.598 | 2041 | 1928.07 | -112.935 | 112.935 | -135.664 | -16.4873 | ajuste_interno_80pct |
| X1 | 31.06 | 27.0645 | 40.2055 | 0.871359 | 1.29444 | 257.902 | 488 | 533.915 | 45.9146 | 45.9146 | 15.8137 | -7.16057 | evaluacion_interna_20pct |
| X2 | 224.244 | 147.844 | 193.341 | 0.659297 | 0.86219 | 717.866 | 2011 | 1418.95 | -592.045 | 592.045 | 193.61 | -101.195 | evaluacion_interna_20pct |
| X3 | 649.674 | 509.139 | 570.544 | 0.783683 | 0.8782 | 977.938 | 3402 | 2781.44 | -620.557 | 620.557 | -876.494 | -488.018 | evaluacion_interna_20pct |
| X4_incremental | 9120.78 | 599.525 | 670.642 | 0.0657317 | 0.0735291 | 1258.7 | 22887 | 23554.1 | 667.07 | 667.07 | 667.07 | 596.373 | evaluacion_interna_20pct |
| P | 904.979 | 599.525 | 670.642 | 0.662474 | 0.741059 | 1258.7 | 4562 | 3968.61 | -593.394 | 593.394 | -667.07 | -596.373 | evaluacion_interna_20pct |

La predicción del bloque interno usa sólo parámetros del bloque inicial. Adicionalmente se reajustó el bloque posterior exclusivamente como diagnóstico de estabilidad; esos coeficientes y su cambio porcentual aparecen en la tabla de parámetros. No se utilizaron para corregir su evaluación fuera de ajuste. El bloque posterior deja de ser una prueba independiente para futuras decisiones de diseño. Tras este diagnóstico se recalibró todo el 70 %, manteniendo ecuaciones, pérdida e hiperparámetros prefijados. Ninguna fila del 30 % reservado fue evaluada.

## Diagnóstico del modelo de primer orden
- X1: sesgo medio -0.341 pedidos; NMAE=0.298, NRMSE=0.507. Sesgos mensuales entre -7.852 y 17.312; por hora entre -7.269 y 4.862; por día semanal entre -17.916 y 7.634.
- X2: sesgo medio 4.010 pedidos; NMAE=0.209, NRMSE=0.302. Sesgos mensuales entre -72.612 y 174.060; por hora entre -12.223 y 23.686; por día semanal entre -79.870 y 65.459.
- X3: sesgo medio 36.019 pedidos; NMAE=0.142, NRMSE=0.194. Sesgos mensuales entre -499.966 y 246.190; por hora entre 34.926 y 37.143; por día semanal entre 15.312 y 59.227.

La mayor dificultad relativa, medida por NRMSE por etapa, corresponde a **X1**. Los errores absolutos deben compararse también porque las escalas de las etapas difieren. Los residuos desagregados por mes, hora y día (0=lunes) están en diagnostico_calendario_entrenamiento.csv. Las diferencias calendario son descriptivas, sin prueba causal ni significación estadística asumida.

El supuesto de aprobación homogénea de riesgo constante puede fallar ante aprobaciones casi inmediatas junto con esperas largas: la entrada uniforme dentro de cada hora también pierde orden intrahorario. Sesgos de X2 y X3 que cambian con el período son compatibles con calendario operativo, heterogeneidad y coeficientes no estacionarios; son hipótesis para investigar, no causas demostradas. No se cambió la estructura matemática para mejorar artificialmente el ajuste.

Identificabilidad local: valores singulares del jacobiano escalado por parámetros [147.06677249421668, 143.40276761393494, 141.7007250254609], condición 1.03787. Rango tres y condición moderada apoyan sensibilidad local diferenciable de las tres tasas; la estabilidad entre inicializaciones aporta evidencia adicional. No demuestran identificabilidad global, ausencia de sesgo ni parámetros físicos únicos. Hay autocorrelación y heterogeneidad; no se presentan intervalos de confianza basados en errores independientes.

## Controles numéricos con parámetros finales
| subpasos | h_horas | segundos | error_maximo_vs_analitico | error_maximo_conservacion | minimo_estado | minimo_transferencia | X4_no_decreciente | NRMSE_numerico_maximo |
|---|---|---|---|---|---|---|---|---|
| 4 | 0.25 | 1.9775 | 7.4893e-07 | 1.74623e-10 | 0 | 0 | True | 1.09926e-09 |
| 8 | 0.125 | 3.66547 | 4.63117e-08 | 3.63798e-10 | 0 | 0 | True | 6.79769e-11 |
| 16 | 0.0625 | 7.43325 | 2.8765e-09 | 5.09317e-10 | 0 | 0 | True | 4.22607e-12 |

Comparaciones entre mallas: `[{"h_grueso": 0.25, "h_fino": 0.125, "max_diferencia": 7.026187631709035e-07, "NRMSE_por_estado": [1.0312786403897093e-09, 1.5921246164365302e-10, 7.06649179594023e-12, 1.8445993220729322e-14], "max_diferencia_transferencias": 1.727592433553582e-07}, {"h_grueso": 0.125, "h_fino": 0.0625, "max_diferencia": 4.343519321992062e-08, "NRMSE_por_estado": [6.375081187017843e-11, 9.841996720674023e-12, 4.3690171092518313e-13, 7.155631460865617e-15], "max_diferencia_transferencias": 1.0679542583602597e-08}]`.

Ambas comparaciones cumplen máximo ≤0,1 pedido y NRMSE≤0,001 por estado con escalas de entrenamiento. La estabilidad lineal, positividad de todas las etapas internas, finitud, X4 no decreciente y flujos no negativos se verificaron en cada corrida. No se recortaron estados. Los errores de conservación cumplen 1e−8·max(1,total). Recomendación numérica: **h=0,25 horas, cuatro subpasos por hora**, que también presenta discrepancia pequeña frente al propagador analítico. Los parámetros no se cambiaron para satisfacer controles.

## Gráficas y archivos
En graficas_calibracion/: T1.png, T2.png, T3.png, T4_incremental.png y pendientes.png comparan todos los cortes históricos con RK4 calibrado, sin suavizado. semana_febrero_2018.png amplía una semana fijada por calendario dentro de entrenamiento. Cada gráfica identifica entrenamiento, fechas, unidad pedidos y ambas curvas. La trayectoria completa y las tablas auxiliares se exportan sin sobrescribir datos históricos.

## Decisión y limitaciones
Se conserva este modelo como referencia calibrada, con limitaciones descriptivas explícitas; no se declara precisión suficiente sólo por convergencia del optimizador. Deben revisarse los errores por etapa y el bloque interno antes de tratarlo como modelo predictivo adecuado. Se recomiendan para una fase posterior contrastes de riesgo dependiente de edad y calendario, particularmente en aprobación, sin implementarlos aquí. La validación final, si se autoriza, debe hacerse con estos parámetros congelados como referencia y sin volver a escogerlos con ese 30 %; si se revisa la estructura antes, se requiere repetir desarrollo y mantener intacta esa reserva.

No hay cancelaciones fechadas, capacidades, costos ni seguimiento individual bajo alternativas. La selección retrospectiva de 95.082 entregados impide interpretar esto como inventario operativo completo. La entrada histórica conocida no constituye un pronóstico de compras. No se ejecutaron validación final, escenarios ni interfaz. Tiempo de cálculo previo a gráficos/informe: 18.019 s. Las pruebas automáticas se registran separadamente en pruebas_calibracion.txt.

## Reproducir
```powershell
.venv/Scripts/python.exe scripts/calibrar_modelo.py
.venv/Scripts/python.exe -m pytest -q
```

Referencias de implementación: [least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html), [expm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html) y [lfilter](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html). Se aplican a las versiones fijadas del entorno, que constan en el JSON.

## Pruebas ejecutadas al finalizar

Se ejecutaron las 48 pruebas anteriores y las nuevas de calibraci?n. Resultado real:

```text
...................................................................      [100%]
67 passed in 4.52s
```

Las pruebas incluyen recuperaci?n de tasas conocidas de datos matem?ticos, reproducibilidad, censura e independencia de datos reservados, alineaci?n, valores inv?lidos, coherencia expm/RK4 y equivalencia con cuatro agentes.
