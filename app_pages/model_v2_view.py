"""Read-only comparison of frozen experiments; no optimizer runs in the UI."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import streamlit as st
from src.validation_v2 import load_frozen_v2

OUT=Path(__file__).resolve().parents[1]/'reports/modelo_v2'
st.subheader('Laboratorio V2 · comparación reproducible')
if not (OUT/'resumen.json').exists():
    st.info('Ejecute scripts/experimentar_modelo_v2.py para generar los resultados.')
    st.stop()


@st.cache_data(max_entries=12)
def read_table(path,modified):
    return pd.read_csv(path)


def table(name):
    p=OUT/name
    return read_table(str(p),p.stat().st_mtime_ns)


choice=st.segmented_control('Versión del modelo',['Modelo original V1','Modelo experimental V2'],default='Modelo experimental V2',required=True,key='v2_version')
scope=st.segmented_control('Período',['Reserva histórica reutilizada','Entrenamiento'],default='Reserva histórica reutilizada',required=True,key='v2_scope')
name='V1_historico' if choice=='Modelo original V1' else 'V2_B'
period='reserva_reutilizada' if scope=='Reserva histórica reutilizada' else 'entrenamiento'
st.warning('Ningún candidato alcanzó NRMSE ≤ 0,30 simultáneamente en X1, X2 y X3. No hay una evaluación nueva independiente. V2 sigue siendo experimental.')
st.caption('La selección utiliza desarrollo cronológico reutilizado. Las compras históricas son entradas conocidas: estos resultados no evalúan un pronóstico de demanda.')
trajectory=table(f'trayectoria_{name}_{period}.csv')
trajectory['fecha']=pd.to_datetime(trajectory.fecha)
metrics=table(f'metricas_{name}_{period}.csv')
st.caption(f'{name} · {scope} · {trajectory.fecha.iloc[0]} a {trajectory.fecha.iloc[-1]} · {len(trajectory)-1} intervalos de una hora')
st.dataframe(metrics[['variable','MAE','RMSE','NRMSE','NMAE','R2','sesgo_medio','error_nivel_maximo_absoluto','error_final_absoluto','cumple']],hide_index=True,alt='Métricas por depósito, errores en pedidos y normalizados adimensionales')
st.latex(r'\dot X_1=\lambda-q_{12},\quad\dot X_2=q_{12}-q_{23},\quad\dot X_3=q_{23}-q_{34},\quad\dot X_4=q_{34}')
st.latex(r'q_{12}=\alpha(t)X_1,\quad q_{23}=\beta(t)X_2,\quad q_{34}=\gamma(t)X_3')
if name=='V2_B':
    _,frozen=load_frozen_v2(OUT.parents[1])
    st.latex(r'k_i(t)=\exp[b_{i0}+b_{i1}\sin(2\pi h/24)+b_{i2}\cos(2\pi h/24)+b_{i3}I_{fin\ de\ semana}]')
    st.dataframe(pd.DataFrame(np.asarray(frozen['theta']).reshape(3,4),index=['α','β','γ'],columns=['log tasa base','seno diario','coseno diario','fin de semana']),alt='Coeficientes congelados del modelo B')
    st.caption('Tasas en h⁻¹, constantes por intervalo horario. Cuatro EDO; RK4 h=0,25 h. Los efectos de calendario son adimensionales.')
else:
    st.code('α = 0.10202378368368686 h⁻¹\nβ = 0.013240792867426554 h⁻¹\nγ = 0.004071911987908591 h⁻¹')
st.markdown('#### Cuatro depósitos en el tiempo')
index=st.slider('Hora desde el origen',0,len(trajectory)-1,0,key='v2_hour')
current=trajectory.iloc[index]
st.caption(f'Instante: {current.fecha} · {name} · {scope}')
with st.container(horizontal=True):
    for j,label in enumerate(['X1 · aprobación','X2 · despacho','X3 · entrega','X4 · entregados acumulados'],1):
        st.metric(label,f'{current[f"sim_X{j}"]:,.2f}',delta=None)
st.bar_chart(pd.DataFrame({'Pedidos simulados':[current[f'sim_X{j}'] for j in range(1,5)]},index=['X1','X2','X3','X4']),alt='Niveles de los cuatro depósitos en la hora seleccionada')
stage=st.segmented_control('Etapa',['X1','X2','X3','X4'],default='X1',required=True,key='v2_stage')
st.line_chart(trajectory.set_index('fecha')[[f'obs_{stage}',f'sim_{stage}']].rename(columns={f'obs_{stage}':'Observado (pedidos)',f'sim_{stage}':'Simulado (pedidos)'}),alt=f'{stage} observado frente a simulado, período completo sin suavizado')
st.download_button('Descargar trayectoria',trajectory.to_csv(index=False).encode('utf8'),file_name=f'{name}_{period}.csv',mime='text/csv',key='v2_download')
st.markdown('#### Comparación interna de candidatos')
comparison_file='metricas_ventanas_ampliadas.csv' if (OUT/'metricas_ventanas_ampliadas.csv').exists() else 'metricas_ventanas.csv'
comparison=table(comparison_file)
st.dataframe(comparison[['modelo','ventana','variable','NRMSE','NMAE','RMSE','cumple']],hide_index=True,alt='A constante, B calendario, C Erlang y M mezcla en las mismas ventanas de desarrollo')
st.caption('C y M tienen siete EDO y se agregan a cuatro etapas. La mezcla fue una investigación adaptativa posterior; tampoco mejoró la selección. El híbrido no se ejecutó porque los candidatos simples no satisficieron su condición previa.')
st.markdown('#### Residuos, conservación y estabilidad')
if stage!='X4':
    st.image(str(OUT/f'graficas/{name}_{period}_{stage}.png'),alt=f'Diagnósticos horarios completos de {stage}, {name}, {scope}')
st.dataframe(table('controles_numericos.csv'),hide_index=True,alt='Conservación en pedidos, mínimos de estados y flujos, monotonicidad de entregas')
st.json(json.loads((OUT/'convergencia.json').read_text(encoding='utf8')))
st.caption('AgentPy publica la misma trayectoria del motor RK4, sin integrar por separado. Pasar estos controles matemáticos no demuestra precisión empírica.')
st.caption('E0, E1 y E2 conservan su significado y sus resultados V1 en las pantallas originales. No se habilitan escenarios V2: el desempeño observado no justifica trasladar las mejoras hipotéticas anteriores. La presentación académica original permanece intacta.')
