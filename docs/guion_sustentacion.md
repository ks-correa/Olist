# Guion de sustentación — OLIST / LAB

Este guion acompaña las [13 diapositivas](guion_presentacion_13_diapositivas.md). No es texto para pegar íntegramente en la presentación. Las cifras se cotejaron con los archivos existentes; no se recalibró ni se produjo una nueva validación.

La guía Word del profesor no está en el proyecto. Las preguntas del final son preparatorias y **no se atribuyen a esa guía**. Cuando se copie el documento original deben incorporarse sus preguntas exactas y verificarse que cada una tenga respuesta. La duración de exposición y los datos de portada quedan por confirmar.

## Diapositiva 1. Portada

«Presentamos OLIST / LAB, una simulación continua de cuatro tanques virtuales aplicada a un proceso logístico de comercio electrónico. Adaptamos el principio de balances: en lugar de agua, los depósitos reúnen pedidos que se encuentran en distintas etapas. Según lo comunicado por el equipo, el profesor aprobó esta adaptación. El propósito es estudiar cómo se distribuyen y acumulan los pedidos y comparar intervenciones hipotéticas sobre las tasas de transferencia. La aprobación debe quedar respaldada con el documento o mensaje real del docente».

Antes de exponer, reemplazar los campos pendientes por los nombres reales y la fecha acordada. No presentar la fecha del cierre documental como fecha de sustentación si no ha sido confirmada.

## Diapositiva 2. Problema y pregunta de decisión

«Un pedido puede haber sido comprado y seguir esperando aprobación, despacho o entrega. Por eso no basta con contar las entregas al final: también interesa cuánto tiempo se mantiene trabajo pendiente. Nuestra pregunta es cuál intervención reduce más esa acumulación dentro del modelo: aumentar un 20 % la tasa de despacho o aumentar un 20 % la tasa de entrega. Conservamos las mismas compras y condiciones iniciales para que la comparación responda al cambio de tasa. El criterio principal es el área de pedidos pendientes a lo largo del tiempo».

Enlazar con el esquema: «Para responderlo necesitamos definir qué acumula cada tanque y cómo se conectan».

## Diapositiva 3. Esquema del sistema

«Las compras ingresan a T1. Cuando se aprueban, pasan a T2; al despacharse, pasan a T3; al entregarse, ingresan a T4. Los tres primeros depósitos representan pendientes. T4 registra todas las entregas acumuladas y no tiene salida en este sistema. La salida logística de la fase pendiente es la entrega desde T3 hacia T4; no estamos eliminando pedidos del balance total. Las conexiones representan cantidades agregadas, no trayectorias individuales. Tampoco conocemos una capacidad física de los tanques: sus alturas son escalas de dibujo».

Señalar en el esquema la única entrada externa y la frontera que contiene los cuatro estados.

## Diapositiva 4. Datos reales

«Usamos el dataset público de Olist, cuya publicación se identifica en Kaggle. No hicimos mediciones con sensores. El archivo original contiene 99.441 pedidos. La depuración conserva 95.082 entregados con compra, aprobación, despacho y entrega completos y en orden temporal. Se excluyeron 4.359 registros mediante criterios documentados. Para reconstruir los niveles contamos eventos acumulados hasta cada hora: compras A, aprobaciones B, despachos C y entregas D. Así obtenemos X1=A−B, X2=B−C, X3=C−D y X4=D. Esta definición permite comprobar el balance con los registros originales».

«La cohorte fue seleccionada sabiendo qué pedidos terminaron entregados. Esa decisión facilita la reconstrucción, pero impide tratarla como todo el inventario que un operador habría conocido en tiempo real».

## Diapositiva 5. Variables, parámetros y unidades

«Los estados X1 a X4 se miden en pedidos. La entrada λ y las transferencias se expresan en pedidos por hora. Los coeficientes α, β y γ tienen unidad de hora inversa: al multiplicarlos por un nivel producen una tasa. Para la ventana principal comenzamos con 113 pendientes de aprobación, 586 de despacho, 3.005 de entrega y 53.963 ya entregados. Ese estado se lee del corte histórico inicial; no se supone que toda ventana empieza vacía. En T4 distinguimos el total acumulado de las entregas adicionales desde ese inicio».

