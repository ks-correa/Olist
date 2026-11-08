# Comparación estructural: base frente a aprobación rápida

## Alcance y protocolo
Se evaluó una sola modificación, definida en [modelo_aprobacion_rapida.md](../docs/modelo_aprobacion_rapida.md). Se mantienen cuatro estados y cuatro agentes. Las dos estructuras comparten λ histórica, unidades, condiciones iniciales y reconstrucción. Se preservó el archivo parametros_calibrados.json: SHA-256 `a3d59cbec7b713d0ad7786ebd243473da83e2c45feec9134c4da06549966d9e9`. El 30 % reservado permanece sin evaluar; los bloques analizados son desarrollo reutilizado, nunca prueba final independiente.

Se inspeccionaron módulos de simulación/calibración/métricas y documentos anteriores. El lector sigue limitado a las primeras 12.804 filas horarias. Timestamps futuros se censuran antes de calcular exposiciones. La cohorte fue seleccionada retrospectivamente por entrega completa: la separación temporal evita contaminación adicional, pero no elimina selección ni censura de población.

Antes de ejecutar el candidato se fijaron cuatro evaluaciones de 1920 horas con ajuste expansivo. Ambos modelos se ajustaron al mismo prefijo, congelaron parámetros y se inicializaron una sola vez con el estado observado del corte. Las escalas s_i=max(1,media del prefijo) son idénticas entre modelos. No se retocaron pérdida, ventanas ni umbrales tras ver resultados.

| ventana | inicio_ajuste | fin_ajuste_inicio_evaluacion | fin_evaluacion | intervalos_ajuste | intervalos_evaluacion |
|---|---|---|---|---|---|
| V1 | 2016-09-15 11:00:00 | 2017-04-16 22:00:00 | 2017-07-05 22:00:00 | 5123 | 1920 |
| V2 | 2016-09-15 11:00:00 | 2017-07-05 22:00:00 | 2017-09-23 22:00:00 | 7043 | 1920 |
| V3 | 2016-09-15 11:00:00 | 2017-09-23 22:00:00 | 2017-12-12 22:00:00 | 8963 | 1920 |
| V4 | 2016-09-15 11:00:00 | 2017-12-12 22:00:00 | 2018-03-02 22:00:00 | 10883 | 1920 |

## Hipótesis y conservación
El candidato usa entradas (1−p)λ a X1 y pλ a X2; q12=αX1 sigue siendo la transferencia convencional. Las aprobaciones totales que se comparan con datos son pλ+q12. No se cuenta dos veces la rama rápida. Al sumar las derivadas se obtiene [(1−p)+p]λ=λ. X4 es terminal y no es cola pendiente. Con p=0 las ecuaciones y las trayectorias RK4 coinciden exactamente con el base. Con p=1 y X1 inicial cero se pierde sensibilidad a α.

Sólo entre aprobaciones observadas hasta el corte: 57554 eventos, mediana 0.296944 h, P95 47.9563 h; fracción con tiempo≤1 h=64.845%, tiempo cero=2.160%. Son descripciones condicionadas a aprobación observada, no el valor de p ni una estimación prospectiva; las esperas incompletas aportan exposición a las inicializaciones. La coexistencia de tiempos cortos y largos motiva, pero no demuestra, la hipótesis.

## Ajuste del candidato y reproducibilidad
Coeficientes con todo el desarrollo: α=0.0765295164692 h⁻¹, β=0.0132395731863 h⁻¹, γ=0.00407189095978 h⁻¹, p=0.247719890778 adimensional. p es una fracción efectiva de aprobación rápida a la resolución horaria; no una instalación real, un porcentaje observado de aprobaciones instantáneas ni una mejora operativa de Olist.

SciPy least_squares TRF, residuos normalizados de X1–X3, pérdida lineal, cotas tasas [0,+∞), p [0,1], diferencias centrales y ftol=xtol=gtol=1e−10. Escalas completas: [44.39279856283684, 330.3622588455831, 1004.1355932203389]. Se utilizó propagador expm auxiliar de las mismas EDO para ajustar; todas las métricas y comparaciones finales de trayectorias usan RK4. X4 no participa en la pérdida. Las tasas preliminares se calculan sólo en cada prefijo por exposición censurada. En candidato sólo inicializan, sin interpretarlas como tasas definitivas de la rama lenta.

