# Comparación de tres escenarios hipotéticos — fase 5

**Experimentos hipotéticos; validación del modelo categoría C; sin recomendaciones operativas para Olist.** La validación final fue categoría C: el motor conserva pedidos y converge, pero la precisión del modelo es insuficiente para recomendaciones sobre la empresa real. Esta limitación se aplica a todas las tablas y conclusiones siguientes.

## Objetivo y modelo
Se investiga cómo modificar una única transferencia cambia las acumulaciones y entregas bajo las mismas llegadas históricas. Se reutilizan las cuatro EDO del modelo base: X1'=λ−αX1, X2'=αX1−βX2, X3'=βX2−γX3, X4'=γX3. X4 es terminal acumulado, no cola pendiente. Los flujos son q12=αX1, q23=βX2 y q34=γX3. No se utiliza aprobación rápida.

## Parámetros e intervenciones congeladas
Los valores se leyeron de parametros_calibrados.json y se comprobaron exactamente. Sólo E1 multiplica β por 1,20 y sólo E2 multiplica γ por 1,20; α no cambia. Las tasas son hora⁻¹. Los incrementos son intervenciones matemáticas, no capacidades reales implementadas ni reducciones demostradas de costos, energía, personal o entregas tardías.

| escenario | nombre | alpha | beta | gamma |
|---|---|---|---|---|
| E0 | Base | 0.102024 | 0.0132408 | 0.00407191 |
| E1 | Despacho +20 % | 0.102024 | 0.015889 | 0.00407191 |
| E2 | Entrega +20 % | 0.102024 | 0.0132408 | 0.00488629 |

En una permanencia exponencial ideal, multiplicar una tasa por 1,20 divide su tiempo medio por 1,20: no obliga a reducir niveles un 20 %. El resultado depende de entradas, estados iniciales y horizonte.

## Ventanas y número de ejecuciones
Principal: 2018-03-02 22:00:00 a 2018-10-17 14:00:00, 5.488 intervalos horarios, 5.489 estados, X0=[113,586,3005,53963], 37.415 compras. Se verificó en los archivos. Los horizontes 168,720,1440,5488 h son lecturas de una sola trayectoria continua por escenario, no nuevas simulaciones ni reinicializaciones. La ventana ya fue usada en validación; aquí se reutiliza exclusivamente para comparación retrospectiva hipotética y no para escoger o calibrar tasas.

Se ejecutaron **6 trayectorias de escenario**: tres en cada una de 2 ventanas. Cada trayectoria se ejecutó en RK4 puro y en AgentPy, es decir 6 ejecuciones por motor. Las pruebas matemáticas/regresiones automáticas no se cuentan como escenarios oficiales adicionales. Sensibilidad de enero ejecutada: True. Si se incluye: 2018-01-01 00:00 a 2018-02-01 00:00, 744 h; horizontes 168,720,744 h. No se extrapolan 1440 h a una ventana más corta. Sus estados iniciales y compras exactas constan en el JSON. Tampoco es validación independiente.

## Método e indicadores
Las tres configuraciones comparten fechas, estado inicial, compras, h=0,25 h, cuatro agentes y las mismas definiciones de indicadores. No se recalibra, no se introducen transiciones observadas como entradas y no se corrigen niveles durante la trayectoria. AgentPy y el solucionador comparten las mismas ecuaciones e integración; no se duplicó RK4.

Áreas: trapecios sobre estados horarios, Σ(Δt/2)(X_k+X_(k+1)), con Δt=1 h, incluyendo inicio y horizonte. Unidad pedidos·hora. La media temporal se define como área/duración, no media aritmética de filas. Es una cuadratura horaria consistente entre escenarios, no la integral obtenida de etapas internas RK4; existe error de cuadratura intrahoraria. Las áreas acumuladas se construyen una sola vez y los horizontes leen sus prefijos. P=X1+X2+X3; su área coincide con la suma de áreas por etapa salvo redondeo.

Máximos y fechas incluyen la condición inicial y todos los cortes hasta el horizonte; se toma la primera fecha en empates. Entregas incrementales=X4(h)−X4(0), sin sumar las 53.963 entregas previas. Transferencias acumuladas y medias provienen de integrales RK4, no eventos observados. Se documentan en CSV para cada horizonte.

