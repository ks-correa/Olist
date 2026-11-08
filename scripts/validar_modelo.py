"""Fase 4B: evaluación final congelada; nunca ejecuta optimización ni escenarios."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import json
import platform
import subprocess
import time
import numpy as np
import pandas as pd
import agentpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.validation import (load_frozen,load_validation,run_frozen,level_arrays,scored_levels,
    block_slices,acceptance,sha256,audit_trajectory,NAMES,START,END)
from src.simulation_engine import simulate
from src.calibration_metrics import metrics


def markdown(table):
    table=table.copy()
    for col in table:
        if pd.api.types.is_float_dtype(table[col]):
            table[col]=table[col].map(lambda value:f'{value:.6g}')
    return '| '+' | '.join(map(str,table.columns))+' |\n|'+'|'.join(['---']*len(table.columns))+'|\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in table.itertuples(index=False,name=None))


def main():
    clock=time.perf_counter();out=ROOT/'reports';figdir=out/'graficas_validacion'
    figdir.mkdir(exist_ok=True)
    protected=[ROOT/name for name in ['reports/parametros_calibrados.json','reports/modelo_seleccionado_desarrollo.json',
        'reports/metricas_entrenamiento.csv','reports/metricas_transferencias_entrenamiento.csv',
        'reports/calibracion_modelo.md','reports/comparacion_modelos.md',
        'docs/modelo_matematico.md','docs/plan_calibracion_validacion.md','docs/implementacion_rk4_agentpy.md',
        'src/rk4_solver.py','src/simulation_engine.py','src/agent_model.py','src/calibration_metrics.py',
        'data/processed/eventos_por_hora.csv','data/processed/niveles_reales_4_tanques.csv']]
    fingerprints={str(path.relative_to(ROOT)):sha256(path) for path in protected}
    code={str(path.relative_to(ROOT)):sha256(path) for path in [ROOT/'src/validation.py',Path(__file__).resolve()]}
    parameters,scales,flow_scales=load_frozen(out)
    data=load_validation(ROOT/'data/processed')
    print(f'Validación final: {data.cuts[0]} a {data.cuts[-1]}, {len(data.arrivals)} intervalos; parámetros congelados',flush=True)
    result,agents=run_frozen(data,parameters)
    conservation=audit_trajectory(result,data.initial,data.arrivals)
    # Los controles físicos anteriores deben pasar antes de producir métricas.
    observed,simulated=level_arrays(data,result)
    final_metrics=scored_levels(data.cuts[1:],observed[1:],simulated[1:],scales)
    transfer_metrics=metrics(data.flows,result.transfers,['aprobaciones','despachos','entregas'],flow_scales)
    block_metrics=[];block_counts=[]
    for name,segment in block_slices():
        table=scored_levels(data.cuts[segment],observed[segment],simulated[segment],scales)
        table['bloque']=name;block_metrics.append(table)
        begin,end=segment.start-1,segment.stop-1
        block_counts.append({'bloque':name,'inicio_abierto':str(data.cuts[begin]),'fin_inclusivo':str(data.cuts[end]),
            'intervalos':end-begin,'compras':float(data.arrivals[begin:end].sum()),
            'horas_sin_compras':int((data.arrivals[begin:end]==0).sum()),
            'aprobaciones_observadas':float(data.flows[begin:end,0].sum()),
            'despachos_observados':float(data.flows[begin:end,1].sum()),
            'entregas_observadas':float(data.flows[begin:end,2].sum())})
    blocks=pd.concat(block_metrics,ignore_index=True);counts=pd.DataFrame(block_counts)
    criteria=acceptance(final_metrics,blocks)
    # Referencia de persistencia: sólo X1-X3, sin simulación de un balance físico.
    persistence=np.tile(data.initial[:3],(len(data.arrivals),1))
    persistence_metrics=metrics(data.observed[1:,:3],persistence,['X1','X2','X3'],scales[:3])
    comparison_persistence=final_metrics.iloc[:3][['variable','MAE','RMSE']].merge(
        persistence_metrics[['variable','MAE','RMSE']],on='variable',suffixes=('_EDO','_persistencia'))
    comparison_persistence['mejora_RMSE_pct']=100*(1-comparison_persistence.RMSE_EDO/comparison_persistence.RMSE_persistencia)
    # Se leen resultados congelados: no se recalcula entrenamiento.
    train=pd.read_csv(out/'metricas_entrenamiento.csv')
    comparison=train.merge(final_metrics,on='variable',suffixes=('_entrenamiento','_validacion'))
    comparison['factor_RMSE']=comparison.RMSE_validacion/comparison.RMSE_entrenamiento
    convergence=[]
    previous=result
    for substeps in (8,16):
        refined=simulate(data.initial,data.arrivals,parameters,substeps)
        audit_trajectory(refined,data.initial,data.arrivals)
        difference=previous.states-refined.states
        normalized=np.sqrt(np.mean(difference[1:]**2,axis=0))/scales[:4]
        record={'h_grueso':1/(substeps//2),'h_fino':1/substeps,'max_diferencia':float(np.max(np.abs(difference))),
            'NRMSE_numerico_por_estado':normalized.tolist(),'max_diferencia_transferencias':float(np.max(np.abs(previous.transfers-refined.transfers))),
            'error_max_conservacion_malla_fina':refined.max_conservation_error}
        if record['max_diferencia']>.1 or (normalized>.001).any():
            raise ValueError('No cumple convergencia numérica con parámetros congelados')
        convergence.append(record);previous=refined
    final_metrics.to_csv(out/'metricas_validacion.csv',index=False)
    blocks.to_csv(out/'metricas_por_bloque.csv',index=False)
    counts.to_csv(out/'conteos_bloques_validacion.csv',index=False)
    transfer_metrics.to_csv(out/'metricas_transferencias_validacion.csv',index=False)
    comparison.to_csv(out/'comparacion_entrenamiento_validacion.csv',index=False)
    persistence_metrics.to_csv(out/'metricas_persistencia_validacion.csv',index=False)
    comparison_persistence.to_csv(out/'comparacion_persistencia_validacion.csv',index=False)
    criteria.to_csv(out/'criterios_validacion.csv',index=False)
    trajectory=pd.DataFrame({'corte_horario':data.cuts,'horas_desde_inicio':result.times})
    for i in range(4):
        trajectory[f'X{i+1}_observado']=data.observed[:,i]
        trajectory[f'X{i+1}_simulado']=result.states[:,i]
        trajectory[f'residuo_X{i+1}']=result.states[:,i]-data.observed[:,i]
    trajectory['X4_incremental_observado']=observed[:,3];trajectory['X4_incremental_simulado']=simulated[:,3]
    trajectory['P_observado']=observed[:,4];trajectory['P_simulado']=simulated[:,4]
    trajectory['compras_intervalo']=np.r_[np.nan,data.arrivals]
    trajectory['error_conservacion']=result.conservation_errors
    trajectory.to_csv(out/'trayectoria_validacion.csv',index=False)
    flow_table=pd.DataFrame({'corte_horario':data.cuts[1:],'compras':data.arrivals})
    for i,name in enumerate(['aprobaciones','despachos','entregas']):
        flow_table[name+'_observado']=data.flows[:,i];flow_table[name+'_simulado']=result.transfers[:,i]
    flow_table.to_csv(out/'transferencias_validacion.csv',index=False)
    # Curvas completas: no hay suavizado, ni reinicialización en los cuatro bloques.
    for i,label in enumerate(NAMES):
        fig,ax=plt.subplots(figsize=(13,4.5))
        ax.plot(data.cuts,observed[:,i],label='Observado',color='#334155',lw=.8)
        ax.plot(data.cuts,simulated[:,i],label='Modelo base congelado, RK4',color='#dd6b20',lw=.8)
        for _,segment in block_slices():
            ax.axvline(data.cuts[segment.start-1],color='gray',ls=':',lw=.6)
        ax.set(title=f'{label} — validación final 2018-03-02 22:00 a 2018-10-17 14:00',xlabel='Fecha del proceso',ylabel='Pedidos')
        ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(figdir/f'{label}.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(13,8),sharex=True)
    for i,ax in enumerate(axes):
        ax.plot(data.cuts[1:],simulated[1:,i]-observed[1:,i],label='Simulado − observado',color='#dd6b20',lw=.65)
        ax.axhline(0,color='black',lw=.6)
        for name,segment in block_slices():
            ax.axvline(data.cuts[segment.start-1],color='gray',ls=':',lw=.6)
        ax.set_ylabel(f'Error X{i+1} (pedidos)');ax.legend();ax.grid(alpha=.2)
    axes[0].set_title('Residuos de validación final: una trayectoria, cuatro bloques de diagnóstico')
    axes[-1].set_xlabel('Fecha del proceso, marzo–octubre de 2018')
    fig.tight_layout();fig.savefig(figdir/'residuos_temporales.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5));positions=np.arange(3)
    ax.bar(positions-.18,comparison.RMSE_entrenamiento.iloc[:3],width=.36,label='Entrenamiento: 2016-09-15 a 2018-03-02')
    ax.bar(positions+.18,comparison.RMSE_validacion.iloc[:3],width=.36,label='Validación: 2018-03-02 a 2018-10-17')
    ax.set_xticks(positions,['X1','X2','X3']);ax.set(title='RMSE: entrenamiento congelado frente a validación final',xlabel='Depósito pendiente',ylabel='RMSE (pedidos)')
    ax.legend();fig.tight_layout();fig.savefig(figdir/'RMSE_entrenamiento_validacion.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(14,4.8))
    labels=[f'{r.bloque}\n{r.inicio_abierto[:10]}\na {r.fin_inclusivo[:10]}' for r in counts.itertuples()]
    for var,ax in zip(['X1','X2','X3'],axes):
        rows=blocks.loc[blocks.variable==var]
        ax.plot(np.arange(4),rows.NRMSE,marker='o',label='NRMSE por bloque')
        ax.axhline(.3,color='#b22222',ls='--',label='Umbral académico 0,30')
        ax.set_xticks(np.arange(4),labels,fontsize=7)
        ax.set(title=var,xlabel='Bloque de validación (1.372 h)',ylabel='NRMSE adimensional');ax.legend(fontsize=7);ax.grid(alpha=.2)
    fig.suptitle('Diagnóstico temporal: trayectoria única y escalas congeladas de entrenamiento')
    fig.tight_layout();fig.savefig(figdir/'errores_por_bloque.png',dpi=150);plt.close(fig)
    for label,mask in [('primeros_siete_dias',(data.cuts>=START)&(data.cuts<=START+pd.Timedelta(days=7))),
                       ('ultimos_siete_dias',(data.cuts>=END-pd.Timedelta(days=7))&(data.cuts<=END))]:
        fig,axes=plt.subplots(3,1,figsize=(13,8),sharex=True)
        for i,ax in enumerate(axes):
            ax.plot(data.cuts[mask],observed[mask,i],label='Observado',lw=1)
            ax.plot(data.cuts[mask],simulated[mask,i],label='Modelo congelado',lw=1)
            ax.set_ylabel(f'X{i+1} (pedidos)');ax.legend();ax.grid(alpha=.2)
        axes[0].set_title(f'Validación final — {label.replace("_"," ")}: {data.cuts[mask][0]} a {data.cuts[mask][-1]}')
        axes[-1].set_xlabel('Fecha del proceso; tramo de la trayectoria completa, sin reinicialización')
        fig.tight_layout();fig.savefig(figdir/f'{label}.png',dpi=150);plt.close(fig)
    # Reglas de interpretación fijadas por el plan; ninguna modificación posterior.
    quantitative=criteria.cumple_criterios_cuantitativos.to_numpy()
    decision='A' if quantitative.all() and not criteria.sesgo_mismo_signo_4_bloques.any() else ('B' if quantitative.any() else 'C')
    last_purchase=data.cuts[1:][np.flatnonzero(data.arrivals>0)[-1]]
    zero_tail=int((END-last_purchase)/pd.Timedelta(hours=1))
    summary={'phase':'4B','model':'base','parameters':dict(zip(['alpha','beta','gamma'],map(float,parameters.array()))),
        'parameter_units':'1/hora','period':{'start':str(START),'end':str(END),'intervals':len(data.arrivals),'states':len(data.cuts)},
        'initial_state':data.initial.tolist(),'initial_total':float(data.initial.sum()),
        'purchases':float(data.arrivals.sum()),'expected_final_total':float(data.initial.sum()+data.arrivals.sum()),
        'final_state':result.states[-1].tolist(),'final_observed_state':data.observed[-1].tolist(),
        'scales':dict(zip(NAMES,map(float,scales))),'flow_scales':flow_scales.tolist(),
        'integration':{'method':'RK4','h_hours':.25,'substeps':4,'initializations':1,'no_corrections':True},
        'max_conservation_error':conservation,'agentpy_states_max_difference':float(np.max(np.abs(result.states-agents.states))),
        'agentpy_transfers_max_difference':float(np.max(np.abs(result.transfers-agents.transfers))),
        'finite_nonnegative_states':True,'nonnegative_transfers':True,'X4_nondecreasing':True,
        'convergence':convergence,'criteria':criteria.to_dict(orient='records'),'decision':decision,
        'last_positive_purchase_interval_end':str(last_purchase),'trailing_hours_without_purchases':zero_tail,
        'sha256_protected_inputs':fingerprints,'sha256_new_code':code,'parameters_recalibrated':False,
        'alternative_model_evaluated':False,'final_validation_evaluated':True,
        'independence_note':'Reserva usada sólo tras congelar estructura y parámetros; cohorte retrospectiva condicionada a entregas completas',
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'agentpy':agentpy.__version__},
        'seconds_before_tests':time.perf_counter()-clock}
    worst_relative=final_metrics.iloc[:3].sort_values('NRMSE',ascending=False).iloc[0].variable
    worst_absolute=final_metrics.iloc[:3].sort_values('RMSE',ascending=False).iloc[0].variable
    stage_diagnostics=[]
    for row in final_metrics.iloc[:3].itertuples(index=False):
        old=comparison.loc[comparison.variable==row.variable].iloc[0]
        bias=blocks.loc[blocks.variable==row.variable,'sesgo_medio'].to_numpy()
        stage_diagnostics.append(
            f'- {row.variable}: RMSE {old.factor_RMSE:.3f} veces el de entrenamiento; '
            f'sesgo global {row.sesgo_medio:+.3f} pedidos. Sesgos B1–B4: '
            + ', '.join(f'{value:+.3f}' for value in bias)
            + f'. El máximo simulado difiere del observado en {row.error_nivel_maximo:+.3f} pedidos '
            + f'({100*row.error_nivel_maximo/max(1,row.maximo_observado):+.2f} %).')
    hashes=pd.DataFrame([{'archivo':k,'SHA256':v} for k,v in {**fingerprints,**code}.items()])
    report=f'''# Validación final independiente — fase 4B

## Modelo congelado y alcance
Se evaluó únicamente el modelo base seleccionado de primer orden. α={parameters.alpha:.17g}, β={parameters.beta:.17g}, γ={parameters.gamma:.17g} hora⁻¹, leídos del JSON original y comprobados exactamente contra los valores autorizados y el archivo de selección. No se recalibraron coeficientes ni se evaluó la aprobación rápida. Se conservan las cuatro EDO, cuatro estados, cuatro agentes y las escalas de entrenamiento.

Esta evaluación mide reproducción retrospectiva fuera de entrenamiento, condicionada a compras históricas conocidas y al estado inicial observado. No es pronóstico de demanda ni demostración causal de operaciones futuras. La independencia de la reserva respecto del ajuste no elimina el sesgo de una cohorte elegida retrospectivamente por entregas completas.

## Ventana, entrada e inicialización
Inicio: {START}; final: {END}. Exactamente 5.488 intervalos y 5.489 estados. Condición inicial comprobada: {data.initial.tolist()}, total 57.667 pedidos. Se inicializó una sola vez; luego se usaron exclusivamente compras en (inicio,fin], con entrada constante por hora y cuatro subpasos RK4 (h=0,25 h). K1–K4 usan la entrada de su misma hora. No se reinició en bloques, no se impusieron transiciones históricas y no se corrigieron estados con observaciones futuras.

Compras durante validación: {data.arrivals.sum():.0f}; total final esperado: {data.initial.sum()+data.arrivals.sum():.0f}. Se verificaron fechas únicas, mallas de compras/niveles iguales, separación horaria y balances de los eventos observados.

## Integridad y convergencia numérica
Todos los controles matemáticos se ejecutaron antes de calcular métricas: estados finitos y no negativos, transferencias no negativas, X4 no decreciente y conservación en todos los intervalos. No hubo recortes ni redondeos. Error máximo absoluto de conservación: **{conservation:.12g} pedidos**, dentro de 1e−8·max(1,total).

AgentPy y RK4 independiente coinciden exactamente en estados y transferencias (diferencia máxima cero). AgentPy completó los 5.488 intervalos con cuatro agentes. Las comprobaciones de la trayectoria no utilizan niveles observados posteriores para modificar la simulación.

Se repitió la integración a h=0,125 y 0,0625 únicamente para verificar convergencia, sin alterar parámetros ni elegir otro modelo. Comparaciones: `{json.dumps(convergence,ensure_ascii=False)}`. Cumplen máximo≤0,1 pedido y NRMSE numérico≤0,001 con escalas congeladas. Se conserva h=0,25 h.

Estado final simulado: {result.states[-1].tolist()}. Estado final observado: {data.observed[-1].tolist()}. El modelo continuo vacía colas asintóticamente: su remanente terminal no debe recortarse para coincidir con el cierre discreto de la cohorte.

## Métricas finales por variable
Los objetivos son los 5.488 cortes posteriores al inicio, sin incluir el error inicial cero. También los máximos y sus fechas se reportan sobre esos mismos cortes; si un máximo se sitúa en la condición inicial, ésta permanece visible en las gráficas y CSV, pero no agrega un objetivo gratuito. Los empates de máximo se resuelven con la primera fecha.

Errores firmados=simulado−observado. Las unidades absolutas son pedidos. NMAE/NRMSE son adimensionales. X1–X3 se normalizan con **{scales[:3].tolist()}**, valores de entrenamiento congelados. Para P y X4 incremental se usan igualmente sus escalas archivadas de entrenamiento: {scales[4]:.9g} y {scales[3]:.9g}, respectivamente. No se calcula una escala con validación. X4 se compara restando 53.963 entregas previas de ambas curvas.

{markdown(final_metrics)}

Mayor error relativo entre pendientes: **{worst_relative}**; mayor error absoluto: **{worst_absolute}**. La acumulación terminal no compensa esos errores.

### Transferencias horarias
Se comparan integrales RK4 de aprobaciones, despachos y entregas con conteos reales por hora. Las unidades absolutas son pedidos por intervalo de una hora; su valor numérico coincide con tasa media en pedidos/hora. Las escalas son las del archivo de transferencias de entrenamiento, no medias de validación.

{markdown(transfer_metrics)}

## Comparación con entrenamiento congelado
Se leyó metricas_entrenamiento.csv de fase 4A sin recalcular entrenamiento. Las filas originales y sus huellas se conservaron.

{markdown(comparison[['variable','MAE_entrenamiento','MAE_validacion','RMSE_entrenamiento','RMSE_validacion','NRMSE_entrenamiento','NRMSE_validacion','factor_RMSE']])}

El factor compara RMSE de validación con el de entrenamiento, con unidades idénticas; no prueba por sí solo una causa del cambio. Los niveles tienen magnitudes diferentes: X1 puede tener error absoluto menor y error relativo mayor. Los errores de pico y sus fechas permiten distinguir amplitud de desfase temporal.

{chr(10).join(stage_diagnostics)}

Ninguno de los tres pendientes mantiene el RMSE de entrenamiento. X2 sobreestima en promedio en los cuatro bloques; X3 pasa de subestimación en B1 a sobreestimación en los siguientes, de modo que su sesgo global oculta cambios importantes de signo. X1 conserva el mayor error relativo y pierde gran parte de la amplitud del pico observado.

## Cuatro bloques: una trayectoria, sin reinicializaciones
Cada bloque contiene exactamente 1.372 intervalos, sin cortes objetivo repetidos. Los bloques son diagnósticos, no nuevas simulaciones ni conjuntos para reajuste. X4 incremental conserva el mismo origen global de validación en todos ellos.

{markdown(counts)}

{markdown(blocks[['bloque','variable','MAE','RMSE','NMAE','NRMSE','sesgo_medio','error_final']])}

Último intervalo con compras positivas termina en {last_purchase}; después hay {zero_tail} horas sin nuevas compras de esta cohorte. La reducción de llegadas observada al final y el vaciado histórico condicionan las métricas del último bloque. No se interpreta como caída demostrada de la demanda total de Olist: la fuente representa una cohorte finita retrospectiva de entregados completos. El coeficiente constante no representa explícitamente calendarios, cambios de mezcla, edad ni heterogeneidad; los sesgos por bloque describen discrepancias, no identifican causalmente su origen.

El menor error de X1 en B4 coincide con la reducción de llegadas y con niveles observados próximos a cero; no implica que haya mejorado su mecanismo de aprobación. X3 mantiene un error grande en ese mismo bloque porque el modelo conserva una cola de decaimiento más lenta que el vaciado registrado. Las horas sin llegadas no deben confundirse con una validación exigente de respuesta a demanda sostenida.

## Comparación descriptiva con persistencia
La referencia mantiene X1–X3 iguales al estado inicial de validación durante toda la ventana. No se reinicia por bloque y no es un modelo conservativo completo.

{markdown(comparison_persistence)}

Superar persistencia es una referencia mínima de desempeño estadístico; no sustituye criterios académicos de precisión ni demuestra utilidad operativa. Si una etapa no la supera, el signo negativo de mejora lo deja explícito.

## Criterios y decisión
Se aplicaron sin modificación los criterios académicos provisionales del plan: NMAE≤0,20; NRMSE≤0,30; error absoluto de máximo≤max(1 pedido,20 % del máximo observado); error final absoluto≤max(1 pedido,20 % de la escala de entrenamiento). Se evalúan por etapa, sin aprobar el conjunto por un buen total. Son umbrales internos, no estándares de Olist.

{markdown(criteria)}

La columna de sesgo con mismo signo en cuatro bloques es un diagnóstico descriptivo de persistencia, sin inventar un umbral de significación o magnitud después de ver resultados. También se examinan magnitudes y cambios temporales de sesgo en la tabla. No se interpreta un promedio cercano a cero como ausencia automática de errores locales.

**Conclusión: categoría {decision}.** Ninguna etapa pendiente cumple conjuntamente los criterios cuantitativos si la categoría es C; una coincidencia visual de X4 o conservación perfecta no cambia esa decisión. Con los resultados obtenidos, el modelo no sustenta recomendaciones operativas confiables. Puede conservarse como ejercicio académico de balances y referencia para simulaciones hipotéticas exploratorias, con limitaciones explícitas; no se ejecutan escenarios en esta fase.

## Cinco conceptos que deben distinguirse
- Correctitud numérica: conservación, positividad, convergencia y equivalencia de motores comprobadas.
- Ajuste: métricas de fase 4A sobre datos usados para estimar parámetros, preservadas como antecedente.
- Desempeño fuera de entrenamiento: cifras actuales sobre reserva antes intacta, sin corregir trayectorias.
- Escenarios hipotéticos: balances comparables bajo supuestos no prueban efectos operativos reales; la precisión observada limita su interpretación.
- Pronóstico futuro: requeriría una entrada futura estimada, incertidumbre y una población operativa adecuada. Aquí se conocen las compras históricas.

## Límites y uso posterior de esta reserva
El modelo agregado de coeficientes constantes no refleja todas las variaciones observadas, no incluye cancelaciones fechadas y no predice retrasos individuales. La cohorte retrospectiva seleccionada por entregas completas omite población pendiente/cancelada y no es el inventario completo de Olist.

La reserva ya fue evaluada y sus resultados se conservan incluso si son desfavorables. No se ajustan coeficientes ni se cambia estructura con ella para volver a presentarla como validación independiente. Cualquier desarrollo posterior motivado por estos errores necesitará un conjunto de prueba nuevo para evaluación independiente. No se implementan escenarios ni Streamlit.

## Archivos y visualizaciones
metricas_validacion.csv, metricas_por_bloque.csv, trayectoria_validacion.csv y resumen_validacion.json contienen resultados principales. Se añaden transferencias, persistencia, criterios, conteos temporales y comparación con entrenamiento como CSV separados. No se sobrescribe ningún archivo de datos, entrenamiento ni selección anterior.

En graficas_validacion/: X1.png, X2.png, X3.png, X4_incremental.png, P.png; residuos_temporales.png; RMSE_entrenamiento_validacion.png; errores_por_bloque.png; primeros_siete_dias.png; ultimos_siete_dias.png. Las dos ampliaciones están fijadas desde el inicio y el final de la ventana, por siete días consecutivos, sin escoger tramos favorables. Las curvas utilizan todos los cortes disponibles, sin suavizado.

## Trazabilidad SHA-256
{markdown(hashes)}

Las huellas se tomaron antes de evaluar y se verifican otra vez al finalizar. Versiones: Python {platform.python_version()}, AgentPy {agentpy.__version__}, NumPy {np.__version__}, pandas {pd.__version__}. Tiempo hasta generar tablas y gráficas: {summary['seconds_before_tests']:.3f} s. Configuración y resultados numéricos completos en resumen_validacion.json.

## Reproducción
```powershell
.venv/Scripts/python.exe scripts/validar_modelo.py
```
El script ejecuta pruebas anteriores y nuevas, guarda su salida y devuelve error si falla alguna. No importa ni llama calibradores. La repetición reproduce esta evaluación; no constituye una segunda prueba independiente.
'''
    (out/'validacion_final.md').write_text(report,encoding='utf-8')
    # El resumen existe antes de probar: las pruebas pueden inspeccionar el artefacto.
    (out/'resumen_validacion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    suite=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    output=suite.stdout+suite.stderr
    (out/'pruebas_validacion.txt').write_text(output,encoding='utf-8')
    summary['test_process_returncode']=suite.returncode;summary['test_output']=output
    summary['seconds_total']=time.perf_counter()-clock
    for path in protected:
        if sha256(path)!=fingerprints[str(path.relative_to(ROOT))]:
            raise ValueError(f'Archivo protegido fue modificado: {path}')
    summary['protected_files_unchanged']=True
    (out/'resumen_validacion.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    with (out/'validacion_final.md').open('a',encoding='utf-8') as f:
        f.write('\n## Pruebas ejecutadas\n\n```text\n'+output.strip()+'\n```\n')
        f.write('\nSe verificó que las huellas de todos los archivos protegidos siguen iguales al finalizar.\n')
    print(final_metrics[['variable','MAE','RMSE','NMAE','NRMSE']].to_string(index=False),flush=True)
    print(counts.to_string(index=False),flush=True)
    print(criteria.to_string(index=False),flush=True)
    print('Decisión:',decision,'; conservación máxima:',conservation,'; AgentPy/RK4: igualdad exacta',flush=True)
    print(output,flush=True)
    if suite.returncode:
        raise SystemExit(suite.returncode)

if __name__=='__main__':
    main()