«El cambio de nivel durante una hora es entrada menos salida. No debe confundirse con cuántos pedidos salieron de ese depósito».

## Diapositiva 6. Modelo matemático

«Suponemos transferencias de primer orden: q12=αX1, q23=βX2 y q34=γX3. En T1 entran las compras y salen las aprobaciones. Cada salida se suma como entrada al siguiente depósito con la misma magnitud. Al sumar las cuatro ecuaciones, los flujos internos se cancelan y sólo queda λ. Por tanto, el total es el inicial más las compras acumuladas. Esto conserva pedidos, pero no garantiza acertar cómo se reparten entre las etapas. La proporcionalidad y las tasas constantes son hipótesis de aproximación; no son leyes hidráulicas medidas en Olist».

Si señalan una ecuación, explicar cada término y sus unidades, sin limitarse a leerla.

## Diapositiva 7. Implementación

«Python resuelve conjuntamente el vector de cuatro estados mediante Runge-Kutta de cuarto orden. Cada registro histórico cubre una hora y se divide en cuatro subpasos de 0,25 horas. AgentPy administra exactamente cuatro agentes, uno por depósito. El modelo calcula todo el nuevo vector antes de publicar los niveles, de modo que no transfiere usando estados parcialmente actualizados. Ambos caminos utilizan el mismo integrador. Streamlit lee las trayectorias y las reproduce; la animación no vuelve a resolver las ecuaciones por fotograma».

Mostrar la captura real: «Se verificaron conservación, estados no negativos y equivalencia entre motores. El último registro contiene 188 pruebas aprobadas. Estas pruebas no sustituyen la comparación con datos reales».

La captura sigue pendiente de obtener; este guion no certifica revisión visual del navegador.

## Diapositiva 8. Calibración

«Los tres coeficientes se estimaron con 12.803 intervalos horarios anteriores al período final. Se minimizaron residuos de X1, X2 y X3, normalizados por escalas calculadas en entrenamiento. Esto evita que la etapa con más pedidos domine por su magnitud. Las tasas se restringieron a valores no negativos y se comprobaron varias inicializaciones prefijadas. Los valores finales son aproximadamente α=0,102023784, β=0,013240793 y γ=0,004071912 por hora».

«Durante la optimización se utilizó un propagador auxiliar de las mismas ecuaciones para reducir el tiempo de cálculo. Las trayectorias definitivas y sus métricas se reprodujeron con RK4 a 0,25 horas y con cuatro agentes. La reserva posterior no se usó para ajustar estas tasas».

## Diapositiva 9. Validación

«Congelados el modelo y los parámetros, lo evaluamos en 5.488 intervalos posteriores. La gráfica muestra diferencias entre observado y simulado. Los RMSE son 44,17, 184,66 y 669,10 pedidos para X1, X2 y X3. Sus NRMSE son 0,995, 0,559 y 0,666. Ninguna etapa cumple el criterio interno de 0,30. Por eso se mantiene categoría C, una clasificación académica del proyecto, no una calificación oficial de Olist».

«El error numérico comprobado es muy pequeño frente a esos errores. El resultado señala limitaciones de la aproximación agregada y su capacidad de reproducción; no demuestra un fallo de RK4. La validación es posterior al ajuste, pero sigue condicionada a compras conocidas y a la cohorte retrospectiva. No es un pronóstico de demanda».

## Diapositiva 10. Escenarios

«E0 conserva las tasas calibradas. E1 multiplica sólo β por 1,20: acelera la salida de T2 y puede enviar antes pedidos a T3. E2 multiplica sólo γ por 1,20: acelera la transferencia de T3 a T4. En los tres casos mantenemos las mismas compras, condiciones iniciales, fechas, paso y motor. No recalibramos para favorecer un escenario. X1 coincide exactamente porque no recibe retroalimentación desde etapas posteriores; en E2, X2 también coincide con el base».

«Aumentar una tasa un 20 % no equivale a reducir todos los niveles ni todos los tiempos un 20 %. La trayectoria depende de las entradas, la carga inicial y las conexiones».

## Diapositiva 11. Resultados y comparación

