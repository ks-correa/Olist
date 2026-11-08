# Segunda ronda adaptativa: desarrollo reutilizado

Se abre después de observar los resultados de A/B/C y la reserva antigua.
Por tanto, esta ronda NO constituye confirmación independiente ni experimento
prerregistrado externo. Motivo: 64.85% de aprobaciones completadas <=1 h,
mediana 0.297 h, P95 47.96 h; la hipótesis Erlang reduce dispersión, mientras
la cohorte presenta una vía rápida y cola larga. Se ensaya M: mezcla de dos
exponenciales por etapa, sin atajo instantáneo. Siete EDO, nueve parámetros:
dos tasas y una probabilidad de entrada por etapa. Ambas vías reciben pedidos
y descargan hacia las dos vías de la etapa siguiente con las mismas fracciones.

Inicialización al origen: ocupación proporcional a p/k de cada vía,
normalizada para sumar exactamente el nivel agregado observado al origen.
No se usa la edad ni el estado observado posterior. Esta aproximación de edad
de equilibrio se declara como limitación. Se comparan las mismas cuatro
ventanas, escalas y criterios de la primera ronda, sin cambiar umbrales.

Objetivo idéntico, sin regularización temporal (modelo estacionario).
Tasas [0.0001,1] h^-1; probabilidades [0.01,0.99]. Dos inicios prefijados:
tasas rápidas 2 y 5 veces V1, lentas 0.5 y 0.2 veces V1, p=0.5 y 0.8.
SciPy least_squares TRF, max_nfev=200, tolerancias 1e-7.
Dos vías se etiquetan por tasa descendente al terminar (simetría de mezcla).
RK4 h=0.25 principal, comparación expm y refinamiento. Se mantienen todos
los fallos y soluciones, incluida proximidad a cotas e identificabilidad.

Selección conjunta de M y A/B/C por el mismo promedio del peor NRMSE de
ventana; empate relativo <=2% favorece menos parámetros y estados.
Solo se usa desarrollo para elegir, y se congela antes de volver a calcular
la reserva reutilizada. No se exige ni permite promesa de éxito.
