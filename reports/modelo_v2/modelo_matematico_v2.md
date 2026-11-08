# Formulación matemática y unidades

V1 se conserva intacto en src/rk4_solver.py. A usa las mismas cuatro EDO,
recalibradas por prefijo para la comparación interna justa. El resultado
histórico de V1 se reproduce por separado con sus tres tasas originales.

## B: calendario, candidato seleccionado de desarrollo

dX1/dt=λ−α(t)X1; dX2/dt=α(t)X1−β(t)X2;
dX3/dt=β(t)X2−γ(t)X3; dX4/dt=γ(t)X3.

k_i(t)=exp(b_i0+b_i1 sin(2πh/24)+b_i2 cos(2πh/24)+b_i3 I_sábado_domingo).
La función es constante en cada intervalo horario, según su extremo izquierdo.
No hay parámetros libres por fecha. El valor b_i0 es logaritmo de la tasa
numérica expresada en h⁻¹, respecto de la referencia 1 h⁻¹.

| variable | b0 | b_sin | b_cos | b_fin_semana |
|---|---|---|---|---|
| X1 | -2.25608 | -0.099826 | -0.190381 | -0.145769 |
| X2 | -4.20056 | -0.115125 | 0.00775009 | -0.537362 |
| X3 | -5.50291 | -0.000676891 | -0.000513232 | -0.0016621 |

Estados en pedidos, flujos en pedidos/h, tiempo en horas; λ es la cantidad
histórica de compras del intervalo dividida por una hora. Coeficientes en h⁻¹;
efectos de calendario adimensionales; áreas en pedidos·hora. Las fechas del
dataset se conservan sin zona horaria inferida. No es un sistema hidráulico.

## C: Erlang de dos fases

Para cada etapa i hay z_i1 y z_i2. d z_i1/dt=u_i−k_i z_i1;
d z_i2/dt=k_i z_i1−k_i z_i2. u_1=λ, u_2=k_1 z_12,
u_3=k_2 z_22 y dX4/dt=k_3 z_32. Xi=z_i1+z_i2.
Son SIETE EDO, no cuatro; permanencia Erlang(2,k_i), media 2/k_i.
Al origen z_i1=z_i2=Xi(0)/2. El reparto se fija sin mirar el futuro.
No se seleccionó C. Sus tasas ajustadas por prefijo están en optimizaciones.json.

## M: mezcla de dos vías exponenciales, segunda ronda adaptativa

Para r=f,s: d z_ir/dt=p_ir u_i−k_ir z_ir;
p_if=p_i, p_is=1−p_i, q_i=Σ_r k_ir z_ir;
u_1=λ, u_2=q_1, u_3=q_2, dX4/dt=q_3, Xi=Σ_r z_ir.
Ley de supervivencia de entrada p_i exp(−k_if t)+(1−p_i)exp(−k_is t).
Son SIETE EDO y nueve parámetros. Inicialización
z_ir(0)=Xi(0)(p_ir/k_ir)/Σ_s(p_is/k_is), aproximación de ocupación estacionaria
que no usa edades observadas posteriores. Es una limitación en transitorios.
La simetría de etiquetas se resuelve ordenando las tasas al finalizar.

## Conservación y numeración

En todos los candidatos Σ_i dXi/dt=λ; sumar subestados una vez, sin duplicar.
Las matrices tienen diagonales no positivas y transferencias no negativas.
RK4 principal usa h=0,25 h, entrada y tasas congeladas por hora también en K4.
El propagador matricial evalúa el polinomio clásico I+Z+Z²/2+Z³/6+Z⁴/24.
La recurrencia triangular se resuelve con solve_banded o lfilter; no es un
suavizador ni usa objetivos futuros. Sin recorte ni restauración artificial
de masa. Se rechazan pasos fuera de las guardas de positividad; controles
de masa usan tolerancia flotante documentada en código, y flujos toleran
solo redondeo de 1e−8 pedidos. No hubo flujos negativos en resultados entregados.
AgentPy mantiene cuatro agentes que publican el agregado del motor común,
incluidos sus subestados cuando existen. Equivalencia exacta verificada.
