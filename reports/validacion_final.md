# Validación final independiente — fase 4B

## Modelo congelado y alcance
Se evaluó únicamente el modelo base seleccionado de primer orden. α=0.10202378368368686, β=0.013240792867426554, γ=0.004071911987908591 hora⁻¹, leídos del JSON original y comprobados exactamente contra los valores autorizados y el archivo de selección. No se recalibraron coeficientes ni se evaluó la aprobación rápida. Se conservan las cuatro EDO, cuatro estados, cuatro agentes y las escalas de entrenamiento.

Esta evaluación mide reproducción retrospectiva fuera de entrenamiento, condicionada a compras históricas conocidas y al estado inicial observado. No es pronóstico de demanda ni demostración causal de operaciones futuras. La independencia de la reserva respecto del ajuste no elimina el sesgo de una cohorte elegida retrospectivamente por entregas completas.

## Ventana, entrada e inicialización
Inicio: 2018-03-02 22:00:00; final: 2018-10-17 14:00:00. Exactamente 5.488 intervalos y 5.489 estados. Condición inicial comprobada: [113.0, 586.0, 3005.0, 53963.0], total 57.667 pedidos. Se inicializó una sola vez; luego se usaron exclusivamente compras en (inicio,fin], con entrada constante por hora y cuatro subpasos RK4 (h=0,25 h). K1–K4 usan la entrada de su misma hora. No se reinició en bloques, no se impusieron transiciones históricas y no se corrigieron estados con observaciones futuras.

Compras durante validación: 37415; total final esperado: 95082. Se verificaron fechas únicas, mallas de compras/niveles iguales, separación horaria y balances de los eventos observados.

## Integridad y convergencia numérica
Todos los controles matemáticos se ejecutaron antes de calcular métricas: estados finitos y no negativos, transferencias no negativas, X4 no decreciente y conservación en todos los intervalos. No hubo recortes ni redondeos. Error máximo absoluto de conservación: **9.45874489844e-10 pedidos**, dentro de 1e−8·max(1,total).

AgentPy y RK4 independiente coinciden exactamente en estados y transferencias (diferencia máxima cero). AgentPy completó los 5.488 intervalos con cuatro agentes. Las comprobaciones de la trayectoria no utilizan niveles observados posteriores para modificar la simulación.

Se repitió la integración a h=0,125 y 0,0625 únicamente para verificar convergencia, sin alterar parámetros ni elegir otro modelo. Comparaciones: `[{"h_grueso": 0.25, "h_fino": 0.125, "max_diferencia": 2.3753568711981643e-07, "NRMSE_numerico_por_estado": [1.3084406297020717e-09, 2.0199429242065256e-10, 8.962266057756993e-12, 7.5557661196029e-14], "max_diferencia_transferencias": 3.157198431580355e-07, "error_max_conservacion_malla_fina": 1.57160684466362e-09}, {"h_grueso": 0.125, "h_fino": 0.0625, "max_diferencia": 1.46847014548257e-08, "NRMSE_numerico_por_estado": [8.088424484119667e-11, 1.2486665150198594e-11, 5.540824474039818e-13, 3.290846826311972e-14], "max_diferencia_transferencias": 1.9516932070473558e-08, "error_max_conservacion_malla_fina": 8.149072527885437e-10}]`. Cumplen máximo≤0,1 pedido y NRMSE numérico≤0,001 con escalas congeladas. Se conserva h=0,25 h.

Estado final simulado: [1.091097865448799e-51, 5.037792036875029e-05, 20.748535988493607, 95061.25141363285]. Estado final observado: [0.0, 0.0, 0.0, 95082.0]. El modelo continuo vacía colas asintóticamente: su remanente terminal no debe recortarse para coincidir con el cierre discreto de la cohorte.

## Métricas finales por variable
Los objetivos son los 5.488 cortes posteriores al inicio, sin incluir el error inicial cero. También los máximos y sus fechas se reportan sobre esos mismos cortes; si un máximo se sitúa en la condición inicial, ésta permanece visible en las gráficas y CSV, pero no agrega un objetivo gratuito. Los empates de máximo se resuelven con la primera fecha.

Errores firmados=simulado−observado. Las unidades absolutas son pedidos. NMAE/NRMSE son adimensionales. X1–X3 se normalizan con **[44.39279856283684, 330.3622588455831, 1004.1355932203389]**, valores de entrenamiento congelados. Para P y X4 incremental se usan igualmente sus escalas archivadas de entrenamiento: 1378.89065 y 15774.9093, respectivamente. No se calcula una escala con validación. X4 se compara restando 53.963 entregas previas de ambas curvas.

