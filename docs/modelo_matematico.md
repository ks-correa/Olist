# Modelo matemático continuo de cuatro depósitos virtuales

## 1. Alcance y evidencia inspeccionada

Esta fase especifica el modelo; no implementa un integrador, calibración, simulación ni interfaz. Se revisaron `src/data_processing.py`, `scripts/analizar_dataset.py`, las pruebas, el informe de auditoría y los CSV reales de `data/processed/`.

Los datos históricos son marcas de compra, aprobación, despacho y entrega. Los niveles son variables reconstruidas por conteo de esas marcas. Las EDO siguientes son hipótesis para aproximar su evolución, no identidades extraídas del dataset. No existen aún parámetros ajustados ni resultados de precisión del modelo.

La fuente tiene 99.441 pedidos; la cohorte contiene 95.082 pedidos delivered con cuatro fechas completas y orden no decreciente. Hay 18.292 cortes horarios, de 2016-09-15 11:00:00 a 2018-10-17 14:00:00, equivalentes a 18.291 intervalos. El corte inicial es una referencia vacía, no un intervalo adicional. No se presume zona horaria: se conserva el reloj del CSV.

## 2. Estados, entradas, parámetros y salidas

Sea s la fecha del calendario y s0 el inicio de la ventana. El tiempo del modelo es t=(s−s0)/(1 hora), medido en horas.

| Símbolo | Significado | Unidad |
|---|---|---|
| X1 | Comprados pendientes de aprobación | pedidos |
| X2 | Aprobados pendientes de despacho | pedidos |
| X3 | Despachados pendientes de entrega al cliente | pedidos |
| X4 | Entregados acumulados, depósito terminal | pedidos |
| λ(t) | Entrada externa de compras de la cohorte | pedidos/hora |
| α, β, γ | Coeficientes de aprobación, despacho y entrega | hora⁻¹ |
| q12, q23, q34 | Transferencias internas calculadas | pedidos/hora |

X4 no es una cola pendiente y no tiene salida en este sistema. Las salidas observables del modelo son los cuatro niveles y los tres flujos calculados; las entregas ingresan en X4 sin abandonar la población total.

La correspondencia con `niveles_reales_4_tanques.csv` es exacta en definición: X1=A−B, X2=B−C, X3=C−D, X4=D, con A, B, C, D como compras, aprobaciones, despachos y entregas acumuladas. La EDO produce aproximaciones continuas, que pueden ser fraccionarias: representan volumen agregado de pedidos, no pedidos individuales fraccionados operativamente. No se redondearán durante la integración.

## 3. Ecuaciones propuestas

\[
q_{12}=\alpha X_1,\qquad q_{23}=\beta X_2,\qquad q_{34}=\gamma X_3.
\]

\[
\begin{aligned}
\dot X_1&=\lambda(t)-\alpha X_1,\\
\dot X_2&=\alpha X_1-\beta X_2,\\
\dot X_3&=\beta X_2-\gamma X_3,\\
\dot X_4&=\gamma X_3.
\end{aligned}
\]

Cada término es una tasa en pedidos/hora. λ añade compras a X1. La aprobación retira αX1 de X1 y añade exactamente esa cantidad a X2; análogamente ocurre en despacho y entrega. Los coeficientes son desconocidos, finitos y no negativos; para tránsito eventual de toda la población se requieren los tres estrictamente positivos.

Es la analogía de balance hidráulico de entrada, acumulación y salida, con pedidos como contenido. La proporcionalidad flujo/nivel es una hipótesis lineal de primer orden; no se deduce de una ley hidráulica, de la capacidad de Olist ni de porcentajes observados.

## 4. Supuestos y contraste descriptivo

Se supone población cerrada salvo compras, recorrido secuencial, ausencia de cancelaciones dentro de la cohorte, homogeneidad agregada y coeficientes inicialmente constantes. No hay capacidad máxima, congestión no lineal, calendario laboral, composición regional ni dependencia explícita del tiempo ya transcurrido en cada etapa.

Interpretado como tránsito independiente con riesgo constante k, el primer orden equivale a una permanencia exponencial: S(u)=exp(−ku), media 1/k, mediana ln(2)/k, P95=−ln(0,05)/k y desviación estándar igual a la media. Esta interpretación es una hipótesis adicional sobre los tiempos individuales; la EDO por sí sola especifica balances agregados.

Las estadísticas verificadas de `duraciones_etapas_horas.csv` son descriptivas de la cohorte completa y no se usarán como estimaciones de entrenamiento:

| Etapa | Media h | Mediana h | P95 h | Desviación h |
|---|---:|---:|---:|---:|
| Compra–aprobación | 9,6505 | 0,3378 | 45,8120 | 19,1169 |
| Aprobación–despacho | 68,4420 | 44,3715 | 195,1400 | 83,5916 |
| Despacho–entrega | 224,7387 | 170,6478 | 583,8366 | 210,4661 |

