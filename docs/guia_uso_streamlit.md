# Guía de uso de la aplicación Olist · Fase 6

## Instalación e inicio

Desde PowerShell, en `C:\Users\User\Desktop\Olist`:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m streamlit run app.py
```

Si el entorno se administra con uv, sustituir el primer comando por `uv pip install --python .venv/Scripts/python.exe -r requirements.txt`. Abrir la dirección local que imprime Streamlit, normalmente http://localhost:8501. No requiere cuentas ni servicios externos. Versiones comprobadas: Python 3.12.13, Streamlit 1.67.0, Plotly 7.1.0 y AgentPy 0.1.5. El archivo requirements.txt fija todas las dependencias instaladas.

## Navegación

La barra superior contiene cinco pantallas y la barra lateral selecciona la ventana:

1. **Vista general:** estados del sistema, pendientes y orientación inicial.
2. **Simulación:** reproducción sincronizada de estados, transferencias y compras; exportación de la trayectoria; experimentación libre.
3. **Escenarios:** curvas completas, transferencias, indicadores y diferencias por horizonte, con descargas CSV.
4. **Datos y validación:** serie histórica observada y validación final congelada. La validación corresponde a la ventana principal, incluso si se consulta enero.
5. **Metodología:** ecuaciones, unidades, integración RK4, cuatro agentes y limitaciones.

La ventana principal contiene 5488 intervalos horarios y 5489 estados. Enero contiene 744 intervalos y 745 estados. Los horizontes disponibles son 168, 720, 1440 y 5488 horas en la principal; 168, 720 y 744 en enero. Cada horizonte es una lectura de la trayectoria completa, sin reinicialización.

## Reproductor y cuatro agentes

El componente central representa cuatro tanques virtuales conectados: T1 pendientes de aprobación, T2 pendientes de despacho, T3 pendientes de entrega y T4 entregados acumulados. Los bloques internos representan cantidades agregadas, nunca agua ni pedidos individuales. Las alturas son proporcionales al nivel y usan escalas relativas de visualización, nunca capacidades físicas. Las escalas de T1–T3 se mantienen al comparar E0, E1 y E2 en una misma ventana. La altura de T4 representa las entregas adicionales desde el inicio de la ventana; su total acumulado aparece por separado.

Fecha, niveles, entradas, salidas, progreso, indicadores y marcador de la gráfica móvil ahora se publican juntos dentro del componente, descartando revisiones antiguas. El deslizador es un control que solicita la hora al reloj de Python; el instante publicado se lee en el componente. La pausa fija también la altura gráfica. Véase la [investigación y protocolo de sincronización](refinamiento_interfaz.md).

Las conexiones muestran λ(t), q12, q23 y q34, con cantidades transferidas durante la última hora. Los trazos avanzan de izquierda a derecha sólo durante reproducción y con flujo positivo. Su rapidez depende cualitativamente del flujo calculado, normalizado con una referencia común de la ventana; no representa velocidad física. Al pausar se detienen; con flujo cero desaparecen. El componente SVG persistente actualiza nodos y alturas con transiciones de presentación de 0,35 segundos. No interpola estados matemáticos ni ejecuta otro modelo. En pantallas estrechas el diagrama admite desplazamiento horizontal para conservar la legibilidad.

Reproducir avanza el reloj; pausar lo detiene; reiniciar vuelve a cero. Los botones permiten avanzar o retroceder una hora y el deslizador permite elegir cualquier corte. Las velocidades son 1, 6, 24, 72 y 168 horas simuladas por segundo real. Un fragmento de Streamlit actualiza la pantalla cada 0,5 segundos aproximadamente; la carga del navegador puede reducir la frecuencia efectiva. No se integra el modelo por fotograma: un único índice consulta las matrices precalculadas y sincroniza tarjetas, fecha, indicadores y marcador.

Al final se detiene y se deshabilita iniciar. Cambiar el escenario pausa y conserva el índice; cambiar la ventana pausa y vuelve al comienzo. Navegar a otra pantalla también pausa. Las transferencias corresponden al intervalo que termina en el corte mostrado; en el corte inicial no existe intervalo anterior dentro de la ventana.

## Escenarios e indicadores

E0 usa los parámetros base congelados; E1 aumenta beta un 20 % y E2 aumenta gamma un 20 %. Se mantienen las llegadas y condiciones iniciales de cada ventana. P es X1+X2+X3; el área acumulada de P usa trapecios sobre cortes horarios y se expresa en pedidos·hora. Las entregas incrementales son X4(t)−X4(0). Las diferencias porcentuales se calculan respecto a E0; no se interpreta un porcentaje con base cero.

Las trayectorias oficiales se leen de los CSV existentes y se comprueban contra sus huellas SHA-256, balances e indicadores. No se recalibran parámetros. Las descargas incluyen la ventana y el escenario elegidos; descargar la trayectoria produce la ventana completa y no sólo el fotograma actual. La tabla de validación exportada es la validación final principal, identificada como tal.

## Experimento personalizado

En Simulación, seleccionar Personalizado, introducir alpha, beta y gamma y pulsar **Ejecutar experimento**. Editar los campos no ejecuta el motor. El cálculo usa RK4 con h=0,25 horas y exactamente cuatro agentes AgentPy, verifica igualdad entre ambos resultados y conserva los datos en memoria de la sesión. No sobrescribe archivos oficiales. Un resultado de otra ventana requiere una nueva ejecución. Parámetros inestables producen un error explícito, sin recortar estados ni cambiar el paso. Se pueden descargar trayectoria e indicadores personalizados.

## Limitaciones científicas

Modelo de simulación académica. Validación categoría C: los resultados de escenarios son hipotéticos y no constituyen mejoras operativas comprobadas para Olist.

Los NRMSE de X1, X2 y X3 son aproximadamente 0,995, 0,559 y 0,666, superiores al criterio 0,30. La cohorte retrospectiva de entregados completos y los depósitos agregados limitan la generalización. No se incorporan pedidos individuales, capacidad, recursos, rutas o causalidad operativa. Los colores y movimientos no añaden evidencia científica.

## Pruebas y revisión visual

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m pytest tests/test_dashboard.py -q
```

Las pruebas cubren lectura de ambas ventanas y seis trayectorias, índices y fechas, flujos, exportación, conservación, reloj, modo personalizado y las cinco pantallas con AppTest. También se inició Streamlit y se consultó su API real de agente, incluyendo navegación y controles. Véase `reports/pruebas_dashboard.txt`.

No hubo navegador disponible en el entorno de ejecución: la animación no fue inspeccionada visualmente. Al abrir la aplicación comprobar:

- Legibilidad y ausencia de solapamientos en escritorio y ventana estrecha; tablas y descargas accesibles.
- Flechas en movimiento al iniciar y detenidas al pausar o llegar al final; respeto de la preferencia de movimiento reducido.
- Fecha, tarjetas, marcador y transferencias sincronizados al mover el deslizador y reproducir a cada velocidad.
- Escenario distinto conserva el corte y pausa; ventana distinta reinicia y pausa; no aparecen valores de la ventana anterior.
- Inicio sin transferencias anteriores, final sin desbordamiento, reinicio correcto y descargas reconocibles en Excel.

## Archivos de la interfaz

`app.py` define navegación y contexto; `app_pages/` contiene las cinco pantallas; `ui/components.py` centraliza presentación y caché; `src/dashboard_data.py` valida y exporta datos y ejecuta experimentos; `src/dashboard_metrics.py` implementa el reloj y la lectura sincronizada; `.streamlit/config.toml` define el tema. Los módulos científicos anteriores permanecen separados.