| variable | escala | MAE | RMSE | NMAE | NRMSE | error_absoluto_maximo | maximo_observado | maximo_simulado | error_nivel_maximo | error_nivel_maximo_absoluto | error_final | sesgo_medio | fecha_maximo_observado | fecha_maximo_simulado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| X1 | 44.3928 | 24.4959 | 44.1688 | 0.551799 | 0.994955 | 471.176 | 577 | 190.239 | -386.761 | 386.761 | 1.0911e-51 | 3.61903 | 2018-04-24 17:00:00 | 2018-05-07 23:00:00 |
| X2 | 330.362 | 138.871 | 184.657 | 0.420359 | 0.558954 | 629.287 | 1017 | 984.345 | -32.655 | 32.655 | 5.03779e-05 | 109.262 | 2018-03-05 17:00:00 | 2018-08-09 03:00:00 |
| X3 | 1004.14 | 546.733 | 669.099 | 0.544481 | 0.666343 | 1824 | 3421 | 3000.56 | -420.442 | 420.442 | 20.7485 | 287.797 | 2018-03-14 03:00:00 | 2018-03-02 23:00:00 |
| X4_incremental | 15774.9 | 634.254 | 763.689 | 0.0402065 | 0.0484116 | 2004.72 | 41119 | 41098.3 | -20.7486 | 20.7486 | -20.7486 | -400.679 | 2018-10-17 14:00:00 | 2018-10-17 14:00:00 |
| P | 1378.89 | 634.254 | 763.689 | 0.459974 | 0.553843 | 2004.72 | 4218 | 3706.77 | -511.227 | 511.227 | 20.7486 | 400.679 | 2018-03-26 14:00:00 | 2018-03-02 23:00:00 |

Mayor error relativo entre pendientes: **X1**; mayor error absoluto: **X3**. La acumulación terminal no compensa esos errores.

### Transferencias horarias
Se comparan integrales RK4 de aprobaciones, despachos y entregas con conteos reales por hora. Las unidades absolutas son pedidos por intervalo de una hora; su valor numérico coincide con tasa media en pedidos/hora. Las escalas son las del archivo de transferencias de entrenamiento, no medias de validación.

| variable | escala | MAE | RMSE | NMAE | NRMSE | error_absoluto_maximo | maximo_observado | maximo_simulado | error_nivel_maximo | error_nivel_maximo_absoluto | error_final | sesgo_medio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aprobaciones | 4.49535 | 4.60044 | 9.56372 | 1.02338 | 2.12747 | 218.566 | 230 | 19.2722 | -210.728 | 210.728 | 1.17195e-52 | -2.45273e-16 |
| despachos | 4.44958 | 9.18868 | 15.6978 | 2.06507 | 3.52792 | 150.295 | 160 | 13.0312 | -146.969 | 146.969 | 6.71479e-07 | -9.17965e-09 |
| entregas | 4.21487 | 8.30626 | 11.2502 | 1.9707 | 2.66918 | 52.7591 | 62 | 12.227 | -49.773 | 49.773 | -0.915342 | -0.00378072 |

## Comparación con entrenamiento congelado
Se leyó metricas_entrenamiento.csv de fase 4A sin recalcular entrenamiento. Las filas originales y sus huellas se conservaron.

| variable | MAE_entrenamiento | MAE_validacion | RMSE_entrenamiento | RMSE_validacion | NRMSE_entrenamiento | NRMSE_validacion | factor_RMSE |
|---|---|---|---|---|---|---|---|
| X1 | 13.2255 | 24.4959 | 22.5291 | 44.1688 | 0.507495 | 0.994955 | 1.96052 |
| X2 | 69.1095 | 138.871 | 99.7243 | 184.657 | 0.301863 | 0.558954 | 1.85168 |
| X3 | 142.448 | 546.733 | 194.937 | 669.099 | 0.194135 | 0.666343 | 3.43238 |
| X4_incremental | 166.47 | 634.254 | 229.916 | 763.689 | 0.0145748 | 0.0484116 | 3.32159 |
| P | 166.47 | 634.254 | 229.916 | 763.689 | 0.16674 | 0.553843 | 3.32159 |

El factor compara RMSE de validación con el de entrenamiento, con unidades idénticas; no prueba por sí solo una causa del cambio. Los niveles tienen magnitudes diferentes: X1 puede tener error absoluto menor y error relativo mayor. Los errores de pico y sus fechas permiten distinguir amplitud de desfase temporal.