«El área acumulada de pendientes es 13.339.474,31 pedidos·hora en E0, 12.860.070,72 en E1 y 11.660.143,58 en E2. Frente al base, las reducciones son 3,59 % y 12,59 %. Evaluamos también 168, 720 y 1440 horas, además de las 5488 horas completas; son lecturas de una misma trayectoria por escenario, no reinicios. En los horizontes principal definidos, E2 presenta menor área».

«E1 no mejora todas las etapas al mismo tiempo: el mayor aumento de X3 respecto a E0 es 73,46 pedidos. Es traslado temporal de acumulación desde T2, no creación de pedidos. El área permite ver diferencias sostenidas que se perderían mirando sólo el último corte, cuando la cohorte casi se ha agotado».

No interpretar 12,59 % como aumento porcentual de entregas, reducción de retrasos individuales o ahorro económico.

## Diapositiva 12. Decisión, limitaciones y conclusiones

«Entre las tres alternativas y según el criterio definido, E2 es la más favorable dentro del modelo: reduce el área de pendientes un 12,59 %. La recomendación es priorizar esa hipótesis para investigación posterior, no implementar una mejora operacional ya demostrada. La validación no alcanzó el criterio en las tres etapas, las compras son históricas conocidas y la cohorte sólo contiene entregados completos. No modelamos capacidad de recursos, costos, rutas, cancelaciones ni toda la heterogeneidad logística».

«El aporte es una simulación continua reproducible con datos trazables, controles numéricos y una comparación honesta. Para avanzar hacia decisiones reales se necesita revisar la población, mejorar y evaluar las hipótesis y disponer de un conjunto nuevo de prueba».

## Diapositiva 13. Referencias y evidencias

«Las fuentes distinguen los registros Olist de nuestra reconstrucción y de los resultados simulados. Conservamos el ZIP, los CSV de calidad y niveles, los coeficientes, las métricas finales, las trayectorias y las gráficas. La documentación técnica y el código muestran cómo se implementaron el ajuste, RK4, AgentPy y la interfaz. El registro de ejecución acredita 188 pruebas aprobadas. Las capturas actuales, la evidencia de descarga y el respaldo docente deben archivarse antes de cerrar el PowerPoint. No sustituimos esas evidencias por ilustraciones ni declaramos ensayos físicos propios».

Al responder preguntas, abrir el archivo correspondiente y conservar la misma definición de ventana, población y unidades usada en la presentación.

## Preguntas preparatorias para ambos integrantes

Estas preguntas anticipan una sustentación de modelado. No son transcripción de la guía ausente. Deben cotejarse y completarse cuando se copie el Word original.

### 1. ¿Por qué es válido hablar de tanques en logística?

Porque se adapta el principio de balance: una cantidad acumulada cambia por entradas y salidas. No se afirma equivalencia física con agua. Las transferencias lineales son hipótesis del modelo logístico. La aceptación académica de esa adaptación fue informada por el equipo y debe respaldarse con la aprobación real del profesor.

### 2. ¿Los tanques tienen capacidades máximas conocidas?

No. Las alturas se normalizan con escalas relativas de visualización y no permiten inferir capacidad de almacenamiento o servicio. Los coeficientes ajustados son tasas efectivas, no mediciones directas de recursos.

### 3. ¿Cómo calcularon los niveles sin observar una cola cada hora?

Contando las marcas temporales originales. A, B, C y D incluyen eventos con fecha menor o igual al corte. Las diferencias A−B, B−C y C−D reconstruyen las etapas pendientes; D acumula entregas. Se verificó no negatividad y conservación en todos los cortes.

### 4. ¿Dónde está la salida final del sistema?

La entrega sale de T3 y entra en T4. Como T4 conserva el registro de entregados, no hay una salida adicional después de él. Por eso el total de los cuatro estados sólo aumenta con compras. Dibujar una salida de T4 exigiría otro balance, que no forma parte del modelo.

### 5. ¿Qué hace exactamente RK4?

Para el vector completo calcula cuatro pendientes k1, k2, k3 y k4 en cada subpaso y combina (X_{n+1}=X_n+h(k_1+2k_2+2k_3+k_4)/6). Hay cuatro subpasos por hora, cada uno con sus cuatro evaluaciones. Se mantiene la compra de esa misma hora en todas las etapas del subpaso, incluida su frontera final. No se integran los tanques de manera secuencial con niveles ya modificados.

