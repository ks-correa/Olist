"""Keep first round intact; additional development experiment, then reused audit."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import hashlib
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from scripts.experimentar_modelo_v2 import figures
from src.calibration import load_training
from src.calibration_v2 import ORIGINS,HORIZON
from src.calibration_mixture import fit_mixture
from src.model_mixture import simulate_mixture,simulate_mixture_agentpy
from src.goodness_of_fit import goodness
from src.validation import load_validation,FROZEN_SCALES

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/modelo_v2'

def main():
    frozen=OUT/'congelado_mezcla.json'
    if frozen.exists():raise RuntimeError('Segunda ronda ya congelada')
    data=load_training(ROOT/'data/processed');rows=[];runs={};controls=[]
    for origin in ORIGINS:
        print('Mezcla',origin,flush=True)
        tr=data.section(0,origin);ev=data.section(origin,origin+HORIZON)
        spec,info=fit_mixture(tr);runs[str(origin)]=info
        x,internal,q,e=simulate_mixture(ev.observed[0],ev.arrivals,ev.cuts,spec)
        t=goodness(ev.observed[1:,:3],x[1:,:3],tr.scales);t['modelo']='M';t['ventana']=origin;t['alcance']='evaluacion_interna_desarrollo_adaptativa';rows.append(t)
        pd.DataFrame(np.column_stack([ev.observed[:,:3],x[:,:3]]),index=ev.cuts,columns=['obs_X1','obs_X2','obs_X3','sim_X1','sim_X2','sim_X3']).to_csv(OUT/f'trayectoria_M_{origin}.csv',index_label='fecha')
        controls.append(dict(ventana=origin,masa_max=float(abs(e).max()),estado_min=float(internal.min()),flujo_min=float(q.min())))
    allrows=pd.concat([pd.read_csv(OUT/'metricas_ventanas.csv'),*rows],ignore_index=True)
    scores=allrows.groupby(['modelo','ventana']).NRMSE.max().groupby('modelo').mean().to_dict()
    complexity={'A':(3,4),'B':(12,4),'C':(3,7),'M':(9,7)}
    selected=min([m for m in scores if scores[m]<=min(scores.values())*1.02],key=lambda m:complexity[m])
    spec,info=fit_mixture(data);runs['completo']=info
    record=dict(modelo='M',selected_overall=selected,theta=spec.theta,scores=scores,scales=data.scales.tolist(),
                fecha_utc=datetime.now(timezone.utc).isoformat(),protocolo_sha256=hashlib.sha256((OUT/'protocolo_mezcla.md').read_bytes()).hexdigest(),
                source_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['src/model_mixture.py','src/calibration_mixture.py','scripts/experimentar_mezcla_v2.py']},
                scope='selección adaptativa de desarrollo; reserva antigua ya observada')
    frozen.write_text(json.dumps(record,indent=2),encoding='utf8')
    (OUT/'optimizaciones_mezcla.json').write_text(json.dumps(runs,indent=2),encoding='utf8')
    allrows.to_csv(OUT/'metricas_ventanas_ampliadas.csv',index=False)
    print('Congelada segunda ronda',scores,'seleccionado',selected,flush=True)
    val=load_validation(ROOT/'data/processed');metrics=[];convergence=[]
    for scope,d,scales in [('entrenamiento',data,data.scales),('reserva_reutilizada',val,FROZEN_SCALES)]:
        x,internal,q,e=simulate_mixture(d.observed[0],d.arrivals,d.cuts,spec)
        t=goodness(d.observed[1:,:3],x[1:,:3],scales);t['modelo']='V2_M';t['alcance']=scope;metrics.append(t)
        t.to_csv(OUT/f'metricas_V2_M_{scope}.csv',index=False)
        table=pd.DataFrame({'fecha':d.cuts})
        for j in range(4):table[f'obs_X{j+1}']=d.observed[:,j];table[f'sim_X{j+1}']=x[:,j]
        table.to_csv(OUT/f'trayectoria_V2_M_{scope}.csv',index=False)
        figures('V2_M_'+scope,d.cuts[1:],d.observed[1:,:3],x[1:,:3],scales)
        controls.append(dict(ventana=scope,masa_max=float(abs(e).max()),estado_min=float(internal.min()),flujo_min=float(q.min())))
        coarse=x
        for substeps in (8,16):
            fine=simulate_mixture(d.observed[0],d.arrivals,d.cuts,spec,substeps)[0]
            convergence.append(dict(alcance=scope,h_grueso=2/substeps,h_fino=1/substeps,diferencia_max=float(abs(coarse-fine).max())));coarse=fine
        exact=simulate_mixture(d.observed[0],d.arrivals,d.cuts,spec,analytical=True)[0]
        controls[-1]['error_vs_expm']=float(abs(x-exact).max())
        agents,_=simulate_mixture_agentpy(d.observed[0],d.arrivals,d.cuts,spec)
        np.testing.assert_array_equal(agents,x)
    pd.DataFrame(controls).to_csv(OUT/'controles_mezcla.csv',index=False)
    (OUT/'convergencia_mezcla.json').write_text(json.dumps(convergence,indent=2),encoding='utf8')
    pd.concat([pd.read_csv(OUT/'comparacion_final.csv'),*metrics]).to_csv(OUT/'comparacion_ampliada.csv',index=False)

if __name__=='__main__':main()
