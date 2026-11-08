"""Carga cacheada y elementos comunes; datos científicos siempre de sólo lectura."""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.dashboard_data import load_dashboard,file_signature,WARNING,LABELS,export_csv
from src.scenarios import COLORS

ROOT=Path(__file__).resolve().parents[1]


@st.cache_data(show_spinner=False,max_entries=2)
def _cached_data(root,signature):
    return load_dashboard(root)


def dataset():
    return _cached_data(str(ROOT),file_signature(ROOT))


def warning():
    st.warning(WARNING,icon=':material/science:')


def exploratory_notice():
    st.caption('Modelo exploratorio basado en datos reales. Los escenarios representan resultados hipotéticos. [Datos y validación](validacion)')


def number(value,digits=2):
    if 0 < abs(value) < .005:
        return '≈ 0'
    return f'{value:,.{digits}f}'.replace(',','_').replace('.',',').replace('_','.')


PUBLIC_NAMES = {
    'escenario':'Escenario','ventana':'Ventana','horizonte_horas':'Horizonte (horas)',
    'variable':'Depósito','P_final':'Pendientes al final','P_maximo':'Máximo de pendientes',
    'P_promedio':'Promedio de pendientes','P_area_pedidos_hora':'Área de pendientes (pedidos·hora)',
    'entregas_incrementales':'Entregas de la ventana','X4_incremental':'Entregas de la ventana',
    'X1_final':'Pendientes de aprobación al final','X2_final':'Pendientes de despacho al final',
    'X3_final':'Pendientes de entrega al final','sesgo_medio':'Sesgo medio (pedidos)',
    'MAE':'Error absoluto medio (pedidos)','RMSE':'Raíz del error cuadrático medio (pedidos)',
    'NRMSE':'Error normalizado (NRMSE)','error_nivel_maximo':'Error en el nivel máximo',
    'error_final':'Error al final','indicador':'Indicador','diferencia_absoluta':'Diferencia absoluta',
    'diferencia_porcentual':'Diferencia (%)','valor_base':'Valor base','valor_escenario':'Valor del escenario',
    'variacion_porcentual':'Variación (%)','compras_acumuladas':'Compras acumuladas',
}
for _variable,_label in [('X1','aprobación'),('X2','despacho'),('X3','entrega'),('P','pendientes totales')]:
    for _suffix,_prefix in [('inicial','Nivel inicial de'),('maximo','Nivel máximo de'),
                             ('promedio','Nivel promedio de'),('area_pedidos_hora','Área de')]:
        PUBLIC_NAMES[f'{_variable}_{_suffix}']=f'{_prefix} {_label}'
for _flow,_label in [('q12','Aprobaciones'),('q23','Despachos'),('q34','Entregas')]:
    PUBLIC_NAMES[f'{_flow}_acumulado']=f'{_label} '+('acumulados' if _flow=='q23' else 'acumuladas')
    PUBLIC_NAMES[f'{_flow}_media_por_hora']=f'{_label}: promedio por hora'


def presentation_table(frame):
    """Copia de presentación; los datos y CSV conservan sus valores originales."""
    result=frame.copy()
    for column in result:
        if pd.api.types.is_numeric_dtype(result[column]):
            digits=3 if column=='NRMSE' else 2
            result[column]=result[column].map(lambda v:'—' if pd.isna(v) else number(v,digits))
        elif column in ('indicador','variable'):
            result[column]=result[column].map(lambda v:PUBLIC_NAMES.get(v,v))
    return result.rename(columns=PUBLIC_NAMES)


def frame_date(value):
    return np.datetime_as_string(np.datetime64(value),unit='m').replace('T',' ')


def base_figure(title,unit='Pedidos',height=340):
    fig=go.Figure()
    fig.update_layout(title=title,height=height,margin=dict(l=20,r=20,t=50,b=25),
        paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial',color='#173347'),legend=dict(orientation='h',y=-.2),
        hovermode='x unified',yaxis_title=unit,xaxis_title='Fecha del dataset',separators=',.')
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='#dce6eb',rangemode='tozero')
    return fig


def plot(fig,key,alt):
    fig.update_traces(hovertemplate='%{x}<br>%{y:,.2f}<extra>%{fullData.name}</extra>',selector=dict(type='scatter'))
    st.plotly_chart(fig,key=key,width='stretch',config={'displaylogo':False,'scrollZoom':False},alt=alt)


def scenario_chart(data,window,variable,horizon=None):
    fig=base_figure({'X4_incremental':'Entregas incrementales','P':'Pedidos pendientes','area':'Acumulación sostenida'}.get(variable,variable),
                    'Pedidos·hora' if variable=='area' else 'Pedidos')
    for code in LABELS:
        s=data.get(window,code);end=s.duration if horizon is None else horizon
        values=(s.states[:,3]-s.states[0,3] if variable=='X4_incremental' else
                s.states[:,:3].sum(axis=1) if variable=='P' else s.area if variable=='area' else s.states[:,int(variable[1])-1])
        fig.add_trace(go.Scatter(x=s.dates[:end+1],y=values[:end+1],name=LABELS[code],
            mode='lines',line=dict(color=COLORS[code],width=1.7)))
    return fig


def download(label,frame,filename,key):
    st.download_button(label,export_csv(frame),file_name=filename,mime='text/csv',key=key,
                       icon=':material/download:',on_click='ignore')


def connector(playing=False):
    # Sólo flechas conceptuales: la animación CSS no representa pedidos individuales.
    motion='running' if playing else 'paused'
    st.html(f'''<style>
    .olist-route{{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px;
      padding:14px 20px;background:#eaf1f5;border-radius:12px;color:#176271;font:600 13px Arial;margin:8px 0 16px}}
    .olist-route .arrow{{font-size:23px;animation:olist-flow 1s ease-in-out infinite;animation-play-state:{motion}}}
    @keyframes olist-flow{{0%,100%{{opacity:.35;transform:translateX(-3px)}}50%{{opacity:1;transform:translateX(3px)}}}}
    @media(prefers-reduced-motion:reduce){{.olist-route .arrow{{animation:none}}}}
    </style><div class="olist-route" aria-label="Compras a aprobación, despacho, transporte y entregas">
    <span>Compras</span><span class="arrow">→</span><span>T1 · Aprobación</span><span class="arrow">→</span>
    <span>T2 · Despacho</span><span class="arrow">→</span><span>T3 · Transporte</span><span class="arrow">→</span>
    <span>T4 · Entregados</span></div>''')
