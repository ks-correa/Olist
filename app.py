"""Aplicación académica Olist: datos existentes y cuatro agentes agregados."""
import streamlit as st
from src.dashboard_metrics import PlayerState
from src.dashboard_data import WINDOWS
from ui.components import dataset

st.set_page_config(page_title='Olist · Laboratorio logístico',page_icon=':material/hub:',layout='wide')
if 'player' not in st.session_state:
    st.session_state.player=PlayerState()
st.session_state.setdefault('window','principal')
st.session_state.setdefault('scenario','E0')
st.session_state.setdefault('source','Oficiales')
with st.sidebar:
    st.markdown('### :material/hub: OLIST / LAB')
    st.caption('MODELADO Y SIMULACIÓN CONTINUA')
    st.selectbox('Ventana de estudio',list(WINDOWS),format_func=lambda w:WINDOWS[w],key='window')
    st.divider()
    st.caption('Cuatro agentes · Un balance de pedidos')
    st.markdown('**RK4 · 0,25 h**  \nPython + AgentPy')
    st.caption('Cohorte retrospectiva de 95.082 pedidos entregados completos.')
page=st.navigation([
    st.Page('app_pages/overview.py',title='Vista general',icon=':material/dashboard:',default=True,url_path='inicio'),
    st.Page('app_pages/simulation.py',title='Simulación',icon=':material/play_circle:',url_path='simulacion'),
    st.Page('app_pages/scenarios_view.py',title='Escenarios',icon=':material/compare_arrows:',url_path='escenarios'),
    st.Page('app_pages/validation_view.py',title='Datos y validación',icon=':material/analytics:',url_path='validacion'),
    st.Page('app_pages/methodology.py',title='Metodología',icon=':material/functions:',url_path='metodologia'),
    st.Page('app_pages/model_v2_view.py',title='Laboratorio V2',icon=':material/science:',url_path='modelo-v2'),
],position='top')
p=st.session_state.player
p.context(st.session_state.window,st.session_state.scenario)
if st.session_state.get('last_page')!=page.url_path:
    p.pause();st.session_state.last_page=page.url_path
try:
    with st.spinner('Verificando trayectorias e indicadores…'):
        dataset()
except (ValueError,OSError,KeyError) as exc:
    st.error(f'No se pudieron verificar los resultados: {exc}')
    st.stop()
page.run()
