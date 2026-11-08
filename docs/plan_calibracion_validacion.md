# Plan de calibración y validación

## Estado del plan

Especificación para una fase posterior. No se ajustaron α, β, γ, no se ejecutó RK4 y no se calcularon métricas predictivas. Los datos y unidades comprobados se detallan en [modelo_matematico.md](modelo_matematico.md). Las estadísticas globales de fase 1 son diagnóstico descriptivo; las escalas, decisiones de ajuste y distribuciones usadas para estimar se calcularán exclusivamente con entrenamiento.

## 1. Separación cronológica por duración

Usar los cortes de `data/processed/niveles_reales_4_tanques.csv`, no dividir aleatoriamente pedidos o filas de pedidos. Existen N=18.291 intervalos de una hora. Definir m=floor(0,70N)=12.803 y s*=s_inicio+m horas.

| Segmento | Inicio | Fin | Intervalos |
|---|---|---|---:|
| Calibración | 2016-09-15 11:00:00 | 2018-03-02 22:00:00 | 12.803 |
| Validación reservada | 2018-03-02 22:00:00 | 2018-10-17 14:00:00 | 5.488 |

Es aproximadamente 70/30 del tiempo transcurrido, no del número de pedidos. El corte común inicializa validación y no se duplica como observación objetivo. Objetivos de entrenamiento: cortes s_inicio<s≤s*. Objetivos de validación: s*<s≤s_fin. Los flujos se asignan al segmento según el extremo derecho del intervalo. La fila inicial vacía no añade una hora.

Se permite que un pedido haya ingresado en entrenamiento y termine en validación: su volumen pendiente debe cruzar el límite a través del estado inicial, no eliminarse. En s* los estados reales son (113,586,3005,53963), con total 57667. Estos valores fueron leídos del archivo existente. No usar eventos posteriores a s* para calcular exposiciones, transferencias ni duraciones de entrenamiento.

La ventana final contiene el agotamiento de una cohorte finita; no es evidencia automática de menor demanda operativa. Reportar métricas por bloques temporales además de toda la ventana, con bloques fijados antes de observar resultados.

## 2. Estimación propuesta

### Objetivo principal: mínimos cuadrados de trayectoria

Sea y_ik el nivel observado de etapa i en el corte k y x_i(t_k;θ) la solución del modelo con compras históricas del entrenamiento e inicialización observada. Estimar posteriormente:

\[
\widehat\theta=\arg\min_{\theta\in[0,\infty)^3}
\frac13\sum_{i=1}^{3}\frac1{N_{tr}}
\sum_{k\in tr}\left[\frac{x_i(t_k;\theta)-y_{ik}}{s_i}\right]^2.
\]

Propuesta de escala fija s_i=max(1 pedido, media de y_i en entrenamiento). Los pesos iguales por etapa evitan que X3 domine sólo por tamaño; reportar también errores absolutos. Las escalas no se calculan con validación. Si se cambia la escala por dispersión robusta o se añade una pérdida robusta, decidirlo dentro de entrenamiento y documentarlo antes de abrir la validación final.

Aplicar mínimos cuadrados no lineales con restricciones de no negatividad. Puede usarse parametrización θ_j=exp(η_j) si se exige tránsito estrictamente positivo; entonces se excluye exactamente cero y se necesita revisar límites prácticos. Un coeficiente nulo admite bloqueo permanente y no explica entregas posteriores sin otra fuente. Cualquier cota superior debe tener justificación temporal/numérica, sin tratarla como capacidad real conocida. Registrar unidades, convergencia del optimizador, sensibilidad a inicializaciones y parámetros en frontera. No se proponen valores numéricos calibrados aquí.

X4 no participa inicialmente en la pérdida principal. Comparar adicionalmente su incremento desde el inicio, evitando el gran acumulado previo. Si se incorporan flujos al objetivo, usar sus integrales por hora y pesos explícitos; niveles y flujos derivan de los mismos eventos, por lo que no constituyen observaciones independientes para inferencia de incertidumbre.

