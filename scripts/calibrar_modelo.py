"""Fase 4A reproducible: sólo entrenamiento, evaluación interna y diagnóstico."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import hashlib
import json
import platform
import time
import numpy as np
import pandas as pd
import scipy
import agentpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.calibration import (load_training,exposure_estimates,multistart_fit,
                              analytical_trajectory,residual_vector)
from src.calibration_metrics import level_metrics,metrics,calendar_diagnostics
from src.simulation_engine import simulate
from src.agent_model import simulate_agentpy


def markdown(table):
    table=table.copy()
    for col in table:
        if pd.api.types.is_float_dtype(table[col]):
            table[col]=table[col].map(lambda value:f'{value:.6g}')
    return '| '+' | '.join(map(str,table.columns))+' |\n|'+'|'.join(['---']*len(table.columns))+'|\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in table.itertuples(index=False,name=None))


def main():
    overall=time.perf_counter()
    out=ROOT/'reports'; figures=out/'graficas_calibracion'
    figures.mkdir(parents=True,exist_ok=True)
    data=load_training(ROOT/'data/processed')
    print(f'Entrenamiento: {data.cuts[0]} a {data.cuts[-1]}, {len(data.arrivals)} intervalos',flush=True)
    events=ROOT/'data/processed/pedidos_limpios.csv'
    # División determinada sólo por duración del entrenamiento, antes de ajustar.
    m=int(.8*len(data.arrivals))
    prefix=data.section(0,m); internal=data.section(m,len(data.arrivals))
    preliminary_prefix=exposure_estimates(events,prefix.cuts[0],prefix.cuts[-1])
    (prefix_p,prefix_info),prefix_runs=multistart_fit(prefix,preliminary_prefix.tasa_inicial.to_numpy())
    pred_prefix=simulate(prefix.observed[0],prefix.arrivals,prefix_p,4).states
    # Evaluación interna: una inicialización observada en el corte; no reajustes posteriores.
    pred_internal=simulate(internal.observed[0],internal.arrivals,prefix_p,4).states
    scale_prefix=np.r_[prefix.scales,max(1,np.mean(prefix.observed[1:,3]-prefix.observed[0,3])),
                       max(1,np.mean(prefix.observed[1:,:3].sum(axis=1)))]
    prefix_metrics=level_metrics(prefix,pred_prefix,scale_prefix);prefix_metrics['periodo']='ajuste_interno_80pct'
    internal_metrics=level_metrics(internal,pred_internal,scale_prefix);internal_metrics['periodo']='evaluacion_interna_20pct'
    # Reajuste descriptivo del bloque posterior para estudiar estabilidad, no para corregir la predicción interna.
    preliminary_internal=exposure_estimates(events,internal.cuts[0],internal.cuts[-1])
    (suffix_p,suffix_info),suffix_runs=multistart_fit(internal,preliminary_internal.tasa_inicial.to_numpy())
    preliminary=exposure_estimates(events,data.cuts[0],data.cuts[-1])
    np.testing.assert_array_equal(preliminary.transferencias,data.flows.sum(axis=0))
    (p,info),runs=multistart_fit(data,preliminary.tasa_inicial.to_numpy())
    analytical=analytical_trajectory(data.observed[0],data.arrivals,p)
    print(f'Parámetros de entrenamiento: {p}',flush=True)
    numeric=[]; trajectories=[]
    scales4=np.r_[data.scales,max(1,np.mean(data.observed[1:,3]-data.observed[0,3]))]
    for substeps in (4,8,16):
        start=time.perf_counter(); r=simulate(data.observed[0],data.arrivals,p,substeps)
        elapsed=time.perf_counter()-start
        diff=r.states-analytical
        numeric.append({'subpasos':substeps,'h_horas':1/substeps,'segundos':elapsed,
            'error_maximo_vs_analitico':float(np.max(np.abs(diff))),
            'error_maximo_conservacion':r.max_conservation_error,
            'minimo_estado':float(r.states.min()),'minimo_transferencia':float(r.transfers.min()),
            'X4_no_decreciente':bool((np.diff(r.states[:,3])>=0).all()),
            'NRMSE_numerico_maximo':float(np.max(np.sqrt(np.mean(diff[1:]**2,axis=0))/scales4))})
        trajectories.append(r)
        print('Control RK4:',numeric[-1],flush=True)
    convergence=[]
    for a,b in ((0,1),(1,2)):
        diff=trajectories[a].states-trajectories[b].states
        convergence.append({'h_grueso':numeric[a]['h_horas'],'h_fino':numeric[b]['h_horas'],
            'max_diferencia':float(np.max(np.abs(diff))),
            'NRMSE_por_estado':(np.sqrt(np.mean(diff[1:]**2,axis=0))/scales4).tolist(),
            'max_diferencia_transferencias':float(np.max(np.abs(trajectories[a].transfers-trajectories[b].transfers)))})
    for row in convergence:
        assert row['max_diferencia']<=.1 and max(row['NRMSE_por_estado'])<=.001
    chosen=trajectories[0];recommended_substeps=4
    agents,model=simulate_agentpy(data.observed[0],data.arrivals,p,recommended_substeps)
    np.testing.assert_array_equal(chosen.states,agents.states)
    np.testing.assert_array_equal(chosen.transfers,agents.transfers)
    print('AgentPy: igualdad exacta con RK4 en entrenamiento completo',flush=True)
    allmetrics=level_metrics(data,chosen.states)
    flowmetrics=metrics(data.flows,chosen.transfers,['aprobaciones','despachos','entregas'])
    diagnostics=calendar_diagnostics(data.cuts[1:],data.observed[1:,:3],chosen.states[1:,:3])
    allmetrics.to_csv(out/'metricas_entrenamiento.csv',index=False)
    flowmetrics.to_csv(out/'metricas_transferencias_entrenamiento.csv',index=False)
    pd.concat([prefix_metrics,internal_metrics]).to_csv(out/'metricas_evaluacion_interna.csv',index=False)
    diagnostics.to_csv(out/'diagnostico_calendario_entrenamiento.csv',index=False)
    preliminary.to_csv(out/'estimaciones_exposicion_entrenamiento.csv',index=False)
    pd.DataFrame(numeric).to_csv(out/'convergencia_parametros_calibrados.csv',index=False)
    comparison=pd.DataFrame({'corte_horario':data.cuts})
    for i in range(4):
        comparison[f'X{i+1}_observado']=data.observed[:,i]
        comparison[f'X{i+1}_simulado']=chosen.states[:,i]
    comparison.to_csv(out/'trayectoria_entrenamiento_calibrada.csv',index=False)
    # Resumen de criterios descriptivos prefijados de fase 2, sin reajustar umbrales.
    criterion_rows=[]
    for table,label in ((allmetrics,'entrenamiento_total'),(internal_metrics,'evaluacion_interna')):
        for row in table.iloc[:3].itertuples(index=False):
            criterion_rows.append({'periodo':label,'variable':row.variable,'NMAE_menor_020':row.NMAE<=.20,
                'NRMSE_menor_030':row.NRMSE<=.30,
                'pico_error_menor_20pct':row.error_nivel_maximo_absoluto<=max(1,.2*row.maximo_observado),
                'error_final_menor_20pct_escala':abs(row.error_final)<=max(1,.2*row.escala)})
    criteria=pd.DataFrame(criterion_rows)
    criteria.to_csv(out/'criterios_diagnostico_entrenamiento.csv',index=False)
    source_hash=hashlib.sha256()
    for array in (data.cuts.asi8,data.arrivals,data.observed,data.flows):
        source_hash.update(np.ascontiguousarray(array).tobytes())
    initial_table=pd.DataFrame([run for _,run in runs])
    initial_table[['initial_factor','cost_half_sse','mean_normalized_squared_error','nfev','njev',
                   'actual_residual_calls','success','status','optimality','seconds']].to_csv(out/'optimizaciones_entrenamiento.csv',index=False)
    nearzero=[]
    for i,name in enumerate(['alpha','beta','gamma']):
        for value in (0.,1e-8):
            candidate=p.array();candidate[i]=value
            rv=residual_vector(candidate,data)
            nearzero.append({'coeficiente':name,'valor':value,'MSE_normalizado':float(np.mean(rv**2))})
    pd.DataFrame(nearzero).to_csv(out/'diagnostico_frontera_cero.csv',index=False)
    code_hash={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in
        [ROOT/'src/calibration.py',ROOT/'src/calibration_metrics.py',ROOT/'src/rk4_solver.py',ROOT/'src/simulation_engine.py',ROOT/'src/agent_model.py',Path(__file__).resolve()]}
    metadata={'phase':'4A','alpha':float(p.alpha),'beta':float(p.beta),'gamma':float(p.gamma),
        'units':'1/hora','interpretation':'coeficientes efectivos de modelo agregado; no capacidades físicas',
        'period':{'start':str(data.cuts[0]),'end':str(data.cuts[-1]),'intervals':len(data.arrivals)},
        'initial_state':data.observed[0].tolist(),'scales_pending':data.scales.tolist(),
        'training_array_sha256':source_hash.hexdigest(),'code_sha256':code_hash,
        'method':'scipy.optimize.least_squares TRF; trayectoria expm de mismas EDO; RK4 y AgentPy para reproducción definitiva',
        'optimizer_configuration':{'bounds':[0,'Infinity'],'jac':'3-point','x_scale':'jac','loss':'linear',
            'ftol':1e-10,'xtol':1e-10,'gtol':1e-10,'max_nfev':200,'initial_factors':[.5,1,2]},
        'preliminary_exposure':preliminary.to_dict(orient='records'),
        'selected_optimizer':info,'all_training_runs':[i for _,i in runs],
        'internal':{'split':str(prefix.cuts[-1]),'fit_intervals':len(prefix.arrivals),
            'evaluation_intervals':len(internal.arrivals),'evaluation_propagator':'RK4, h=0.25 horas','prefix_fit':prefix_info,
            'prefix_runs':[i for _,i in prefix_runs],'posterior_diagnostic_refit':suffix_info,
            'posterior_runs':[i for _,i in suffix_runs]},
        'numeric':numeric,'grid_comparisons':convergence,'recommended_substeps':recommended_substeps,
        'recommended_h_hours':1/recommended_substeps,'agentpy_states_exact':True,'agentpy_transfers_exact':True,
        'final_validation_evaluated':False,'versions':{'python':platform.python_version(),'numpy':np.__version__,
            'scipy':scipy.__version__,'pandas':pd.__version__,'agentpy':agentpy.__version__},
        'total_seconds':time.perf_counter()-overall}
    (out/'parametros_calibrados.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    # Gráficas sin suavizado: se utilizan todos los cortes horarios del entrenamiento.
    y=data.observed.copy();x=chosen.states.copy();y[:,3]-=y[0,3];x[:,3]-=x[0,3]
    for i,label in enumerate(['T1: pendientes de aprobación','T2: pendientes de despacho',
                               'T3: pendientes de entrega','T4: entregas incrementales','P: total de pendientes']):
        observed=y[:,i] if i<4 else y[:,:3].sum(axis=1)
        simulated=x[:,i] if i<4 else x[:,:3].sum(axis=1)
        fig,ax=plt.subplots(figsize=(13,4.5))
        ax.plot(data.cuts,observed,label='Observado',linewidth=.8,color='#334155')
        ax.plot(data.cuts,simulated,label='Simulado RK4 calibrado',linewidth=.8,color='#e76f00',alpha=.85)
        ax.set_title(f'{label} — entrenamiento (2016-09-15 a 2018-03-02)')
        ax.set_xlabel('Fecha del proceso');ax.set_ylabel('Pedidos');ax.legend();ax.grid(alpha=.2)
        fig.tight_layout();fig.savefig(figures/f'{["T1","T2","T3","T4_incremental","pendientes"][i]}.png',dpi=150);plt.close(fig)
    # Semana prefijada del último bloque de entrenamiento, sin selección por calidad de ajuste.
    mask=(data.cuts>=pd.Timestamp('2018-02-01'))&(data.cuts<pd.Timestamp('2018-02-08'))
    fig,axes=plt.subplots(3,1,figsize=(13,9),sharex=True)
    for i,ax in enumerate(axes):
        ax.plot(data.cuts[mask],y[mask,i],label='Observado',linewidth=1)
        ax.plot(data.cuts[mask],x[mask,i],label='RK4 calibrado',linewidth=1)
        ax.set_ylabel(f'X{i+1} (pedidos)');ax.legend();ax.grid(alpha=.2)
    axes[-1].set_xlabel('Fecha del proceso');fig.suptitle('Entrenamiento: ampliación 1–7 febrero de 2018, sin suavizado')
    fig.tight_layout();fig.savefig(figures/'semana_febrero_2018.png',dpi=150);plt.close(fig)
    # Informe generado con resultados de esta ejecución, no cifras copiadas manualmente.
    param_table=pd.DataFrame({'coeficiente':['alpha','beta','gamma'],'inicial_exposicion':preliminary.tasa_inicial,
        'ajustado':p.array(),'ajuste_interno':prefix_p.array(),'reajuste_bloque_posterior':suffix_p.array(),
        'cambio_bloques_pct':100*(suffix_p.array()/prefix_p.array()-1)})
    names=['X1','X2','X3']
    diagnosis=[]
    for name in names:
        row=allmetrics.loc[allmetrics.variable==name].iloc[0]
        months=diagnostics.loc[(diagnostics.variable==name)&(diagnostics.grupo=='mes')]
        hours=diagnostics.loc[(diagnostics.variable==name)&(diagnostics.grupo=='hora')]
        weekdays=diagnostics.loc[(diagnostics.variable==name)&(diagnostics.grupo=='dia_semana')]
        diagnosis.append(f'- {name}: sesgo medio {row.sesgo_medio:.3f} pedidos; NMAE={row.NMAE:.3f}, NRMSE={row.NRMSE:.3f}. Sesgos mensuales entre {months.sesgo_medio.min():.3f} y {months.sesgo_medio.max():.3f}; por hora entre {hours.sesgo_medio.min():.3f} y {hours.sesgo_medio.max():.3f}; por día semanal entre {weekdays.sesgo_medio.min():.3f} y {weekdays.sesgo_medio.max():.3f}.')
    worst=allmetrics.iloc[:3].sort_values('NRMSE',ascending=False).iloc[0].variable
    spread=np.ptp(np.array([v.array() for v,_ in runs]),axis=0)/p.array()
    report=f'''# Calibración del modelo — fase 4A

## Objetivo y población
Estimar tres coeficientes efectivos de primer orden que reproduzcan X1–X3. Se conservan las cuatro EDO de fase 2, el motor RK4 y cuatro agentes de fase 3. Los resultados describen ajuste en entrenamiento, no validación predictiva final ni capacidades físicas de Olist.

Se usaron exclusivamente {len(data.arrivals)} intervalos horarios desde {data.cuts[0]} hasta {data.cuts[-1]}, y {len(data.cuts)} estados incluidos los iniciales. Estado inicial leído: {data.observed[0].tolist()}. Compras integradas: {data.arrivals.sum():.0f}; A final: {data.observed[-1].sum():.0f}. Se verificaron mallas iguales, fechas únicas, orden horario, flujos/acumulados coherentes y extremo derecho de cada intervalo.

El lector de calibración limita nrows=12804 antes de cualquier análisis; no carga las filas horarias reservadas. No usa el lector general que verifica la malla completa. La membresía de la cohorte ya fue elegida retrospectivamente por entregas completas: se mantiene ese sesgo y no se afirma validación prospectiva. En los timestamps originales, las fechas posteriores al corte se censuran antes de convertirlas o calcular duraciones. Los pedidos aún pendientes aportan exposición hasta el corte, sin su fecha futura de salida. Las pruebas antiguas siguen comprobando integridad global, pero ningún resultado de reserva entra al ajuste o diagnóstico de esta fase.

## Estimación preliminar por exposición
Para cada etapa: k0=transferencias observadas / exposición exacta. La exposición es Σ max(0,min(salida,corte)−max(entrada,inicio)), en horas, sólo para entradas ya observadas; si no hay salida observada se usa el corte. Esto es una razón de conteos/exposición, compatible con un estimador de riesgo exponencial bajo supuestos, no el mínimo cuadrado de flujos por intervalo ni el inverso de una mediana. Eventos simultáneos pueden aportar transferencia sin duración positiva; la exposición agregada de las tres etapas es informativa.

{markdown(preliminary)}

Las transferencias de esta tabla coinciden exactamente con las sumas del CSV horario de entrenamiento.

## Método y reproducibilidad
Se utilizó scipy.optimize.least_squares, método TRF, pérdida lineal de residuos (X_sim−X_obs)/s_i, con s_i=max(1,media de X_i en los N cortes objetivo de entrenamiento). Escalas: {data.scales.tolist()}. Se excluye la fila inicial de la pérdida. Cada etapa aporta N residuos; X4 no entra. La función minimizada por SciPy es 0,5·Σr²; MSE normalizado=Σr²/(3N), proporcional al objetivo académico.

Cotas 0≤α,β,γ<∞: la no negatividad tiene justificación física y no hay cota superior arbitraria. Las exploraciones de coeficientes nulos usan el propagador bien definido sin invertir matrices. Con tasa cero se bloquea una transición y puede acumularse carga. Los valores ajustados no están en frontera (active_mask={info['active_mask']}); el diagnóstico de cero y 1e−8 se guarda en diagnostico_frontera_cero.csv, sin modificar los otros parámetros y sin constituir perfiles reoptimizados.

Tolerancias ftol=xtol=gtol=1e−10; jacobiano por diferencias centrales, x_scale=jac, max_nfev=200. Inicializaciones prefijadas: 0,5, 1 y 2 veces tasas de exposición del subperíodo correspondiente. Se elige el menor costo entre convergencias satisfactorias. No se usaron coeficientes artificiales de pruebas.

{markdown(param_table)}

Todos los coeficientes están en hora⁻¹.

{markdown(initial_table[['initial_factor','cost_half_sse','mean_normalized_squared_error','nfev','njev','actual_residual_calls','success','status','optimality','seconds']])}

La ejecución seleccionada terminó con: `{info['message']}`. Costo={info['cost_half_sse']:.9g}; MSE normalizado={info['mean_normalized_squared_error']:.9g}. El criterio de parada no demuestra óptimo global. Dispersión relativa pico a pico entre soluciones de las tres inicializaciones: {spread.tolist()}. Los detalles de iniciales/finales, mensajes, versiones, tiempos, metadatos y huellas de código/arrays de entrenamiento están en parametros_calibrados.json. nfev no incluye todas las evaluaciones de diferencias finitas; se registran también llamadas reales.

## Propagador auxiliar y reproducción definitiva
La matriz lineal se construye evaluando rhs existente sobre vectores base. Se aumenta a 5×5 para la entrada constante y se calcula una exponencial por conjunto de parámetros. Se aplica causalmente x[k+1]=F x[k]+g compras[k]. lfilter ejecuta las recurrencias triangulares; no suaviza datos ni reduce intervalos. Es la solución de las mismas EDO por tramos, exacta salvo redondeo. Se contrastó con RK4 en pruebas artificiales y en todo el entrenamiento. Las trayectorias definitivas, métricas y gráficas usan RK4 con h=0,25 y AgentPy produjo exactamente los mismos niveles y transferencias. No se imponen transferencias históricas durante la simulación.

## Métricas de entrenamiento (reproducción RK4)
Errores firmados=simulado−observado. NMAE/NRMSE usan las medias observadas sólo de entrenamiento (mínimo 1); X4 usa entregas incrementales y P usa su propia escala. Error de máximo compara amplitudes máximas, mientras error absoluto máximo compara instantes iguales. Todas las métricas absolutas se expresan en pedidos.

{markdown(allmetrics)}

### Transferencias integradas por hora
Comparación de las cuadraturas RK4 con conteos observados de cada hora, sin imponerlos como entradas. Unidades absolutas: pedidos por intervalo de una hora (mismo valor numérico que tasa media en pedidos/hora).

{markdown(flowmetrics)}

## Evaluación cronológica interna
Se fijó m=floor(0,8·12803)={m}. Ajuste inicial: {prefix.cuts[0]} a {prefix.cuts[-1]}, {len(prefix.arrivals)} intervalos. Evaluación interna posterior: {internal.cuts[0]} a {internal.cuts[-1]}, {len(internal.arrivals)} intervalos. Se inicializó una vez desde el estado observado de ese corte, con compras conocidas; no se corrigió la trayectoria con estados posteriores. Escalas de ambos bloques fijadas en el ajuste inicial. Este experimento no es pronóstico de demanda.

{markdown(pd.concat([prefix_metrics,internal_metrics]))}

La predicción del bloque interno usa sólo parámetros del bloque inicial. Adicionalmente se reajustó el bloque posterior exclusivamente como diagnóstico de estabilidad; esos coeficientes y su cambio porcentual aparecen en la tabla de parámetros. No se utilizaron para corregir su evaluación fuera de ajuste. El bloque posterior deja de ser una prueba independiente para futuras decisiones de diseño. Tras este diagnóstico se recalibró todo el 70 %, manteniendo ecuaciones, pérdida e hiperparámetros prefijados. Ninguna fila del 30 % reservado fue evaluada.

## Diagnóstico del modelo de primer orden
{chr(10).join(diagnosis)}

La mayor dificultad relativa, medida por NRMSE por etapa, corresponde a **{worst}**. Los errores absolutos deben compararse también porque las escalas de las etapas difieren. Los residuos desagregados por mes, hora y día (0=lunes) están en diagnostico_calendario_entrenamiento.csv. Las diferencias calendario son descriptivas, sin prueba causal ni significación estadística asumida.

El supuesto de aprobación homogénea de riesgo constante puede fallar ante aprobaciones casi inmediatas junto con esperas largas: la entrada uniforme dentro de cada hora también pierde orden intrahorario. Sesgos de X2 y X3 que cambian con el período son compatibles con calendario operativo, heterogeneidad y coeficientes no estacionarios; son hipótesis para investigar, no causas demostradas. No se cambió la estructura matemática para mejorar artificialmente el ajuste.

Identificabilidad local: valores singulares del jacobiano escalado por parámetros {info['scaled_jacobian_singular_values']}, condición {info['scaled_jacobian_condition']:.6g}. Rango tres y condición moderada apoyan sensibilidad local diferenciable de las tres tasas; la estabilidad entre inicializaciones aporta evidencia adicional. No demuestran identificabilidad global, ausencia de sesgo ni parámetros físicos únicos. Hay autocorrelación y heterogeneidad; no se presentan intervalos de confianza basados en errores independientes.

## Controles numéricos con parámetros finales
{markdown(pd.DataFrame(numeric))}

Comparaciones entre mallas: `{json.dumps(convergence,ensure_ascii=False)}`.

Ambas comparaciones cumplen máximo ≤0,1 pedido y NRMSE≤0,001 por estado con escalas de entrenamiento. La estabilidad lineal, positividad de todas las etapas internas, finitud, X4 no decreciente y flujos no negativos se verificaron en cada corrida. No se recortaron estados. Los errores de conservación cumplen 1e−8·max(1,total). Recomendación numérica: **h=0,25 horas, cuatro subpasos por hora**, que también presenta discrepancia pequeña frente al propagador analítico. Los parámetros no se cambiaron para satisfacer controles.

## Gráficas y archivos
En graficas_calibracion/: T1.png, T2.png, T3.png, T4_incremental.png y pendientes.png comparan todos los cortes históricos con RK4 calibrado, sin suavizado. semana_febrero_2018.png amplía una semana fijada por calendario dentro de entrenamiento. Cada gráfica identifica entrenamiento, fechas, unidad pedidos y ambas curvas. La trayectoria completa y las tablas auxiliares se exportan sin sobrescribir datos históricos.

## Decisión y limitaciones
Se conserva este modelo como referencia calibrada, con limitaciones descriptivas explícitas; no se declara precisión suficiente sólo por convergencia del optimizador. Deben revisarse los errores por etapa y el bloque interno antes de tratarlo como modelo predictivo adecuado. Se recomiendan para una fase posterior contrastes de riesgo dependiente de edad y calendario, particularmente en aprobación, sin implementarlos aquí. La validación final, si se autoriza, debe hacerse con estos parámetros congelados como referencia y sin volver a escogerlos con ese 30 %; si se revisa la estructura antes, se requiere repetir desarrollo y mantener intacta esa reserva.

No hay cancelaciones fechadas, capacidades, costos ni seguimiento individual bajo alternativas. La selección retrospectiva de 95.082 entregados impide interpretar esto como inventario operativo completo. La entrada histórica conocida no constituye un pronóstico de compras. No se ejecutaron validación final, escenarios ni interfaz. Tiempo de cálculo previo a gráficos/informe: {metadata['total_seconds']:.3f} s. Las pruebas automáticas se registran separadamente en pruebas_calibracion.txt.

## Reproducir
```powershell
.venv/Scripts/python.exe scripts/calibrar_modelo.py
.venv/Scripts/python.exe -m pytest -q
```

Referencias de implementación: [least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html), [expm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html) y [lfilter](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html). Se aplican a las versiones fijadas del entorno, que constan en el JSON.
'''
    (out/'calibracion_modelo.md').write_text(report,encoding='utf-8')
    print(allmetrics.to_string(index=False),flush=True)
    print('Evaluación interna:',internal_metrics.to_string(index=False),flush=True)
    print('Informe y JSON guardados; reserva final sin evaluar.',flush=True)

if __name__=='__main__':
    main()