Nueve inicios: factores de tasas {0,5;1;2} por p inicial {0;0,5;0,9}. Cada uno, con sus parámetros finales, costo, evaluaciones, llamadas reales, mensaje y tiempo se registra en parametros_aprobacion_rapida.json. Dispersión relativa pico a pico entre soluciones completas: [8.111253217213023e-06, 9.533349164358672e-10, 1.4460023084738544e-10, 2.3547356268335468e-05]. Terminación elegida: ``ftol` termination condition is satisfied.`; nfev=9, llamadas reales=81, costo 0,5Σr²=2435.3109. La terminación es convergencia local del algoritmo, no certificado de óptimo global.

### Métricas de ajuste con todo el desarrollo
Unidades absolutas: pedidos; NMAE y NRMSE son adimensionales. Error firmado=simulado−observado. X4 es incremento desde el inicio de la ventana, P suma de pendientes. El base usa sus parámetros originales congelados de fase 4A.

| modelo | variable | MAE | RMSE | NMAE | NRMSE | error_absoluto_maximo | error_nivel_maximo | sesgo_medio | error_final |
|---|---|---|---|---|---|---|---|---|---|
| base | X1 | 13.2255 | 22.5291 | 0.29792 | 0.507495 | 255.278 | 58.6847 | -0.341087 | 19.8539 |
| base | X2 | 69.1095 | 99.7243 | 0.209193 | 0.301863 | 617.436 | -518.505 | 4.01017 | 270.379 |
| base | X3 | 142.448 | 194.937 | 0.141861 | 0.194135 | 687.565 | -357.277 | 36.0192 | -548.299 |
| base | X4_incremental | 166.47 | 229.916 | 0.0105528 | 0.0145748 | 794.198 | 258.067 | -39.6883 | 258.067 |
| base | P | 166.47 | 229.916 | 0.120727 | 0.16674 | 794.198 | -290.592 | 39.6883 | -258.067 |
| candidate | X1 | 13.2703 | 22.3006 | 0.298929 | 0.502347 | 260.317 | 5.43996 | -0.243589 | 15.8837 |
| candidate | X2 | 68.8501 | 99.3285 | 0.208408 | 0.300665 | 620.553 | -541.19 | 4.04012 | 274.517 |
| candidate | X3 | 142.452 | 194.905 | 0.141865 | 0.194102 | 685.226 | -359.379 | 36.021 | -548.276 |
| candidate | X4_incremental | 166.483 | 229.887 | 0.0105536 | 0.014573 | 793.439 | 257.876 | -39.8175 | 257.876 |
| candidate | P | 166.483 | 229.887 | 0.120737 | 0.166719 | 793.439 | -290.981 | 39.8175 | -257.876 |

## Resultados cronológicos internos
Mejora %=100·(1−NRMSE_candidato/NRMSE_base). Un signo negativo indica deterioro, no reducción. Las escalas en el denominador proceden sólo del ajuste de la ventana. La comparación por variable incluye X4 incremental y P en comparacion_modelos.csv; aprobaciones totales, despachos y entregas integrados en comparacion_flujos_modelos.csv.

| ventana | mejora_X1_pct | mejora_X2_pct | mejora_X3_pct |
|---|---|---|---|
| V1 | 0.75046 | -0.0826902 | -0.0138702 |
| V2 | -1.39102 | 0.738101 | 0.0102784 |
| V3 | 1.3437 | 0.0209475 | -0.00539629 |
| V4 | 0.329743 | 1.0561 | 0.024412 |

Mediana de mejora de X1: **0.540101 %**. Menor mejora de X2/X3 entre ventanas: [-0.08269019500317665, -0.013870198431553682]. No basta reducir error de entrenamiento porque hay un parámetro extra.

### Parámetros del candidato por prefijo
| ventana | alpha | beta | gamma | p | condicion_J | coseno_sensibilidad_alpha_p |
|---|---|---|---|---|---|---|
| V1 | 0.0791445 | 0.0139016 | 0.00447985 | 0.374496 | 11.3245 | 0.980457 |
| V2 | 0.0779402 | 0.0147215 | 0.00446656 | 0.257311 | 10.6485 | 0.980641 |
| V3 | 0.0876347 | 0.0150517 | 0.00467745 | 0.178919 | 10.0238 | 0.979319 |
| V4 | 0.0728266 | 0.0134921 | 0.00452795 | 0.275229 | 9.78616 | 0.976693 |