Variaciones: **100·(escenario−base)/base**, mismo signo y fórmula para todas las magnitudes. Negativo en pendientes/áreas indica reducción; positivo en entregas indica aumento. Con base cero el porcentaje se deja ausente, nunca infinito. Con bases muy pequeñas las variaciones porcentuales pueden ser grandes aunque la diferencia absoluta sea irrelevante; se muestran ambas. Las magnitudes no se redondean durante la integración.

## Resultados principales por horizonte
| escenario | horizonte_horas | P_final | P_maximo | P_promedio | P_area_pedidos_hora | entregas_incrementales |
|---|---|---|---|---|---|---|
| E0 | 168 | 3455.15 | 3706.77 | 3529.89 | 593022 | 1886.85 |
| E0 | 720 | 3011 | 3706.77 | 3301.16 | 2.37683e+06 | 7363 |
| E0 | 1440 | 2937.03 | 3706.77 | 3141.14 | 4.52324e+06 | 13890 |
| E0 | 5488 | 20.7486 | 3706.77 | 2430.66 | 1.33395e+07 | 41098.3 |
| E1 | 168 | 3416.93 | 3706.77 | 3514.39 | 590417 | 1925.07 |
| E1 | 720 | 2900.82 | 3706.77 | 3231.8 | 2.3269e+06 | 7473.18 |
| E1 | 1440 | 2827.62 | 3706.77 | 3050.7 | 4.393e+06 | 13999.4 |
| E1 | 5488 | 19.3187 | 3706.77 | 2343.31 | 1.28601e+07 | 41099.7 |
| E2 | 168 | 3199.99 | 3704.33 | 3381.02 | 568011 | 2142.01 |
| E2 | 720 | 2620.62 | 3704.33 | 2993.55 | 2.15535e+06 | 7753.38 |
| E2 | 1440 | 2572.75 | 3704.33 | 2798.1 | 4.02926e+06 | 14254.3 |
| E2 | 5488 | 6.80362 | 3704.33 | 2124.66 | 1.16601e+07 | 41112.2 |

### Cambios individuales por etapa
| escenario | horizonte_horas | X1_final | X2_final | X3_final | X1_area_pedidos_hora | X2_area_pedidos_hora | X3_area_pedidos_hora |
|---|---|---|---|---|---|---|---|
| E0 | 168 | 107.329 | 726.455 | 2621.37 | 16110.7 | 113529 | 463382 |
| E0 | 720 | 113.156 | 592.861 | 2304.98 | 65375.4 | 503216 | 1.80824e+06 |
| E0 | 1440 | 136.718 | 660.656 | 2139.66 | 128394 | 983674 | 3.41117e+06 |
| E0 | 5488 | 1.0911e-51 | 5.03779e-05 | 20.7485 | 367837 | 2.87853e+06 | 1.00931e+07 |
| E1 | 168 | 107.329 | 616.333 | 2693.27 | 16110.7 | 101538 | 472768 |
| E1 | 720 | 113.156 | 483.632 | 2304.03 | 65375.4 | 426222 | 1.8353e+06 |
| E1 | 1440 | 136.718 | 551.95 | 2138.95 | 128394 | 826570 | 3.43804e+06 |
| E1 | 5488 | 1.0911e-51 | 1.68904e-06 | 19.3187 | 367837 | 2.39877e+06 | 1.00935e+07 |
| E2 | 168 | 107.329 | 726.455 | 2366.21 | 16110.7 | 113529 | 438371 |
| E2 | 720 | 113.156 | 592.861 | 1914.6 | 65375.4 | 503216 | 1.58676e+06 |
| E2 | 1440 | 136.718 | 660.656 | 1775.37 | 128394 | 983674 | 2.91719e+06 |
| E2 | 5488 | 1.0911e-51 | 5.03779e-05 | 6.80357 | 367837 | 2.87853e+06 | 8.41378e+06 |