- X1: RMSE 1.961 veces el de entrenamiento; sesgo global +3.619 pedidos. Sesgos B1–B4: -1.663, +8.763, +4.624, +2.752. El máximo simulado difiere del observado en -386.761 pedidos (-67.03 %).
- X2: RMSE 1.852 veces el de entrenamiento; sesgo global +109.262 pedidos. Sesgos B1–B4: +82.162, +167.226, +132.687, +54.975. El máximo simulado difiere del observado en -32.655 pedidos (-3.21 %).
- X3: RMSE 3.432 veces el de entrenamiento; sesgo global +287.797 pedidos. Sesgos B1–B4: -497.918, +318.807, +769.936, +560.363. El máximo simulado difiere del observado en -420.442 pedidos (-12.29 %).

Ninguno de los tres pendientes mantiene el RMSE de entrenamiento. X2 sobreestima en promedio en los cuatro bloques; X3 pasa de subestimación en B1 a sobreestimación en los siguientes, de modo que su sesgo global oculta cambios importantes de signo. X1 conserva el mayor error relativo y pierde gran parte de la amplitud del pico observado.

## Cuatro bloques: una trayectoria, sin reinicializaciones
Cada bloque contiene exactamente 1.372 intervalos, sin cortes objetivo repetidos. Los bloques son diagnósticos, no nuevas simulaciones ni conjuntos para reajuste. X4 incremental conserva el mismo origen global de validación en todos ellos.

| bloque | inicio_abierto | fin_inclusivo | intervalos | compras | horas_sin_compras | aprobaciones_observadas | despachos_observados | entregas_observadas |
|---|---|---|---|---|---|---|---|---|
| B1 | 2018-03-02 22:00:00 | 2018-04-29 02:00:00 | 1372 | 12507 | 173 | 12560 | 12597 | 13620 |
| B2 | 2018-04-29 02:00:00 | 2018-06-25 06:00:00 | 1372 | 11896 | 178 | 11861 | 11751 | 12489 |
| B3 | 2018-06-25 06:00:00 | 2018-08-21 10:00:00 | 1372 | 12145 | 178 | 12196 | 12133 | 11890 |
| B4 | 2018-08-21 10:00:00 | 2018-10-17 14:00:00 | 1372 | 867 | 1218 | 911 | 1633 | 3120 |

| bloque | variable | MAE | RMSE | NMAE | NRMSE | sesgo_medio | error_final |
|---|---|---|---|---|---|---|---|
| B1 | X1 | 36.4814 | 66.473 | 0.821786 | 1.49738 | -1.66252 | 16.5928 |
| B1 | X2 | 156.239 | 183.58 | 0.472934 | 0.555692 | 82.1624 | 138.718 |
| B1 | X3 | 517.96 | 611.602 | 0.515827 | 0.609083 | -497.918 | 168.929 |
| B1 | X4_incremental | 499.262 | 577.351 | 0.0316491 | 0.0365994 | 417.418 | -324.24 |
| B1 | P | 499.262 | 577.351 | 0.362075 | 0.418707 | -417.418 | 324.24 |
| B2 | X1 | 25.0445 | 33.0808 | 0.564157 | 0.745185 | 8.76294 | -29.5231 |
| B2 | X2 | 185.858 | 227.086 | 0.562589 | 0.687385 | 167.226 | -54.7714 |
| B2 | X3 | 338.671 | 407.794 | 0.337277 | 0.406114 | 318.807 | 783.508 |
| B2 | X4_incremental | 512.418 | 590.388 | 0.0324831 | 0.0374257 | -494.796 | -699.213 |
| B2 | P | 512.418 | 590.388 | 0.371616 | 0.428161 | 494.796 | 699.213 |
| B3 | X1 | 33.6591 | 47.0566 | 0.758211 | 1.06 | 4.62357 | 35.69 |
| B3 | X2 | 158.41 | 190.968 | 0.479505 | 0.578055 | 132.687 | 22.9389 |
| B3 | X3 | 769.936 | 805.492 | 0.766765 | 0.802174 | 769.936 | 1119.04 |
| B3 | X4_incremental | 907.246 | 944.457 | 0.057512 | 0.0598708 | -907.246 | -1177.66 |
| B3 | P | 907.246 | 944.457 | 0.657954 | 0.68494 | 907.246 | 1177.66 |
| B4 | X1 | 2.79869 | 8.73039 | 0.0630437 | 0.196662 | 2.75215 | 1.0911e-51 |
| B4 | X2 | 54.9749 | 121.059 | 0.166408 | 0.366443 | 54.9749 | 5.03779e-05 |
| B4 | X3 | 560.363 | 775.632 | 0.558055 | 0.772437 | 560.363 | 20.7485 |
| B4 | X4_incremental | 618.09 | 871.202 | 0.0391819 | 0.055227 | -618.09 | -20.7486 |
| B4 | P | 618.09 | 871.202 | 0.448252 | 0.631813 | 618.09 | 20.7486 |

