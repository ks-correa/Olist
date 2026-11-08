# Diagnóstico técnico de OLIST / LAB

Se auditó el commit 6b732fba7bba43071cbf5ad1624eec4e10f1ded8, con Git limpio
antes de crear feature/modelo-v2-bondad-ajuste. Las 156 huellas de entrada y
archivos inspeccionados están en auditoria_previa.json. Se revisaron motores,
datos, informes, interfaz, escenarios, pruebas y documentación anteriores.
No se modificó ningún archivo científico V1 ni su población.

## Hallazgos respaldados por mediciones

1. **X1 y permanencias:** entre eventos completados al corte, 64,845% dura
menos de una hora, mediana 0,296944 h y P95 47,9563 h. La exponencial V1
tiene media 9,801636 h. KM, con 113 censuras de aprobación, presenta distancia
máxima descriptiva 0,555 frente a esa ley. Hay heterogeneidad no representada;
esto no demuestra que una mezcla particular sea correcta. El Erlang de dos
fases empeora el criterio interno. La mezcla ensayada mejora levemente la ley
de X1 pero no las trayectorias de desarrollo: ajuste distributivo y dinámico
son objetivos distintos. Ver permanencias_resumen.csv,
distancias_permanencia.csv y graficas/permanencias_comparadas.png.

| variable | n | completadas | censuradas | mediana_completadas | p95_completadas | media_exponencial_V1 |
|---|---|---|---|---|---|---|
| X1 | 57667 | 57554 | 113 | 0.296944 | 47.9563 | 9.80164 |
| X2 | 57554 | 56968 | 586 | 49.1592 | 202.633 | 75.5242 |
| X3 | 56968 | 53963 | 3005 | 183.887 | 548.439 | 245.585 |

2. **Calendario:** B reduce especialmente RMSE de despacho, pero la media
del peor NRMSE interno solo pasa de 1.277873
a 1.249219. No basta atribuir todo el error
a tasas constantes. En X3 el efecto de calendario ajustado es casi nulo.
Los residuos por mes, hora, día semanal y bloque de 168 h se entregan completos
en errores_temporales_*.csv, sin cambiar sus escalas por grupo.

3. **Estabilidad temporal:** tasas mensuales descriptivas por exposición exacta
censurada, sin consultar eventos posteriores al corte mensual:

| variable | min | max |
|---|---|---|
| X1 | 0.0807806 | 4.04494 |
| X2 | 0.00925438 | 0.0159149 |
| X3 | 0.00335771 | 0.00525898 |

Estos cambios mezclan calendario, composición y carga; no identifican por sí
solos una causa operativa. Las tasas ajustadas por prefijo y los resultados
en cada ventana están en estabilidad_parametros.csv y metricas_ventanas_ampliadas.csv.
Las ventanas no son réplicas independientes y tienen escalas distintas por
prefijo, fijadas antes de puntuar. El crecimiento de demanda con medias
tempranas pequeñas hace exigente el NRMSE interno; no se cambió el denominador.

4. **Sesgo y picos:** en la reserva reutilizada V1 tiene sesgo positivo de
3,619 / 109,262 / 287,797 pedidos en X1/X2/X3. B conserva sesgos de
3,779 / 109,264 / 287,332. Ese promedio coexiste con subestimación de los picos
de X1. Ver picos_persistencia.csv para amplitud, desfase y rachas, y
subidas_descensos.csv para subida/descenso y error del cambio horario.
No se interpreta una media próxima a cero como ausencia de fallos locales.

5. **Error numérico:** diferencia RK4 h=0,25 frente a 0,125 en todo el desarrollo
de B = 1.11194583e-06 pedidos, muy inferior a RMSE
empíricos de decenas/centenares. Refinar a 0,0625 vuelve a reducir el error.
No hay evidencia de que el integrador explique el mal ajuste.

6. **Agregación:** al distribuir las mismas compras por sus marcas originales
en 15 minutos, conservando objetivos horarios, la sensibilidad de V1 es:

| variable | RMSE | NRMSE | max_diferencia_vs_entrada_horaria |
|---|---|---|---|
| X1 | 22.5388 | 0.507713 | 2.29126 |
| X2 | 99.7261 | 0.301869 | 2.38652 |
| X3 | 194.941 | 0.194138 | 0.205864 |

Es un diagnóstico retrospectivo adicional, sin reajustar parámetros ni
reemplazar la convención oficial. No resuelve los errores; tampoco descarta
otros efectos de agregación individual o heterogeneidad de pedidos.

7. **Selección de población:** los 95.082 pedidos son entregados con cronología
válida y cuatro fechas completas. La pertenencia usa información futura
respecto de muchos orígenes. Se mantuvo esa población explícitamente; no es
todo el inventario de Olist ni incluye cancelaciones con fechas verificadas.
KM incorpora censuras administrativas de etapa al corte, pero no elimina
el sesgo de selección de cohorte ni garantiza censura no informativa.
La cola final sin compras se conserva: no se recortó para favorecer métricas.

## Balance de causas

Evidencia fuerte contra explicación numérica; sensibilidad de entrada
intrahoraria pequeña bajo la convención ensayada. Evidencia de desajuste de
permanencias en aprobación, errores temporales persistentes y parámetros
efectivos variables entre prefijos. El calendario explica parte del error de
despacho, sin resolver aprobación ni entrega. No puede aislarse causalmente
el efecto de selección, heterogeneidad logística o cambios operativos con
esta comparación observacional. No se inventan capacidades ni mecanismos.
