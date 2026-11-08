import streamlit as st
from ui.components import dataset,number,connector,scenario_chart,plot
from src.dashboard_data import WINDOWS

data=dataset();window=st.session_state.window
st.title('Un sistema. Cuatro depósitos. Un balance.')
st.markdown('Explore cómo las compras se convierten en entregas y cómo las tasas de transferencia cambian la acumulación de pedidos.')
with st.container(horizontal=True):
    for label,value,detail in [('Pedidos de la cohorte','95.082','Entregados completos'),('Depósitos virtuales','4','Agentes agregados'),
                                ('Escenarios oficiales','3','Base, despacho y entrega'),('Paso RK4','0,25 h','Cuatro subpasos por hora')]:
        with st.container(border=True,width=245):
            st.metric(label,value)
            st.caption(detail)
connector()
left,right=st.columns([2,1],gap='large')
with left:
    st.subheader('De la compra a la entrega')
    st.write('Cada depósito reúne pedidos en una etapa del proceso. Una salida alimenta al siguiente depósito; el total conserva todas las compras acumuladas. T4 registra entregas y no representa trabajo pendiente.')
    plot(scenario_chart(data,window,'P'),'overview_chart','Pedidos pendientes de E0, E1 y E2 en la ventana seleccionada')
with right:
    with st.container(border=True):
        st.subheader('Ruta de exploración')
        st.markdown('**01 · Reproduzca** las cuatro estaciones en Simulación.\n\n**02 · Compare** intervenciones hipotéticas y horizontes.\n\n**03 · Contraste** el modelo con los registros históricos.')
        st.caption(WINDOWS[window])
        s=data.get(window,'E0')
        st.metric('Compras de la ventana',number(s.purchases.sum(),0))
