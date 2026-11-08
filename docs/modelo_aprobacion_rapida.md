# Aprobación rápida: hipótesis, protocolo previo y arquitectura

## Alcance
Se evalúa una sola modificación: una fracción efectiva p de la entrada alcanza T2 inmediatamente a la resolución del modelo. Se mantienen cuatro estados agregados, cuatro agentes y las transferencias convencionales de primer orden. No se afirma infraestructura instantánea real de Olist. El modelo base y sus parámetros JSON permanecen como referencia; no se evalúa el 30 % reservado.

## Formulación y unidades

\[
\begin{aligned}
\dot X_1&=(1-p)\lambda-\alpha X_1,\\
\dot X_2&=p\lambda+\alpha X_1-\beta X_2,\\
\dot X_3&=\beta X_2-\gamma X_3,\\
\dot X_4&=\gamma X_3.
\end{aligned}
\]

α,β,γ≥0 tienen unidades hora⁻¹; p∈[0,1] es adimensional, λ≥0 se mide en pedidos/hora, los estados en pedidos. La entrada se divide en a1=(1−p)λ y a2=pλ. Su suma es λ. La transferencia convencional q12=αX1 no incluye a2; las aprobaciones totales simuladas son q12+a2. q23=βX2 y q34=γX3 mantienen su significado. Cada pedido rápido entra una vez, directamente en X2; no se suma además a X1 ni a q12.

Al sumar las cuatro derivadas se obtiene [(1−p)+p]λ=λ, por cancelación de todos los flujos internos. Para estados iniciales no negativos, coeficientes finitos no negativos y entrada localmente integrable no negativa, las derivadas sobre las fronteras Xi=0 son no negativas. La solución continua conserva positividad y X4 no disminuye. Los controles discretos siguen siendo necesarios.

Con p=0 se recupera exactamente el modelo base. Con p=1, X1 inicial sólo decae; si X1(0)=0, X1 permanece cero y α deja de identificarse a partir de la trayectoria. Para p cercano a uno la sensibilidad puede ser muy pequeña. Con p cercano a cero, el parámetro podría no justificar complejidad adicional. A tasas iguales y entrada constante, X1 estacionario=(1−p)λ/α: puede existir confusión entre p y α si faltan transitorios informativos.

La aprobación rápida aproxima permanencias pequeñas frente a una hora como masa efectiva de tiempo cero. No reproduce tiempos exactos intrahorarios ni atribuye pedidos a la rama rápida individualmente. No equivale a observar una fecha nueva ni convierte p en el porcentaje real de aprobaciones instantáneas.

## Protocolo fijado antes del cálculo del candidato

Datos: sólo `load_training`, 12.803 intervalos hasta 2018-03-02 22:00:00. El bloque interno de fase 4A y todos los bloques nuevos pertenecen al desarrollo y ya no se consideran una reserva intacta.

Cuatro ventanas expansivas: H=floor(0,15·12803)=1920 horas, primer corte de ajuste=12803−4H=5123. Los ajustes empiezan siempre en el primer corte y terminan en los índices 5123,7043,8963,10883. Sus evaluaciones son respectivamente (5123,7043], (7043,8963], (8963,10883], (10883,12803]. Los índices se refieren a intervalos desde el corte inicial; son horizontes iguales y sin solapamiento entre evaluaciones. No se seleccionan por errores observados.

En cada ventana se calibran los dos modelos con idéntico prefijo. Se congelan sus parámetros y se inicializa el bloque posterior una vez con el mismo vector observado; luego se usan sólo compras y EDO. Escalas X1–X3=max(1,media del prefijo de ajuste), iguales para ambos. X4 incremental y P, y los flujos, también usan escalas del prefijo respectivo. Ninguna escala se recalcula con evaluación. X4 no participa en la pérdida.

TRF y residuos normalizados de fase 4A. Tasas con cotas [0,+∞), candidato con p∈[0,1]. Iniciales base: 0,5,1,2 veces las tasas de exposición del prefijo. Iniciales candidato: combinación cartesiana de esos tres factores y p0∈{0,0,5,0,9}, es decir nueve inicios prefijados. No se emplean los parámetros de la reserva ni inicios artificiales del integrador. Cotas de p son estructurales y no capacidades de servicio.

