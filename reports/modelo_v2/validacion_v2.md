# Evaluación temporal y límites de aceptación

Se distinguen entrenamiento ajustado, evaluación interna de desarrollo
reutilizado y reserva histórica reutilizada. NO existe una reserva nueva
independiente. Los protocolos y congelaciones no borran el uso previo.
No se anticipan compras futuras: las entradas históricas se condicionan.

## Comparación equivalente en desarrollo

Todos usan los mismos 1920 objetivos por ventana, estado agregado al origen,
entrada horaria y escalas de su prefijo. A se reajusta en cada prefijo:
usar tasas V1 de todo el desarrollo aquí habría introducido información futura.
Las hipótesis de reparto interno inicial de C/M son diferentes, pero no usan
estados futuros y se declaran explícitamente.

| modelo | ventana | X1 | X2 | X3 |
|---|---|---|---|---|
| A | 5123 | 2.14622 | 0.82386 | 0.640402 |
| A | 7043 | 0.744934 | 0.538559 | 0.246325 |
| A | 8963 | 1.26898 | 0.936591 | 0.446823 |
| A | 10883 | 0.95136 | 0.571502 | 0.560439 |
| B | 5123 | 2.108 | 0.699309 | 0.642048 |
| B | 7043 | 0.719426 | 0.41683 | 0.247511 |
| B | 8963 | 1.25296 | 0.80041 | 0.432437 |
| B | 10883 | 0.916492 | 0.4844 | 0.557136 |
| C | 5123 | 2.19584 | 0.840697 | 0.625544 |
| C | 7043 | 0.762925 | 0.568224 | 0.231724 |
| C | 8963 | 1.31808 | 0.933042 | 0.384583 |
| C | 10883 | 0.968501 | 0.59228 | 0.658946 |
| M | 5123 | 2.13488 | 0.821531 | 0.633409 |
| M | 7043 | 0.754322 | 0.499906 | 0.254729 |
| M | 8963 | 1.26928 | 1.08753 | 0.523552 |
| M | 10883 | 0.960012 | 0.566858 | 0.559916 |

Ningún candidato cumple NRMSE<=0,30 en las tres etapas a lo largo de las
ventanas. Ver todas las métricas, criterios de pico/final y sesgos en
metricas_ventanas_ampliadas.csv. No se promedian incumplimientos para aceptarlos.

## Reproducción histórica y resultado final de B

| modelo | variable | NRMSE | NMAE | cumple |
|---|---|---|---|---|
| V1_historico | X1 | 0.994955 | 0.551799 | False |
| V1_historico | X2 | 0.558954 | 0.420359 | False |
| V1_historico | X3 | 0.666343 | 0.544481 | False |
| V2_B | X1 | 0.972705 | 0.528464 | False |
| V2_B | X2 | 0.511986 | 0.386852 | False |
| V2_B | X3 | 0.664788 | 0.544114 | False |

Las cifras V1 se reproducen con tolerancia flotante de 1e−7 pedidos frente
al motor RK4 original; los CSV e informes V1 quedan intactos. Se mantienen
NRMSE<=0,30; NMAE<=0,20; error pico<=max(1,0,2*pico observado);
error final<=max(1,0,2*escala de entrenamiento), por cada etapa. No hay
aceptación completa ni evidencia nueva de generalización externa.

Controles físicos por ventana y período: masa máxima de B
6.5483619e-10 pedidos,
sin estados negativos ni X4 decreciente. Refinamiento en convergencia.json.
AgentPy coincide exactamente en publicación de los cuatro agregados de B
durante las 5488 h de reserva; las pruebas también cubren A/C/D y M.
La ausencia de error numérico no compensa el error respecto de observaciones.

Limitaciones: cohorte entregada retrospectiva, inicialización interna de
fases aproximada, pocas estructuras e hiperparámetros prefijados, óptimos
locales posibles, validación interna ya reutilizada, no incertidumbre de
demanda ni efectos causales de escenarios. No se afirma haber agotado todos
los modelos matemáticamente posibles ni que más complejidad garantice precisión.