Último intervalo con compras positivas termina en 2018-08-29 16:00:00; después hay 1174 horas sin nuevas compras de esta cohorte. La reducción de llegadas observada al final y el vaciado histórico condicionan las métricas del último bloque. No se interpreta como caída demostrada de la demanda total de Olist: la fuente representa una cohorte finita retrospectiva de entregados completos. El coeficiente constante no representa explícitamente calendarios, cambios de mezcla, edad ni heterogeneidad; los sesgos por bloque describen discrepancias, no identifican causalmente su origen.

El menor error de X1 en B4 coincide con la reducción de llegadas y con niveles observados próximos a cero; no implica que haya mejorado su mecanismo de aprobación. X3 mantiene un error grande en ese mismo bloque porque el modelo conserva una cola de decaimiento más lenta que el vaciado registrado. Las horas sin llegadas no deben confundirse con una validación exigente de respuesta a demanda sostenida.

## Comparación descriptiva con persistencia
La referencia mantiene X1–X3 iguales al estado inicial de validación durante toda la ventana. No se reinicia por bloque y no es un modelo conservativo completo.

| variable | MAE_EDO | RMSE_EDO | MAE_persistencia | RMSE_persistencia | mejora_RMSE_pct |
|---|---|---|---|---|---|
| X1 | 24.4959 | 44.1688 | 63.4127 | 75.9253 | 41.8259 |
| X2 | 138.871 | 184.657 | 240.275 | 315.707 | 41.5099 |
| X3 | 546.733 | 669.099 | 1509.69 | 1787.79 | 62.5739 |

Superar persistencia es una referencia mínima de desempeño estadístico; no sustituye criterios académicos de precisión ni demuestra utilidad operativa. Si una etapa no la supera, el signo negativo de mejora lo deja explícito.

## Criterios y decisión
Se aplicaron sin modificación los criterios académicos provisionales del plan: NMAE≤0,20; NRMSE≤0,30; error absoluto de máximo≤max(1 pedido,20 % del máximo observado); error final absoluto≤max(1 pedido,20 % de la escala de entrenamiento). Se evalúan por etapa, sin aprobar el conjunto por un buen total. Son umbrales internos, no estándares de Olist.

| variable | NMAE_cumple | NRMSE_cumple | error_pico_cumple | error_final_cumple | sesgo_mismo_signo_4_bloques | cumple_criterios_cuantitativos |
|---|---|---|---|---|---|---|
| X1 | False | False | False | True | False | False |
| X2 | False | False | True | True | True | False |
| X3 | False | False | True | True | False | False |

La columna de sesgo con mismo signo en cuatro bloques es un diagnóstico descriptivo de persistencia, sin inventar un umbral de significación o magnitud después de ver resultados. También se examinan magnitudes y cambios temporales de sesgo en la tabla. No se interpreta un promedio cercano a cero como ausencia automática de errores locales.

**Conclusión: categoría C.** Ninguna etapa pendiente cumple conjuntamente los criterios cuantitativos si la categoría es C; una coincidencia visual de X4 o conservación perfecta no cambia esa decisión. Con los resultados obtenidos, el modelo no sustenta recomendaciones operativas confiables. Puede conservarse como ejercicio académico de balances y referencia para simulaciones hipotéticas exploratorias, con limitaciones explícitas; no se ejecutan escenarios en esta fase.

## Cinco conceptos que deben distinguirse
- Correctitud numérica: conservación, positividad, convergencia y equivalencia de motores comprobadas.
- Ajuste: métricas de fase 4A sobre datos usados para estimar parámetros, preservadas como antecedente.
- Desempeño fuera de entrenamiento: cifras actuales sobre reserva antes intacta, sin corregir trayectorias.
- Escenarios hipotéticos: balances comparables bajo supuestos no prueban efectos operativos reales; la precisión observada limita su interpretación.
- Pronóstico futuro: requeriría una entrada futura estimada, incertidumbre y una población operativa adecuada. Aquí se conocen las compras históricas.

## Límites y uso posterior de esta reserva
El modelo agregado de coeficientes constantes no refleja todas las variaciones observadas, no incluye cancelaciones fechadas y no predice retrasos individuales. La cohorte retrospectiva seleccionada por entregas completas omite población pendiente/cancelada y no es el inventario completo de Olist.

