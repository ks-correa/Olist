# Escenarios propuestos para una fase posterior

## Pregunta de decisión

Con las mismas compras y condiciones iniciales, ¿una intervención hipotética del 20 % en el coeficiente de despacho o en el de entrega reduce más la acumulación de pedidos pendientes, y en qué etapas aparecen desplazamientos de carga?

Este documento sólo especifica comparaciones. No se ejecutaron escenarios, no se estimaron parámetros y no existen mejoras medidas. La formulación se encuentra en [modelo_matematico.md](modelo_matematico.md) y el protocolo de estimación en [plan_calibracion_validacion.md](plan_calibracion_validacion.md).

## Configuraciones

Sean α̂, β̂ y γ̂ coeficientes obtenidos posteriormente sólo con entrenamiento:

| Configuración | Aprobación | Despacho | Entrega |
|---|---|---|---|
| Base | α̂ | β̂ | γ̂ |
| Escenario 1: despacho | α̂ | 1,20 β̂ | γ̂ |
| Escenario 2: entrega | α̂ | β̂ | 1,20 γ̂ |

Los tres usarán las mismas llegadas λ(t), población, inicio y fin, X(0), malla numérica y criterio de convergencia. No se recalibrarán los restantes parámetros para favorecer una intervención. Si un escenario requiere un paso menor por estabilidad o precisión, se adoptará ese mismo paso validado en los tres para la comparación final. No cambiar simultáneamente demanda o estado inicial.

Los porcentajes son intervenciones hipotéticas sobre coeficientes de primer orden, no mejoras históricas documentadas ni aumentos comprobados de capacidad. En la interpretación exponencial ideal, multiplicar un coeficiente por 1,20 divide su tiempo medio por 1,20: reducción de 1−1/1,20≈16,67 %, no 20 %. Esto es una consecuencia de la hipótesis, no una reducción real estimada para Olist.

## Comparación futura

Usar pendientes P=X1+X2+X3, áreas bajo cada nivel y bajo P (pedidos·hora), picos por etapa y su fecha, y pendientes al final. Reportar diferencias absolutas respecto del base; porcentajes sólo con denominador distinto de cero y claramente definido. Comparar entregas incrementales X4(t)−X4(0), no dejar que las entregas previas dominen la interpretación.

La igualdad S(t)=S(0)+∫λ obliga a que el total sea igual en los tres. Aumentar entregas al corte equivale a reducir pendientes totales en ese corte. No implica que cada cola se reduzca: acelerar despacho puede trasladar carga de X2 a X3. En este modelo sin retroalimentación, intervenir β no cambia X1, e intervenir γ no cambia X1 ni X2. Estas dependencias son consecuencias estructurales que deberán comprobarse al implementar, no resultados numéricos ya observados.

El efecto de las intervenciones dependerá del horizonte, condiciones iniciales y parámetros. Sin llegadas posteriores, todas las configuraciones con coeficientes positivos terminan asintóticamente con la misma población entregada; el interés está en la trayectoria y las entregas dentro de una ventana finita. No se declarará una intervención universalmente superior por una sola métrica o una sola ventana. Examinar también sensibilidad e incertidumbre de parámetros cuando estén disponibles.

## Alcance de las conclusiones

No atribuir ahorro de energía, costos, capacidad física real ni porcentajes de entregas tardías: las cuatro EDO carecen de esas variables y relaciones. La comparación será un experimento sobre una cohorte retrospectiva entregada, no una recomendación causal demostrada para toda la operación de Olist.

`order_estimated_delivery_date` y `order_delivered_customer_date`, conservadas en `pedidos_limpios.csv`, permiten describir retrasos históricos reales con una convención explícita de fecha límite. Debe revisarse que la fecha estimada aparece a medianoche y definir si la promesa corresponde al día completo antes de clasificar retrasos. Este análisis sería complementario. Los cuatro estados agregados no vinculan una entrega simulada a un pedido ni a su promesa, por lo que no permiten calcular directamente retrasos individuales contrafactuales bajo los escenarios. Haría falta seguimiento individual o una estructura adicional validada.

## Condición para avanzar

Revisar la formulación y el plan antes de implementar RK4; calibrar y validar después el modelo base, documentando cualquier insuficiencia. Sólo entonces ejecutar y comparar las tres configuraciones. Esta fase termina con documentación; no incluye código de escenarios, animaciones, AgentPy ni interfaz.
