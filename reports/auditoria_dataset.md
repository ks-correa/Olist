# Auditoría del dataset Olist — fase 1

## Fuente y reproducibilidad
ZIP original leído directamente, sin modificar. SHA-256: `967e41e04fc306fe604e2a693f488995a8b41e5047418f8a5c8e4abd6deca784`.
CSV del archivo:

- olist_customers_dataset.csv
- olist_geolocation_dataset.csv
- olist_order_items_dataset.csv
- olist_order_payments_dataset.csv
- olist_order_reviews_dataset.csv
- olist_orders_dataset.csv
- olist_products_dataset.csv
- olist_sellers_dataset.csv
- product_category_name_translation.csv

## Población
Originales: **99,441**. Identificadores únicos no nulos: **99,441**.
Incluidos: **95,082**. Excluidos: **4,359**.
Referencia de 99.441 originales y 95.082 incluidos: **coincide**.

Se modela exclusivamente la cohorte retrospectiva de pedidos delivered con cuatro fechas completas, válidas y no decrecientes. La igualdad entre fechas es válida.

### Estados
```
     estado  pedidos
  delivered    96478
    shipped     1107
   canceled      625
unavailable      609
   invoiced      314
 processing      301
    created        5
   approved        2
```
### Calidad y rango temporal (dataset completo)
```
                      columna  faltantes  invalidas_no_vacias              minimo              maximo
     order_purchase_timestamp          0                    0 2016-09-04 21:15:19 2018-10-17 17:30:18
            order_approved_at        160                    0 2016-09-15 12:16:38 2018-09-03 17:40:06
 order_delivered_carrier_date       1783                    0 2016-10-08 10:34:01 2018-09-11 19:48:28
order_delivered_customer_date       2965                    0 2016-10-11 13:46:32 2018-10-17 13:22:46
order_estimated_delivery_date          0                    0 2016-09-30 00:00:00 2018-11-12 00:00:00
```
### Exclusiones
```
                           criterio  detectados_independientes  excluidos_secuenciales
             identificador_faltante                          0                       0
  identificador_duplicado_posterior                          0                       0
          estado_distinto_delivered                       2963                    2963
fecha_principal_faltante_o_invalida                       2980                      23
                cronologia_invalida                       1382                    1373
```
Los conteos independientes pueden solaparse. Los secuenciales son disjuntos y suman el total excluido. Se excluyen identificadores ausentes/duplicados para contar pedidos una sola vez, estados distintos de delivered por definición de cohorte, fechas principales incompletas por falta de eventos verificables y cronología inversa por incompatibilidad con transferencias causales. La fecha estimada no determina la inclusión.

### Inversiones cronológicas (pares adyacentes, dataset completo)
```
order_purchase_timestamp > order_approved_at                       0
order_approved_at > order_delivered_carrier_date                1359
order_delivered_carrier_date > order_delivered_customer_date      23
```
### Duraciones de la cohorte (horas)
```
                       count        mean         std       min         5%        25%         50%         75%         90%         95%         99%          max
compra_aprobacion    95082.0    9.650495   19.116863  0.000000   0.143889   0.214444    0.337778   13.539514   33.343583   45.812014   85.366264   741.443611
aprobacion_despacho  95082.0   68.441959   83.591601  0.004167   7.721139  21.611667   44.371528   86.781111  144.465222  195.140042  411.338894  3018.301667
despacho_entrega     95082.0  224.738670  210.466074  0.000000  27.031792  98.666944  170.647778  289.387708  454.719306  583.836611  984.617664  4924.583333
```
Estas duraciones no se convierten en tasas de servicio. Los percentiles describen tiempos observados entre marcas de eventos.

## Reconstrucción y conservación
18,292 cortes horarios desde 2016-09-15 11:00:00 hasta 2018-10-17 14:00:00.
Los eventos originales se conservan en pedidos_limpios.csv. Cada acumulado cuenta eventos con fecha <= t; cada flujo cuenta eventos en (t−1 hora, t]. Se incluye un corte inicial vacío y el final posterior o igual al último evento. No se interpola ni se cambia la hora de los eventos; no se atribuye una zona horaria no documentada.

X1=A−B, X2=B−C, X3=C−D, X4=D. Por cancelación algebraica, X1+X2+X3+X4=A.
Verificación ejecutada sobre todos los cortes: niveles no negativos, conservación exacta y ΔX=(compras−aprobaciones, aprobaciones−despachos, despachos−entregas, entregas).
Estado final: {'X1': 0, 'X2': 0, 'X3': 0, 'X4': 95082}.
Cada transferencia se resta de un depósito y se añade al siguiente en el mismo intervalo. X4 es terminal acumulado.
Las columnas *_por_hora son conteos divididos por intervalos de exactamente una hora: observaciones históricas, no parámetros calibrados.

## Archivos y gráficas
Los CSV de data/processed incluyen cohorte, flujos y tasas horarias, niveles y acumulados, calidad de fechas, exclusiones, anomalías, estados y estadísticas de duración.
- niveles_observados.png: cuatro paneles con X1–X4; X4 crece con las entregas.
- flujos_historicos.png: compras, aprobaciones, despachos y entregas por hora; se mantienen picos y horas sin actividad.

## Limitaciones y decisiones antes de las EDO
Hay sesgo de selección por exigir entrega y fechas completas: esta cohorte no es el inventario operativo completo ni representa automáticamente los pedidos pendientes de Olist. No existen aquí fechas explícitas de cancelación que permitan reconstruir sus salidas. Los estados finales no sustituyen eventos fechados.
La precisión horaria oculta variaciones dentro del intervalo; las marcas originales permanecen disponibles. Los extremos de la ventana sufren efectos de cohorte y no describen una operación estacionaria.
Antes de las EDO deben definirse población objetivo, condiciones iniciales, tratamiento de cancelaciones y censura, ventana de calibración/validación y método estadístico de estimación de transferencias. No asumir capacidad de servicio como el inverso del tiempo medio de etapa.
No se implementan simulación, EDO, RK4, AgentPy, escenarios ni interfaz.
