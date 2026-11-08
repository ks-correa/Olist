# Rediseño de cuatro tanques conectados

## Implementación

El componente `ui/tanks.py` usa la API instalada `st.components.v2.component` de Streamlit 1.67.0. HTML, SVG, CSS y JavaScript se registran como contenido inline: no se añaden paquetes, recursos remotos ni otro motor. Su clave estable permite conservar el dibujo entre actualizaciones; JavaScript construye los nodos una vez y actualiza texto, altura y animación. Los estilos se aíslan dentro del componente.

`visual_payload` recibe la misma fotografía `snapshot` que usan la fecha, las métricas y el marcador de la gráfica. Las cantidades originales se transmiten con precisión completa. Cada altura es nivel/escala; para T4 se usa (X4−X4 inicial)/escala. La variación neta es X(t)−X(t−1) y se distingue de las transferencias calculadas por RK4. En el instante inicial no se inventa una hora anterior.

Los contornos son verticales y los bloques abstractos representan agregados de pedidos. Las conexiones están orientadas Compras → T1 → T2 → T3 → T4, con flechas y trazos que se desplazan en ese sentido. T4 no tiene salida: registra entregas ya terminadas. Cada conexión se anima sólo cuando el reproductor avanza y su transferencia es positiva. Su período visual varía de 2,6 a 0,8 segundos según la raíz de la magnitud normalizada; esta transformación es exclusivamente gráfica. Se respeta `prefers-reduced-motion`.

Las escalas de nivel y referencias de flujo se calculan antes del fragmento y comparten máximos de los tres escenarios oficiales de la ventana. Una trayectoria personalizada puede ampliar su propia escala para contener sus niveles; nunca cambia los oficiales. No se muestran porcentajes de capacidad física. Los mínimos y máximos corresponden a la trayectoria completa seleccionada.

## Pantalla y transparencia

La simulación muestra encabezado breve, selectores y controles compactos, tanques protagonistas, métricas del instante y detalles/gráfica. Se conserva el reloj de Python, las cinco velocidades y todas las acciones anteriores. El SVG tiene ancho mínimo de 1000 píxeles dentro de una región desplazable horizontalmente y escala proporcionalmente en escritorio.

Simulación y Escenarios muestran el aviso breve solicitado y una referencia a Datos y validación. Esta última conserva categoría C, NRMSE originales y criterio 0,30, explica calibración frente a validación y aclara que C es una clasificación interna académica, no oficial de Olist. Las áreas completas siguen siendo E0 13.339.474,31; E1 12.860.070,72; E2 11.660.143,58 pedidos·hora. Las reducciones de 3,59 % y 12,59 % son resultados internos del modelo.

Las tablas usan copias de presentación con nombres comprensibles, separadores españoles y dos decimales (tres para NRMSE); valores no nulos menores de 0,005 pedidos se muestran como ≈ 0. Los valores en memoria y CSV no se redondean.

## Integridad y verificaciones

`reports/integridad_redisenio.json` contiene las huellas SHA-256 tomadas antes de editar los archivos científicos existentes en src, data y reports. La prueba de integridad comprueba que siguen intactos; incluye parámetros, motores, trayectorias y validación. No se han recalibrado tasas ni modificado configuraciones E0/E1/E2.

Las 146 pruebas anteriores se conservan sin cambios. Se añaden 30 pruebas de alturas, escalas, transferencias, flujo cero, T4, fechas, controles, formato, exportación e integridad. Se comprueba también el contenido enviado al componente desde AppTest. El informe de ejecución es `reports/pruebas_tanques.txt`.

La API real de Streamlit se utiliza para comprobar el arranque, las cinco pantallas, ambas ventanas, escenarios, límites temporales, experimentación libre y concordancia entre índice del componente y deslizador. `node --check` revisa la sintaxis JavaScript; estas verificaciones no renderizan ni comprueban visualmente las animaciones.

## Revisión visual pendiente

No hay navegador conectado en esta sesión (`apps=[]`, `browsers=[]`). Para revisar la apariencia y el movimiento, enviar:

1. Captura de Simulación completa a 1920×1080, con T1–T4 y controles visibles, en la hora 168 de E0.
2. Captura a 1366×768 y otra en ventana estrecha, comprobando desplazamiento horizontal y nombres completos.
3. Grabación de 20–30 segundos: reproducir a 24 y 168 horas/segundo real, pausar, retroceder una hora, cambiar E0→E1→E2, pasar a enero y llevar el deslizador al final.

Comprobar que los trazos avanzan hacia la derecha sólo con flujo positivo; alturas cambian suavemente sin parpadeo; pausa congela transferencias, fecha y estado; escalas permanecen al alternar escenarios; enero reinicia; T4 distingue incremento de total. En el final debe detenerse sin desbordamiento. Con movimiento reducido, no debe haber animación CSS.

## Inicio

```powershell
cd C:\Users\User\Desktop\Olist
.venv/Scripts/python.exe -m streamlit run app.py
```

Archivos de esta iteración: `ui/tanks.py`, `ui/components.py`, `app.py`, `app_pages/simulation.py`, `app_pages/scenarios_view.py`, `app_pages/validation_view.py`, `.streamlit/config.toml`, `tests/test_tanks.py`, README, guía de uso, esta nota y los nuevos informes de integridad y pruebas. No se añaden dependencias.
