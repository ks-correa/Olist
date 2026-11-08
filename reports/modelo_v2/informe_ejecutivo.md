# Resultado ejecutivo — 8 de noviembre de 2026

**No se alcanzó NRMSE ≤ 0,30 simultáneamente en X1, X2 y X3.**
La mejora de B es pequeña y no permite sustituir V1 como modelo aceptado.

| modelo | variable | MAE | RMSE | NRMSE |
|---|---|---|---|---|
| V1_historico | X1 | 24.4959 | 44.1688 | 0.994955 |
| V1_historico | X2 | 138.871 | 184.657 | 0.558954 |
| V1_historico | X3 | 546.733 | 669.099 | 0.666343 |
| V2_B | X1 | 23.46 | 43.1811 | 0.972705 |
| V2_B | X2 | 127.801 | 169.141 | 0.511986 |
| V2_B | X3 | 546.365 | 667.537 | 0.664788 |

1. Precisión original: NRMSE 0,994955 / 0,558954 / 0,666343, reproducida.
2. Se añadieron diagnóstico dinámico, tasas de calendario, Erlang de dos fases,
mezcla de vías rápidas/lentas, calibración multiorigen, bondad de ajuste,
congelaciones, pruebas e interfaz de comparación. Se preservó V1.
3. B obtiene NRMSE 0.972705 / 0.511986 /
0.664788 en la reserva histórica reutilizada.
4. Ninguna de sus tres etapas llega al objetivo de 0,30 en ese bloque.
5. Tampoco satisface todos los criterios NMAE, pico y final de manera conjunta.
6. Persisten autocorrelación, colas de error y sesgos; la conservación y
convergencia son buenas, pero no demuestran precisión empírica.
7. La media del peor NRMSE entre ventanas pasa de 1,277873 (A) a 1,249219 (B).
La mejora es 2,24%; el desempeño es inestable. Erlang y mezcla no la mejoran.
8. No hay datos nuevos independientes. La segunda ronda fue adaptativa.
9. Conservar V1 como referencia reproducible; B como candidato experimental
separado. No proclamar superioridad estable ni aceptación operativa.
10. Persisten heterogeneidad, sesgo retrospectivo de población, ausencia de
validación nueva, inicialización de fases e identificación débil de la mezcla.

La suite completa registrada tiene **207 aprobadas y 1 fallo preexistente**:
el hash de pedidos_limpios.csv difiere del manifiesto histórico, pero coincide
exactamente con la huella tomada antes de trabajar. No se cambió ese archivo,
el manifiesto ni la prueba. Las 20 pruebas nuevas pasan. Las advertencias de
pandas por dayofweek se conservan en el registro; no alteran los resultados.
La interfaz se comprobó con AppTest y seis interacciones HTTP reales listas
sin excepciones, sin comprobación visual completa del navegador.

Índice de evidencias: diagnostico_tecnico.md, modelo_matematico_v2.md,
calibracion_v2.md, bondad_ajuste.md, validacion_v2.md,
escenarios_y_presentacion.md, reproduccion.md, CSV/JSON y graficas/.