### Diferencias absolutas y porcentuales respecto de E0
| escenario | horizonte_horas | indicador | valor_base | valor_escenario | diferencia_absoluta | variacion_porcentual |
|---|---|---|---|---|---|---|
| E0 | 168 | entregas_incrementales | 1886.85 | 1886.85 | 0 | 0 |
| E0 | 168 | P_final | 3455.15 | 3455.15 | 0 | 0 |
| E0 | 168 | P_maximo | 3706.77 | 3706.77 | 0 | 0 |
| E0 | 168 | P_area_pedidos_hora | 593022 | 593022 | 0 | 0 |
| E0 | 720 | entregas_incrementales | 7363 | 7363 | 0 | 0 |
| E0 | 720 | P_final | 3011 | 3011 | 0 | 0 |
| E0 | 720 | P_maximo | 3706.77 | 3706.77 | 0 | 0 |
| E0 | 720 | P_area_pedidos_hora | 2.37683e+06 | 2.37683e+06 | 0 | 0 |
| E0 | 1440 | entregas_incrementales | 13890 | 13890 | 0 | 0 |
| E0 | 1440 | P_final | 2937.03 | 2937.03 | 0 | 0 |
| E0 | 1440 | P_maximo | 3706.77 | 3706.77 | 0 | 0 |
| E0 | 1440 | P_area_pedidos_hora | 4.52324e+06 | 4.52324e+06 | 0 | 0 |
| E0 | 5488 | entregas_incrementales | 41098.3 | 41098.3 | 0 | 0 |
| E0 | 5488 | P_final | 20.7486 | 20.7486 | 0 | 0 |
| E0 | 5488 | P_maximo | 3706.77 | 3706.77 | 0 | 0 |
| E0 | 5488 | P_area_pedidos_hora | 1.33395e+07 | 1.33395e+07 | 0 | 0 |
| E1 | 168 | entregas_incrementales | 1886.85 | 1925.07 | 38.2188 | 2.02554 |
| E1 | 168 | P_final | 3455.15 | 3416.93 | -38.2188 | -1.10614 |
| E1 | 168 | P_maximo | 3706.77 | 3706.77 | -0.00314538 | -8.48549e-05 |
| E1 | 168 | P_area_pedidos_hora | 593022 | 590417 | -2604.84 | -0.439248 |
| E1 | 720 | entregas_incrementales | 7363 | 7473.18 | 110.173 | 1.49631 |
| E1 | 720 | P_final | 3011 | 2900.82 | -110.173 | -3.65903 |
| E1 | 720 | P_maximo | 3706.77 | 3706.77 | -0.00314538 | -8.48549e-05 |
| E1 | 720 | P_area_pedidos_hora | 2.37683e+06 | 2.3269e+06 | -49938 | -2.10103 |
| E1 | 1440 | entregas_incrementales | 13890 | 13999.4 | 109.41 | 0.787692 |
| E1 | 1440 | P_final | 2937.03 | 2827.62 | -109.41 | -3.7252 |
| E1 | 1440 | P_maximo | 3706.77 | 3706.77 | -0.00314538 | -8.48549e-05 |
| E1 | 1440 | P_area_pedidos_hora | 4.52324e+06 | 4.393e+06 | -130235 | -2.87924 |
| E1 | 5488 | entregas_incrementales | 41098.3 | 41099.7 | 1.42989 | 0.00347919 |
| E1 | 5488 | P_final | 20.7486 | 19.3187 | -1.42989 | -6.8915 |
| E1 | 5488 | P_maximo | 3706.77 | 3706.77 | -0.00314538 | -8.48549e-05 |
| E1 | 5488 | P_area_pedidos_hora | 1.33395e+07 | 1.28601e+07 | -479404 | -3.59387 |
| E2 | 168 | entregas_incrementales | 1886.85 | 2142.01 | 255.16 | 13.5231 |
| E2 | 168 | P_final | 3455.15 | 3199.99 | -255.16 | -7.38492 |
| E2 | 168 | P_maximo | 3706.77 | 3704.33 | -2.43944 | -0.0658103 |
| E2 | 168 | P_area_pedidos_hora | 593022 | 568011 | -25010.6 | -4.21748 |
| E2 | 720 | entregas_incrementales | 7363 | 7753.38 | 390.38 | 5.30191 |
| E2 | 720 | P_final | 3011 | 2620.62 | -390.38 | -12.9651 |
| E2 | 720 | P_maximo | 3706.77 | 3704.33 | -2.43944 | -0.0658103 |
| E2 | 720 | P_area_pedidos_hora | 2.37683e+06 | 2.15535e+06 | -221481 | -9.31831 |
| E2 | 1440 | entregas_incrementales | 13890 | 14254.3 | 364.282 | 2.62263 |
| E2 | 1440 | P_final | 2937.03 | 2572.75 | -364.282 | -12.4031 |
| E2 | 1440 | P_maximo | 3706.77 | 3704.33 | -2.43944 | -0.0658103 |
| E2 | 1440 | P_area_pedidos_hora | 4.52324e+06 | 4.02926e+06 | -493976 | -10.9208 |
| E2 | 5488 | entregas_incrementales | 41098.3 | 41112.2 | 13.945 | 0.0339308 |
| E2 | 5488 | P_final | 20.7486 | 6.80362 | -13.945 | -67.2092 |
| E2 | 5488 | P_maximo | 3706.77 | 3704.33 | -2.43944 | -0.0658103 |
| E2 | 5488 | P_area_pedidos_hora | 1.33395e+07 | 1.16601e+07 | -1.67933e+06 | -12.5892 |