### Diagnóstico e inicialización opcional: mínimos cuadrados de transferencias

Para una etapa con coeficiente k, la hipótesis implica F_j≈k E_j, donde F_j es la transferencia observada en el intervalo j y E_j=∫X_origen(s)ds es la exposición, en pedidos·hora. Minimizar Σw_j(F_j−kE_j)² con k≥0. Para pesos fijos no negativos y denominador positivo:

\[
\widehat k=\max\left(0,\frac{\sum_j w_jE_jF_j}{\sum_j w_jE_j^2}\right).
\]

Esto sólo define un método posterior, no una estimación realizada. La exposición puede calcularse exactamente a partir de eventos de entrenamiento: integrar los niveles escalonados sobre cada intervalo, truncando toda permanencia en s*. Si sólo se usan niveles horarios, una regla trapezoidal es aproximada y debe etiquetarse. No usar automáticamente el nivel de inicio como exposición exacta: un pedido puede entrar y salir dentro de una hora, incluso si el nivel inicial es cero. Si ΣwE²=0, no hay información para estimar ese coeficiente; no asignar una tasa arbitraria.

Este ajuste con exposición observada puede servir como inicialización o contraste, pero no reemplaza la evaluación de trayectoria libre. No imponer F_j reales al simular. Correlación temporal, heterocedasticidad y error de medición limitan la interpretación estadística de mínimos cuadrados ordinarios. Si se estiman intervalos de incertidumbre, considerar remuestreo por bloques dentro de entrenamiento y revisar identificabilidad; no inventar intervalos a partir de errores independientes.

### Duraciones y supuesto exponencial

Bajo permanencias exponenciales independientes, sin censura ni selección y con riesgo constante, la media es 1/k y la mediana ln(2)/k. Por tanto, incluso bajo esa hipótesis, 1/mediana no es el coeficiente: sería ln(2)/mediana. Ninguna de estas relaciones justifica aplicar automáticamente inversos de duraciones a esta cohorte seleccionada.

En entrenamiento, pedidos sin transición al corte aportan exposición censurada, no tiempos futuros completos. No filtrar únicamente por etapas completadas antes del corte para calcular una supuesta media representativa. El método de exposición aprovecha el tiempo observado sin mirar la fecha posterior de salida, aunque el sesgo de membresía retrospectiva de la cohorte permanece.

## 3. Prevención de filtración futura

1. Fijar y registrar s*, ventanas, convención de entrada, escalas, pérdida y métricas antes de calibrar.
2. Recortar los objetivos y flujos de entrenamiento al corte; cualquier integración de exposición termina allí. No usar futuras entregas ni la fecha estimada como información explicativa adicional de estas EDO.
3. Dentro del 70 %, usar subdivisiones cronológicas con origen móvil para seleccionar restricciones, pesos o complejidad y revisar estabilidad de parámetros. Recalibrar finalmente sólo con ese 70 %.
4. Congelar parámetros y decisiones antes del 30 %. Si se rediseña el modelo tras inspeccionarlo, ese bloque pasa a ser desarrollo y hará falta otra prueba no utilizada; no presentar el mismo bloque como prueba independiente.
5. Inicializar validación una sola vez desde el corte y no corregirla con estados posteriores. Las transferencias reales de validación sólo son referencias de evaluación.
6. Mantener λ independiente de las transferencias internas. Para el experimento retrospectivo se usan las compras realizadas en validación, conocidas después de los hechos; no se afirma capacidad de anticiparlas.

La selección original por estado delivered y cuatro fechas completas usa información futura respecto de muchos cortes. El protocolo evita contaminación adicional del ajuste, pero no elimina esa selección. Los resultados sólo validarán una dinámica retrospectiva condicionada a esta cohorte. Una validación prospectiva de todos los pedidos requerirá redefinir población por compras conocidas al origen, observación censurada y tratamiento verificable de cancelaciones. No reconstruir cancelaciones sin fechas.