### 6. ¿Por qué h=0,25 horas y no el intervalo de reproducción?

Es el paso numérico comprobado mediante estabilidad, positividad y convergencia. La reproducción usa segundos reales y consulta resultados guardados. Cambiar de 24 a 168 horas simuladas por segundo no cambia h, las ecuaciones ni las trayectorias.

### 7. ¿Qué aporta AgentPy si el motor ya resuelve las EDO?

Mantiene cuatro agentes identificados con su nivel y organiza la evolución y el registro del sistema. La integración conjunta se delega al motor común. Es una implementación agregada determinista; no se afirma que modele decisiones autónomas o interacciones individuales de miles de pedidos.

### 8. ¿El ajuste fue una simple división de transferencias entre tiempo medio?

No. Las razones de eventos sobre exposición censurada se usaron como estimaciones preliminares e inicializaciones. Los coeficientes finales proceden de mínimos cuadrados normalizados de trayectorias, bajo no negatividad. Son estimaciones de un modelo de primer orden, no capacidades observadas.

### 9. ¿Cuál fue la función de pérdida?

Con (r_{ki}=(X^{sim}_{ki}-X^{obs}_{ki})/s_i), se minimizó (0,5\sum_{k,i}r_{ki}^2), para i=1,2,3 y los N=12.803 cortes objetivo de entrenamiento, excluyendo el inicial. (s_i=\max(1,\text{media observada de entrenamiento de }X_i)). X4 no participa en la pérdida; no se le permite dominar por su gran acumulado previo. Se utilizó `scipy.optimize.least_squares`, método TRF y pérdida lineal. La convergencia del optimizador no prueba óptimo global.

### 10. ¿Se usó otro método en lugar de RK4?

Durante el ajuste se aceleraron evaluaciones con la solución matricial de las mismas EDO con entrada constante por hora. Ese propagador auxiliar se contrastó con RK4. Las trayectorias finales, transferencias y métricas presentadas se calcularon con RK4 h=0,25 y se verificó equivalencia con AgentPy. No se sustituyeron datos por curvas suavizadas.

### 11. ¿La validación es realmente independiente?

Está separada cronológicamente del ajuste: 12.803 intervalos antes del corte y 5.488 después, con parámetros y estructura congelados. El estado del corte se comparte como condición inicial, no como intervalo usado dos veces. Sin embargo, la cohorte se seleccionó retrospectivamente por entrega completa y la demanda es conocida. Se trata de reproducción fuera del ajuste, no evaluación prospectiva libre de toda selección. La reserva ya evaluada no puede reutilizarse como una nueva prueba independiente.

### 12. ¿Qué significan MAE, RMSE y NRMSE?

MAE es el promedio del error absoluto; RMSE es la raíz del promedio de errores al cuadrado y penaliza más los grandes errores. Ambos están en pedidos. NRMSE divide RMSE por una escala fijada con entrenamiento y es adimensional. Un NRMSE de 0,995 no significa que el 99,5 % de los pedidos esté mal clasificado ni que el modelo tenga una exactitud porcentual determinada.

### 13. ¿Por qué categoría C si las pruebas pasan?

Porque son evaluaciones distintas. Las pruebas y la convergencia apoyan que el software integra el modelo especificado y conserva pedidos. La validación pregunta si ese modelo reproduce la realidad observada. X1–X3 exceden NRMSE 0,30. C es la clasificación académica interna de precisión insuficiente; no indica automáticamente un error de programación ni un estándar de Olist.

### 14. ¿Cómo descartan que el error se deba a un paso grande?

El resumen final conserva comparaciones entre h=0,25, 0,125 y 0,0625. La diferencia máxima entre los estados de las dos primeras mallas es aproximadamente 2,38×10⁻⁷ pedidos, muy inferior a RMSE de decenas o cientos de pedidos frente a observaciones. También hay equivalencia exacta entre las dos ejecuciones que comparten RK4. Esa evidencia distingue error numérico de error de modelo, sin afirmar que explica todas las causas estadísticas.

### 15. ¿Por qué E2 resulta más favorable?