Todos los indicadores por depósito (inicial/final/máximo/fecha/media/área), aprobaciones, despachos y entregas acumuladas y medias se conservan en indicadores_horizontes.csv y diferencias_escenarios.csv. indicadores_escenarios.csv resume el horizonte completo de cada ventana, sin perder los otros horizontes.

## Comparación de criterios y horizontes
| ventana | horizonte_horas | menor_P_final | menor_P_area_pedidos_hora | menor_P_maximo | mayor_entregas |
|---|---|---|---|---|---|
| principal | 168 | E2 | E2 | E2 | E2 |
| principal | 720 | E2 | E2 | E2 | E2 |
| principal | 1440 | E2 | E2 | E2 | E2 |
| principal | 5488 | E2 | E2 | E2 | E2 |
| sensibilidad_enero | 168 | E2 | E2 | E2 | E2 |
| sensibilidad_enero | 720 | E2 | E2 | E2 | E2 |
| sensibilidad_enero | 744 | E2 | E2 | E2 | E2 |

Los ganadores se calculan por separado para pendientes finales, pico, área y entregas: no se elige un único último instante favorable. Las diferencias y sus magnitudes deben leerse junto a los ganadores, particularmente si son pequeñas. No se declara estrategia universal para operaciones reales ni para entradas diferentes.

- 168 h: pendientes finales E0=3455.150711, E1=3416.931862, E2=3199.990509 pedidos. Las entregas adicionales respecto de E0 son 38.218849 en E1 y 255.160201 en E2.
- 720 h: pendientes finales E0=3010.995759, E1=2900.822509, E2=2620.615847 pedidos. Las entregas adicionales respecto de E0 son 110.173250 en E1 y 390.379912 en E2.
- 1440 h: pendientes finales E0=2937.029376, E1=2827.619225, E2=2572.747248 pedidos. Las entregas adicionales respecto de E0 son 109.410152 en E1 y 364.282128 en E2.
- 5488 h: pendientes finales E0=20.748586, E1=19.318698, E2=6.803624 pedidos. Las entregas adicionales respecto de E0 son 1.429888 en E1 y 13.944963 en E2.

En esta ejecución E2 presenta menores pendientes finales, área y pico, y mayores entregas, en todos los horizontes predefinidos de la ventana principal. No aparece un cambio de orden entre siete, treinta y sesenta días, ni al final. Esto describe estos datos y este modelo; no demuestra dominancia universal.

En el período completo, E1 reduce el área de P en 479403.591571 pedidos·hora (3.593872 %), y E2 en 1679330.727028 pedidos·hora (12.589182 %). La ventaja de entregas al último instante es mucho menor que durante la ventana, por el agotamiento de la cohorte.

Los picos principales se sitúan en la primera hora desde un estado inicial común de 3704 pendientes. Sus reducciones frente a E0 son apenas 0.003145 pedidos en E1 y 2.439439 en E2: no debe presentarse el mejor pico como una reducción material grande. El área revela diferencias sostenidas que el pico inicial casi común oculta.

### Desplazamiento entre T2 y T3
| ventana | max_aumento_X3_E1 | fecha_max_aumento_X3_E1 | max_reduccion_X3_E1 | fecha_max_reduccion_X3_E1 |
|---|---|---|---|---|
| principal | 73.4632 | 2018-03-08 15:00:00 | -63.4167 | 2018-09-03 19:00:00 |
| sensibilidad_enero | 61.0057 | 2018-01-07 09:00:00 | -0.600556 | 2018-01-31 18:00:00 |

