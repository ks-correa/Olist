# OLIST / LAB — Guion de presentación en 13 diapositivas

Documento para revisión previa al PowerPoint. La guía Word original no está en el proyecto; se sigue exactamente el orden de 13 diapositivas indicado en el Prompt 11. Integrantes y fecha quedan por confirmar. No se han creado capturas, figuras nuevas ni un archivo PowerPoint.

Cada sección separa el texto que se verá en pantalla de las instrucciones de preparación. Estas instrucciones y las fuentes extensas no deben copiarse como párrafos a las diapositivas. El desarrollo oral está en [guion_sustentacion.md](guion_sustentacion.md).

## Diapositiva 1. Portada

**Idea principal:** presentar el proyecto y su alcance académico.

**Título en pantalla:** OLIST / LAB: simulación continua de cuatro tanques logísticos.

**Texto en pantalla:**

- Integrantes: [nombre del integrante 1] · [nombre del integrante 2].
- Asignatura: Modelado y Simulación.
- Fecha de sustentación: [por confirmar].

**Visual:** portada tipográfica limpia; subtítulo «Adaptación del principio de balances al flujo de pedidos». No usar fotografías de instalaciones o sensores que sugieran mediciones propias.

**Fuente:** alcance del proyecto y aprobación informada por el estudiante; respaldo documental del docente pendiente de archivo.

**Mensaje oral:** estudiamos la acumulación de pedidos mediante una analogía matemática autorizada por el profesor, según lo informado por el equipo.

## Diapositiva 2. Problema y pregunta de decisión

**Idea principal:** decidir qué etapa conviene acelerar dentro del modelo.

**Título en pantalla:** ¿Conviene acelerar el despacho o la entrega?

**Texto en pantalla:**

- Los pedidos se acumulan mientras esperan aprobación, despacho o entrega.
- Comparamos dos aumentos hipotéticos de tasa: despacho +20 % y entrega +20 %.
- Criterio: menor acumulación sostenida de pendientes, medida en pedidos·hora.

**Visual:** pregunta destacada y definición breve (P=X_1+X_2+X_3). No adelantar todavía el escenario ganador ni confundir la pregunta con una recomendación empresarial.

**Fuente:** [modelo matemático](modelo_matematico.md); [definición de escenarios](../reports/escenarios_resultados.md).

**Mensaje oral:** la pregunta compara mecanismos agregados manteniendo las mismas compras, no presupuestos, personal ni costos no modelados.

## Diapositiva 3. Esquema del sistema

**Idea principal:** cada transferencia sale de una etapa y entra en la siguiente.

**Título en pantalla:** Cuatro depósitos conectados por transferencias de pedidos.

**Texto en pantalla:**

«Compras λ → T1: aprobación → q12 → T2: despacho → q23 → T3: entrega → q34 → T4: entregados».

Pie breve: «T1–T3 son pendientes; T4 es acumulado terminal. Sin capacidades físicas medidas».

**Visual:** esquema conceptual editable de los cuatro tanques y las conexiones, basado en la estructura real de `ui/tanks.py`. Señalar el límite del sistema alrededor de T1–T4 y la entrada externa λ. La entrega es salida de la etapa pendiente T3 hacia el estado terminal T4; **no dibujar un flujo que retire pedidos de T4**. El esquema es conceptual, no una captura de ejecución. La captura real se reserva para la diapositiva 7.

**Fuente:** [formulación y límites](modelo_matematico.md), secciones 2–5; `src/rk4_solver.py`.

**Mensaje oral:** se conserva el principio de entrada, acumulación y transferencia; el contenido son pedidos agregados y no agua.

## Diapositiva 4. Datos reales

**Idea principal:** los niveles se reconstruyen a partir de registros operacionales reales.

**Título en pantalla:** De 99.441 pedidos a una cohorte trazable de 95.082.

**Texto en pantalla:**

- Fuente: Brazilian E-Commerce Public Dataset by Olist, publicado en Kaggle.
- Cohorte: entregados con cuatro fechas completas y ordenadas; 4.359 exclusiones.
- Eventos: compra, aprobación, despacho y entrega; reconstrucción por hora.
- Son registros históricos de terceros, no mediciones propias con sensores.

**Visual:** secuencia de depuración «99.441 → criterios de calidad → 95.082» acompañada de los nombres de los cuatro campos temporales. Añadir una pequeña evidencia real de la ficha Olist/Kaggle cuando se archive; no inventarla. Evitar proyectar identificadores de pedidos innecesarios.

