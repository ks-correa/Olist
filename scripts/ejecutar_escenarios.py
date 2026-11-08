"""Tres escenarios hipotéticos, sin calibración y sin interfaz; validez externa C."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import argparse
import hashlib
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
from src.scenarios import (load_base_parameters,load_scenario_window,run_official_scenarios,
                           check_structural,COLORS,HORIZONS)
from src.scenario_metrics import cumulative_areas,comparisons
from src.validation import sha256,START,END


LIMIT='Experimentos hipotéticos; validación del modelo categoría C; sin recomendaciones operativas para Olist.'


def markdown(table):
    table=table.copy()
    for col in table:
        if pd.api.types.is_float_dtype(table[col]):
            table[col]=table[col].map(lambda value:f'{value:.6g}')
    return '| '+' | '.join(map(str,table.columns))+' |\n|'+'|'.join(['---']*len(table.columns))+'|\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in table.itertuples(index=False,name=None))


def plot_runs(runs,window_name,figdir):
    cuts=runs[0].window.cuts
    for i,name in enumerate(['X1','X2','X3','X4_incremental','P','area_acumulada_P']):
        fig,ax=plt.subplots(figsize=(13,4.8))
        for run in runs:
            x=run.result.states
            if i<3: values=x[:,i]
            elif i==3: values=x[:,3]-x[0,3]
            elif i==4: values=x[:,:3].sum(axis=1)
            else: values=cumulative_areas(run.result.times,x[:,:3].sum(axis=1)[:,None])[:,0]
            ax.plot(cuts,values,label=run.definition.name,color=COLORS[run.definition.code],lw=.9)
        unit='Pedidos·hora' if i==5 else 'Pedidos'
        ax.set(title=f'{name} — {window_name}: {cuts[0]} a {cuts[-1]}',xlabel='Fecha del proceso',ylabel=unit)
        ax.legend();ax.grid(alpha=.2)
        fig.text(.5,.012,'Simulación hipotética; modelo validado categoría C.',ha='center',fontsize=8)
        fig.tight_layout(rect=[0,.035,1,1]);fig.savefig(figdir/f'{window_name}_{name}.png',dpi=145);plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(13,9),sharex=True)
    for i,ax in enumerate(axes):
        for run in runs:
            ax.plot(cuts[1:],run.result.transfers[:,i],label=run.definition.name,color=COLORS[run.definition.code],lw=.7)
        ax.set_ylabel(f'q{i+1}{i+2} (pedidos/h)');ax.legend();ax.grid(alpha=.2)
    axes[0].set_title(f'Transferencias medias horarias — {window_name}, {cuts[0].date()} a {cuts[-1].date()}')
    axes[-1].set_xlabel('Fecha; integrales RK4 de una hora, sin sustituir por eventos observados')
    fig.text(.5,.01,'Escenarios hipotéticos; validación categoría C.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.03,1,1]);fig.savefig(figdir/f'{window_name}_transferencias.png',dpi=145);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5));positions=np.arange(4)
    for j,run in enumerate(runs):
        row=run.indicators.iloc[-1]
        ax.bar(positions+(j-1)*.24,[row[v+'_maximo'] for v in ['X1','X2','X3','P']],width=.24,
               color=COLORS[run.definition.code],label=run.definition.name)
    ax.set_xticks(positions,['X1','X2','X3','P'])
    ax.set(title=f'Picos del modelo — {window_name}, {cuts[0].date()} a {cuts[-1].date()}',xlabel='Depósito o total pendiente',ylabel='Pedidos')
    ax.legend();fig.tight_layout();fig.savefig(figdir/f'{window_name}_maximos.png',dpi=145);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(13,9))
    for ax,col,unit in zip(axes.flat,['P_final','P_area_pedidos_hora','P_maximo','entregas_incrementales'],
                           ['Pedidos','Pedidos·hora','Pedidos','Pedidos']):
        for run in runs:
            ax.plot(run.indicators.horizonte_horas.astype(str),run.indicators[col],marker='o',
                    color=COLORS[run.definition.code],label=run.definition.name)
        ax.set(title=col,xlabel='Horizonte desde el mismo inicio (horas)',ylabel=unit);ax.legend();ax.grid(alpha=.2)
        if col=='P_maximo':
            ax.set_ylim(bottom=0)  # No exagerar diferencias pequeñas alrededor del estado inicial.
    fig.suptitle(f'{window_name}: horizontes predefinidos — inicio {cuts[0]}, modelo categoría C')
    fig.tight_layout();fig.savefig(figdir/f'{window_name}_indicadores_horizontes.png',dpi=145);plt.close(fig)
    # X4 incremental y entregas incrementales son la misma variable; no se duplica una gráfica idéntica.


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sensibilidad',action='store_true',help='Añade las tres configuraciones en enero de 2018, sin nueva validación')
    args=parser.parse_args();clock=time.perf_counter()
    out=ROOT/'reports';figdir=out/'graficas_escenarios';figdir.mkdir(exist_ok=True)
    protected=[ROOT/name for name in [
        'reports/parametros_calibrados.json','reports/modelo_seleccionado_desarrollo.json',
        'reports/calibracion_modelo.md','reports/comparacion_modelos.md','reports/validacion_final.md',
        'reports/resumen_validacion.json','reports/metricas_validacion.csv','reports/metricas_por_bloque.csv',
        'reports/trayectoria_validacion.csv','reports/pruebas_validacion.txt','reports/metricas_entrenamiento.csv',
        'src/rk4_solver.py','src/simulation_engine.py','src/agent_model.py','src/validation.py',
        'docs/modelo_matematico.md','docs/escenarios_propuestos.md','docs/plan_calibracion_validacion.md',
        'data/processed/eventos_por_hora.csv','data/processed/niveles_reales_4_tanques.csv',
        'Brazilian_E-Commerce_Public_Dataset_by_Olist.zip']]
    protected+=list((out/'graficas_validacion').glob('*.png'))
    fingerprints={str(p.relative_to(ROOT)):sha256(p) for p in protected}
    base=load_base_parameters(out)
    definitions=[('principal',load_scenario_window(ROOT/'data/processed'),HORIZONS)]
    if args.sensibilidad:
        aux=load_scenario_window(ROOT/'data/processed','2018-01-01 00:00:00','2018-02-01 00:00:00')
        if len(aux.arrivals)!=744:
            raise ValueError('Ventana de sensibilidad no tiene 744 horas')
        definitions.append(('sensibilidad_enero',aux,(168,720,744)))
    allruns={};tables=[];trajectories=[];transfers=[];metadata_runs=[];structural={};shifts=[]
    for name,window,horizons in definitions:
        print(LIMIT,flush=True)
        print(name,window.cuts[0],window.cuts[-1],len(window.arrivals),'intervalos; compras=',window.arrivals.sum(),flush=True)
        runs=run_official_scenarios(window,base,horizons)
        allruns[name]=runs;structural[name]=check_structural(runs)
        if name=='principal':
            state_columns=[f'X{i+1}_simulado' for i in range(4)]
            archived=pd.read_csv(out/'trayectoria_validacion.csv',dtype={c:str for c in state_columns})
            archived_x=archived[state_columns].to_numpy(dtype=float)
            np.testing.assert_array_equal(archived_x,runs[0].result.states)
        for run in runs:
            table=run.indicators.copy();table['ventana']=name;table['escenario']=run.definition.code;tables.append(table)
            trajectory=pd.DataFrame({'ventana':name,'escenario':run.definition.code,'corte_horario':window.cuts,
                                      'horas_desde_inicio':run.result.times})
            for i in range(4): trajectory[f'X{i+1}']=run.result.states[:,i]
            trajectory['X4_incremental']=run.result.states[:,3]-window.initial[3]
            trajectory['P']=run.result.states[:,:3].sum(axis=1)
            trajectory['area_acumulada_P']=cumulative_areas(run.result.times,trajectory[['P']].to_numpy())[:,0]
            trajectory['error_conservacion']=run.result.conservation_errors
            trajectories.append(trajectory)
            flow=pd.DataFrame(run.result.transfers,columns=['q12_integrado','q23_integrado','q34_integrado'])
            flow['ventana']=name;flow['escenario']=run.definition.code;flow['corte_horario']=window.cuts[1:];flow['compras']=window.arrivals
            transfers.append(flow)
            metadata_runs.append({'window':name,'code':run.definition.code,'name':run.definition.name,
                'description':run.definition.description,'parameters':dict(zip(['alpha','beta','gamma'],map(float,run.definition.parameters.array()))),
                'start':str(window.cuts[0]),'end':str(window.cuts[-1]),'initial':window.initial.tolist(),
                'intervals':len(window.arrivals),'purchases':float(window.arrivals.sum()),'horizons':list(horizons),
                'arrivals_sha256':hashlib.sha256(window.arrivals.tobytes()).hexdigest(),
                'states_sha256':hashlib.sha256(run.result.states.tobytes()).hexdigest(),
                'checks':run.checks})
            print(run.definition.code,run.indicators[['horizonte_horas','P_final','P_maximo','P_area_pedidos_hora','entregas_incrementales']].to_string(index=False),flush=True)
        shift=runs[1].result.states[:,2]-runs[0].result.states[:,2]
        shifts.append({'ventana':name,'max_aumento_X3_E1':float(shift.max()),'fecha_max_aumento_X3_E1':str(window.cuts[int(shift.argmax())]),
            'max_reduccion_X3_E1':float(shift.min()),'fecha_max_reduccion_X3_E1':str(window.cuts[int(shift.argmin())])})
        plot_runs(runs,name,figdir)
    indicators=pd.concat(tables,ignore_index=True)
    differences=comparisons(indicators)
    main_table=indicators.loc[indicators.ventana=='principal']
    complete=indicators.loc[indicators.apply(lambda row:row.horizonte_horas==(5488 if row.ventana=='principal' else 744),axis=1)]
    indicators.to_csv(out/'indicadores_horizontes.csv',index=False)
    complete.to_csv(out/'indicadores_escenarios.csv',index=False)
    differences.to_csv(out/'diferencias_escenarios.csv',index=False)
    pd.concat(trajectories,ignore_index=True).to_csv(out/'trayectorias_escenarios.csv',index=False)
    pd.concat(transfers,ignore_index=True).to_csv(out/'transferencias_escenarios.csv',index=False)
    # Lecturas automáticas de los ganadores: se muestran todas las métricas y horizontes.
    winners=[]
    for window,group in indicators.groupby('ventana',sort=False):
        for horizon,part in group.groupby('horizonte_horas',sort=False):
            row={'ventana':window,'horizonte_horas':int(horizon)}
            for col in ['P_final','P_area_pedidos_hora','P_maximo']:
                row['menor_'+col]=str(part.loc[part[col].idxmin(),'escenario'])
            row['mayor_entregas']=str(part.loc[part.entregas_incrementales.idxmax(),'escenario'])
            winners.append(row)
    winner_table=pd.DataFrame(winners);winner_table.to_csv(out/'comparacion_por_horizonte.csv',index=False)
    units={c:('pedidos·hora' if '_area_' in c else 'pedidos/hora' if '_media_por_hora' in c else
              'fecha/hora del dataset' if 'fecha' in c else 'horas' if c=='horizonte_horas' else
              'identificador' if c in ['ventana','escenario'] else 'pedidos') for c in indicators.columns}
    meta={'phase':'5','purpose':LIMIT,'base_validation_category':'C','independent_validation':False,
        'parameters_recalibrated':False,'official_configurations':3,'scenario_trajectories':len(metadata_runs),
        'rk4_executions':len(metadata_runs),'agentpy_executions':len(metadata_runs),
        'sensitivity_executed':bool(args.sensibilidad),'runs':metadata_runs,'structural_checks':structural,
        'shift_X3':shifts,'integration':{'method':'RK4','substeps_per_hour':4,'h_hours':.25,
            'area_method':'trapecios sobre todos los cortes horarios, incluidos inicial y final',
            'mean_definition':'area / duración en horas','percent_change':'100*(escenario-base)/base; nulo si base=0'},
        'units':units,'comparative_percent_unit':'porcentaje','sha256_preserved_files':fingerprints,
        'code_sha256':{str(p.relative_to(ROOT)):sha256(p) for p in [ROOT/'src/scenarios.py',ROOT/'src/scenario_metrics.py',Path(__file__).resolve()]},
        'horizon_indicators':indicators.to_dict(orient='records'),'winners':winners,
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'agentpy':agentpy.__version__},
        'seconds_before_tests':time.perf_counter()-clock}
    parameter_table=pd.DataFrame([{'escenario':r.definition.code,'nombre':r.definition.name,**dict(zip(['alpha','beta','gamma'],r.definition.parameters.array()))} for r in allruns['principal']])
    concise_cols=['escenario','horizonte_horas','P_final','P_maximo','P_promedio','P_area_pedidos_hora','entregas_incrementales']
    level_cols=['escenario','horizonte_horas','X1_final','X2_final','X3_final','X1_area_pedidos_hora','X2_area_pedidos_hora','X3_area_pedidos_hora']
    diff_main=differences.loc[(differences.ventana=='principal')&(differences.indicador.isin(['P_final','P_area_pedidos_hora','P_maximo','entregas_incrementales']))]
    checks=pd.DataFrame([{'ventana':r['window'],'escenario':r['code'],**r['checks']} for r in metadata_runs])
    quantitative=[]
    for horizon in HORIZONS:
        part=main_table.loc[main_table.horizonte_horas==horizon].set_index('escenario')
        quantitative.append(
            f'- {horizon} h: pendientes finales E0={part.loc["E0","P_final"]:.6f}, '
            f'E1={part.loc["E1","P_final"]:.6f}, E2={part.loc["E2","P_final"]:.6f} pedidos. '
            f'Las entregas adicionales respecto de E0 son '
            f'{part.loc["E1","entregas_incrementales"]-part.loc["E0","entregas_incrementales"]:.6f} en E1 y '
            f'{part.loc["E2","entregas_incrementales"]-part.loc["E0","entregas_incrementales"]:.6f} en E2.')
    total_main=main_table.loc[main_table.horizonte_horas==5488].set_index('escenario')
    week_main=main_table.loc[main_table.horizonte_horas==168].set_index('escenario')
    report=f'''# Comparación de tres escenarios hipotéticos — fase 5

**{LIMIT}** La validación final fue categoría C: el motor conserva pedidos y converge, pero la precisión del modelo es insuficiente para recomendaciones sobre la empresa real. Esta limitación se aplica a todas las tablas y conclusiones siguientes.

## Objetivo y modelo
Se investiga cómo modificar una única transferencia cambia las acumulaciones y entregas bajo las mismas llegadas históricas. Se reutilizan las cuatro EDO del modelo base: X1'=λ−αX1, X2'=αX1−βX2, X3'=βX2−γX3, X4'=γX3. X4 es terminal acumulado, no cola pendiente. Los flujos son q12=αX1, q23=βX2 y q34=γX3. No se utiliza aprobación rápida.

## Parámetros e intervenciones congeladas
Los valores se leyeron de parametros_calibrados.json y se comprobaron exactamente. Sólo E1 multiplica β por 1,20 y sólo E2 multiplica γ por 1,20; α no cambia. Las tasas son hora⁻¹. Los incrementos son intervenciones matemáticas, no capacidades reales implementadas ni reducciones demostradas de costos, energía, personal o entregas tardías.

{markdown(parameter_table)}

En una permanencia exponencial ideal, multiplicar una tasa por 1,20 divide su tiempo medio por 1,20: no obliga a reducir niveles un 20 %. El resultado depende de entradas, estados iniciales y horizonte.

## Ventanas y número de ejecuciones
Principal: {START} a {END}, 5.488 intervalos horarios, 5.489 estados, X0=[113,586,3005,53963], 37.415 compras. Se verificó en los archivos. Los horizontes 168,720,1440,5488 h son lecturas de una sola trayectoria continua por escenario, no nuevas simulaciones ni reinicializaciones. La ventana ya fue usada en validación; aquí se reutiliza exclusivamente para comparación retrospectiva hipotética y no para escoger o calibrar tasas.

Se ejecutaron **{len(metadata_runs)} trayectorias de escenario**: tres en cada una de {len(definitions)} ventanas. Cada trayectoria se ejecutó en RK4 puro y en AgentPy, es decir {len(metadata_runs)} ejecuciones por motor. Las pruebas matemáticas/regresiones automáticas no se cuentan como escenarios oficiales adicionales. Sensibilidad de enero ejecutada: {args.sensibilidad}. Si se incluye: 2018-01-01 00:00 a 2018-02-01 00:00, 744 h; horizontes 168,720,744 h. No se extrapolan 1440 h a una ventana más corta. Sus estados iniciales y compras exactas constan en el JSON. Tampoco es validación independiente.

## Método e indicadores
Las tres configuraciones comparten fechas, estado inicial, compras, h=0,25 h, cuatro agentes y las mismas definiciones de indicadores. No se recalibra, no se introducen transiciones observadas como entradas y no se corrigen niveles durante la trayectoria. AgentPy y el solucionador comparten las mismas ecuaciones e integración; no se duplicó RK4.

Áreas: trapecios sobre estados horarios, Σ(Δt/2)(X_k+X_(k+1)), con Δt=1 h, incluyendo inicio y horizonte. Unidad pedidos·hora. La media temporal se define como área/duración, no media aritmética de filas. Es una cuadratura horaria consistente entre escenarios, no la integral obtenida de etapas internas RK4; existe error de cuadratura intrahoraria. Las áreas acumuladas se construyen una sola vez y los horizontes leen sus prefijos. P=X1+X2+X3; su área coincide con la suma de áreas por etapa salvo redondeo.

Máximos y fechas incluyen la condición inicial y todos los cortes hasta el horizonte; se toma la primera fecha en empates. Entregas incrementales=X4(h)−X4(0), sin sumar las 53.963 entregas previas. Transferencias acumuladas y medias provienen de integrales RK4, no eventos observados. Se documentan en CSV para cada horizonte.

Variaciones: **100·(escenario−base)/base**, mismo signo y fórmula para todas las magnitudes. Negativo en pendientes/áreas indica reducción; positivo en entregas indica aumento. Con base cero el porcentaje se deja ausente, nunca infinito. Con bases muy pequeñas las variaciones porcentuales pueden ser grandes aunque la diferencia absoluta sea irrelevante; se muestran ambas. Las magnitudes no se redondean durante la integración.

## Resultados principales por horizonte
{markdown(main_table[concise_cols])}

### Cambios individuales por etapa
{markdown(main_table[level_cols])}

### Diferencias absolutas y porcentuales respecto de E0
{markdown(diff_main[['escenario','horizonte_horas','indicador','valor_base','valor_escenario','diferencia_absoluta','variacion_porcentual']])}

Todos los indicadores por depósito (inicial/final/máximo/fecha/media/área), aprobaciones, despachos y entregas acumuladas y medias se conservan en indicadores_horizontes.csv y diferencias_escenarios.csv. indicadores_escenarios.csv resume el horizonte completo de cada ventana, sin perder los otros horizontes.

## Comparación de criterios y horizontes
{markdown(winner_table)}

Los ganadores se calculan por separado para pendientes finales, pico, área y entregas: no se elige un único último instante favorable. Las diferencias y sus magnitudes deben leerse junto a los ganadores, particularmente si son pequeñas. No se declara estrategia universal para operaciones reales ni para entradas diferentes.

{chr(10).join(quantitative)}

En esta ejecución E2 presenta menores pendientes finales, área y pico, y mayores entregas, en todos los horizontes predefinidos de la ventana principal. No aparece un cambio de orden entre siete, treinta y sesenta días, ni al final. Esto describe estos datos y este modelo; no demuestra dominancia universal.

En el período completo, E1 reduce el área de P en {-float(total_main.loc['E1','P_area_pedidos_hora']-total_main.loc['E0','P_area_pedidos_hora']):.6f} pedidos·hora ({100*(1-total_main.loc['E1','P_area_pedidos_hora']/total_main.loc['E0','P_area_pedidos_hora']):.6f} %), y E2 en {-float(total_main.loc['E2','P_area_pedidos_hora']-total_main.loc['E0','P_area_pedidos_hora']):.6f} pedidos·hora ({100*(1-total_main.loc['E2','P_area_pedidos_hora']/total_main.loc['E0','P_area_pedidos_hora']):.6f} %). La ventaja de entregas al último instante es mucho menor que durante la ventana, por el agotamiento de la cohorte.

Los picos principales se sitúan en la primera hora desde un estado inicial común de 3704 pendientes. Sus reducciones frente a E0 son apenas {total_main.loc['E0','P_maximo']-total_main.loc['E1','P_maximo']:.6f} pedidos en E1 y {total_main.loc['E0','P_maximo']-total_main.loc['E2','P_maximo']:.6f} en E2: no debe presentarse el mejor pico como una reducción material grande. El área revela diferencias sostenidas que el pico inicial casi común oculta.

### Desplazamiento entre T2 y T3
{markdown(pd.DataFrame(shifts))}

X1 es exactamente igual en los tres escenarios porque no existe retroalimentación desde β o γ hacia aprobación. E1 reduce la permanencia de X2 al aumentar su salida, pero anticipa entrada a X3: un aumento positivo de X3 frente al base es traslado de acumulación, no creación de pedidos. En la cola tardía ese signo puede cambiar porque los pedidos anticipados ya salieron. E2 conserva exactamente X1 y X2 y aumenta la salida de X3 hacia X4. Estas son dependencias del modelo, no causalidad demostrada en Olist.

A los siete días E1 reduce X2 en {week_main.loc['E0','X2_final']-week_main.loc['E1','X2_final']:.6f} pedidos y aumenta X3 en {week_main.loc['E1','X3_final']-week_main.loc['E0','X3_final']:.6f}; la diferencia neta es su reducción de pendientes totales. E2 reduce X3 en {week_main.loc['E0','X3_final']-week_main.loc['E2','X3_final']:.6f}, sin alterar las etapas anteriores.

A igualdad de entradas y estado inicial, Δentregas=−Δpendientes en cada corte. Las entregas incrementales que gana una configuración son exactamente los pedidos que deja de tener pendientes en ese corte, dentro de redondeo. Las áreas incorporan el beneficio temporal sostenido y pueden distinguir configuraciones aunque ambas terminen casi vacías. El pico puede seguir determinado por el estado inicial común; no debe confundirse con una mejora de todos los períodos.

## Sensibilidad de calendario
'''
    if args.sensibilidad:
        auxiliary=indicators.loc[indicators.ventana=='sensibilidad_enero']
        auxiliary_window=allruns['sensibilidad_enero'][0].window
        report+=f'Estado inicial observado: {auxiliary_window.initial.tolist()}; compras: {auxiliary_window.arrivals.sum():.0f}; duración: 744 h.\n\n'
        report+=markdown(auxiliary[concise_cols])+'''\n\nSe aplicaron las mismas tres intervenciones sin nuevos ajustes. La tabla de ganadores distingue la ventana auxiliar; en los horizontes calculados también favorece E2 según las cuatro métricas. No se presenta como nueva validación ni se utiliza para retocar los escenarios.\n'''
    else:
        report+='No se ejecutó en esta llamada. Repetir con `--sensibilidad` añade enero de 2018 sin cambiar las configuraciones.\n'
    report+=f'''
## Controles de integridad y estructura
{markdown(checks)}

Identidades entre escenarios: `{json.dumps(structural,ensure_ascii=False)}`. La tolerancia de conservación es 1e−8·max(1,total). Se verificaron estados finitos/no negativos, etapas internas RK4 no negativas, flujos no negativos, X4 no decreciente y estabilidad. No se recortaron valores ni corrigieron balances. AgentPy y RK4 coinciden exactamente en todas las ejecuciones de escenario. E0 en la ventana principal reproduce exactamente los estados del CSV de validación final al leerlo con conversión round_trip; no se recalculan métricas de precisión ni se modifica aquel informe.

## Interpretación académica y límites obligatorios
La conclusión cuantitativa se limita a las trayectorias e indicadores anteriores. Las intervenciones actúan sobre coeficientes efectivos agregados de un modelo de validez categoría C. No se modelan capacidades máximas, contratación, costos o consumo energético; no existe modelo validado de retrasos individuales contrafactuales. Las fechas estimadas históricas no permiten asignar promesas individuales a entregas agregadas simuladas.

Las compras son llegadas históricas conocidas, no un pronóstico. La cohorte retrospectiva contiene sólo entregados completos y excluye pedidos no entregados y cancelaciones, por lo que no representa el inventario operativo completo. La cola final tiene agotamiento de esa población; con tasas positivas las configuraciones tienden asintóticamente al mismo total entregado si cesan las compras. Por eso se comparan también siete, treinta y sesenta días y áreas bajo curvas. Un remanente final no se recorta para fingir vaciado completo.

La exactitud del balance y la equivalencia de motores no subsanan errores estadísticos de la validación. Estos experimentos ilustran interacciones entre depósitos y compromisos temporales bajo hipótesis; no prueban mejoras aplicables directamente por Olist. No se seleccionan coeficientes nuevos con el período ya evaluado. Cualquier desarrollo predictivo posterior requerirá un conjunto de prueba nuevo. No se implementaron Streamlit ni animaciones.

## Archivos y trazabilidad
Se crearon src/scenarios.py y src/scenario_metrics.py, reutilizables para consumir trayectorias e indicadores desde una futura interfaz. ScenarioDefinition y ScenarioRun conservan descripción, parámetros, ventana, entradas, resultados y comprobaciones. El script exporta indicadores_escenarios.csv, indicadores_horizontes.csv, diferencias_escenarios.csv, trayectorias_escenarios.csv, transferencias_escenarios.csv y comparacion_escenarios.json, sin sobrescribir resultados anteriores.

Las gráficas en graficas_escenarios/ incluyen X1, X2, X3, X4 incremental (equivale a entregas incrementales), P, área acumulada de P, transferencias, máximos e indicadores por horizonte para cada ventana ejecutada. Colores fijos E0={COLORS['E0']}, E1={COLORS['E1']}, E2={COLORS['E2']}. No hay suavizado. Cada gráfico identifica fechas y unidades; se conserva la advertencia de categoría C.

Huellas de parámetros, datos, ZIP, código y resultados anteriores en comparacion_escenarios.json. Se verifican otra vez al terminar. Tiempo antes de pruebas: {meta['seconds_before_tests']:.3f} s. Versiones Python {platform.python_version()}, AgentPy {agentpy.__version__}, NumPy {np.__version__}, pandas {pd.__version__}.

## Reproducción
```powershell
.venv/Scripts/python.exe scripts/ejecutar_escenarios.py
.venv/Scripts/python.exe scripts/ejecutar_escenarios.py --sensibilidad
```
La primera llamada ejecuta tres escenarios principales; la segunda, los mismos tres más tres trayectorias auxiliares en enero. Repetir no constituye nueva validación independiente. El script ejecuta las 100 pruebas previas y las nuevas, y guarda su salida real en pruebas_escenarios.txt.
'''
    (out/'escenarios_resultados.md').write_text(report,encoding='utf-8')
    (out/'comparacion_escenarios.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    suite=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    output=suite.stdout+suite.stderr
    (out/'pruebas_escenarios.txt').write_text(output,encoding='utf-8')
    for path in protected:
        if sha256(path)!=fingerprints[str(path.relative_to(ROOT))]:
            raise ValueError(f'Se modificó un resultado protegido: {path}')
    meta['protected_files_unchanged']=True;meta['test_returncode']=suite.returncode;meta['test_output']=output
    meta['seconds_total']=time.perf_counter()-clock
    (out/'comparacion_escenarios.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    with (out/'escenarios_resultados.md').open('a',encoding='utf-8') as f:
        f.write('\n## Pruebas ejecutadas\n\n```text\n'+output.strip()+'\n```\n\nSe verificó que todos los archivos protegidos conservan su huella.\n')
    print(output,flush=True)
    print('Resultados guardados. '+LIMIT,flush=True)
    if suite.returncode: raise SystemExit(suite.returncode)

if __name__=='__main__':
    main()
