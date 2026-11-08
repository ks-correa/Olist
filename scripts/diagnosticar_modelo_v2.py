"""Post-selection diagnostics; no selection or calibration decisions here."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import hashlib
import numpy as np
import pandas as pd
from scipy.stats import CensoredData, ecdf
from src.data_processing import read_orders,audit_and_clean,DATES
from src.calibration import load_training,TRAIN_END
from src.calibration_v2 import BASE
from src.rk4_solver import Parameters,rk4_step
from src.goodness_of_fit import kaplan_meier,goodness
from src.model_mixture import MixtureSpec
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/modelo_v2'


def main():
    data=load_training(ROOT/'data/processed')
    raw,_=read_orders(ROOT/'Brazilian_E-Commerce_Public_Dataset_by_Olist.zip')
    _,clean,_,_,_,_=audit_and_clean(raw)
    rows=[]
    # Exact exposure monthly, including orders entering before month and censored exits.
    for end in pd.date_range('2017-01-01','2018-03-01',freq='MS'):
        start=max(data.cuts[0],end-pd.DateOffset(months=1))
        for j,(a,b) in enumerate(zip(DATES[:-1],DATES[1:])):
            entry=clean[a].where(clean[a]<=end)
            exit=clean[b].where(clean[b]<=end)
            exposure=((exit.fillna(end)-entry.clip(lower=start)).dt.total_seconds()/3600).clip(lower=0).fillna(0).sum()
            exits=int((exit.gt(start)&exit.le(end)).sum())
            rows.append(dict(inicio=start,fin=end,variable=f'X{j+1}',exposicion=exposure,salidas=exits,tasa=exits/exposure if exposure else np.nan))
    pd.DataFrame(rows).to_csv(OUT/'tasas_exposicion_mensuales.csv',index=False)
    # Additional dwell-law comparison includes Erlang and mixed exponential, with censures.
    mixed=MixtureSpec(tuple(json.loads((OUT/'congelado_mezcla.json').read_text())['theta']))
    k,p=mixed.coefficients
    runs=json.loads((OUT/'optimizaciones.json').read_text())
    c=min([r for r in runs['C_10883'] if r['success']],key=lambda r:r['cost'])
    fig,axes=plt.subplots(3,2,figsize=(13,11));ks=[]
    from scipy.stats import gamma
    for j,(a,b) in enumerate(zip(DATES[:-1],DATES[1:])):
        entry=clean[a].where(clean[a]<=TRAIN_END);exit=clean[b].where(clean[b]<=TRAIN_END);valid=entry.notna()
        t=(exit.fillna(TRAIN_END)[valid]-entry[valid]).dt.total_seconds().to_numpy()/3600
        done=exit[valid].notna().to_numpy();km=kaplan_meier(t,done)
        reference=ecdf(CensoredData(uncensored=t[done],right=t[~done]))
        np.testing.assert_allclose(reference.sf.evaluate(km.horas),km.supervivencia,atol=1e-12)
        grid=km.horas.to_numpy();exp_sf=np.exp(-BASE[j]*grid)
        mix_sf=p[j]*np.exp(-k[j,0]*grid)+(1-p[j])*np.exp(-k[j,1]*grid)
        erlang_sf=gamma.sf(grid,2,scale=1/np.exp(c['theta'][j]))
        # Parameter C here from last prefix, explicit, not asserted full fit.
        for model,surv in [('V1',exp_sf),('M completo',mix_sf),('C prefijo 10883',erlang_sf)]:
            ks.append(dict(variable=f'X{j+1}',modelo=model,max_distancia_KM=float(abs(km.supervivencia-surv).max()),p_valor='no calculado: censura, parámetros ajustados y selección'))
        axes[j,0].step(grid,km.supervivencia,where='post',label='KM censurada')
        axes[j,0].plot(grid,exp_sf,label='V1');axes[j,0].plot(grid,mix_sf,label='M');axes[j,0].plot(grid,erlang_sf,label='C prefijo 10883')
        axes[j,0].set(xlim=(0,np.quantile(t,.99)),xlabel='Permanencia (h)',ylabel='Supervivencia',title=f'X{j+1} · desarrollo al {TRAIN_END}');axes[j,0].legend()
        # Q-Q KM quantiles: only identified probabilities; avoid dropping censures.
        probs=np.arange(.05,.96,.05)
        empirical=np.array([grid[np.flatnonzero(km.supervivencia.to_numpy()<=1-pr)[0]] if (km.supervivencia<=1-pr).any() else np.nan for pr in probs])
        theoretical=-np.log(1-probs)/BASE[j]
        axes[j,1].plot(theoretical,empirical,'o');axes[j,1].plot(theoretical,theoretical,'--')
        axes[j,1].set(xlabel='Cuantil V1 (h)',ylabel='Cuantil KM (h)',title='Q-Q censurado descriptivo')
    fig.suptitle('Leyes de permanencia · desarrollo retrospectivo reutilizado');fig.tight_layout();fig.savefig(OUT/'graficas/permanencias_comparadas.png',dpi=110);plt.close(fig)
    pd.DataFrame(ks).to_csv(OUT/'distancias_permanencia.csv',index=False)
    # Hourly aggregation sensitivity: same training purchases, quarter-hour timing from archive.
    edges=pd.date_range(data.cuts[0],data.cuts[-1],freq='15min')
    times=np.sort(clean.loc[clean[DATES[0]]<=TRAIN_END,DATES[0]].to_numpy())
    cumulative=np.searchsorted(times,edges.to_numpy(),side='right')
    counts=np.diff(cumulative)
    np.testing.assert_array_equal(counts.reshape(-1,4).sum(axis=1),data.arrivals)
    state=data.observed[0].copy();states=[state.copy()]
    for i,count in enumerate(counts):
        state,_=rk4_step(state,4*count,Parameters(*BASE),h=.25)
        if i%4==3:states.append(state.copy())
    states=np.asarray(states)
    uniform=pd.read_csv(OUT/'trayectoria_V1_historico_entrenamiento.csv')[[f'sim_X{j}' for j in range(1,5)]].to_numpy()
    metrics=goodness(data.observed[1:,:3],states[1:,:3],data.scales)
    metrics['max_diferencia_vs_entrada_horaria']=abs(states-uniform).max(axis=0)[:3]
    metrics.to_csv(OUT/'sensibilidad_agregacion_15min.csv',index=False)
    # Rise/fall, peaks, persistent signed errors on both final trajectories.
    rows=[];peaks=[]
    for name in ['V1_historico','V2_B','V2_M']:
        for scope in ['entrenamiento','reserva_reutilizada']:
            tr=pd.read_csv(OUT/f'trayectoria_{name}_{scope}.csv',parse_dates=['fecha'])
            for j in range(1,4):
                y=tr[f'obs_X{j}'].to_numpy();x=tr[f'sim_X{j}'].to_numpy();e=x[1:]-y[1:];dy=np.diff(y)
                for label,mask in [('subida',dy>0),('descenso',dy<0),('estable',dy==0)]:
                    rows.append(dict(modelo=name,alcance=scope,variable=f'X{j}',movimiento=label,n=int(mask.sum()),
                                     RMSE=float(np.sqrt(np.mean(e[mask]**2))),sesgo=float(e[mask].mean()),
                                     RMSE_cambio_horario=float(np.sqrt(np.mean((np.diff(x)[mask]-dy[mask])**2)))))
                signs=e>0;bound=np.r_[0,np.flatnonzero(signs[1:]!=signs[:-1])+1,len(e)]
                peaks.append(dict(modelo=name,alcance=scope,variable=f'X{j}',pico_observado=y[1:].max(),pico_simulado=x[1:].max(),
                                  fecha_pico_observado=str(tr.fecha.iloc[1+np.argmax(y[1:])]),fecha_pico_simulado=str(tr.fecha.iloc[1+np.argmax(x[1:])]),
                                  desfase_pico_h=int(np.argmax(x[1:])-np.argmax(y[1:])),racha_mismo_signo_max_h=int(np.diff(bound).max())))
    pd.DataFrame(rows).to_csv(OUT/'subidas_descensos.csv',index=False);pd.DataFrame(peaks).to_csv(OUT/'picos_persistencia.csv',index=False)
    audit=json.loads((OUT/'auditoria_previa.json').read_text(encoding='utf8'))
    original=json.loads((ROOT/'reports/integridad_redisenio.json').read_text(encoding='utf8'))
    mismatches=[]
    for path,h in original.items():
        current=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        if current!=h:
            initial=audit['files'].get(str(Path(path)))
            mismatches.append(dict(path=path,historico=h,inicio_tarea=initial,actual=current,preexistente=initial==current))
    (OUT/'discrepancias_integridad_preexistentes.json').write_text(json.dumps(mismatches,indent=2),encoding='utf8')
    print('Diagnósticos completos; discrepancias históricas:',len(mismatches))

if __name__=='__main__':main()