## 4. Métricas por etapa

Con errores e_ik=x_i(t_k)−y_ik, reportar para cada i=1,2,3 por separado:

\[
MAE_i=\frac1N\sum_k|e_{ik}|,\qquad
RMSE_i=\sqrt{\frac1N\sum_k e_{ik}^2}.
\]

Unidades: pedidos. NMAE_i=MAE_i/s_i y NRMSE_i=RMSE_i/s_i son adimensionales con escalas congeladas del entrenamiento. No usar MAPE en horas con nivel cero. Para etapas con escala cercana a cero, priorizar errores absolutos y explicar que la normalización por 1 pedido es una convención.

Error de máximo: Emax_i=max_k x_i−max_k y_i, con versión absoluta |Emax_i|; no es igual a max_k|e_ik|, que también se reportará como peor error puntual. Informar desfase temporal de los picos si es relevante, pues amplitudes iguales pueden aparecer en momentos distintos.

Error final: Efin_i=x_i(t_fin)−y_i(t_fin), además de su magnitud. Para pendientes totales P=X1+X2+X3, reportar el error final y el área ∫Pdt en pedidos·hora. No permitir que errores de signo opuesto entre etapas oculten un problema mediante el total.

Para X4: comparar incrementos x4(t)−x4(0) frente a y4(t)−y4(0), entregas por hora y error final. El acumulado previo no debe dominar una pérdida. Los flujos predichos se comparan integrando q12, q23 y q34 sobre cada hora, no tomando sólo su valor en un extremo.

Presentar tabla por etapa, errores temporales, picos y bloques de validación. Una cifra global será secundaria y acompañada por el peor resultado entre etapas. La conservación es una prueba física independiente, no una métrica de acierto predictivo.

## 5. Criterios de evaluación propuestos

Primero deben pasar coherencia dimensional, entrada acumulada, conservación, positividad y convergencia numérica del documento matemático. Sólo después evaluar ajuste estadístico. La diferencia entre mallas debe ser pequeña frente al error frente a datos, para no atribuir a parámetros un error del integrador.

Como umbrales académicos provisionales para revisar antes de ajustar, proponer en cada etapa pendiente: NMAE≤0,20, NRMSE≤0,30, error absoluto de pico≤max(1 pedido, 0,20·pico observado de esa etapa en validación) y error final absoluto≤max(1 pedido, 0,20·s_i). Son reglas de decisión propuestas, no estándares de Olist ni logros comprobados. La referencia al pico observado sólo define la métrica de evaluación; no se utiliza para ajustar pesos ni parámetros. Aprobar el agregado no compensa que una etapa incumpla. Exigir además ausencia de patrones persistentes de sesgo por bloques y explicar fallos locales aunque la media cumpla.

Comparar con una referencia sencilla predefinida, por ejemplo persistencia del nivel inicial para X1–X3, como referencia de error por etapa, sin atribuirle conservación física. Si una métrica de referencia es cero, no calcular una mejora porcentual indefinida. Los umbrales deberán acordarse según la finalidad académica y la variabilidad de entrenamiento, antes de inspeccionar la validación final.

Si fallan los criterios, reportar insuficiencia del modelo y revisar residuos de entrenamiento, resolución horaria, heterogeneidad o riesgo dependiente de edad. Comparar coeficientes constantes con calendarios o funciones temporales de baja complejidad sólo si hay evidencia en entrenamiento y mejora en evaluación cronológica interna. No introducir coeficientes libres para cada hora: pueden reproducir observaciones sin generalizar. La validación reservada evalúa la elección final, no la dirige.

## 6. Dos preguntas distintas

La validación con llegadas históricas conocidas pregunta si el modelo reproduce acumulaciones y transferencias dado el flujo real de compras. El pronóstico genuino requiere un modelo separado de λ futura, entrenado sólo con el pasado, más propagación de incertidumbre de demanda y parámetros. La fase propuesta cubre la primera pregunta. Ninguna métrica aún ha sido calculada.
