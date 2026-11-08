import numpy as np
import streamlit as st
import plotly.graph_objects as go
from ui.components import dataset,number,base_figure,plot,download,presentation_table

st.title('Datos reales y validez del modelo')
st.write('Resultados de validación del modelo: el sistema fue calibrado con registros históricos de Olist y evaluado posteriormente con datos independientes. La comparación permitió identificar diferencias entre los niveles observados y los simulados. Estas diferencias se cuantifican mediante MAE, RMSE y NRMSE y delimitan el alcance de los escenarios estudiados.')
data=dataset();window=st.session_state.window
st.caption('Los registros observados y el modelo base se distinguen explícitamente. Los escenarios E1 y E2 no son datos históricos.')
with st.container(horizontal=True):
    for row in data.validation.iloc[:3].itertuples():
        st.metric(f'{row.variable} · NRMSE',number(row.NRMSE,3),border=True)
    st.metric('Criterio académico','≤ 0,30',border=True)
with st.expander('Detalle técnico · criterio y clasificación de validación'):
    st.write('Ninguna de las tres etapas X1, X2 y X3 alcanzó el criterio interno NRMSE ≤ 0,30. La clasificación final se mantiene en C: el modelo tiene diferencias importantes frente a los niveles observados y no acredita beneficios operativos reales.')
    st.caption('Categoría C es una clasificación académica interna adoptada en este proyecto. No es una calificación oficial de Olist.')
left,right=st.columns([1,2])
with left:
    variable=st.selectbox('Depósito histórico',['X1','X2','X3','X4'],key='historical_variable')
    scope=st.segmented_control('Cobertura',['Ventana actual','Cohorte completa'],default='Ventana actual',required=True,key='historical_scope')
    st.caption('X4 se presenta incremental en la ventana actual y acumulado desde el origen en la cohorte completa. Fechas originales, sin conversión de zona horaria.')
with right:
    reference=data.get(window,'E0');history=data.historical
    if scope=='Ventana actual':
        history=history.loc[(history.corte_horario>=reference.dates[0])&(history.corte_horario<=reference.dates[-1])]
    observed=history[variable].to_numpy(dtype=float)
    simulated=reference.states[:,int(variable[1])-1].copy()
    if variable=='X4' and scope=='Ventana actual':
        observed=observed-reference.states[0,3];simulated=simulated-reference.states[0,3]
    fig=base_figure(f'{variable} · observado frente a modelo base')
    fig.add_trace(go.Scatter(x=history.corte_horario,y=observed,name='Observado Olist',line=dict(color='#087F8C',width=1.4)))
    fig.add_trace(go.Scatter(x=reference.dates,y=simulated,name='E0 simulado',line=dict(color='#334155',width=1.5)))
    plot(fig,'historical_chart','Serie histórica observada y modelo base, identificados por leyenda')
st.subheader('Evaluación final congelada · marzo–octubre 2018')
st.caption('La tabla corresponde exclusivamente al período final, incluso si está seleccionada enero como ventana de exploración.')
st.dataframe(presentation_table(data.validation[['variable','MAE','RMSE','NRMSE','sesgo_medio','error_nivel_maximo','error_final']]),hide_index=True,alt='Métricas finales por depósito')
with st.container(horizontal=True):
    for label,explanation in [('MAE','Magnitud media del error, en pedidos.'),('RMSE','Penaliza más los errores grandes, en pedidos.'),
                              ('NRMSE','RMSE dividido por la escala congelada de entrenamiento; adimensional.')]:
        with st.container(border=True,width=270):
            st.markdown(f'**{label}**');st.write(explanation)
st.write('La conservación y convergencia verifican el algoritmo. El ajuste mide entrenamiento; la validación mide desempeño fuera del ajuste. Los escenarios son hipótesis condicionadas a compras conocidas. Pronosticar operaciones futuras requiere demanda futura y un modelo suficientemente validado.')
download('Descargar tabla de validación',data.validation,'metricas_validacion_final.csv','export_validation')