Dentro de estas trayectorias, acelerar la salida de T3 reduce más la acumulación sostenida. La conclusión se apoya en el área de pendientes calculada, no sólo en observar que γ es la tasa menor. Las entradas, condiciones iniciales y conexiones condicionan el resultado; no se demuestra que entrega sea siempre la mejor intervención para cualquier operación.

### 16. ¿E1 empeora el sistema?

Reduce el área total un 3,59 %, pero puede incrementar temporalmente el nivel de T3 porque adelanta pedidos desde T2. El máximo aumento diferencial de X3 es 73,46 pedidos en la ventana principal. Hay que distinguir el efecto total de la carga local de una etapa y el horizonte en que se mide.

### 17. ¿Qué mide un área en pedidos·hora?

La acumulación de pendientes a lo largo del tiempo: se integra P=X1+X2+X3 mediante trapecios entre cortes horarios. Se calcula  \(\sum_k (P_k+P_{k+1})\Delta t/2\), con Δt=1 h. No es una cantidad de pedidos únicos ni una duración individual; tampoco es costo monetario. Es una cuadratura sobre salidas horarias, no la integral de las etapas internas de RK4.

### 18. ¿El 12,59 % son más entregas o menos retrasos reales?

No. Es (100(A_0-A_2)/A_0), donde A representa área de pendientes de la misma ventana principal. Los valores originales son 13.339.474,306616245 y 11.660.143,579588065 pedidos·hora. No se modelaron promesas individuales contrafactuales, costos ni intervenciones reales, por lo que no se atribuye ese porcentaje a esos resultados.

### 19. ¿Para qué comparar horizontes si existe un resultado final?

Porque la cohorte es finita y las compras cesan; las configuraciones pueden terminar casi vacías sin haber acumulado el mismo trabajo durante el período. Los cortes 168, 720, 1440 y 5488 horas evitan elegir sólo un extremo favorable. Enero añade sensibilidad con 168, 720 y 744 horas, pero no es nueva validación independiente ni un cuarto escenario.

### 20. ¿Se probó una estructura alternativa?

Sí, existe una comparación de desarrollo con un candidato de aprobación rápida. Según la regla predefinida se conservó el modelo base; el candidato no se evaluó en la validación final. Su documentación está en `reports/comparacion_modelos.md`. No debe confundirse esa investigación previa con los tres escenarios, que sólo cambian β o γ del modelo base congelado.

### 21. ¿Cómo saben que la animación corresponde al cálculo?

Se publica una fotografía con un único índice y una revisión creciente; fecha, estados, transferencias, indicadores y marcador se actualizan juntos. Los callbacks atrasados se descartan. Hay pruebas de backend, API y ejecución JavaScript con DOM simulado. No hubo navegador conectado para verificar visualmente esta versión, por lo que esa revisión y sus capturas siguen pendientes. Las partículas son efectos agregados y no equivalen a pedidos individuales.

### 22. ¿Qué falta para recomendar una acción real?

Una población apropiada que incluya las situaciones operativas relevantes, datos de recursos y restricciones, hipótesis que reproduzcan mejor las etapas y un período nuevo de evaluación. Si se buscan decisiones económicas se necesitan costos; si se buscan retrasos se necesita un modelo adecuado de pedidos y compromisos de entrega. Este trabajo no estima esos beneficios.

## Preparación conjunta

Ambos integrantes deben poder explicar las cuatro EDO, reconstruir los niveles desde A–D y leer la tabla de validación sin recurrir al compañero. Alternar las diapositivas en cada ensayo y pedir al otro que responda preguntas fuera de su sección habitual. La división de voz puede acordarse por fluidez, pero no debe convertirse en división del conocimiento.

Antes de exponer, abrir el proyecto y localizar juntos `parametros_calibrados.json`, `metricas_validacion.csv`, `indicadores_horizontes.csv`, `resumen_validacion.json` y `pruebas_refinamiento.txt`. Ensayar una demostración corta con E0 pausado, cambio a E1/E2 en el mismo corte y consulta de Datos y validación. Preparar capturas y una grabación reales como respaldo sin presentarlas como ejecución en vivo.

No cambiar parámetros, volver a calibrar ni reinterpretar la categoría C para mejorar el relato. Si una pregunta exige información no modelada, explicar el límite en lugar de inventar una cifra. Revisar las preguntas originales del profesor en cuanto se copie la guía.
