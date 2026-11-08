import streamlit as st
from ui.components import dataset,connector

st.title('Balances que conectan las cuatro estaciones')
st.caption('El principio de tanques se aplica a pedidos, no a litros. No se añaden estados logísticos sin fechas verificables.')
connector()
left,right=st.columns([1.3,1],gap='large')
with left:
    st.latex(r'\begin{aligned}\dot X_1&=\lambda(t)-\alpha X_1\\\dot X_2&=\alpha X_1-\beta X_2\\\dot X_3&=\beta X_2-\gamma X_3\\\dot X_4&=\gamma X_3\end{aligned}')
    st.latex(r'\frac{d}{dt}(X_1+X_2+X_3+X_4)=\lambda(t)')
    st.write('Cada transferencia sale de una estación y entra a la siguiente. T4 acumula entregas y no tiene salida. La condición inicial y las compras acumuladas fijan el total de pedidos.')
with right:
    with st.container(border=True):
        st.subheader('Unidades y parámetros')
        a,b,g=dataset().parameters
        st.markdown(f'**Estados X1–X4:** pedidos  \n**Tiempo:** horas  \n**λ:** pedidos/hora  \n**α:** {a:.9g} h⁻¹  \n**β:** {b:.9g} h⁻¹  \n**γ:** {g:.9g} h⁻¹')
        st.caption('Coeficientes efectivos estimados en entrenamiento, no capacidades físicas demostradas.')
for title,text in [('RK4 · integración conjunta','Las cuatro ecuaciones se resuelven simultáneamente con cuatro subpasos por hora. Se conserva la entrada de la misma hora en K1–K4, incluido el borde final.'),
                   ('AgentPy · cuatro agentes','Cada agente mantiene identidad y nivel de un depósito. El modelo lee el vector completo, delega la integración y publica los cuatro nuevos niveles. No existe un agente por pedido.'),
                   ('Reconstrucción histórica','X1=A−B, X2=B−C, X3=C−D, X4=D; A, B, C, D son eventos acumulados con fecha menor o igual al corte. La fila de transferencias pertenece a la hora que termina en ese corte.'),
                   ('Muestreo y reproducción','Los datos se muestrean cada hora; RK4 integra cada 0,25 h. El reproductor recorre estados ya calculados y su velocidad se expresa en horas simuladas por segundo de reloj real.'),
                   ('Supuestos y límites','Transferencias de primer orden, tasas constantes y estados agregados. La cohorte seleccionada retrospectivamente excluye no entregados y cancelaciones. No permite calcular costos, energía o retrasos individuales contrafactuales.')]:
    with st.expander(title):st.write(text)