X1 es exactamente igual en los tres escenarios porque no existe retroalimentación desde β o γ hacia aprobación. E1 reduce la permanencia de X2 al aumentar su salida, pero anticipa entrada a X3: un aumento positivo de X3 frente al base es traslado de acumulación, no creación de pedidos. En la cola tardía ese signo puede cambiar porque los pedidos anticipados ya salieron. E2 conserva exactamente X1 y X2 y aumenta la salida de X3 hacia X4. Estas son dependencias del modelo, no causalidad demostrada en Olist.

A los siete días E1 reduce X2 en 110.122261 pedidos y aumenta X3 en 71.903413; la diferencia neta es su reducción de pendientes totales. E2 reduce X3 en 255.160201, sin alterar las etapas anteriores.

A igualdad de entradas y estado inicial, Δentregas=−Δpendientes en cada corte. Las entregas incrementales que gana una configuración son exactamente los pedidos que deja de tener pendientes en ese corte, dentro de redondeo. Las áreas incorporan el beneficio temporal sostenido y pueden distinguir configuraciones aunque ambas terminen casi vacías. El pico puede seguir determinado por el estado inicial común; no debe confundirse con una mejora de todos los períodos.

## Sensibilidad de calendario
Estado inicial observado: [57.0, 563.0, 1874.0, 41078.0]; compras: 7045; duración: 744 h.

| escenario | horizonte_horas | P_final | P_maximo | P_promedio | P_area_pedidos_hora | entregas_incrementales |
|---|---|---|---|---|---|---|
| E0 | 168 | 2582.67 | 2582.67 | 2457.45 | 412852 | 1251.33 |
| E0 | 720 | 3088.42 | 3255.35 | 2901.71 | 2.08923e+06 | 6199.58 |
| E0 | 744 | 3114.82 | 3255.35 | 2907.15 | 2.16292e+06 | 6424.18 |
| E1 | 168 | 2551.64 | 2551.64 | 2444.89 | 410741 | 1282.36 |
| E1 | 720 | 2975.36 | 3149.08 | 2834.23 | 2.04064e+06 | 6312.64 |
| E1 | 744 | 3001.8 | 3149.08 | 2838.19 | 2.11161e+06 | 6537.2 |
| E2 | 168 | 2412.07 | 2494 | 2360.41 | 396550 | 1421.93 |
| E2 | 720 | 2719.94 | 2926.05 | 2654.01 | 1.91089e+06 | 6568.06 |
| E2 | 744 | 2744.72 | 2926.05 | 2655.52 | 1.97571e+06 | 6794.28 |

Se aplicaron las mismas tres intervenciones sin nuevos ajustes. La tabla de ganadores distingue la ventana auxiliar; en los horizontes calculados también favorece E2 según las cuatro métricas. No se presenta como nueva validación ni se utiliza para retocar los escenarios.

## Controles de integridad y estructura
| ventana | escenario | max_error_conservacion | estabilidad_RK4 | estados_finitos_no_negativos | X4_no_decreciente | transferencias_no_negativas | agentes | AgentPy_RK4_diferencia_estados | AgentPy_RK4_diferencia_transferencias | inicializaciones |
|---|---|---|---|---|---|---|---|---|---|---|
| principal | E0 | 9.45874e-10 | True | True | True | True | 4 | 0 | 0 | 1 |
| principal | E1 | 3.20142e-10 | True | True | True | True | 4 | 0 | 0 | 1 |
| principal | E2 | 4.36557e-10 | True | True | True | True | 4 | 0 | 0 | 1 |
| sensibilidad_enero | E0 | 1.23691e-10 | True | True | True | True | 4 | 0 | 0 | 1 |
| sensibilidad_enero | E1 | 9.45874e-11 | True | True | True | True | 4 | 0 | 0 | 1 |
| sensibilidad_enero | E2 | 1.45519e-10 | True | True | True | True | 4 | 0 | 0 | 1 |