**Fuente:** [auditoría](../reports/auditoria_dataset.md); ZIP original; `data/processed/exclusiones.csv`, `pedidos_limpios.csv`; [publicación original](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

**Mensaje oral:** exigir entrega completa permite reconstruir las etapas, pero introduce selección retrospectiva y limita la población representada.

## Diapositiva 5. Variables, parámetros y unidades

**Idea principal:** los estados y los flujos tienen significados y unidades distintos.

**Título en pantalla:** Niveles en pedidos; transferencias en pedidos por hora.

**Contenido en pantalla:**

| Símbolo | Significado | Unidad |
|---|---|---|
| X1, X2, X3 | Pendientes de aprobación, despacho y entrega | pedidos |
| X4 | Entregados acumulados | pedidos |
| λ | Compras nuevas | pedidos/hora |
| α, β, γ | Tasas efectivas de aprobación, despacho y entrega | h⁻¹ |

Pie: «Inicio principal: X(0)=(113; 586; 3005; 53963). Tiempo del modelo: horas».

**Visual:** esta tabla y la condición inicial, sin otra gráfica. Las cifras completas de coeficientes se presentan en calibración, no se repiten aquí.

**Fuente:** [modelo](modelo_matematico.md); [resumen de validación](../reports/resumen_validacion.json).

**Mensaje oral:** una variación neta de nivel no es igual al flujo de salida; resulta de entradas menos salidas durante el intervalo.

## Diapositiva 6. Modelo matemático

**Idea principal:** las cuatro EDO implementan un balance conservativo.

**Título en pantalla:** Un mismo flujo conecta dos balances.

**Ecuaciones en pantalla:**

\[
\dot X_1=\lambda-\alpha X_1,\qquad
\dot X_2=\alpha X_1-\beta X_2,
\]
\[
\dot X_3=\beta X_2-\gamma X_3,\qquad
\dot X_4=\gamma X_3.
\]
\[
q_{12}=\alpha X_1,\quad q_{23}=\beta X_2,\quad q_{34}=\gamma X_3,
\qquad \frac{d}{dt}\sum_{i=1}^{4}X_i=\lambda.
\]

**Visual:** ecuaciones en dos filas con color coherente para el mismo término que sale y entra; una frase inferior: «Tasas constantes y transferencias proporcionales al nivel: hipótesis de primer orden».

**Fuente:** [modelo matemático](modelo_matematico.md); `src/rk4_solver.py`, `rhs`.

**Mensaje oral:** los flujos internos se cancelan al sumar balances; acertar esa suma no demuestra que la distribución por etapas reproduzca bien los datos.

## Diapositiva 7. Implementación

**Idea principal:** una implementación verificable resuelve y presenta el mismo modelo.

**Título en pantalla:** RK4 integra; cuatro agentes mantienen los depósitos.

**Texto en pantalla:**

- Python + RK4 vectorial: cuatro subpasos de 0,25 h por registro horario.
- AgentPy: exactamente cuatro agentes, uno por depósito; motor de integración compartido.
- Streamlit: estados precalculados y reproducción sincronizada.
- 188 pruebas registradas; conservación máxima en validación ≈9,46×10⁻¹⁰ pedidos.

**Visual obligatorio:** captura **real y actual** de Simulación, ventana principal, E0, hora 168, pausada. Debe mostrar fecha, controles, cuatro tanques, unidades y flujos. Nombre propuesto, aún pendiente: `reports/evidencias_streamlit/simulacion_intermedia_E0_h168.png`. No sustituir por un mockup. El registro de pruebas puede citarse en el pie, sin llenar la diapositiva con una terminal.

**Fuente:** [implementación](implementacion_rk4_agentpy.md); `src/agent_model.py`; [resumen numérico](../reports/resumen_validacion.json); [188 pruebas](../reports/pruebas_refinamiento.txt); [sincronización](refinamiento_interfaz.md).

**Mensaje oral:** las pruebas acreditan controles del algoritmo y del software; la precisión frente a datos se evalúa por separado en la diapositiva 9.

## Diapositiva 8. Calibración

**Idea principal:** las tasas se estimaron usando exclusivamente el período de desarrollo.

**Título en pantalla:** Tres coeficientes ajustados con 12.803 intervalos horarios.

**Texto en pantalla:**

- Entrenamiento: 2016-09-15 11:00 → 2018-03-02 22:00.
- Mínimos cuadrados de residuos normalizados de X1–X3, con tasas no negativas.
- Parámetros congelados antes de evaluar el período posterior.

| Parámetro | Valor para exposición (h⁻¹) |
|---|---:|
| α | 0,102023784 |
| β | 0,013240793 |
| γ | 0,004071912 |

Pie: «Redondeo sólo visual. Precisión completa en parametros_calibrados.json».

**Visual:** tabla y una línea temporal simple que separe desarrollo y validación. No usar una curva de entrenamiento como prueba de desempeño fuera de muestra.

**Fuente:** [calibración](../reports/calibracion_modelo.md); `src/calibration.py`; [parámetros originales](../reports/parametros_calibrados.json).

**Mensaje oral:** se usó un propagador auxiliar de las mismas EDO para acelerar la optimización; las trayectorias y métricas definitivas se reprodujeron con RK4 h=0,25 y se contrastaron con AgentPy.

## Diapositiva 9. Validación

**Idea principal:** la reproducción fuera de entrenamiento mostró errores importantes.

**Título en pantalla:** La validación delimita la precisión del modelo.

**Contenido en pantalla:**

| Etapa | MAE (pedidos) | RMSE (pedidos) | NRMSE |
|---|---:|---:|---:|
| X1 | 24,50 | 44,17 | 0,995 |
| X2 | 138,87 | 184,66 | 0,559 |
| X3 | 546,73 | 669,10 | 0,666 |

Texto breve: «5.488 intervalos posteriores. Ninguna etapa cumple NRMSE ≤ 0,30. Categoría C: clasificación académica interna».

**Visual:** [X3 observado frente a simulado](../reports/graficas_validacion/X3.png) y la tabla de tres etapas. La figura fue inspeccionada: incluye título, fechas, eje de pedidos y leyenda; no ocultar la separación entre curvas. X3 es ilustrativa, no el único resultado evaluado. X1 y X2 quedan disponibles para preguntas en sus archivos, sin añadir diapositivas fuera de las 13.

**Fuente:** [métricas](../reports/metricas_validacion.csv); [validación final](../reports/validacion_final.md); [criterio interno](plan_calibracion_validacion.md).

**Mensaje oral:** categoría C señala precisión insuficiente para recomendaciones operativas confiables; no es una calificación oficial de Olist ni prueba de fallo de RK4.

## Diapositiva 10. Escenarios

**Idea principal:** sólo una tasa cambia en cada intervención hipotética.

**Título en pantalla:** Tres configuraciones con las mismas compras y condiciones iniciales.

**Contenido en pantalla:**

| Escenario | α | β | γ |
|---|---|---|---|
| E0 · Base | α₀ | β₀ | γ₀ |
| E1 · Despacho +20 % | α₀ | 1,20 β₀ | γ₀ |
| E2 · Entrega +20 % | α₀ | β₀ | 1,20 γ₀ |

Pie: «E1 reduce acumulación en T2 y puede trasladarla a T3; E2 actúa sobre la salida de T3. Sin recalibración».

**Visual:** tabla junto a [X3 por escenario](../reports/graficas_escenarios/principal_X3.png), ya existente. La figura fue inspeccionada y muestra las tres curvas con leyenda y unidades; la diferencia E1/E0 es pequeña en la escala completa. Para señalarla, usar una anotación con valor sustentado (+73,46 pedidos como máximo diferencial), sin deformar ejes ni crear una mejora ficticia.

**Fuente:** `src/scenarios.py`; [metadatos](../reports/comparacion_escenarios.json); [resultados](../reports/escenarios_resultados.md).

**Mensaje oral:** aumentar una tasa un 20 % no obliga a reducir niveles un 20 %. X1 es idéntico en las tres configuraciones; E2 también conserva X2.

## Diapositiva 11. Resultados y comparación

**Idea principal:** E2 reduce más la acumulación sostenida de pendientes en la ventana principal.

**Título en pantalla:** E2 reduce el área de pendientes un 12,59 % frente a E0.

**Contenido en pantalla:**

| Escenario | Área (pedidos·hora) | Reducción frente a E0 |
|---|---:|---:|
| E0 | 13.339.474,31 | — |
| E1 | 12.860.070,72 | 3,59 % |
| E2 | 11.660.143,58 | 12,59 % |

Pie: «Horizontes: 168, 720, 1440 y 5488 h. Una trayectoria por escenario; resultados internos del modelo».

**Visual:** [área acumulada de P](../reports/graficas_escenarios/principal_area_acumulada_P.png) y la tabla final. En la figura original el eje usa `1e7`: explicar esa escala o, al maquetar, usar un gráfico editable desde el CSV con eje «millones de pedidos·hora». No modificar los archivos originales. En la explicación oral retomar el traslado T2→T3 de E1 sin repetir la figura de la diapositiva 10.

**Fuente:** [indicadores por horizonte](../reports/indicadores_horizontes.csv), [diferencias](../reports/diferencias_escenarios.csv), [resultados](../reports/escenarios_resultados.md).

**Mensaje oral:** el área mide cuántos pedidos permanecen pendientes y durante cuánto tiempo; distingue escenarios aunque la cohorte termine casi vacía. No es costo ni porcentaje de entregas reales ganadas.

## Diapositiva 12. Decisión, limitaciones y conclusiones

**Idea principal:** la decisión es cuantitativa dentro del modelo y exploratoria fuera de él.

**Título en pantalla:** Priorizar E2 como hipótesis de estudio, con alcance limitado.

**Texto en pantalla:**

- E2 es la alternativa más favorable entre las tres: área de pendientes −12,59 %.
- La validación no alcanzó el criterio en X1–X3; no sustenta mejoras operativas reales.
- Cohorte retrospectiva, compras conocidas y tasas constantes limitan la generalización.
- Siguiente paso científico: nueva población de prueba y evaluación de heterogeneidad antes de aplicar decisiones.

**Visual:** una conclusión destacada y sus límites; no repetir la gráfica de área ni agregar ahorros monetarios, energía, personal o reducción de retrasos no modelados.

**Fuente:** [validación final](../reports/validacion_final.md); [escenarios](../reports/escenarios_resultados.md); [matriz de cumplimiento](../reports/matriz_cumplimiento_guia.md).

**Mensaje oral:** el proyecto demuestra una simulación reproducible y una comparación trazable, no una recomendación validada para intervenir operaciones de Olist.

## Diapositiva 13. Referencias y evidencias

**Idea principal:** cada afirmación puede rastrearse a datos, método o registro de ejecución.

**Título en pantalla:** Fuentes y evidencias verificables.

**Texto visible recomendado:**

- Olist/Kaggle: dataset original y registros operacionales históricos.
- SciPy: mínimos cuadrados; AgentPy: modelo y agentes; Streamlit: interfaz.
- Proyecto: auditoría, parámetros, validación y comparación de escenarios.
- Evidencias: ZIP con hash, CSV, gráficas y registro de 188 pruebas; capturas reales por archivar.

**Visual:** bibliografía breve con hipervínculos y rutas legibles. La autorización docente debe incorporarse como evidencia sólo cuando se archive el respaldo real. No describir los eventos Olist como experimentos físicos hechos por los integrantes.

**Fuentes enlazadas:**

1. [Olist. Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). Publicación identificada; completar evidencia de descarga y condiciones de uso.
2. [SciPy. scipy.optimize.least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html). Referencia del método; configuración efectiva en el código y JSON locales.
3. [AgentPy. Agent-based models](https://agentpy.readthedocs.io/en/latest/reference_model.html). La página latest identifica 0.1.6.dev0; el proyecto utiliza 0.1.5 y su implementación instalada fue contrastada.
4. [Streamlit. st.components.v2.component](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component). Referencia consultada para la interfaz; proyecto en 1.67.0.
5. [Formulación e implementación RK4 propias](implementacion_rk4_agentpy.md), con `src/rk4_solver.py` como evidencia ejecutable del algoritmo.
6. [Auditoría](../reports/auditoria_dataset.md), [parámetros](../reports/parametros_calibrados.json), [validación](../reports/validacion_final.md), [escenarios](../reports/escenarios_resultados.md) y [registro de pruebas](../reports/pruebas_refinamiento.txt).

**Mensaje oral:** entregamos una cadena verificable desde registros históricos hasta conclusiones; las evidencias pendientes se identifican expresamente.

## Revisión editorial antes de maquetar

Mantener exactamente 13 diapositivas; las preguntas y archivos de apoyo se consultan sin añadir láminas obligatorias nuevas. Preferir una composición amplia y texto breve. No reducir la letra para acomodar párrafos del guion oral. Mantener títulos, unidades y leyendas al insertar gráficos, colores consistentes por escenario y precisión interna original.

Faltan la guía Word, los nombres y la fecha de portada, el respaldo documental del docente y capturas actuales. La duración de exposición no se presume: ajustar el ensayo cuando se consulte la guía. Esta entrega prepara el contenido; el PowerPoint definitivo queda pendiente de revisión.
