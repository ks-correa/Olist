import streamlit as st
import plotly.graph_objects as go
from src.dashboard_data import LABELS
from src.scenarios import COLORS
from ui.components import dataset,scenario_chart,plot,download,number,frame_date,base_figure,presentation_table

st.title('Tres escenarios, las mismas compras')
st.caption('Comparación de estrategias hipotéticas mediante un modelo calibrado con datos históricos de Olist.')
data=dataset();window=st.session_state.window
horizons=data.horizons(window)
horizon=st.select_slider('Horizonte de comparación (horas)',options=horizons,value=horizons[-1],key=f'horizon_{window}')
reference=data.get(window,'E0')
st.caption(f'Desde {frame_date(reference.dates[0])} hasta {frame_date(reference.dates[horizon])} · {horizon} horas')
selected=data.indicators.loc[(data.indicators.ventana==window)&(data.indicators.horizonte_horas==horizon)].copy()
for code,column in zip(LABELS,st.columns(3)):
    row=selected.loc[selected.escenario==code].iloc[0]
    with column.container(border=True):
        st.markdown(f'**{LABELS[code]}**')
        st.metric('Pedidos pendientes al horizonte',number(row.P_final))
        st.metric('Área de pendientes (pedidos·hora)',number(row.P_area_pedidos_hora))
        st.caption(f'Entregas incrementales: {number(row.entregas_incrementales)} · Pico P: {number(row.P_maximo)}')
st.write('E1 aumenta un 20 % la tasa efectiva de despacho y reduce la acumulación en T2, aunque puede trasladar temporalmente pedidos hacia T3. E2 aumenta un 20 % la tasa efectiva de entrega y obtiene la menor acumulación sostenida de pedidos dentro del modelo.')
st.caption('X1 coincide en los tres escenarios; E2 también conserva X2. Cada horizonte lee la misma trayectoria, sin reinicialización.')
view=st.segmented_control('Variable para comparar',['P','X1','X2','X3','X4_incremental','area'],
    format_func=lambda v:{'P':'Pendientes totales','X1':'T1 · Aprobación','X2':'T2 · Despacho','X3':'T3 · Entrega','X4_incremental':'Entregas de la ventana','area':'Área de pendientes'}[v],default='P',required=True,key='compare_variable')
plot(scenario_chart(data,window,view,horizon),'comparison_chart','Trayectorias E0, E1 y E2 hasta el horizonte seleccionado')
flow_panel=st.expander('Transferencias integradas por hora',on_change='rerun')
if flow_panel.open:
 with flow_panel:
    flow_kind=st.selectbox('Transferencia',['Aprobaciones','Despachos','Entregas'],key='flow_kind')
    i=['Aprobaciones','Despachos','Entregas'].index(flow_kind)
    fig=base_figure(flow_kind,'Pedidos / intervalo de una hora')
    for code in LABELS:
        s=data.get(window,code)
        fig.add_trace(go.Scatter(x=s.dates[1:horizon+1],y=s.flows[:horizon,i],name=LABELS[code],line=dict(color=COLORS[code],width=1.4)))
    plot(fig,'flows_comparison','Transferencias RK4 horarias de los tres escenarios')
columns=['escenario','P_final','P_maximo','P_promedio','P_area_pedidos_hora','entregas_incrementales','X1_final','X2_final','X3_final']
st.subheader('Indicadores al horizonte')
st.dataframe(presentation_table(selected[columns]),hide_index=True,alt='Indicadores de los tres escenarios al horizonte elegido')
difference=data.differences.loc[(data.differences.ventana==window)&(data.differences.horizonte_horas==horizon)].copy()
st.caption('Variación = 100 × (escenario − E0) / E0. Negativo en pendientes indica reducción; sin porcentaje cuando E0 es cero.')
with st.expander('Diferencias absolutas y porcentuales frente a E0'):
    st.dataframe(presentation_table(difference),hide_index=True,alt='Diferencias de indicadores respecto al base')
if window=='principal':
    st.caption('En el período principal, E1 reduce el área de pendientes un 3,59 % y E2 un 12,59 % frente a E0. E1 puede trasladar temporalmente carga a T3: máximo +73,46 pedidos frente a E0. Son resultados hipotéticos del modelo, no beneficios operativos comprobados.')
else:
    st.caption('Enero de 2018 es sensibilidad sobre desarrollo ya utilizado; no es validación independiente. Sólo se ofrecen 168, 720 y 744 horas.')
with st.container(horizontal=True):
    download('Indicadores del horizonte',selected,f'indicadores_{window}_{horizon}h.csv','export_horizon')
    download('Todos los horizontes de esta ventana',data.indicators.loc[data.indicators.ventana==window],f'indicadores_{window}.csv','export_indicators')
    download('Comparación de diferencias',difference,f'diferencias_{window}_{horizon}h.csv','export_comparison')
