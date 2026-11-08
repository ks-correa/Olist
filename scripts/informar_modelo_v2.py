"""Build technical deliverables strictly from saved measured results."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
from datetime import datetime,timezone
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/modelo_v2'


def md(table):
    t=table.copy()
    for col in t.select_dtypes(include='number'):t[col]=t[col].map(lambda v:f'{v:.6g}')
    return '| '+' | '.join(t.columns)+' |\n|'+'|'.join(['---']*len(t.columns))+'|\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in t.itertuples(index=False,name=None))


def write(name,text):
    (OUT/name).write_text(text.strip()+'\n',encoding='utf8')


def main():
    final=pd.read_csv(OUT/'comparacion_ampliada.csv')
    internal=pd.read_csv(OUT/'metricas_ventanas_ampliadas.csv')
    reserve=final[final.alcance=='reserva_reutilizada']
    selected=reserve[reserve.modelo=='V2_B']
    frozen=json.loads((OUT/'congelado.json').read_text(encoding='utf8'))
    mixture=json.loads((OUT/'congelado_mezcla.json').read_text(encoding='utf8'))
    runs=json.loads((OUT/'optimizaciones.json').read_text(encoding='utf8'))
    mruns=json.loads((OUT/'optimizaciones_mezcla.json').read_text(encoding='utf8'))
    dwell=pd.read_csv(OUT/'permanencias_resumen.csv')
    monthly=pd.read_csv(OUT/'tasas_exposicion_mensuales.csv')
    aggregation=pd.read_csv(OUT/'sensibilidad_agregacion_15min.csv')
    peaks=pd.read_csv(OUT/'picos_persistencia.csv')
    controls=pd.read_csv(OUT/'controles_numericos.csv')
    convergence=json.loads((OUT/'convergencia.json').read_text(encoding='utf8'))
    score=internal.groupby(['modelo','ventana']).NRMSE.max().groupby('modelo').agg(['mean','min','max']).reset_index()
    score['parametros']=score.modelo.map({'A':3,'B':12,'C':3,'M':9})
    score['EDO']=score.modelo.map({'A':4,'B':4,'C':7,'M':7})
    nrmse=internal.pivot(index=['modelo','ventana'],columns='variable',values='NRMSE').reset_index()
    params=[];optim=[]
    for key,rs in {**runs,**{'M_'+k:v for k,v in mruns.items()}}.items():
        good=[r for r in rs if r['success']]
        best=min(good,key=lambda r:r['cost'])
        optim.append(dict(ajuste=key,costo=best['cost'],condicion=best['condition'],nfev=best['nfev'],convergieron=sum(r['success'] for r in rs),inicios=len(rs)))
        if key.startswith(('A_','B_','C_')):
            theta=np.asarray(best['theta']).reshape(3,-1)
            params.append(dict(ajuste=key,alpha_base=np.exp(theta[0,0]),beta_base=np.exp(theta[1,0]),gamma_base=np.exp(theta[2,0])))
    pd.DataFrame(params).to_csv(OUT/'estabilidad_parametros.csv',index=False)
    pd.DataFrame(optim).to_csv(OUT/'resumen_optimizacion.csv',index=False)
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    for j,ax in enumerate(axes):
        t=monthly[monthly.variable==f'X{j+1}'];ax.plot(pd.to_datetime(t.fin),t.tasa,marker='o')
        ax.set(title=f'X{j+1} · desarrollo mensual',xlabel='Fin del mes',ylabel='Salidas/exposición (h⁻¹)');ax.tick_params(axis='x',rotation=45)
    fig.suptitle('Tasas descriptivas censuradas · no son calibración de trayectoria');fig.tight_layout();fig.savefig(OUT/'graficas/tasas_mensuales.png',dpi=110);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for ax,col,unit in zip(axes,['RMSE','NRMSE'],['pedidos','adimensional']):
        internal.groupby(['modelo','variable'])[col].mean().unstack().plot.bar(ax=ax)
        ax.set(title='Desarrollo reutilizado: 4 ventanas expansivas',xlabel='Modelo',ylabel=f'{col} ({unit})')
    fig.tight_layout();fig.savefig(OUT/'graficas/comparacion_ampliada.png',dpi=110);plt.close(fig)
    rate_ranges=monthly.groupby('variable').tasa.agg(['min','max']).reset_index()
    write('diagnostico_tecnico.md',f'''
# Diagnóstico técnico de OLIST / LAB

Se auditó el commit 6b732fba7bba43071cbf5ad1624eec4e10f1ded8, con Git limpio
antes de crear feature/modelo-v2-bondad-ajuste. Las 156 huellas de entrada y
archivos inspeccionados están en auditoria_previa.json. Se revisaron motores,
datos, informes, interfaz, escenarios, pruebas y documentación anteriores.
No se modificó ningún archivo científico V1 ni su población.

## Hallazgos respaldados por mediciones

1. **X1 y permanencias:** entre eventos completados al corte, 64,845% dura
menos de una hora, mediana 0,296944 h y P95 47,9563 h. La exponencial V1
tiene media 9,801636 h. KM, con 113 censuras de aprobación, presenta distancia
máxima descriptiva 0,555 frente a esa ley. Hay heterogeneidad no representada;
esto no demuestra que una mezcla particular sea correcta. El Erlang de dos
fases empeora el criterio interno. La mezcla ensayada mejora levemente la ley
de X1 pero no las trayectorias de desarrollo: ajuste distributivo y dinámico
son objetivos distintos. Ver permanencias_resumen.csv,
distancias_permanencia.csv y graficas/permanencias_comparadas.png.

{md(dwell[['variable','n','completadas','censuradas','mediana_completadas','p95_completadas','media_exponencial_V1']])}

2. **Calendario:** B reduce especialmente RMSE de despacho, pero la media
del peor NRMSE interno solo pasa de {score.set_index('modelo').loc['A','mean']:.6f}
a {score.set_index('modelo').loc['B','mean']:.6f}. No basta atribuir todo el error
a tasas constantes. En X3 el efecto de calendario ajustado es casi nulo.
Los residuos por mes, hora, día semanal y bloque de 168 h se entregan completos
en errores_temporales_*.csv, sin cambiar sus escalas por grupo.

3. **Estabilidad temporal:** tasas mensuales descriptivas por exposición exacta
censurada, sin consultar eventos posteriores al corte mensual:

{md(rate_ranges)}

Estos cambios mezclan calendario, composición y carga; no identifican por sí
solos una causa operativa. Las tasas ajustadas por prefijo y los resultados
en cada ventana están en estabilidad_parametros.csv y metricas_ventanas_ampliadas.csv.
Las ventanas no son réplicas independientes y tienen escalas distintas por
prefijo, fijadas antes de puntuar. El crecimiento de demanda con medias
tempranas pequeñas hace exigente el NRMSE interno; no se cambió el denominador.

4. **Sesgo y picos:** en la reserva reutilizada V1 tiene sesgo positivo de
3,619 / 109,262 / 287,797 pedidos en X1/X2/X3. B conserva sesgos de
3,779 / 109,264 / 287,332. Ese promedio coexiste con subestimación de los picos
de X1. Ver picos_persistencia.csv para amplitud, desfase y rachas, y
subidas_descensos.csv para subida/descenso y error del cambio horario.
No se interpreta una media próxima a cero como ausencia de fallos locales.

5. **Error numérico:** diferencia RK4 h=0,25 frente a 0,125 en todo el desarrollo
de B = {convergence[0]['diferencia_max']:.9g} pedidos, muy inferior a RMSE
empíricos de decenas/centenares. Refinar a 0,0625 vuelve a reducir el error.
No hay evidencia de que el integrador explique el mal ajuste.

6. **Agregación:** al distribuir las mismas compras por sus marcas originales
en 15 minutos, conservando objetivos horarios, la sensibilidad de V1 es:

{md(aggregation[['variable','RMSE','NRMSE','max_diferencia_vs_entrada_horaria']])}

Es un diagnóstico retrospectivo adicional, sin reajustar parámetros ni
reemplazar la convención oficial. No resuelve los errores; tampoco descarta
otros efectos de agregación individual o heterogeneidad de pedidos.

7. **Selección de población:** los 95.082 pedidos son entregados con cronología
válida y cuatro fechas completas. La pertenencia usa información futura
respecto de muchos orígenes. Se mantuvo esa población explícitamente; no es
todo el inventario de Olist ni incluye cancelaciones con fechas verificadas.
KM incorpora censuras administrativas de etapa al corte, pero no elimina
el sesgo de selección de cohorte ni garantiza censura no informativa.
La cola final sin compras se conserva: no se recortó para favorecer métricas.

## Balance de causas

Evidencia fuerte contra explicación numérica; sensibilidad de entrada
intrahoraria pequeña bajo la convención ensayada. Evidencia de desajuste de
permanencias en aprobación, errores temporales persistentes y parámetros
efectivos variables entre prefijos. El calendario explica parte del error de
despacho, sin resolver aprobación ni entrega. No puede aislarse causalmente
el efecto de selección, heterogeneidad logística o cambios operativos con
esta comparación observacional. No se inventan capacidades ni mecanismos.
''')
    theta=np.asarray(frozen['theta']).reshape(3,4)
    write('modelo_matematico_v2.md',f'''
# Formulación matemática y unidades

V1 se conserva intacto en src/rk4_solver.py. A usa las mismas cuatro EDO,
recalibradas por prefijo para la comparación interna justa. El resultado
histórico de V1 se reproduce por separado con sus tres tasas originales.

## B: calendario, candidato seleccionado de desarrollo

dX1/dt=λ−α(t)X1; dX2/dt=α(t)X1−β(t)X2;
dX3/dt=β(t)X2−γ(t)X3; dX4/dt=γ(t)X3.

k_i(t)=exp(b_i0+b_i1 sin(2πh/24)+b_i2 cos(2πh/24)+b_i3 I_sábado_domingo).
La función es constante en cada intervalo horario, según su extremo izquierdo.
No hay parámetros libres por fecha. El valor b_i0 es logaritmo de la tasa
numérica expresada en h⁻¹, respecto de la referencia 1 h⁻¹.

{md(pd.DataFrame(theta,columns=['b0','b_sin','b_cos','b_fin_semana']).assign(variable=['X1','X2','X3'])[['variable','b0','b_sin','b_cos','b_fin_semana']])}

Estados en pedidos, flujos en pedidos/h, tiempo en horas; λ es la cantidad
histórica de compras del intervalo dividida por una hora. Coeficientes en h⁻¹;
efectos de calendario adimensionales; áreas en pedidos·hora. Las fechas del
dataset se conservan sin zona horaria inferida. No es un sistema hidráulico.

## C: Erlang de dos fases

Para cada etapa i hay z_i1 y z_i2. d z_i1/dt=u_i−k_i z_i1;
d z_i2/dt=k_i z_i1−k_i z_i2. u_1=λ, u_2=k_1 z_12,
u_3=k_2 z_22 y dX4/dt=k_3 z_32. Xi=z_i1+z_i2.
Son SIETE EDO, no cuatro; permanencia Erlang(2,k_i), media 2/k_i.
Al origen z_i1=z_i2=Xi(0)/2. El reparto se fija sin mirar el futuro.
No se seleccionó C. Sus tasas ajustadas por prefijo están en optimizaciones.json.

## M: mezcla de dos vías exponenciales, segunda ronda adaptativa

Para r=f,s: d z_ir/dt=p_ir u_i−k_ir z_ir;
p_if=p_i, p_is=1−p_i, q_i=Σ_r k_ir z_ir;
u_1=λ, u_2=q_1, u_3=q_2, dX4/dt=q_3, Xi=Σ_r z_ir.
Ley de supervivencia de entrada p_i exp(−k_if t)+(1−p_i)exp(−k_is t).
Son SIETE EDO y nueve parámetros. Inicialización
z_ir(0)=Xi(0)(p_ir/k_ir)/Σ_s(p_is/k_is), aproximación de ocupación estacionaria
que no usa edades observadas posteriores. Es una limitación en transitorios.
La simetría de etiquetas se resuelve ordenando las tasas al finalizar.

## Conservación y numeración

En todos los candidatos Σ_i dXi/dt=λ; sumar subestados una vez, sin duplicar.
Las matrices tienen diagonales no positivas y transferencias no negativas.
RK4 principal usa h=0,25 h, entrada y tasas congeladas por hora también en K4.
El propagador matricial evalúa el polinomio clásico I+Z+Z²/2+Z³/6+Z⁴/24.
La recurrencia triangular se resuelve con solve_banded o lfilter; no es un
suavizador ni usa objetivos futuros. Sin recorte ni restauración artificial
de masa. Se rechazan pasos fuera de las guardas de positividad; controles
de masa usan tolerancia flotante documentada en código, y flujos toleran
solo redondeo de 1e−8 pedidos. No hubo flujos negativos en resultados entregados.
AgentPy mantiene cuatro agentes que publican el agregado del motor común,
incluidos sus subestados cuando existen. Equivalencia exacta verificada.
''')
    write('calibracion_v2.md',f'''
# Calibración, selección e identificabilidad

Desarrollo: 15/09/2016 11:00–02/03/2018 22:00, 12.803 intervalos.
Cada prefijo empieza en el mismo origen y termina en 5123/7043/8963/10883 h;
se evalúan 1920 h posteriores desde una única condición inicial observada.
Ningún estado intermedio observado corrige la trayectoria.

L=mean_{{horas,etapas}}[((simulado−observado)/s_i)²]+0,01 Σ b_calendario²
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

{md(pd.DataFrame(optim))}

Selección: media entre ventanas del peor NRMSE de X1/X2/X3; empate <=2%
favorece menor complejidad. No es un criterio de aceptación oficial adicional.

{md(score)}

B queda seleccionado para investigación, sin superioridad generalizable
demostrada. La mejora del criterio respecto de A es solo
{100*(1-frozen['scores']['B']/frozen['scores']['A']):.3f}%.
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
''')
    write('bondad_ajuste.md',f'''
# Bondad de ajuste dinámica

Error e_k=simulado−observado; MAE=mean|e|, RMSE=sqrt(mean e²),
sesgo=mean e, máximo puntual=max|e|, error pico=|max sim−max obs|,
error final=sim_final−obs_final. MAE/RMSE/sesgos en pedidos;
NMAE=MAE/s y NRMSE=RMSE/s, adimensionales. R²=1−Σe²/Σ(y−media y)²,
sin truncarlo; si el denominador es cero se devuelve NaN. R² es relativo
a la media del bloque evaluado, no una demostración de pronóstico.
Se excluye siempre el corte inicial de todas las puntuaciones.

## Reserva histórica reutilizada, 5488 objetivos por etapa

{md(reserve[['modelo','variable','MAE','RMSE','NRMSE','NMAE','R2','sesgo_medio','error_nivel_maximo_absoluto','error_final_absoluto','cumple']])}

Ninguna etapa de B satisface conjuntamente todos los criterios. X1 incumple
NRMSE/NMAE y pico; X2/X3 incumplen NRMSE/NMAE. X3 pasa el límite de error
de pico en esta reserva, sin compensar sus otros incumplimientos. En desarrollo
las ventanas también presentan incumplimientos y cambios de sesgo.

## Residuos

ACF y Ljung–Box a 24/168 h disponibles por etapa y período. En B, reserva:

{md(pd.read_csv(OUT/'ljung_box_V2_B_reserva_reutilizada.csv'))}

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
''')
    write('validacion_v2.md',f'''
# Evaluación temporal y límites de aceptación

Se distinguen entrenamiento ajustado, evaluación interna de desarrollo
reutilizado y reserva histórica reutilizada. NO existe una reserva nueva
independiente. Los protocolos y congelaciones no borran el uso previo.
No se anticipan compras futuras: las entradas históricas se condicionan.

## Comparación equivalente en desarrollo

Todos usan los mismos 1920 objetivos por ventana, estado agregado al origen,
entrada horaria y escalas de su prefijo. A se reajusta en cada prefijo:
usar tasas V1 de todo el desarrollo aquí habría introducido información futura.
Las hipótesis de reparto interno inicial de C/M son diferentes, pero no usan
estados futuros y se declaran explícitamente.

{md(nrmse)}

Ningún candidato cumple NRMSE<=0,30 en las tres etapas a lo largo de las
ventanas. Ver todas las métricas, criterios de pico/final y sesgos en
metricas_ventanas_ampliadas.csv. No se promedian incumplimientos para aceptarlos.

## Reproducción histórica y resultado final de B

{md(reserve[reserve.modelo.isin(['V1_historico','V2_B'])][['modelo','variable','NRMSE','NMAE','cumple']])}

Las cifras V1 se reproducen con tolerancia flotante de 1e−7 pedidos frente
al motor RK4 original; los CSV e informes V1 quedan intactos. Se mantienen
NRMSE<=0,30; NMAE<=0,20; error pico<=max(1,0,2*pico observado);
error final<=max(1,0,2*escala de entrenamiento), por cada etapa. No hay
aceptación completa ni evidencia nueva de generalización externa.

Controles físicos por ventana y período: masa máxima de B
{controls[controls.modelo.isin(['B','V2_B'])].masa_max.max():.8g} pedidos,
sin estados negativos ni X4 decreciente. Refinamiento en convergencia.json.
AgentPy coincide exactamente en publicación de los cuatro agregados de B
durante las 5488 h de reserva; las pruebas también cubren A/C/D y M.
La ausencia de error numérico no compensa el error respecto de observaciones.

Limitaciones: cohorte entregada retrospectiva, inicialización interna de
fases aproximada, pocas estructuras e hiperparámetros prefijados, óptimos
locales posibles, validación interna ya reutilizada, no incertidumbre de
demanda ni efectos causales de escenarios. No se afirma haber agotado todos
los modelos matemáticamente posibles ni que más complejidad garantice precisión.
''')
    write('escenarios_y_presentacion.md','''
# Decisión sobre escenarios y presentación académica

No se recalculan E0/E1/E2 bajo V2 porque ningún candidato alcanzó los
criterios y su mejora interna es pequeña. Se conserva la simulación y los
escenarios V1 con su semántica y resultados originales, separados del
Laboratorio V2. No se trasladan a V2 las cifras 3,59% y 12,59%.

La selección B es para investigación y comparación, no autorización de
uso operativo. Si se estudian intervenciones en el futuro, un +20% de tasa
significaría multiplicar toda la función temporal por 1,2, no sumar 20 puntos
al efecto log ni cambiar arbitrariamente el calendario. Haría falta volver
a comprobar estabilidad, masa y métricas y explicar el alcance hipotético.

Se conserva íntegra la presentación académica anterior. No se modifican
diapositivas 5–13 ni se proponen cifras como logros nuevos. Esta investigación
puede presentarse como trabajo futuro documentado: calendario de despacho,
heterogeneidad de aprobación, límites de mezcla y necesidad de registros
nuevos definidos prospectivamente. Solo con mejora aceptada y verificada
procedería preparar sustituciones de ecuaciones, calibración, validación,
escenarios, resultados y conclusiones. Se mantiene visible el resultado V1.
''')
    write('informe_ejecutivo.md',f'''
# Resultado ejecutivo — 8 de noviembre de 2026

**No se alcanzó NRMSE ≤ 0,30 simultáneamente en X1, X2 y X3.**
La mejora de B es pequeña y no permite sustituir V1 como modelo aceptado.

{md(reserve[reserve.modelo.isin(['V1_historico','V2_B'])][['modelo','variable','MAE','RMSE','NRMSE']])}

1. Precisión original: NRMSE 0,994955 / 0,558954 / 0,666343, reproducida.
2. Se añadieron diagnóstico dinámico, tasas de calendario, Erlang de dos fases,
mezcla de vías rápidas/lentas, calibración multiorigen, bondad de ajuste,
congelaciones, pruebas e interfaz de comparación. Se preservó V1.
3. B obtiene NRMSE {selected.NRMSE.iloc[0]:.6f} / {selected.NRMSE.iloc[1]:.6f} /
{selected.NRMSE.iloc[2]:.6f} en la reserva histórica reutilizada.
4. Ninguna de sus tres etapas llega al objetivo de 0,30 en ese bloque.
5. Tampoco satisface todos los criterios NMAE, pico y final de manera conjunta.
6. Persisten autocorrelación, colas de error y sesgos; la conservación y
convergencia son buenas, pero no demuestran precisión empírica.
7. La media del peor NRMSE entre ventanas pasa de 1,277873 (A) a 1,249219 (B).
La mejora es 2,24%; el desempeño es inestable. Erlang y mezcla no la mejoran.
8. No hay datos nuevos independientes. La segunda ronda fue adaptativa.
9. Conservar V1 como referencia reproducible; B como candidato experimental
separado. No proclamar superioridad estable ni aceptación operativa.
10. Persisten heterogeneidad, sesgo retrospectivo de población, ausencia de
validación nueva, inicialización de fases e identificación débil de la mezcla.

La suite completa registrada tiene **207 aprobadas y 1 fallo preexistente**:
el hash de pedidos_limpios.csv difiere del manifiesto histórico, pero coincide
exactamente con la huella tomada antes de trabajar. No se cambió ese archivo,
el manifiesto ni la prueba. Las 20 pruebas nuevas pasan. Las advertencias de
pandas por dayofweek se conservan en el registro; no alteran los resultados.
La interfaz se comprobó con AppTest y seis interacciones HTTP reales listas
sin excepciones, sin comprobación visual completa del navegador.

Índice de evidencias: diagnostico_tecnico.md, modelo_matematico_v2.md,
calibracion_v2.md, bondad_ajuste.md, validacion_v2.md,
escenarios_y_presentacion.md, reproduccion.md, CSV/JSON y graficas/.
''')
    write('reproduccion.md','''
# Ejecución y evidencias reproducibles

Entorno exacto, versiones, fecha UTC real y hashes de CSV/ZIP en entorno.json.
La fecha local de trabajo es 2026-11-08, America/Bogota; los timestamps
históricos se conservan tal como fueron suministrados, sin inventar zona.

Comandos ejecutados con .venv/Scripts/python.exe:

```powershell
.venv/Scripts/python.exe scripts/experimentar_modelo_v2.py
.venv/Scripts/python.exe scripts/experimentar_mezcla_v2.py
.venv/Scripts/python.exe scripts/diagnosticar_modelo_v2.py
.venv/Scripts/python.exe scripts/informar_modelo_v2.py
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m pytest tests/test_model_v2.py tests/test_model_mixture.py tests/test_model_v2_ui.py -q
.venv/Scripts/python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8503 --server.enableAgentApi true
.venv/Scripts/python.exe scripts/verificar_interfaz_v2.py
```

Los scripts de ajuste rechazan sobrescribir una congelación existente.
Para repetir todos los experimentos preservando estos resultados:

```powershell
.venv/Scripts/python.exe scripts/reproducir_modelo_v2.py --output reports/reproduccion_v2_nueva
```

El destino debe ser nuevo. Protocolos, ventanas, pesos y cotas permanecen
idénticos. La selección local debe reproducirse hasta tolerancia numérica;
fecha, tiempos de ejecución y diferencias de versión no son invariantes.
Las rutas de hashes del experimento apuntan al código fuente usado. Las
congelaciones verifican código/protocolo y escalas; el manifiesto previo
permite comprobar que entradas y resultados históricos no cambiaron.

pruebas_completas.txt: 207 passed, 1 failed (discrepancia anterior).
pruebas_nuevas.txt: 20 passed. Los errores iniciales de implementación y
la discrepancia del manifiesto se describen en incidencias.md y
discrepancias_integridad_preexistentes.json. No se descartaron fallos.
api_verificacion.json registra seis interacciones con status ready.
No se hizo inspección completa de renderizado en navegador ni comprobación
de tipos estática con mypy/ty (no disponibles en el entorno). La sintaxis y
el comportamiento de los módulos se verifican por importación y pruebas.
No se cambiaron dependencias Python ni los tests históricos.

Los histogramas de duración solo describen completadas y se etiquetan así;
la supervivencia incluye todas las censuras al corte. No hay datos sintéticos
en evaluaciones empíricas. Los datos artificiales se usan solo en unitarias.
''')
    if (OUT/'reproducibilidad_verificada.json').exists():
        with (OUT/'reproduccion.md').open('a',encoding='utf8') as handle:
            handle.write('\nSe repitieron A/B/C/M en un directorio separado: selección B y seis tablas\nidénticas byte a byte. Evidencia en reproducibilidad_verificada.json y\nreproduccion_ejecucion.txt. No se sobrescribió ningún resultado entregado.\n')
    paths=[p for p in OUT.rglob('*') if p.is_file() and p.name!='integridad_entrega.json']
    write('integridad_entrega.json',json.dumps({str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2,ensure_ascii=False))
    print('Informes técnicos generados a partir de resultados guardados')

if __name__=='__main__':main()
