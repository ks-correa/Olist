"""Reproducible development selection and explicitly reused retrospective audit."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
import hashlib
import subprocess
from datetime import datetime, timezone
import platform
from importlib.metadata import version
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import probplot, expon, gamma
from src.calibration import load_training, TRAIN_END
from src.calibration_v2 import fit_v2, make_spec, BASE, ORIGINS, HORIZON
from src.model_v2 import simulate_v2, simulate_agentpy_v2
from src.goodness_of_fit import goodness, grouped_errors, residual_diagnostics, kaplan_meier
from src.simulation_engine import simulate
from src.rk4_solver import Parameters
from src.validation import load_validation, FROZEN_SCALES
from src.data_processing import read_orders, audit_and_clean, DATES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/modelo_v2'


def dump(name, obj):
    (OUT/name).write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding='utf8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def figures(label, cuts, y, x, scales):
    """Unsmoothed hourly series; period/model/scope on every figure."""
    folder = OUT/'graficas'; folder.mkdir(exist_ok=True)
    title = f'{label}\n{cuts[0]} — {cuts[-1]} (horario)'
    e = x-y
    formal, acf = residual_diagnostics(e)
    formal.to_csv(OUT/f'ljung_box_{label}.csv', index=False)
    grouped_errors(cuts, y, x, scales).to_csv(OUT/f'errores_temporales_{label}.csv', index=False)
    for j in range(3):
        fig, axes = plt.subplots(3, 2, figsize=(13, 10))
        a = axes.ravel()
        a[0].plot(cuts, y[:, j], label='observado', lw=.7)
        a[0].plot(cuts, x[:, j], label='simulado', lw=.7); a[0].legend()
        a[0].set(xlabel='Fecha', ylabel='Pedidos', title='Trayectoria')
        a[1].plot(cuts, e[:, j], lw=.5); a[1].axhline(0, color='k', lw=.5)
        a[1].set(xlabel='Fecha', ylabel='Error (pedidos)', title='Residuos')
        a[2].scatter(x[:, j], e[:, j], s=1)
        a[2].set(xlabel='Simulado (pedidos)', ylabel='Error (pedidos)', title='Error frente a nivel')
        a[3].hist(e[:, j], bins=50)
        a[3].set(xlabel='Error (pedidos)', ylabel='Horas', title='Distribución del error')
        a[4].plot(np.arange(1, acf.shape[1]+1), acf[j])
        a[4].set(xlabel='Retardo (h)', ylabel='ACF (adimensional)', title='Dependencia serial')
        probplot(e[:, j], plot=a[5]); a[5].set(xlabel='Cuantil normal teórico', ylabel='Error (pedidos)', title='Q-Q descriptivo; no supone normalidad')
        fig.suptitle(f'X{j+1} · {title}'); fig.tight_layout()
        fig.savefig(folder/f'{label}_X{j+1}.png', dpi=110); plt.close(fig)
    g = grouped_errors(cuts, y, x, scales)
    fig, ax = plt.subplots(figsize=(11, 4))
    for name in ('X1', 'X2', 'X3'):
        t = g[(g.grupo=='mes') & (g.variable==name)]
        ax.plot(t.valor, t.RMSE, label=name, marker='o')
    ax.set(title=title+'\nError mensual', xlabel='Mes', ylabel='RMSE (pedidos)'); ax.legend(); ax.tick_params(axis='x', rotation=45)
    fig.tight_layout(); fig.savefig(folder/f'{label}_mensual.png', dpi=110); plt.close(fig)


def dwell_audit(spec):
    raw, _ = read_orders(ROOT/'Brazilian_E-Commerce_Public_Dataset_by_Olist.zip')
    _, clean, _, _, _, _ = audit_and_clean(raw)
    rows = []
    fig, axes = plt.subplots(3, 2, figsize=(12, 11))
    for j, (a, b) in enumerate(zip(DATES[:-1], DATES[1:])):
        entry = clean[a].where(clean[a] <= TRAIN_END)
        exit = clean[b].where(clean[b] <= TRAIN_END)
        valid = entry.notna()
        t = (exit.fillna(TRAIN_END)[valid]-entry[valid]).dt.total_seconds().to_numpy()/3600
        done = exit[valid].notna().to_numpy()
        km = kaplan_meier(t, done); km.to_csv(OUT/f'permanencia_X{j+1}_KM.csv', index=False)
        # Compare baseline and selected mathematical dwell laws, not fitted p-values.
        rate = np.exp(np.asarray(spec.theta).reshape(3, -1)[j, 0])
        grid = np.linspace(0, max(1, np.quantile(t, .99)), 500)
        axes[j, 0].step(km.horas, km.supervivencia, where='post', label='KM censurada')
        axes[j, 0].plot(grid, expon.sf(grid, scale=1/BASE[j]), label='V1 exponencial')
        if spec.name in ('A', 'C'):
            axes[j, 0].plot(grid, gamma.sf(grid, spec.phases[j], scale=1/rate), label=f'{spec.name} ley postulada')
        axes[j, 0].set(xlim=(0, grid[-1]), xlabel='Permanencia (h)', ylabel='Supervivencia', title=f'X{j+1}, desarrollo al {TRAIN_END}'); axes[j, 0].legend()
        axes[j, 1].hist(t[done], bins=100, density=True)
        axes[j, 1].set(xlabel='Duración completada (h)', ylabel='Densidad (1/h)', title='Completadas: condicionadas; censuras en CSV')
        rows.append(dict(variable=f'X{j+1}',n=len(t),completadas=int(done.sum()),censuradas=int((~done).sum()),
                         mediana_completadas=float(np.median(t[done])),p95_completadas=float(np.quantile(t[done],.95)),
                         fraccion_completadas_menos_1h=float(np.mean(t[done]<=1)),
                         media_exponencial_V1=1/BASE[j],exposicion_h=float(t.sum()),
                         tasa_eventos_exposicion=float(done.sum()/t.sum())))
    fig.suptitle('Permanencias · cohorte retrospectiva · desarrollo reutilizado'); fig.tight_layout()
    fig.savefig(OUT/'graficas/permanencias.png',dpi=110); plt.close(fig)
    pd.DataFrame(rows).to_csv(OUT/'permanencias_resumen.csv',index=False)


def main():
    OUT.mkdir(exist_ok=True)
    if (OUT/'congelado.json').exists():
        raise RuntimeError('Experimento ya congelado: conservar resultados; usar otro directorio/version para repetir')
    protocol_hash = sha(OUT/'protocolo.md')
    data = load_training(ROOT/'data/processed')
    records, runs, controls = [], {}, []
    models = ['A','B','C']

    def evaluate(name):
        for origin in ORIGINS:
            print(f'Ajustando {name}, origen {origin}', flush=True)
            train = data.section(0, origin); ev = data.section(origin, origin+HORIZON)
            spec, info = fit_v2(name, train); runs[f'{name}_{origin}'] = info
            states, internal, flows, errors = simulate_v2(ev.observed[0], ev.arrivals, ev.cuts, spec)
            t = goodness(ev.observed[1:, :3], states[1:, :3], train.scales)
            t['modelo']=name; t['ventana']=origin; t['alcance']='evaluacion_interna_desarrollo'
            records.append(t)
            control = dict(modelo=name, ventana=origin, masa_max=float(abs(errors).max()),
                           estado_min=float(internal.min()), flujo_min=float(flows.min()), X4_monotono=bool((np.diff(states[:,3])>=0).all()))
            controls.append(control)
            pd.DataFrame(np.column_stack([ev.observed[:, :3], states[:, :3]]),index=ev.cuts,
                         columns=['obs_X1','obs_X2','obs_X3','sim_X1','sim_X2','sim_X3']).to_csv(OUT/f'trayectoria_{name}_{origin}.csv',index_label='fecha')
            dump('optimizaciones.json',runs)

    for name in models:
        evaluate(name)
    def score(name):
        t = pd.concat(records); t=t[t.modelo==name]
        return float(t.groupby('ventana').NRMSE.max().mean())
    hybrid = all(score(name) <= .95*score('A') for name in ('B','C'))
    if hybrid:
        models.append('D'); evaluate('D')
    scores = {name:score(name) for name in models}
    best = min(scores.values())
    # Same parameter count: A preferred over C (fewer states).
    complexity = {'A':(3,4), 'C':(3,7), 'B':(12,4), 'D':(12,7)}
    selected = min([n for n in models if scores[n] <= best*1.02], key=lambda n:complexity[n])
    spec, full_runs = fit_v2(selected,data); runs['completo_'+selected]=full_runs
    dump('optimizaciones.json',runs)
    dump('congelado.json',dict(modelo=selected,theta=spec.theta,phases=spec.phases,
                              scales=data.scales.tolist(),scores=scores,hybrid_executed=hybrid,
                              protocolo_sha256=protocol_hash,fecha_utc=datetime.now(timezone.utc).isoformat(),
                              alcance='desarrollo reutilizado; no validación independiente',
                              source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'src/model_v2.py',ROOT/'src/calibration_v2.py',ROOT/'src/goodness_of_fit.py',Path(__file__)]}))
    print('Selección congelada:',selected,scores,flush=True)
    pd.concat(records).to_csv(OUT/'metricas_ventanas.csv',index=False)
    # Only now load historical reused reserve. No model changes based on it.
    validation = load_validation(ROOT/'data/processed')
    outputs = {}
    for label, d, scale in [('entrenamiento',data,data.scales),('reserva_reutilizada',validation,FROZEN_SCALES)]:
        results = {}
        for name, fitted in [('V1_historico',make_spec('A', np.log(BASE))),('V2_'+selected,spec)]:
            states, internal, flows, error = simulate_v2(d.observed[0],d.arrivals,d.cuts,fitted)
            results[name]=states
            t=goodness(d.observed[1:,:3],states[1:,:3],scale)
            t['modelo']=name; t['alcance']=label
            outputs[name+'_'+label]=t.to_dict('records')
            t.to_csv(OUT/f'metricas_{name}_{label}.csv',index=False)
            table=pd.DataFrame({'fecha':d.cuts})
            for j in range(4):
                table[f'obs_X{j+1}']=d.observed[:,j]; table[f'sim_X{j+1}']=states[:,j]
            table.to_csv(OUT/f'trayectoria_{name}_{label}.csv',index=False)
            figures(name+'_'+label,d.cuts[1:],d.observed[1:,:3],states[1:,:3],scale)
            controls.append(dict(modelo=name,ventana=label,masa_max=float(abs(error).max()),estado_min=float(internal.min()),flujo_min=float(flows.min()),X4_monotono=bool((np.diff(states[:,3])>=0).all())))
        original=simulate(d.observed[0],d.arrivals,Parameters(*BASE)).states
        np.testing.assert_allclose(results['V1_historico'],original,rtol=1e-11,atol=1e-7)
        print('V1 reproducido:',label,flush=True)
    # Numerical validation on whole training trajectory, not tiny toy only.
    coarse=simulate_v2(data.observed[0],data.arrivals,data.cuts,spec,4)[0]
    convergence=[]
    for steps in (8,16):
        fine=simulate_v2(data.observed[0],data.arrivals,data.cuts,spec,steps)[0]
        convergence.append(dict(h_grueso=2/steps,h_fino=1/steps,diferencia_max=float(abs(coarse-fine).max())))
        coarse=fine
    published, agents=simulate_agentpy_v2(validation.observed[0],validation.arrivals,validation.cuts,spec)
    direct=simulate_v2(validation.observed[0],validation.arrivals,validation.cuts,spec)[0]
    np.testing.assert_array_equal(published,direct)
    # Perturb parameter only, no recalibration: sensitivity of training loss.
    sensitivity=[]
    for j in range(len(spec.theta)):
        for delta in (-.05,.05):
            theta=np.array(spec.theta); theta[j]+=delta
            states=simulate_v2(data.observed[0],data.arrivals,data.cuts,make_spec(selected,theta))[0]
            sensitivity.append(dict(parametro=j,delta_log=delta,MSE_normalizado=float(np.mean(((states[1:,:3]-data.observed[1:,:3])/data.scales)**2))))
    pd.DataFrame(sensitivity).to_csv(OUT/'sensibilidad.csv',index=False)
    pd.DataFrame(controls).to_csv(OUT/'controles_numericos.csv',index=False)
    dump('convergencia.json',convergence)
    dwell_audit(spec)
    all_metrics=pd.concat([pd.DataFrame(t) for t in outputs.values()])
    all_metrics.to_csv(OUT/'comparacion_final.csv',index=False)
    internal=pd.concat(records)
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for ax,col,unit in zip(axes,['RMSE','NRMSE'],['pedidos','adimensional']):
        internal.groupby(['modelo','variable'])[col].mean().unstack().plot.bar(ax=ax)
        ax.set(title='Evaluación interna: cuatro ventanas de 1920 h',ylabel=f'{col} ({unit})',xlabel='Modelo')
    fig.tight_layout();fig.savefig(OUT/'graficas/comparacion_modelos.png',dpi=110);plt.close(fig)
    dump('resumen.json',dict(selected=selected,scores=scores,hybrid_executed=hybrid,
                            internal_all_criteria=bool(internal[internal.modelo==selected].cumple.all()),
                            retrospective_all_criteria=bool(all_metrics[all_metrics.alcance=='reserva_reutilizada'].query('modelo != "V1_historico"').cumple.all()),
                            independent_data=False,agentpy_exact=True,agentpy_hours=agents.t,
                            outputs=outputs,convergence=convergence))
    dump('entorno.json',dict(python=sys.version,platform=platform.platform(),fecha_utc=datetime.now(timezone.utc).isoformat(),
                            dependencies={n:version(n) for n in ['numpy','pandas','scipy','matplotlib','streamlit','agentpy']},
                            inputs={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'data/processed').glob('*.csv')},
                            archive_sha256=sha(ROOT/'Brazilian_E-Commerce_Public_Dataset_by_Olist.zip'),
                            git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()))
    print(json.dumps(scores),flush=True)


if __name__=='__main__':
    main()
