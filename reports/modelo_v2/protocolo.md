# Protocolo fijado antes de los experimentos V2

Desarrollo reutilizado: 2016-09-15 11:00 a 2018-03-02 22:00 (12803 h).
Cuatro orígenes expansivos: 5123, 7043, 8963, 10883 h; evaluación posterior
de 1920 h cada uno. La reserva antigua de 5488 h es retrospectiva reutilizada.
No hay datos independientes nuevos. Toda la cohorte fue examinada anteriormente.

A: tres tasas constantes, reajustadas en cada prefijo; V1 histórico congelado
se reproduce separadamente y nunca se usa como competidor ajustado con futuro.
B: log tasa = intercepto + seno/coseno diario + indicador fin de semana
(12 parámetros, calendario constante en cada intervalo horario).
C: dos fases Erlang por etapa, tres tasas internas; siete EDO, cuatro niveles
visibles. Las fases iniciales reparten por igual cada nivel observado al origen;
es una hipótesis explícita, no se consulta su futuro. No se ajusta ese reparto.
D se permite solamente si B y C reducen cada uno al menos 5% la media del
peor NRMSE de ventana frente a A. De lo contrario se descarta sin ejecutarlo.

Objetivo: media de residuos cuadrados de X1–X3 normalizados por
max(1, media del objetivo del prefijo), igual peso por etapa. En B se añade
0.01 por suma de cuadrados de efectos de calendario; penalización fija.
SciPy least_squares TRF; dos inicios (tasas históricas x 0.5 y x 1.5),
máximo 100 evaluaciones, tolerancias 1e-7. Tasas internas 0.0001 a 1 h^-1;
En B/D el intercepto de tasa tiene cota superior 0.15 h^-1 (tasa efectiva
máxima 0.15 exp(3)); efectos log calendario [-1,1]. Los límites garantizan etapas RK4 positivas
con h=0.25 en los candidatos simples. No recorte ni corrección de masa.

Selección: mínimo promedio entre ventanas del máximo NRMSE X1–X3;
si diferencia relativa <=2%, preferir menor número de parámetros y estados.
Solo optimizaciones convergidas y controles físicos satisfactorios elegibles.
No retocar candidatos, pesos ni ventanas tras resultados. La selección no
equivale a aceptación: NRMSE<=0.30, NMAE<=0.20, error de pico<=max(1,20%
pico observado), error final<=max(1,20% escala), todos por etapa/ventana.
Registrar sesgo persistente aunque se satisfagan umbrales.

RK4 principal h=0.25; tasas B constantes dentro de cada hora, incluyendo K4
izquierdo. Convergencia h=0.125 y 0.0625. Las compras históricas son entradas
condicionadas conocidas, no un pronóstico. Solo se consulta el estado al origen.
Congelar selección, parámetros, escalas y huellas antes de cargar la reserva
antigua para la comparación final. Escalas de reserva: las originales intactas.

No inferir normalidad ni independencia de residuos. Ljung–Box es descriptivo
por dependencia, no prueba de exactitud. Duraciones al corte: censura derecha,
Kaplan–Meier empírico; no aplicar KS con parámetros estimados ni p-valores
de datos completos seleccionados. No se modifica la población retrospectiva.