La aprobación rápida puede transferir parte de las compras directamente a T2; la exposición preliminar sólo sirve como escala de inicialización del candidato, no como estimación correcta de su tasa lenta. Se estima conjuntamente α,β,γ,p mediante trayectoria.

Selección: calcular por ventana 100·(1−NRMSE_candidato/NRMSE_base), con las mismas escalas. Exigir mediana de mejora de X1≥15 % y deterioro máximo de X2 y X3≤10 % en cualquier ventana. Si un denominador es cero, no generar porcentajes indefinidos: igualdad cero se considera sin mejora; empeoramiento desde cero invalida la condición.

Además exigir controles numéricos, convergencia del optimizador y parámetros interpretables. Guardas académicas explícitas de estabilidad antes del ajuste: rango de p entre ventanas≤0,20; cociente máximo/mínimo de cada tasa≤2; ninguna solución con p≥0,99; condición del jacobiano escalado<1000; correlación de columnas de sensibilidad α,p en magnitud<0,98. Son criterios operativos de esta comparación, no umbrales estadísticos universales. Si p≤0,01, inspeccionar su aporte por perfiles de costo; no declarar ventaja por un mínimo entrenamiento apenas menor. Se documentarán los valores aunque no se cumplan las guardas.

Los perfiles de costo fijan p en una rejilla predefinida {0;0,25;0,5;0,75;0,9;0,99;1} y reestiman tres tasas sólo en el entrenamiento completo; son diagnósticos de identificabilidad, no candidatos estructurales adicionales ni intervalos de confianza. Se usarán jacobiano, dispersión multiinicio y variación temporal; no se inferirá identificación global sólo por rango local.

Después de la decisión interna se recalibrará el seleccionado con todo el desarrollo; también se conservará el ajuste completo del candidato para documentarlo. No se reemplaza `reports/parametros_calibrados.json`. La reproducción definitiva y métricas se obtienen con RK4 y se contrastan con el propagador auxiliar de las mismas ecuaciones; no se cambia el paso para mejorar el ajuste.

## Implementación y comprobaciones

`RapidParameters` distingue el candidato del modelo base. La función vectorial y la división de entradas son compartidas por RK4, el propagador analítico y AgentPy. La matriz homogénea y sus autovalores no cambian; sólo cambia el vector de entrada a [(1−p),p,0,0]. Los balances horarios separan la llegada rápida de la transferencia q12.

Se conserva el significado de `SimulationResult.transfers` como tres transferencias convencionales. `rapid_arrivals` registra la entrada directa en T2; las aprobaciones totales por hora se forman como transfers[:,0]+rapid_arrivals. AgentPy añade ese registro sin crear agentes nuevos. Con p=0, las salidas matemáticas base deben ser exactamente iguales.

Se comprueba conservación con tolerancia 1e−8·max(1,total), estados finitos no negativos, etapas internas RK4 no negativas, X4 no decreciente y flujos convencionales/directos no negativos. Las entradas siguen congeladas para K1–K4 de cada hora, sin tomar la hora siguiente en su frontera. Se prueban h=0,25,0,125,0,0625, con criterios previos de máximo 0,1 pedido y NRMSE numérico 0,001. Un caso inestable se rechaza; no se recorta estado ni se cambian parámetros para ocultarlo.

## Interpretación y límites

Una pérdida de entrenamiento menor no basta: se añadió un parámetro. La selección usa desempeño cronológico interno y estabilidad. Si se conserva el base, no se borra el candidato ni se afirma que la hipótesis es universalmente falsa. Si se elige el candidato, tampoco se afirma validación final.

La cohorte contiene sólo entregados completos retrospectivos; censurar fechas para estimación no elimina ese sesgo. No representa todo el inventario operativo, cancelaciones ni decisiones causales de Olist. La entrada histórica conocida evalúa dinámica condicionada, no pronóstico de demanda. La aproximación instantánea y los parámetros constantes pueden seguir fallando ante calendarios, edad y heterogeneidad. Los resultados se documentarán en `reports/comparacion_modelos.md`.
