# Bondad de ajuste dinámica

Error e_k=simulado−observado; MAE=mean|e|, RMSE=sqrt(mean e²),
sesgo=mean e, máximo puntual=max|e|, error pico=|max sim−max obs|,
error final=sim_final−obs_final. MAE/RMSE/sesgos en pedidos;
NMAE=MAE/s y NRMSE=RMSE/s, adimensionales. R²=1−Σe²/Σ(y−media y)²,
sin truncarlo; si el denominador es cero se devuelve NaN. R² es relativo
a la media del bloque evaluado, no una demostración de pronóstico.
Se excluye siempre el corte inicial de todas las puntuaciones.

## Reserva histórica reutilizada, 5488 objetivos por etapa

| modelo | variable | MAE | RMSE | NRMSE | NMAE | R2 | sesgo_medio | error_nivel_maximo_absoluto | error_final_absoluto | cumple |
|---|---|---|---|---|---|---|---|---|---|---|
| V1_historico | X1 | 24.4959 | 44.1688 | 0.994955 | 0.551799 | 0.409559 | 3.61903 | 386.761 | 1.0911e-51 | False |
| V1_historico | X2 | 138.871 | 184.657 | 0.558954 | 0.420359 | 0.516316 | 109.262 | 32.655 | 5.03779e-05 | False |
| V1_historico | X3 | 546.733 | 669.099 | 0.666343 | 0.544481 | 0.586321 | 287.797 | 420.442 | 20.7485 | False |
| V2_B | X1 | 23.46 | 43.1811 | 0.972705 | 0.528464 | 0.435673 | 3.77904 | 394.606 | 1.2645e-51 | False |
| V2_B | X2 | 127.801 | 169.141 | 0.511986 | 0.386852 | 0.594187 | 109.264 | 69.5405 | 4.9293e-05 | False |
| V2_B | X3 | 546.365 | 667.537 | 0.664788 | 0.544114 | 0.58825 | 287.332 | 418.862 | 20.6972 | False |
| V2_M | X1 | 25.2875 | 44.1521 | 0.994579 | 0.569631 | 0.410006 | 5.7676 | 396.993 | 1.45273e-06 | False |
| V2_M | X2 | 138.774 | 184.24 | 0.55769 | 0.420067 | 0.518502 | 109.495 | 29.9889 | 7.8422e-05 | False |
| V2_M | X3 | 546.83 | 668.914 | 0.666159 | 0.544578 | 0.58655 | 287.902 | 420.446 | 20.893 | False |

Ninguna etapa de B satisface conjuntamente todos los criterios. X1 incumple
NRMSE/NMAE y pico; X2/X3 incumplen NRMSE/NMAE. X3 pasa el límite de error
de pico en esta reserva, sin compensar sus otros incumplimientos. En desarrollo
las ventanas también presentan incumplimientos y cambios de sesgo.

## Residuos

ACF y Ljung–Box a 24/168 h disponibles por etapa y período. En B, reserva:

| variable | lag | Q | p_descriptivo | n |
|---|---|---|---|---|
| X1 | 24 | 57000.8 | 0 | 5488 |
| X1 | 168 | 68808.3 | 0 | 5488 |
| X2 | 24 | 81806.2 | 0 | 5488 |
| X2 | 168 | 210982 | 0 | 5488 |
| X3 | 24 | 129457 | 0 | 5488 |
| X3 | 168 | 815971 | 0 | 5488 |

El cero numérico de p representa subdesbordamiento, no probabilidad exactamente
nula. Se usa aproximación chi-cuadrado con lag grados de libertad, model_df=0,
sin afirmar el ajuste ARMA ni calibración exacta para estas EDO. Tendencia,
heterocedasticidad, selección y dependencia limitan interpretación inferencial:
se reporta como señal descriptiva de dependencia, nunca como precisión.
Los Q-Q de residuos son descriptivos de colas y asimetría; no se supone
normalidad ni independencia para intervalos o aceptación.

Las figuras por modelo/etapa contienen las 5488 o 12803 observaciones sin
suavizar: trayectoria, error temporal, error frente a simulado, histograma,
ACF y Q-Q. Las fechas, alcance, unidades y modelo aparecen en los títulos.
Los errores agrupados mensuales, por hora y día semanal conservan las mismas
escalas del entrenamiento; no se recalculan denominadores en cada grupo.

## Permanencias y contrastes admisibles

Kaplan–Meier maneja 113/586/3005 censuras administrativas al corte de desarrollo.
Su implementación se contrastó numéricamente contra scipy.stats.ecdf(CensoredData).
Supervivencias, histogramas de completadas identificados como tales, Q-Q con
cuantiles KM identificables y distancias máximas descriptivas están en CSV/PNG.
No se aplicó KS/AD ingenuo: los parámetros se estimaron, las duraciones son
censuradas y la cohorte está seleccionada. Un bootstrap paramétrico simple
ignoraría dependencia y selección; no se inventa un p-valor válido.
No se ajusta una distribución por apariencia ni se sustituye la evaluación
de trayectorias por distancias distributivas. La mezcla no corrige X1 lo
suficiente y sus vías posteriores colapsan. No hay aceptación empírica.

Referencias metodológicas primarias consultadas:
[SciPy ecdf y censura](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ecdf.html),
[SciPy goodness_of_fit y reestimación Monte Carlo](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.goodness_of_fit.html),
[statsmodels Ljung–Box](https://www.statsmodels.org/dev/generated/statsmodels.stats.diagnostic.acorr_ljungbox.html).