Identidades entre escenarios: `{"principal": {"max_diferencia_totales_entre_escenarios": 1.2660166248679161e-09, "max_error_delta_entregas_mas_delta_pendientes": 1.2767316093231784e-09, "X1_invariante_beta": true, "X1_X2_invariantes_gamma": true}, "sensibilidad_enero": {"max_diferencia_totales_entre_escenarios": 1.7462298274040222e-10, "max_error_delta_entregas_mas_delta_pendientes": 1.7143975128419697e-10, "X1_invariante_beta": true, "X1_X2_invariantes_gamma": true}}`. La tolerancia de conservación es 1e−8·max(1,total). Se verificaron estados finitos/no negativos, etapas internas RK4 no negativas, flujos no negativos, X4 no decreciente y estabilidad. No se recortaron valores ni corrigieron balances. AgentPy y RK4 coinciden exactamente en todas las ejecuciones de escenario. E0 en la ventana principal reproduce exactamente los estados del CSV de validación final al leerlo con conversión round_trip; no se recalculan métricas de precisión ni se modifica aquel informe.

## Interpretación académica y límites obligatorios
La conclusión cuantitativa se limita a las trayectorias e indicadores anteriores. Las intervenciones actúan sobre coeficientes efectivos agregados de un modelo de validez categoría C. No se modelan capacidades máximas, contratación, costos o consumo energético; no existe modelo validado de retrasos individuales contrafactuales. Las fechas estimadas históricas no permiten asignar promesas individuales a entregas agregadas simuladas.

Las compras son llegadas históricas conocidas, no un pronóstico. La cohorte retrospectiva contiene sólo entregados completos y excluye pedidos no entregados y cancelaciones, por lo que no representa el inventario operativo completo. La cola final tiene agotamiento de esa población; con tasas positivas las configuraciones tienden asintóticamente al mismo total entregado si cesan las compras. Por eso se comparan también siete, treinta y sesenta días y áreas bajo curvas. Un remanente final no se recorta para fingir vaciado completo.

La exactitud del balance y la equivalencia de motores no subsanan errores estadísticos de la validación. Estos experimentos ilustran interacciones entre depósitos y compromisos temporales bajo hipótesis; no prueban mejoras aplicables directamente por Olist. No se seleccionan coeficientes nuevos con el período ya evaluado. Cualquier desarrollo predictivo posterior requerirá un conjunto de prueba nuevo. No se implementaron Streamlit ni animaciones.

## Archivos y trazabilidad
Se crearon src/scenarios.py y src/scenario_metrics.py, reutilizables para consumir trayectorias e indicadores desde una futura interfaz. ScenarioDefinition y ScenarioRun conservan descripción, parámetros, ventana, entradas, resultados y comprobaciones. El script exporta indicadores_escenarios.csv, indicadores_horizontes.csv, diferencias_escenarios.csv, trayectorias_escenarios.csv, transferencias_escenarios.csv y comparacion_escenarios.json, sin sobrescribir resultados anteriores.

Las gráficas en graficas_escenarios/ incluyen X1, X2, X3, X4 incremental (equivale a entregas incrementales), P, área acumulada de P, transferencias, máximos e indicadores por horizonte para cada ventana ejecutada. Colores fijos E0=#334155, E1=#d56b16, E2=#16805d. No hay suavizado. Cada gráfico identifica fechas y unidades; se conserva la advertencia de categoría C.

Huellas de parámetros, datos, ZIP, código y resultados anteriores en comparacion_escenarios.json. Se verifican otra vez al terminar. Tiempo antes de pruebas: 8.543 s. Versiones Python 3.12.13, AgentPy 0.1.5, NumPy 2.5.4, pandas 3.1.1.

## Reproducción
```powershell
.venv/Scripts/python.exe scripts/ejecutar_escenarios.py
.venv/Scripts/python.exe scripts/ejecutar_escenarios.py --sensibilidad
```
La primera llamada ejecuta tres escenarios principales; la segunda, los mismos tres más tres trayectorias auxiliares en enero. Repetir no constituye nueva validación independiente. El script ejecuta las 100 pruebas previas y las nuevas, y guarda su salida real en pruebas_escenarios.txt.

## Pruebas ejecutadas

```text
........................................................................ [ 59%]
..................................................                       [100%]
122 passed in 10.77s
```

Se verificó que todos los archivos protegidos conservan su huella.