Rango de p: 0.195577; cocientes máximo/mínimo de tasas: [1.2033326725954556, 1.1155970711747356, 1.047213580613083]. Las diferencias temporales y de sensibilidad se consideran en la selección, sin presentar las cuatro ventanas como réplicas estadísticas independientes.

## Identificabilidad y perfil de p
Condición del jacobiano escalado completo: 10.124; valores singulares [245.71814209430863, 143.4038015894076, 141.6997446673862, 24.270830001734883]. Para tasas se usa escala del coeficiente y para p escala unitaria, incluso en p=0. Coseno entre columnas de sensibilidad α,p: 0.97876; valores cercanos a ±1 indican confusión local. Multiinicio, rango local y perfil aportan evidencia, pero no garantizan identificación global ni estabilidad bajo heterogeneidad.

El mínimo completo tiene rango local cuatro y p interior, por lo que p aporta sensibilidad distinguible en ese ajuste, con fuerte dependencia de α. No equivale a identificar una fracción física única ni a demostrar estabilidad temporal: p cambia entre los prefijos. Algunas ventanas superan la guarda de colinealidad prefijada; aun sin esa guarda secundaria, la mejora interna de X1 queda lejos del 15 % requerido.

| p_fijo | MSE_normalizado | alpha | beta | gamma | success | nfev | seconds |
|---|---|---|---|---|---|---|---|
| 0 | 0.128787 | 0.102024 | 0.0132408 | 0.00407191 | True | 6 | 0.0336082 |
| 0.25 | 0.12681 | 0.0762952 | 0.0132396 | 0.00407189 | True | 4 | 0.0209267 |
| 0.5 | 0.12928 | 0.0506104 | 0.0132372 | 0.00407185 | True | 5 | 0.0249167 |
| 0.75 | 0.1381 | 0.0250445 | 0.0132312 | 0.0040717 | True | 5 | 0.0253926 |
| 0.9 | 0.154079 | 0.00996563 | 0.0132199 | 0.0040712 | True | 5 | 0.0247452 |
| 0.99 | 0.201403 | 0.000866979 | 0.0132096 | 0.00406907 | True | 5 | 0.0255867 |
| 1 | 0.710169 | 0.0765295 | 0.0132337 | 0.0040758 | True | 17 | 0.0359179 |

La rejilla es diagnóstica y predefinida; cada punto reajusta únicamente tres tasas, manteniendo p fijo. p=1 hace α no identificable si X1 inicial es cero: su valor ajustado en ese punto es arbitrario y no se interpreta. No se obtienen intervalos de confianza de la rejilla ni de mínimos cuadrados con errores seriales supuestamente independientes. Véase perfil_p.png. El cambio de p frente a α puede reproducir niveles medios similares; importan las excitaciones temporales para distinguirlos.

## Controles matemáticos y numéricos
Se verificó equivalencia exacta p=0 frente al base en todo el desarrollo, además de pruebas artificiales. La reproducción del CSV antiguo difiere a lo sumo 0 pedidos (redondeo de CSV). No se sobrescribió el JSON base.

Convergencia completa del candidato: `[{"h_grueso": 0.25, "h_fino": 0.125, "max_diferencia": 2.5353165256092325e-07, "NRMSE_por_estado": [2.861442872505423e-10, 4.6444673249528453e-11, 2.7726237032666316e-12, 1.4657385913083225e-14]}, {"h_grueso": 0.125, "h_fino": 0.0625, "max_diferencia": 1.57160684466362e-08, "NRMSE_por_estado": [1.7737240477588044e-11, 2.87897307349791e-12, 1.717889234066366e-13, 6.361789931306382e-15]}]`.

| caso | subpasos | h_horas | error_conservacion_max | minimo_estado | minimo_transferencia | minimo_entrada_rapida | X4_no_decrece | error_max_vs_analitico |
|---|---|---|---|---|---|---|---|---|
| candidato_desarrollo_completo | 4 | 0.25 | 4.80213e-10 | 0 | 0 | 0 | True | 2.70288e-07 |
| candidato_desarrollo_completo | 8 | 0.125 | 2.32831e-10 | 0 | 0 | 0 | True | 1.67568e-08 |
| candidato_desarrollo_completo | 16 | 0.0625 | 4.80213e-10 | 0 | 0 | 0 | True | 1.04069e-09 |
| base_original_desarrollo_completo | 4 | 0.25 | 1.74623e-10 | 0 | 0 | 0 | True | nan |