La reserva ya fue evaluada y sus resultados se conservan incluso si son desfavorables. No se ajustan coeficientes ni se cambia estructura con ella para volver a presentarla como validación independiente. Cualquier desarrollo posterior motivado por estos errores necesitará un conjunto de prueba nuevo para evaluación independiente. No se implementan escenarios ni Streamlit.

## Archivos y visualizaciones
metricas_validacion.csv, metricas_por_bloque.csv, trayectoria_validacion.csv y resumen_validacion.json contienen resultados principales. Se añaden transferencias, persistencia, criterios, conteos temporales y comparación con entrenamiento como CSV separados. No se sobrescribe ningún archivo de datos, entrenamiento ni selección anterior.

En graficas_validacion/: X1.png, X2.png, X3.png, X4_incremental.png, P.png; residuos_temporales.png; RMSE_entrenamiento_validacion.png; errores_por_bloque.png; primeros_siete_dias.png; ultimos_siete_dias.png. Las dos ampliaciones están fijadas desde el inicio y el final de la ventana, por siete días consecutivos, sin escoger tramos favorables. Las curvas utilizan todos los cortes disponibles, sin suavizado.

## Trazabilidad SHA-256
| archivo | SHA256 |
|---|---|
| reports\parametros_calibrados.json | a3d59cbec7b713d0ad7786ebd243473da83e2c45feec9134c4da06549966d9e9 |
| reports\modelo_seleccionado_desarrollo.json | 0ef089c77c816d409ef098d8327fd812b7641b9f946fa1bfc3496ed3ad091d21 |
| reports\metricas_entrenamiento.csv | aab80215a2b850a96c26a8b3d61486cf6e736d208eb0bc94de21df3c598d0dda |
| reports\metricas_transferencias_entrenamiento.csv | 489d312953ee3d99d673de30c1644ab9af62c54f35bf3846e25d00fb08aff7ae |
| reports\calibracion_modelo.md | e6efe56bcfb633e4ff9fdc75cfbe6aff038f1a356783b15de4baefd3a29b5d38 |
| reports\comparacion_modelos.md | 5148ace97695090f0260cc57050d54231f97402ffb6d0bef85f07273da66bc0e |
| docs\modelo_matematico.md | da5b342c21303c440fdc024e895ee9d8fed3b80b7012988d28231b46efdf6984 |
| docs\plan_calibracion_validacion.md | 917b1474e8f1c970e50aa693624d1f68828becb5731e7168ae8769a1fa213bd8 |
| docs\implementacion_rk4_agentpy.md | e12d79bd1ded4b1db8b80929bb54e3bbfb860bcd25983ef7db4603850a39d892 |
| src\rk4_solver.py | 696fdb8182dc21b461b9155535c10dc97aeb52eb971caf0f949de175e75823ae |
| src\simulation_engine.py | b9ca1b066f3fd6a90ce630d3c0281d2b971b47750875c33e0b5706c53fdf401c |
| src\agent_model.py | f057be054ce7540ad504421c26b36d87734f3aa636a77b55f0330c7180bdd26c |
| src\calibration_metrics.py | e90bc955ad6018ab0a692f94cedf5b5318eebeded3def25693011d285b382e29 |
| data\processed\eventos_por_hora.csv | d2129b3ab9870023ae471f84e9557b7b4bbb8ce378b1b5301fd6453f21bbbff5 |
| data\processed\niveles_reales_4_tanques.csv | 879f9d839fd3e0cfa1a8c3199a35d9697622b809ccd935e3505db6574c214eaf |
| src\validation.py | 4e1f7948b313c5ec4505ec9eb495e318f15b1fad570bd7993eace5df6ed40cd7 |
| scripts\validar_modelo.py | 6685f9198a5e1df9e69b5521fb3fe190a8b0b1bd2ee3348a285eacbb4fce273b |

Las huellas se tomaron antes de evaluar y se verifican otra vez al finalizar. Versiones: Python 3.12.13, AgentPy 0.1.5, NumPy 2.5.4, pandas 3.1.1. Tiempo hasta generar tablas y gráficas: 7.760 s. Configuración y resultados numéricos completos en resumen_validacion.json.

## Reproducción
```powershell
.venv/Scripts/python.exe scripts/validar_modelo.py
```
El script ejecuta pruebas anteriores y nuevas, guarda su salida y devuelve error si falla alguna. No importa ni llama calibradores. La repetición reproduce esta evaluación; no constituye una segunda prueba independiente.

## Pruebas ejecutadas

```text
........................................................................ [ 72%]
............................                                             [100%]
100 passed in 11.07s
```

Se verificó que las huellas de todos los archivos protegidos siguen iguales al finalizar.
