# Calibración, selección e identificabilidad

Desarrollo: 15/09/2016 11:00–02/03/2018 22:00, 12.803 intervalos.
Cada prefijo empieza en el mismo origen y termina en 5123/7043/8963/10883 h;
se evalúan 1920 h posteriores desde una única condición inicial observada.
Ningún estado intermedio observado corrige la trayectoria.

L=mean_{horas,etapas}[((simulado−observado)/s_i)²]+0,01 Σ b_calendario²
solo para B/D. s_i=max(1,media del objetivo del entrenamiento correspondiente),
excluyendo el estado inicial. X1, X2, X3 tienen igual peso. X4 no domina la
pérdida por acumulación. Las escalas completas originales son
44,39279856283684; 330,3622588455831; 1004,1355932203389 pedidos.
No se modifican para evaluar la reserva histórica.

TRF de SciPy least_squares con cotas y dos inicios, diferencias finitas,
ftol=xtol=gtol=1e−7. Se elige el menor costo entre inicios convergidos.
Las especificaciones exactas, cotas y penalización están en protocolo.md y
protocolo_mezcla.md. Los vectores de residuos dividen por raíz del número
de objetivos; por ello costo de SciPy = L/2. No se recalibró con la reserva.
Se registran todos los inicios, mensajes, evaluaciones y jacobianos, no solo
el mejor. No se garantiza óptimo global ni identificación física.

| ajuste | costo | condicion | nfev | convergieron | inicios |
|---|---|---|---|---|---|
| A_5123 | 0.217373 | 1.07234 | 7 | 2 | 2 |
| A_7043 | 0.116242 | 1.079 | 5 | 2 | 2 |
| A_8963 | 0.0688573 | 1.0564 | 5 | 2 | 2 |
| A_10883 | 0.0683395 | 1.13666 | 5 | 2 | 2 |
| B_5123 | 0.208565 | 8.63175 | 6 | 2 | 2 |
| B_7043 | 0.109804 | 8.06984 | 8 | 2 | 2 |
| B_8963 | 0.0638798 | 7.56142 | 6 | 2 | 2 |
| B_10883 | 0.0633015 | 8.32659 | 6 | 2 | 2 |
| C_5123 | 0.226894 | 1.09966 | 5 | 2 | 2 |
| C_7043 | 0.120861 | 1.08779 | 7 | 2 | 2 |
| C_8963 | 0.0720447 | 1.06526 | 7 | 2 | 2 |
| C_10883 | 0.0708341 | 1.1288 | 7 | 2 | 2 |
| completo_B | 0.0594997 | 7.90259 | 7 | 2 | 2 |
| M_5123 | 0.211343 | 2.22143e+07 | 19 | 2 | 2 |
| M_7043 | 0.113799 | 1162.85 | 17 | 2 | 2 |
| M_8963 | 0.0673871 | 4.57101e+07 | 25 | 2 | 2 |
| M_10883 | 0.0650523 | 3.68098e+07 | 23 | 2 | 2 |
| M_completo | 0.0624411 | 2.61994e+07 | 20 | 1 | 2 |

Selección: media entre ventanas del peor NRMSE de X1/X2/X3; empate <=2%
favorece menor complejidad. No es un criterio de aceptación oficial adicional.

| modelo | mean | min | max | parametros | EDO |
|---|---|---|---|---|---|
| A | 1.27787 | 0.744934 | 2.14622 | 3 | 4 |
| B | 1.24922 | 0.719426 | 2.108 | 12 | 4 |
| C | 1.31134 | 0.762925 | 2.19584 | 3 | 7 |
| M | 1.27962 | 0.754322 | 2.13488 | 9 | 7 |

B queda seleccionado para investigación, sin superioridad generalizable
demostrada. La mejora del criterio respecto de A es solo
2.242%.
D no se ejecutó: B y C no redujeron cada uno 5% el criterio de A.
M se ensayó después en desarrollo reutilizado por su hipótesis de dispersión;
no mejoró el criterio y no sustituyó a B. Esa investigación es adaptativa,
no confirmatoria. Su optimización colapsa las tasas de X2 y X3 a valores casi
iguales, con jacobianos muy mal condicionados: sus vías no se identifican
separadamente de manera defendible. Ver optimizaciones_mezcla.json.

Los parámetros definitivos de B son los de congelado.json, fijados antes de
cargar la reserva de esta ejecución. La reserva ya era conocida por trabajos
previos. Los de M se congelan en congelado_mezcla.json antes de su nueva
evaluación, después de haber visto la comparación retrospectiva de B.
sensibilidad.csv perturba cada coeficiente de B ±0,05 en su escala log/efecto,
sin reajustar. Es sensibilidad local, no intervalo de confianza. No se usan
errores independientes para fabricar intervalos de incertidumbre.