En una exponencial, mediana/media≈0,693 y P95/media≈2,996. Aquí esos cocientes son aproximadamente (0,035; 4,747), (0,648; 2,851) y (0,759; 2,598). La aprobación presenta la incompatibilidad descriptiva más marcada: muchas aprobaciones rápidas junto con una cola larga. Las otras etapas se aproximan más a algunos cocientes, pero sus desviaciones y percentiles tampoco prueban riesgo constante. Hay duraciones cero en aprobación y entrega; una exponencial continua no asigna masa a cero. Pueden reflejar registros simultáneos o resolución de medición.

Se conserva el modelo lineal como referencia por su parsimonia y trazabilidad. Los resúmenes no bastan para aceptar o rechazar formalmente una distribución. Más adelante se examinarán supervivencia y riesgo por edad, residuos por hora/día, heterogeneidad y cambios temporales, usando entrenamiento. Si falla: coeficientes por calendario, flujos saturables, mezclas, retardos o modelos estructurados por edad/fases. Las fases adicionales serían estados latentes matemáticos, nunca eventos logísticos observados inventados; ampliar los cuatro estados requerirá revisión expresa.

## 5. Conservación, positividad y existencia

Al sumar las ecuaciones, cada flujo interno aparece una vez con signo positivo y otra con signo negativo:

\[
\dot S=\dot X_1+\dot X_2+\dot X_3+\dot X_4=\lambda(t),\qquad
S(t)=S(0)+\int_0^t\lambda(u)\,du.
\]

En cortes de observación, con inicialización consistente y entrada que conserve compras, el total debe coincidir con A(s). Esto no implica acertar la distribución entre etapas: diferentes parámetros conservan igualmente el total.

Para X(0)≥0, α,β,γ≥0 y λ≥0 localmente integrable, la solución continua permanece no negativa. En una frontera Xi=0, su derivada es respectivamente λ, αX1, βX2 o γX3, todas no negativas. Equivalentemente, la matriz del sistema tiene elementos fuera de diagonal no negativos y su exponencial preserva el cono positivo. El sistema lineal con entrada por tramos tiene solución única absolutamente continua, diferenciable salvo posibles saltos de λ. X4 es no decreciente. Coeficientes finitos y entrada integrable en ventanas finitas evitan explosión en tiempo finito.

Positividad continua no garantiza positividad de RK4 para cualquier paso. No corregir niveles negativos mediante recorte o redondeo: alteraría balances y ocultaría problemas del integrador.

## 6. Condiciones iniciales observadas

Para iniciar en un corte s0, localizar la fila exacta por `corte_horario` en `niveles_reales_4_tanques.csv`, exigir fecha única y leer `[X1,X2,X3,X4]`. Mantener X4 acumulado desde el origen de la cohorte. Si se presenta entrega incremental, usar X4(t)−X4(0) como salida auxiliar, sin cambiar el estado.

En el comienzo completo, la fila realmente observada es (0,0,0,0); no es una condición universal. Para el corte de validación propuesto, 2018-03-02 22:00:00, la fila real es (113,586,3005,53963), con A=57667. Los estados suman 57667. Se verificó este valor leyendo el CSV, sin ajustar parámetros.

Si s0 no es un corte, debe reconstruirse desde las marcas originales con desigualdades inclusivas: contar compras, aprobaciones, despachos y entregas con fecha ≤s0 y aplicar las diferencias; no tomar la fila siguiente ni interpolar estados futuros. Es preferible alinear ventanas con cortes horarios.

Inicializar validación una sola vez con el estado observado en s0. Luego usar únicamente compras de cada intervalo y las EDO, sin reiniciar con estados reales posteriores. Este experimento evalúa dinámica condicionada a un estado inicial conocido. Una evaluación de trayectoria libre desde entrenamiento, sin reinicializar al corte, será distinta y deberá etiquetarse por separado.

La membresía de la cohorte se decidió con entregas y calidad de fechas posteriores: incluso el estado inicial reconstruido pertenece a una población seleccionada retrospectivamente. Puede calcularse contando eventos ya ocurridos de esa población, pero no representa el estado que un operador habría podido conocer para todos los pedidos reales en esa fecha. Esta limitación no se elimina con la separación temporal.

## 7. Entrada horaria y alineación

En `eventos_por_hora.csv`, la fila de fecha s_k contiene `compras` n_k ocurridas en (s_{k−1},s_k]; `compras_por_hora` tiene el mismo valor numérico porque Δ=1 hora. Para integrar hacia adelante desde s_{k−1}, definir:

\[
\lambda(t)=n_k/\Delta\quad\text{en }[t_{k-1},t_k),\qquad
\int_{t_{k-1}}^{t_k}\lambda(t)dt=n_k.
\]

La asignación de valores en puntos aislados no cambia la integral. El integrador sí necesita una convención de evaluación en las fronteras (sección siguiente). No usar la fila s_{k−1} como llegada de la hora siguiente: desplazaría la entrada una hora. La fila inicial de referencia no se integra como una hora extra. En validación se usan filas con fecha estrictamente mayor que s0; la compra ocurrida exactamente en s0 ya pertenece al estado inicial.