Se cumplen los criterios de diferencia entre mallas≤0,1 pedido y NRMSE≤0,001. Se mantuvo h=0,25 h; no se alteró automáticamente. Los controles incluyen estabilidad de RK4, etapas internas no negativas, finitud, flujos convencionales/directos no negativos, X4 no decreciente y conservación con tolerancia 1e−8·max(1,total). Controles por ventana en controles_numericos_comparacion.csv. AgentPy produjo estados, transferencias convencionales y entradas rápidas exactamente iguales al motor independiente en las cuatro evaluaciones de ambos modelos y en todo el desarrollo del candidato. No se crean agentes por pedido.

## Regla de decisión y modelo recomendado
Guardas fijadas antes de calcular resultados: mediana X1≥15 %, ningún deterioro de X2/X3>10 % en ninguna ventana, controles numéricos, convergencia; rango p≤0,20, cocientes de tasas≤2, p<0,99, condición local<1000 y |coseno sensibilidad α,p|<0,98 en cada prefijo. Son criterios académicos, no estándares externos ni intervalos estadísticos.

| criterio | cumple |
|---|---|
| median_X1_improvement_at_least_15 | False |
| no_X2_X3_deterioration_above_10_any_window | True |
| numerical_checks | True |
| optimizers_converged | True |
| p_range_at_most_020 | True |
| rate_ratios_at_most_2 | True |
| no_p_near_one | True |
| local_condition_below_1000 | True |
| alpha_p_sensitivity_cosine_below_098 | False |

Modelo seleccionado por esta regla: **base**. Se recalibró el seleccionado después de la comparación usando todo el 70 %, con parámetros [0.10202378368368686, 0.013240792867426554, 0.004071911987908591]; metadatos en modelo_seleccionado_desarrollo.json. No reemplaza el archivo original base ni implica validación final. Si un criterio falla se conserva el base aunque el candidato ajuste mejor dentro de muestra.

## Visualizaciones y archivos
En graficas_comparacion/: X1/X2/X3/P_ajuste.png (todo el desarrollo ajustado); X1/X2/X3/P_evaluacion_interna.png (cuatro bloques con prefijos expansivos); residuos_evaluacion_interna.png (errores horarios sin suavizado); NRMSE_por_ventana.png y perfil_p.png. Las tablas de fechas identifican exactamente ajuste y evaluación; las líneas verticales marcan sus orígenes. Se retienen todos los cortes horarios. Las curvas simuladas pueden ser suaves por las EDO, sin filtrado visual.

comparacion_modelos.csv contiene métricas completas por variable, modelo y ventana tanto de ajuste como evaluación. Las tablas auxiliares separan flujos, mejoras, diseño, perfil, trayectorias y controles. flujos_candidato_desarrollo.csv distingue entrada_T1, entrada_rapida_T2, q12 convencional y aprobaciones totales.

## Límites antes de la validación final
Aproximar todo evento corto por aprobación inmediata pierde detalle intrahorario; p efectivo no identifica pedidos ni infraestructura. La rama lenta sigue siendo homogénea de primer orden y β,γ constantes. Calendario, edad y heterogeneidad permanecen sin representar. Se ha añadido sólo el parámetro p y ninguna variable de estado.

Una ventaja de ajuste no asegura generalización, y el desarrollo ya fue utilizado repetidamente. Debe conservarse la reserva intacta hasta revisar esta selección y congelar estructura/parámetros. La cohorte retrospectiva de entregados completos no representa el inventario total ni cancelaciones; la entrada conocida no es pronóstico de demanda. No se evalúan costos, energía, retrasos individuales, escenarios ni interfaz. Tiempo previo a gráficos: 36.905 s.

## Reproducción
```powershell
.venv/Scripts/python.exe scripts/comparar_modelos.py
.venv/Scripts/python.exe -m pytest -q
```
Pruebas ejecutadas y resultados en pruebas_comparacion_modelos.txt. No se afirma éxito de pruebas no ejecutadas.

## Pruebas automáticas ejecutadas

```text
........................................................................ [ 84%]
.............                                                            [100%]
85 passed in 5.29s
```

La prueba de p=1 sin contenido inicial en X1 comprueba invariancia exacta de RK4 frente a α. En expm se usa únicamente una cota de redondeo de ocho épsilon por la magnitud del estado: cambiar el bloque no utilizado produjo diferencias de 2,84×10⁻¹⁴ pedidos. Las pruebas p=0 y AgentPy continúan exigiendo igualdad exacta.
