import time
from typing import cast
import numpy as np
import streamlit as st
from src.dashboard_data import LABELS,ScenarioSeries,custom_experiment,custom_indicators
from src.dashboard_metrics import snapshot,SPEEDS
from ui.components import dataset,download
from ui.tanks import connected_tanks,visual_payload,frame_payload

st.subheader('Cuatro tanques · Un sistema logístico')
data=dataset();window=st.session_state.window
series: ScenarioSeries
with st.container(horizontal=True,vertical_alignment='bottom'):
    source=st.segmented_control('Fuente de la trayectoria',['Oficiales','Personalizado'],key='source',required=True,persist_state='session',label_visibility='collapsed')
    if source=='Oficiales':
        code=st.segmented_control('Escenario',list(LABELS),format_func=lambda c:LABELS[c],key='scenario',required=True,persist_state='session',label_visibility='collapsed')
if source=='Oficiales':
    series=data.get(window,code)
else:
    st.subheader('Experimento personalizado no validado')
    st.caption('Cambiar los valores no ejecuta el motor. Se requiere confirmación explícita; los escenarios oficiales permanecen separados.')
    with st.form('custom_form'):
        columns=st.columns(3)
        values=[column.number_input(label,min_value=0.,value=float(v),format='%.9f',step=.001,key=key)
                for column,label,v,key in zip(columns,['α · aprobación (h⁻¹)','β · despacho (h⁻¹)','γ · entrega (h⁻¹)'],data.parameters,['custom_alpha','custom_beta','custom_gamma'])]
        execute=st.form_submit_button('Ejecutar experimento',key='run_custom',type='primary')
    if execute:
        try:
            with st.spinner('Integrando con RK4 y comprobando cuatro agentes…'):
                st.session_state.custom_result=custom_experiment(data.get(window,'E0'),tuple(values))
            st.session_state.player.seek(0)
        except (ValueError,AssertionError) as exc:
            st.error(f'No se ejecutó el experimento: {exc}. Se mantiene h=0,25 h, sin recortes ni correcciones.')
    custom_result=st.session_state.get('custom_result')
    if custom_result is None or custom_result.window!=window:
        st.info('Ejecute un experimento para esta ventana antes de reproducirlo.')
        st.stop()
    series=cast(ScenarioSeries,custom_result)
    code='Personalizado'
    st.info('Experimento personalizado no validado. α={:.9g}, β={:.9g}, γ={:.9g} h⁻¹'.format(*series.parameters))
player=st.session_state.player
player.context(window,code)
maxima=np.maximum(data.visual_maxima(window),series.states[:,:3].max(axis=0))
cumulative_purchases=series.cumulative_purchases
terminal_max=max(1.,*(data.get(window,c).states[-1,3]-data.get(window,c).states[0,3] for c in LABELS),series.states[-1,3]-series.states[0,3])
visual_maxima=np.r_[maxima,terminal_max]
visual_quantities=np.column_stack([series.states[:,:3],series.states[:,3]-series.states[0,3]])
minima=visual_quantities.min(axis=0);observed_maxima=visual_quantities.max(axis=0)
flow_maxima=np.maximum(1.,np.stack([np.r_[s.purchases.max(),s.flows.max(axis=0)]
    for s in [*(data.get(window,c) for c in LABELS),series]]).max(axis=0))


def seek_widget():
    player.seek(int(st.session_state.time_index))


def move(amount):
    player.seek(max(0,min(series.duration,player.index+amount)))


def speed_change():
    player.set_speed(st.session_state.play_speed,time.monotonic(),series.duration)


@st.fragment(run_every=.5)
def playback():
    player.tick(time.monotonic(),series.duration)
    st.session_state.time_index=player.index
    with st.container(horizontal=True,vertical_alignment='bottom'):
        st.button('Reproducir',icon=':material/play_arrow:',key='play',on_click=lambda:player.play(time.monotonic(),series.duration),disabled=player.index==series.duration)
        st.button('Pausar',icon=':material/pause:',key='pause',on_click=player.pause)
        st.button('Reiniciar',icon=':material/restart_alt:',key='reset',on_click=lambda:player.seek(0))
        st.button('−1 hora',key='previous_hour',on_click=move,args=(-1,),disabled=player.index==0)
        st.button('+1 hora',key='next_hour',on_click=move,args=(1,),disabled=player.index==series.duration)
        st.selectbox('Horas simuladas / segundo real',SPEEDS,index=SPEEDS.index(player.speed),key='play_speed',on_change=speed_change,width=180)
    st.slider('Seleccionar hora de la trayectoria (control)',min_value=0,max_value=series.duration,step=1,key='time_index',on_change=seek_widget,label_visibility='collapsed',help='El instante publicado aparece en los tanques. Este control solicita una hora; no mantiene otro reloj.')
    snap=snapshot(series,player.index,cumulative_purchases)
    payload=visual_payload(snap,visual_maxima,flow_maxima,minima,observed_maxima,player.playing,window,code)
    st.session_state.frame_revision=st.session_state.get('frame_revision',0)+1
    connected_tanks(frame_payload(payload,series,snap,st.session_state.frame_revision,player.speed))
    st.caption('Cada registro histórico corresponde a una hora. RK4 calcula cuatro subpasos de 0,25 horas. Los flujos mostrados son pedidos transferidos durante la última hora; no son la variación neta de un tanque.')
    st.caption('La gráfica móvil muestra contexto cercano, sin suavizado; las trayectorias completas y sus picos están en Escenarios.')


playback()
st.divider()
st.caption('Descargas de la trayectoria completa seleccionada; el índice del reproductor no recorta los archivos.')
download('Descargar trayectoria',series.frame(),f'trayectoria_{window}_{code}.csv','export_trajectory')
if series.custom:
    download('Descargar indicadores personalizados',custom_indicators(series,data.horizons(window)),f'indicadores_personalizados_{window}.csv','export_custom')