La entrada distribuye uniformemente dentro de la hora el conteo real. Conserva totales por intervalo y acumulados en cortes, pero aproxima el instante de cada compra dentro de la hora. No conserva la trayectoria escalonada intrahoraria de A. No se añade interpolación suavizante ni extrapolación fuera de la ventana.

Sólo las compras son entrada externa. Las columnas aprobaciones, despachos y entregas son referencias de ajuste o evaluación dentro de sus respectivos períodos; nunca se imponen como entradas a X2, X3 o X4. Usar compras realizadas después del inicio es válido para reproducción retrospectiva condicionada; no es pronóstico de demanda.

## 8. Forma vectorial y preparación de RK4

\[
X=(X_1,X_2,X_3,X_4)^T,\quad\theta=(\alpha,\beta,\gamma)^T,\quad
f(t,X,\theta)=MX+b\lambda(t),
\]

\[
M=\begin{pmatrix}
-\alpha&0&0&0\\
\alpha&-\beta&0&0\\
0&\beta&-\gamma&0\\
0&0&\gamma&0
\end{pmatrix},\qquad b=(1,0,0,0)^T.
\]

Todos los componentes se avanzarán simultáneamente con estados intermedios vectoriales completos:

\[
\begin{aligned}
k_1&=f(t_n,X_n,\theta),\\
k_2&=f(t_n+h/2,X_n+hk_1/2,\theta),\\
k_3&=f(t_n+h/2,X_n+hk_2/2,\theta),\\
k_4&=f(t_n+h,X_n+hk_3,\theta),\\
X_{n+1}&=X_n+\frac h6(k_1+2k_2+2k_3+k_4).
\end{aligned}
\]

Estas son especificaciones, no un algoritmo implementado. No actualizar depósitos secuencialmente usando estados ya modificados.

Paso candidato h=0,25 horas, cuatro pasos por intervalo observado. Ningún paso debe cruzar un salto de entrada. Mantener para las cuatro evaluaciones, incluido k4 que coincide con la frontera final, la λ del intervalo que se está integrando; el siguiente paso usa la nueva λ. Así se evita mezclar dos entradas en un paso y alterar el total integrado.

| Concepto | Definición |
|---|---|
| Muestreo | 1 hora entre cortes históricos |
| Integración | h candidato 0,25 h; puede reducirse |
| Tiempo simulado | Horas del proceso entre inicio y fin de la ventana |
| Tiempo de ejecución | Segundos de reloj del ordenador; depende de implementación/equipo |

La malla subhoraria no crea observaciones adicionales. Verificar convergencia con h=0,25; 0,125; 0,0625, alineados a horas, manteniendo parámetros y entrada. Comparar estados a los mismos cortes y flujos integrados. Propuesta de tolerancia numérica: diferencia máxima entre las dos mallas más finas ≤0,1 pedido y NRMSE de esa diferencia ≤0,001 por etapa, usando escalas del entrenamiento. Si no se cumple, refinar. Estos umbrales son propuestas, no resultados.

Los autovalores son −α,−β,−γ,0. Para coeficientes positivos, revisar estabilidad de RK4: |R(−hk)|≤1 para k∈{α,β,γ}, con R(z)=1+z+z²/2+z³/6+z⁴/24; sobre el eje real negativo el límite aproximado es hk≤2,785. Es condición de estabilidad, no garantía de precisión ni positividad. Parámetros grandes podrían exigir pasos menores o un integrador apropiado para rigidez.

La conservación discreta debe verificarse contra S(0)+compras acumuladas; propuesta de tolerancia de redondeo 10⁻⁸·max(1,S), separada del error predictivo. Comprobar positividad de estados finales y etapas internas con tolerancia documentada; no aceptar violaciones físicas como error de datos. Un caso sin llegadas y con una etapa aislada admite decaimiento exponencial analítico para verificar orden de convergencia sin calibrar datos. También puede usarse la solución lineal por exponencial matricial con entrada constante como referencia futura.

## 9. Limitaciones y pendientes

La selección por entrega completa excluye cancelados, pendientes y cronologías incompatibles; no hay fechas de cancelación para modelar salidas. No se extrapola al inventario operativo completo. Las marcas estimadas de entrega se conservan para otro análisis, pero no entran en estas cuatro EDO.

El modelo no contiene edad de los pedidos, rutas, capacidades ni tiempos individuales. No estima automáticamente retrasos por pedido, costos o energía. Con entrada constante positiva los tres estados pendientes pueden tender a niveles estacionarios si los coeficientes son positivos; X4 continúa creciendo y el sistema completo no tiene equilibrio finito. Con entrada nula, el vaciado de pendientes es asintótico: no debe exigirse entrega exacta de todos en un tiempo finito como sucede en el registro histórico.

Antes de implementar: revisar esta formulación; fijar protocolo de calibración y tolerancias; acordar tratamiento del sesgo retrospectivo; verificar información suficiente por etapa; mantener alineación de λ y cortes; establecer pruebas de convergencia, estabilidad, positividad y conservación. Véanse los otros dos documentos para estimación y escenarios todavía no ejecutados.
