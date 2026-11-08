"""Compara exclusivamente base y aprobación rápida dentro del desarrollo."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import json
import hashlib
import platform
import subprocess
import time
import numpy as np
import pandas as pd
import scipy
import agentpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.calibration import load_training,exposure_estimates,multistart_fit,analytical_trajectory
from src.rapid_calibration import (development_windows,candidate_multistart,fit_candidate,
    percent_improvement,assess_selection,PROFILE_P)
from src.rk4_solver import Parameters,RapidParameters,check_stability
from src.simulation_engine import simulate
from src.agent_model import simulate_agentpy
from src.calibration_metrics import level_metrics,metrics
from scripts.calibrar_modelo import markdown


def scales5(data):
    return np.r_[data.scales,max(1,np.mean(data.observed[1:,3]-data.observed[0,3])),
                  max(1,np.mean(data.observed[1:,:3].sum(axis=1)))]


def flow_totals(result):
    flows=result.transfers.copy()
    flows[:,0]+=result.rapid_arrivals
    return flows


def numerical_summary(result,parameters,substeps,label):
    check_stability(parameters,1/substeps)
    return {'caso':label,'subpasos':substeps,'h_horas':1/substeps,
        'error_conservacion_max':result.max_conservation_error,
        'minimo_estado':float(result.states.min()),'minimo_transferencia':float(result.transfers.min()),
        'minimo_entrada_rapida':float(result.rapid_arrivals.min()),
        'X4_no_decrece':bool((np.diff(result.states[:,3])>=0).all())}


def main():
    clock=time.perf_counter()
    out=ROOT/'reports';figdir=out/'graficas_comparacion';figdir.mkdir(exist_ok=True)
    base_path=out/'parametros_calibrados.json'
    original_bytes=base_path.read_bytes();original=json.loads(original_bytes)
    protected_hash=hashlib.sha256(original_bytes).hexdigest()
    data=load_training(ROOT/'data/processed')
    original_p=Parameters(*(original[k] for k in ['alpha','beta','gamma']))
    design=development_windows(data)  # Fijado antes de ajustar candidato.
    design_table=pd.DataFrame([{'ventana':name,'inicio_ajuste':str(fit.cuts[0]),
        'fin_ajuste_inicio_evaluacion':str(test.cuts[0]),'fin_evaluacion':str(test.cuts[-1]),
        'intervalos_ajuste':len(fit.arrivals),'intervalos_evaluacion':len(test.arrivals)} for name,fit,test in design])
    design_table.to_csv(out/'ventanas_comparacion.csv',index=False)
    allmetrics=[];allflows=[];numerics=[];fits=[];gains=[];evaluations=[]
    windows_parameters=[]
    events=ROOT/'data/processed/pedidos_limpios.csv'
    for name,train,test in design:
        preliminary=exposure_estimates(events,train.cuts[0],train.cuts[-1]).tasa_inicial.to_numpy()
        (bp,bi),bruns=multistart_fit(train,preliminary)
        (cp,ci),cruns=candidate_multistart(train,preliminary)
        windows_parameters.append(ci)
        fits.append({'window':name,'base':bi,'base_all_starts':[i for _,i in bruns],
            'candidate':ci,'candidate_all_starts':[i for _,i in cruns]})
        scales=scales5(train);flow_scales=np.maximum(1,train.flows.mean(axis=0))
        eval_results={}
        for model,p in [('base',bp),('candidate',cp)]:
            for period,part in [('ajuste',train),('evaluacion_interna',test)]:
                result=simulate(part.observed[0],part.arrivals,p,4)
                numerical=numerical_summary(result,p,4,f'{name}_{period}_{model}')
                analytical=analytical_trajectory(part.observed[0],part.arrivals,p)
                numerical['error_max_vs_analitico']=float(np.max(np.abs(result.states-analytical)))
                assert numerical['error_max_vs_analitico']<.1
                numerics.append(numerical)
                table=level_metrics(part,result.states,scales)
                table['modelo']=model;table['ventana']=name;table['periodo']=period
                allmetrics.append(table)
                tablef=metrics(part.flows,flow_totals(result),['aprobaciones_totales','despachos','entregas'],flow_scales)
                tablef['modelo']=model;tablef['ventana']=name;tablef['periodo']=period
                allflows.append(tablef)
                if period=='evaluacion_interna':
                    agents,agent_model=simulate_agentpy(part.observed[0],part.arrivals,p,4)
                    np.testing.assert_array_equal(result.states,agents.states)
                    np.testing.assert_array_equal(result.transfers,agents.transfers)
                    np.testing.assert_array_equal(result.rapid_arrivals,agents.rapid_arrivals)
                    eval_results[model]=(result,table)
        improvements=[]
        for variable in ['X1','X2','X3']:
            base_value=float(eval_results['base'][1].set_index('variable').loc[variable,'NRMSE'])
            candidate_value=float(eval_results['candidate'][1].set_index('variable').loc[variable,'NRMSE'])
            gain=percent_improvement(base_value,candidate_value)
            if gain is None:
                raise RuntimeError('Empeoramiento desde error cero; comparación porcentual indefinida')
            improvements.append(gain)
        gains.append({'ventana':name,'mejora_X1_pct':improvements[0],'mejora_X2_pct':improvements[1],
                       'mejora_X3_pct':improvements[2]})
        evaluations.append((name,test,eval_results))
        print(name, 'candidate=',cp.full_array(),'mejoras internas %=',improvements,flush=True)
    # Ajustes completos, sin tocar el archivo del modelo base de fase 4A.
    preliminary_full=exposure_estimates(events,data.cuts[0],data.cuts[-1]).tasa_inicial.to_numpy()
    (candidate,ci),candidate_runs=candidate_multistart(data,preliminary_full)
    candidate_analytical=analytical_trajectory(data.observed[0],data.arrivals,candidate)
    candidate_trajectories=[];convergence=[]
    scale4=scales5(data)[:4]
    for n in (4,8,16):
        result=simulate(data.observed[0],data.arrivals,candidate,n)
        candidate_trajectories.append(result)
        record=numerical_summary(result,candidate,n,'candidato_desarrollo_completo')
        record['error_max_vs_analitico']=float(np.max(np.abs(result.states-candidate_analytical)))
        numerics.append(record)
    for i in (0,1):
        difference=candidate_trajectories[i].states-candidate_trajectories[i+1].states
        normalized=np.sqrt(np.mean(difference[1:]**2,axis=0))/scale4
        row={'h_grueso':1/(4*2**i),'h_fino':1/(8*2**i),'max_diferencia':float(np.max(np.abs(difference))),
             'NRMSE_por_estado':normalized.tolist()}
        assert row['max_diferencia']<=.1 and (normalized<=.001).all()
        convergence.append(row)
    full_candidate=candidate_trajectories[0]
    agents,model=simulate_agentpy(data.observed[0],data.arrivals,candidate,4)
    np.testing.assert_array_equal(agents.states,full_candidate.states)
    np.testing.assert_array_equal(agents.transfers,full_candidate.transfers)
    np.testing.assert_array_equal(agents.rapid_arrivals,full_candidate.rapid_arrivals)
    gains_table=pd.DataFrame(gains)
    selection=assess_selection(gains_table[['mejora_X1_pct','mejora_X2_pct','mejora_X3_pct']].to_numpy(),windows_parameters,True)
    # Recalibración final del seleccionado después de la comparación interna.
    if selection['selected_model']=='base':
        (selected,selected_info),selected_runs=multistart_fit(data,preliminary_full)
    else:
        (selected,selected_info),selected_runs=candidate_multistart(data,preliminary_full)
    # Reproducción de referencia con parámetros originales conservados.
    full_base=simulate(data.observed[0],data.arrivals,original_p,4)
    zero=simulate(data.observed[0],data.arrivals,RapidParameters(*original_p.array(),0.),4)
    np.testing.assert_array_equal(zero.states,full_base.states)
    np.testing.assert_array_equal(zero.transfers,full_base.transfers)
    stored=pd.read_csv(out/'trayectoria_entrenamiento_calibrada.csv')
    old_states=stored[[f'X{i}_simulado' for i in range(1,5)]].to_numpy()
    regression_error=float(np.max(np.abs(old_states-full_base.states)))
    np.testing.assert_allclose(old_states,full_base.states,rtol=0,atol=1e-9)
    numerics.append(numerical_summary(full_base,original_p,4,'base_original_desarrollo_completo'))
    for label,result in [('base',full_base),('candidate',full_candidate)]:
        table=level_metrics(data,result.states,scales5(data))
        table['modelo']=label;table['ventana']='desarrollo_completo';table['periodo']='ajuste_completo'
        allmetrics.append(table)
        table=metrics(data.flows,flow_totals(result),['aprobaciones_totales','despachos','entregas'],np.maximum(1,data.flows.mean(axis=0)))
        table['modelo']=label;table['ventana']='desarrollo_completo';table['periodo']='ajuste_completo'
        allflows.append(table)
    profile=[]
    for fraction in PROFILE_P:
        pp,ii=fit_candidate(data,candidate.full_array(),fixed_p=fraction)
        profile.append({'p_fijo':fraction,'MSE_normalizado':ii['mean_normalized_squared_error'],
            'alpha':float(pp.alpha),'beta':float(pp.beta),'gamma':float(pp.gamma),
            'success':ii['success'],'nfev':ii['nfev'],'seconds':ii['seconds']})
    # Evidencia sobre tiempos sólo de aprobaciones ya observadas en desarrollo.
    dates=pd.read_csv(events,usecols=['order_purchase_timestamp','order_approved_at'],dtype=str)
    observed=dates.loc[dates.order_approved_at.le(str(data.cuts[-1]))].copy()
    durations=(pd.to_datetime(observed.order_approved_at)-pd.to_datetime(observed.order_purchase_timestamp)).dt.total_seconds()/3600
    approval_evidence={'completed_approvals':len(durations),'median_hours':float(durations.median()),
        'fraction_under_1h':float((durations<=1).mean()),'fraction_zero':float((durations==0).mean()),
        'p95_hours':float(durations.quantile(.95))}
    comparison=pd.concat(allmetrics,ignore_index=True);flow_comparison=pd.concat(allflows,ignore_index=True)
    comparison.to_csv(out/'comparacion_modelos.csv',index=False)
    flow_comparison.to_csv(out/'comparacion_flujos_modelos.csv',index=False)
    gains_table.to_csv(out/'mejoras_ventanas_modelos.csv',index=False)
    pd.DataFrame(numerics).to_csv(out/'controles_numericos_comparacion.csv',index=False)
    pd.DataFrame(profile).to_csv(out/'perfil_p_aprobacion_rapida.csv',index=False)
    # Trayectoria completa separada, sin sobrescribir salidas históricas ni base.
    trajectory=pd.DataFrame({'corte_horario':data.cuts})
    for i in range(4):
        trajectory[f'X{i+1}_base']=full_base.states[:,i]
        trajectory[f'X{i+1}_candidato']=full_candidate.states[:,i]
    trajectory.to_csv(out/'trayectorias_comparacion_desarrollo.csv',index=False)
    flow_trajectory=pd.DataFrame({'corte_horario':data.cuts[1:],
        'compras':data.arrivals,'entrada_T1':data.arrivals-full_candidate.rapid_arrivals,
        'entrada_rapida_T2':full_candidate.rapid_arrivals,'q12_integrado':full_candidate.transfers[:,0],
        'aprobaciones_totales':flow_totals(full_candidate)[:,0],
        'q23_integrado':full_candidate.transfers[:,1],'q34_integrado':full_candidate.transfers[:,2]})
    flow_trajectory.to_csv(out/'flujos_candidato_desarrollo.csv',index=False)
    metadata={'alpha':float(candidate.alpha),'beta':float(candidate.beta),'gamma':float(candidate.gamma),'p':float(candidate.p),
        'units':{'alpha':'1/hora','beta':'1/hora','gamma':'1/hora','p':'adimensional'},
        'period':{'start':str(data.cuts[0]),'end':str(data.cuts[-1]),'intervals':len(data.arrivals)},
        'scales':data.scales.tolist(),'selected_optimizer':ci,'all_starts':[i for _,i in candidate_runs],
        'window_design':design_table.to_dict(orient='records'),'window_fits':fits,'selection':selection,
        'convergence':convergence,'profile':profile,'approval_duration_evidence':approval_evidence,
        'base_parameters_file_sha256':protected_hash,'base_reproduction_max_difference':regression_error,
        'versions':{'python':platform.python_version(),'scipy':scipy.__version__,'numpy':np.__version__,
                    'pandas':pd.__version__,'agentpy':agentpy.__version__},
        'optimizer_configuration':{'method':'TRF','bounds_rates':[0,'Infinity'],'bounds_p':[0,1],
            'jac':'3-point','x_scale':'jac','loss':'linear','ftol':1e-10,'xtol':1e-10,'gtol':1e-10,'max_nfev':200,
            'rate_factors':[.5,1,2],'p_initials':[0,.5,.9]},
        'recommended_h_hours':.25,'agentpy_exact':True,'p0_exact':True,'final_validation_evaluated':False,
        'seconds_before_plots':time.perf_counter()-clock,
        'code_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [ROOT/'src/rapid_calibration.py',ROOT/'src/rk4_solver.py',ROOT/'src/simulation_engine.py',ROOT/'src/agent_model.py',ROOT/'docs/modelo_aprobacion_rapida.md',Path(__file__).resolve()]}}
    (out/'parametros_aprobacion_rapida.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    selected_metadata={'model':selection['selected_model'],'parameters':selected_info['parameters'],
        'units':['1/hora','1/hora','1/hora']+(['adimensional'] if selection['selected_model']=='candidate' else []),
        'period':metadata['period'],'optimizer':selected_info,'all_starts':[i for _,i in selected_runs],
        'selection':selection,'final_validation_evaluated':False}
    (out/'modelo_seleccionado_desarrollo.json').write_text(json.dumps(selected_metadata,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    # Visualizaciones sin suavizado, con separación explícita de ajuste y evaluación.
    for i,name in enumerate(['X1','X2','X3','P']):
        fig,ax=plt.subplots(figsize=(13,4.5))
        yy=data.observed[:,i] if i<3 else data.observed[:,:3].sum(axis=1)
        bb=full_base.states[:,i] if i<3 else full_base.states[:,:3].sum(axis=1)
        cc=full_candidate.states[:,i] if i<3 else full_candidate.states[:,:3].sum(axis=1)
        ax.plot(data.cuts,yy,label='Observado',color='#334155',lw=.8)
        ax.plot(data.cuts,bb,label='Base calibrado',color='#dd6b20',lw=.8)
        ax.plot(data.cuts,cc,label='Candidato calibrado',color='#16805d',lw=.8)
        ax.set(title=f'{name} — ajuste con todo el desarrollo (2016-09-15 a 2018-03-02)',xlabel='Fecha',ylabel='Pedidos')
        ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(figdir/f'{name}_ajuste.png',dpi=140);plt.close(fig)
        fig,ax=plt.subplots(figsize=(13,4.5))
        for k,(window,part,results) in enumerate(evaluations):
            yy=part.observed[:,i] if i<3 else part.observed[:,:3].sum(axis=1)
            ax.plot(part.cuts,yy,label='Observado' if k==0 else None,color='#334155',lw=.8)
            for label,color in [('base','#dd6b20'),('candidate','#16805d')]:
                states=results[label][0].states
                values=states[:,i] if i<3 else states[:,:3].sum(axis=1)
                ax.plot(part.cuts,values,label=label if k==0 else None,color=color,lw=.8)
            ax.axvline(part.cuts[0],color='gray',ls=':',lw=.7)
            ax.text(part.cuts[len(part.cuts)//2],.97,window,transform=ax.get_xaxis_transform(),ha='center',va='top')
        ax.set(title=f'{name} — cuatro evaluaciones internas, ajuste expansivo previo a cada origen',xlabel='Fecha de evaluación interna',ylabel='Pedidos')
        ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(figdir/f'{name}_evaluacion_interna.png',dpi=140);plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(13,8),sharex=True)
    for i,ax in enumerate(axes):
        for k,(window,part,results) in enumerate(evaluations):
            for label,color in [('base','#dd6b20'),('candidate','#16805d')]:
                error=results[label][0].states[:,i]-part.observed[:,i]
                ax.plot(part.cuts,error,label=label if k==0 else None,color=color,lw=.6)
            ax.axvline(part.cuts[0],color='gray',ls=':',lw=.7)
        ax.axhline(0,color='black',lw=.5);ax.set_ylabel(f'Error X{i+1} (pedidos)');ax.legend()
    axes[0].set_title('Residuos de evaluación interna: simulado − observado; sin suavizado')
    axes[-1].set_xlabel('Fecha; parámetros congelados dentro de cada bloque, ajuste sólo en prefijo')
    fig.tight_layout();fig.savefig(figdir/'residuos_evaluacion_interna.png',dpi=140);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(13,4))
    eval_table=comparison.loc[(comparison.periodo=='evaluacion_interna')]
    for ax,var in zip(axes,['X1','X2','X3']):
        for label,color in [('base','#dd6b20'),('candidate','#16805d')]:
            rows=eval_table.loc[(eval_table.variable==var)&(eval_table.modelo==label)]
            ax.plot(rows.ventana,rows.NRMSE,marker='o',label=label,color=color)
        ax.set(title=var,xlabel='Ventana interna (fechas en tabla)',ylabel='NRMSE adimensional');ax.legend();ax.grid(alpha=.2)
    fig.suptitle('Evaluación interna: escalas del ajuste respectivo, iguales para ambos modelos')
    fig.tight_layout();fig.savefig(figdir/'NRMSE_por_ventana.png',dpi=140);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4));profile_table=pd.DataFrame(profile)
    ax.plot(profile_table.p_fijo,profile_table.MSE_normalizado,marker='o',label='Perfil: tres tasas reajustadas')
    ax.scatter([candidate.p],[ci['mean_normalized_squared_error']],label='Ajuste conjunto',color='#16805d')
    ax.set(title='Perfil de p en desarrollo completo; diagnóstico, sin reserva final',xlabel='p (adimensional)',ylabel='MSE normalizado adimensional');ax.legend();ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(figdir/'perfil_p.png',dpi=140);plt.close(fig)
    # Informe con cifras de esta ejecución, no resultados supuestos.
    param_table=pd.DataFrame([{'ventana':item['window'],'alpha':item['candidate']['parameters'][0],
        'beta':item['candidate']['parameters'][1],'gamma':item['candidate']['parameters'][2],
        'p':item['candidate']['parameters'][3],'condicion_J':item['candidate']['jacobian_condition'],
        'coseno_sensibilidad_alpha_p':item['candidate']['sensitivity_cosine_alpha_p']} for item in fits])
    full_metrics=comparison.loc[comparison.periodo=='ajuste_completo']
    relative_spread=np.ptp(np.array([p.full_array() for p,_ in candidate_runs]),axis=0)/candidate.full_array()
    report=f'''# Comparación estructural: base frente a aprobación rápida

## Alcance y protocolo
Se evaluó una sola modificación, definida en [modelo_aprobacion_rapida.md](../docs/modelo_aprobacion_rapida.md). Se mantienen cuatro estados y cuatro agentes. Las dos estructuras comparten λ histórica, unidades, condiciones iniciales y reconstrucción. Se preservó el archivo parametros_calibrados.json: SHA-256 `{protected_hash}`. El 30 % reservado permanece sin evaluar; los bloques analizados son desarrollo reutilizado, nunca prueba final independiente.

Se inspeccionaron módulos de simulación/calibración/métricas y documentos anteriores. El lector sigue limitado a las primeras 12.804 filas horarias. Timestamps futuros se censuran antes de calcular exposiciones. La cohorte fue seleccionada retrospectivamente por entrega completa: la separación temporal evita contaminación adicional, pero no elimina selección ni censura de población.

Antes de ejecutar el candidato se fijaron cuatro evaluaciones de 1920 horas con ajuste expansivo. Ambos modelos se ajustaron al mismo prefijo, congelaron parámetros y se inicializaron una sola vez con el estado observado del corte. Las escalas s_i=max(1,media del prefijo) son idénticas entre modelos. No se retocaron pérdida, ventanas ni umbrales tras ver resultados.

{markdown(design_table)}

## Hipótesis y conservación
El candidato usa entradas (1−p)λ a X1 y pλ a X2; q12=αX1 sigue siendo la transferencia convencional. Las aprobaciones totales que se comparan con datos son pλ+q12. No se cuenta dos veces la rama rápida. Al sumar las derivadas se obtiene [(1−p)+p]λ=λ. X4 es terminal y no es cola pendiente. Con p=0 las ecuaciones y las trayectorias RK4 coinciden exactamente con el base. Con p=1 y X1 inicial cero se pierde sensibilidad a α.

Sólo entre aprobaciones observadas hasta el corte: {approval_evidence['completed_approvals']} eventos, mediana {approval_evidence['median_hours']:.6g} h, P95 {approval_evidence['p95_hours']:.6g} h; fracción con tiempo≤1 h={approval_evidence['fraction_under_1h']:.3%}, tiempo cero={approval_evidence['fraction_zero']:.3%}. Son descripciones condicionadas a aprobación observada, no el valor de p ni una estimación prospectiva; las esperas incompletas aportan exposición a las inicializaciones. La coexistencia de tiempos cortos y largos motiva, pero no demuestra, la hipótesis.

## Ajuste del candidato y reproducibilidad
Coeficientes con todo el desarrollo: α={candidate.alpha:.12g} h⁻¹, β={candidate.beta:.12g} h⁻¹, γ={candidate.gamma:.12g} h⁻¹, p={candidate.p:.12g} adimensional. p es una fracción efectiva de aprobación rápida a la resolución horaria; no una instalación real, un porcentaje observado de aprobaciones instantáneas ni una mejora operativa de Olist.

SciPy least_squares TRF, residuos normalizados de X1–X3, pérdida lineal, cotas tasas [0,+∞), p [0,1], diferencias centrales y ftol=xtol=gtol=1e−10. Escalas completas: {data.scales.tolist()}. Se utilizó propagador expm auxiliar de las mismas EDO para ajustar; todas las métricas y comparaciones finales de trayectorias usan RK4. X4 no participa en la pérdida. Las tasas preliminares se calculan sólo en cada prefijo por exposición censurada. En candidato sólo inicializan, sin interpretarlas como tasas definitivas de la rama lenta.

Nueve inicios: factores de tasas {{0,5;1;2}} por p inicial {{0;0,5;0,9}}. Cada uno, con sus parámetros finales, costo, evaluaciones, llamadas reales, mensaje y tiempo se registra en parametros_aprobacion_rapida.json. Dispersión relativa pico a pico entre soluciones completas: {relative_spread.tolist()}. Terminación elegida: `{ci['message']}`; nfev={ci['nfev']}, llamadas reales={ci['actual_residual_calls']}, costo 0,5Σr²={ci['cost_half_sse']:.8g}. La terminación es convergencia local del algoritmo, no certificado de óptimo global.

### Métricas de ajuste con todo el desarrollo
Unidades absolutas: pedidos; NMAE y NRMSE son adimensionales. Error firmado=simulado−observado. X4 es incremento desde el inicio de la ventana, P suma de pendientes. El base usa sus parámetros originales congelados de fase 4A.

{markdown(full_metrics[['modelo','variable','MAE','RMSE','NMAE','NRMSE','error_absoluto_maximo','error_nivel_maximo','sesgo_medio','error_final']])}

## Resultados cronológicos internos
Mejora %=100·(1−NRMSE_candidato/NRMSE_base). Un signo negativo indica deterioro, no reducción. Las escalas en el denominador proceden sólo del ajuste de la ventana. La comparación por variable incluye X4 incremental y P en comparacion_modelos.csv; aprobaciones totales, despachos y entregas integrados en comparacion_flujos_modelos.csv.

{markdown(gains_table)}

Mediana de mejora de X1: **{selection['median_X1_improvement_percent']:.6g} %**. Menor mejora de X2/X3 entre ventanas: {selection['minimum_X2_X3_improvement_percent']}. No basta reducir error de entrenamiento porque hay un parámetro extra.

### Parámetros del candidato por prefijo
{markdown(param_table)}

Rango de p: {selection['p_range']:.6g}; cocientes máximo/mínimo de tasas: {selection['rate_max_min_ratios']}. Las diferencias temporales y de sensibilidad se consideran en la selección, sin presentar las cuatro ventanas como réplicas estadísticas independientes.

## Identificabilidad y perfil de p
Condición del jacobiano escalado completo: {ci['jacobian_condition']:.6g}; valores singulares {ci['jacobian_singular_values']}. Para tasas se usa escala del coeficiente y para p escala unitaria, incluso en p=0. Coseno entre columnas de sensibilidad α,p: {ci['sensitivity_cosine_alpha_p']:.6g}; valores cercanos a ±1 indican confusión local. Multiinicio, rango local y perfil aportan evidencia, pero no garantizan identificación global ni estabilidad bajo heterogeneidad.

El mínimo completo tiene rango local cuatro y p interior, por lo que p aporta sensibilidad distinguible en ese ajuste, con fuerte dependencia de α. No equivale a identificar una fracción física única ni a demostrar estabilidad temporal: p cambia entre los prefijos. Algunas ventanas superan la guarda de colinealidad prefijada; aun sin esa guarda secundaria, la mejora interna de X1 queda lejos del 15 % requerido.

{markdown(profile_table)}

La rejilla es diagnóstica y predefinida; cada punto reajusta únicamente tres tasas, manteniendo p fijo. p=1 hace α no identificable si X1 inicial es cero: su valor ajustado en ese punto es arbitrario y no se interpreta. No se obtienen intervalos de confianza de la rejilla ni de mínimos cuadrados con errores seriales supuestamente independientes. Véase perfil_p.png. El cambio de p frente a α puede reproducir niveles medios similares; importan las excitaciones temporales para distinguirlos.

## Controles matemáticos y numéricos
Se verificó equivalencia exacta p=0 frente al base en todo el desarrollo, además de pruebas artificiales. La reproducción del CSV antiguo difiere a lo sumo {regression_error:.6g} pedidos (redondeo de CSV). No se sobrescribió el JSON base.

Convergencia completa del candidato: `{json.dumps(convergence,ensure_ascii=False)}`.

{markdown(pd.DataFrame(numerics).loc[lambda d:d.caso.str.contains('desarrollo_completo')])}

Se cumplen los criterios de diferencia entre mallas≤0,1 pedido y NRMSE≤0,001. Se mantuvo h=0,25 h; no se alteró automáticamente. Los controles incluyen estabilidad de RK4, etapas internas no negativas, finitud, flujos convencionales/directos no negativos, X4 no decreciente y conservación con tolerancia 1e−8·max(1,total). Controles por ventana en controles_numericos_comparacion.csv. AgentPy produjo estados, transferencias convencionales y entradas rápidas exactamente iguales al motor independiente en las cuatro evaluaciones de ambos modelos y en todo el desarrollo del candidato. No se crean agentes por pedido.

## Regla de decisión y modelo recomendado
Guardas fijadas antes de calcular resultados: mediana X1≥15 %, ningún deterioro de X2/X3>10 % en ninguna ventana, controles numéricos, convergencia; rango p≤0,20, cocientes de tasas≤2, p<0,99, condición local<1000 y |coseno sensibilidad α,p|<0,98 en cada prefijo. Son criterios académicos, no estándares externos ni intervalos estadísticos.

{markdown(pd.DataFrame([{'criterio':k,'cumple':v} for k,v in selection['checks'].items()]))}

Modelo seleccionado por esta regla: **{selection['selected_model']}**. Se recalibró el seleccionado después de la comparación usando todo el 70 %, con parámetros {selected_info['parameters']}; metadatos en modelo_seleccionado_desarrollo.json. No reemplaza el archivo original base ni implica validación final. Si un criterio falla se conserva el base aunque el candidato ajuste mejor dentro de muestra.

## Visualizaciones y archivos
En graficas_comparacion/: X1/X2/X3/P_ajuste.png (todo el desarrollo ajustado); X1/X2/X3/P_evaluacion_interna.png (cuatro bloques con prefijos expansivos); residuos_evaluacion_interna.png (errores horarios sin suavizado); NRMSE_por_ventana.png y perfil_p.png. Las tablas de fechas identifican exactamente ajuste y evaluación; las líneas verticales marcan sus orígenes. Se retienen todos los cortes horarios. Las curvas simuladas pueden ser suaves por las EDO, sin filtrado visual.

comparacion_modelos.csv contiene métricas completas por variable, modelo y ventana tanto de ajuste como evaluación. Las tablas auxiliares separan flujos, mejoras, diseño, perfil, trayectorias y controles. flujos_candidato_desarrollo.csv distingue entrada_T1, entrada_rapida_T2, q12 convencional y aprobaciones totales.

## Límites antes de la validación final
Aproximar todo evento corto por aprobación inmediata pierde detalle intrahorario; p efectivo no identifica pedidos ni infraestructura. La rama lenta sigue siendo homogénea de primer orden y β,γ constantes. Calendario, edad y heterogeneidad permanecen sin representar. Se ha añadido sólo el parámetro p y ninguna variable de estado.

Una ventaja de ajuste no asegura generalización, y el desarrollo ya fue utilizado repetidamente. Debe conservarse la reserva intacta hasta revisar esta selección y congelar estructura/parámetros. La cohorte retrospectiva de entregados completos no representa el inventario total ni cancelaciones; la entrada conocida no es pronóstico de demanda. No se evalúan costos, energía, retrasos individuales, escenarios ni interfaz. Tiempo previo a gráficos: {metadata['seconds_before_plots']:.3f} s.

## Reproducción
```powershell
.venv/Scripts/python.exe scripts/comparar_modelos.py
.venv/Scripts/python.exe -m pytest -q
```
Pruebas ejecutadas y resultados en pruebas_comparacion_modelos.txt. No se afirma éxito de pruebas no ejecutadas.
'''
    (out/'comparacion_modelos.md').write_text(report,encoding='utf-8')
    assert base_path.read_bytes()==original_bytes,'Se modificó indebidamente el JSON base'
    suite=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,
                         capture_output=True,text=True,encoding='utf-8',errors='replace')
    test_output=suite.stdout+suite.stderr
    (out/'pruebas_comparacion_modelos.txt').write_text(test_output,encoding='utf-8')
    with (out/'comparacion_modelos.md').open('a',encoding='utf-8') as report_file:
        report_file.write('\n## Pruebas automáticas ejecutadas\n\n```text\n'+test_output.strip()+'\n```\n')
        report_file.write('\nLa prueba de p=1 sin contenido inicial en X1 comprueba invariancia exacta de RK4 frente a α. En expm se usa únicamente una cota de redondeo de ocho épsilon por la magnitud del estado: cambiar el bloque no utilizado produjo diferencias de 2,84×10⁻¹⁴ pedidos. Las pruebas p=0 y AgentPy continúan exigiendo igualdad exacta.\n')
    print(test_output,flush=True)
    if suite.returncode:
        raise SystemExit(suite.returncode)
    print('Candidato completo:',candidate,flush=True)
    print('Selección:',selection,flush=True)
    print(full_metrics[['modelo','variable','MAE','RMSE','NRMSE']].to_string(index=False),flush=True)
    print('Reserva final sin evaluar; base original preservado.',flush=True)

if __name__=='__main__':
    main()
