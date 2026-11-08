# Evidencias pendientes para el cierre académico — OLIST / LAB

## Estado de la revisión

Se localizaron y revisaron informes, CSV, código y registros de ejecución. Se inspeccionaron visualmente los PNG existentes `graficas_validacion/X3.png`, `graficas_escenarios/principal_area_acumulada_P.png` y `graficas_escenarios/principal_X3.png`. **No se inspeccionó visualmente una pantalla actual de Streamlit ni se tomaron capturas de la aplicación en esta revisión.** El registro previo informa que no había navegador conectado.

No se encontró la guía `Guia_Proyecto_Simulacion_Tanques_Parejas (1).docx`, respaldo docente archivado, ficha de descarga/licencia local ni capturas actuales identificadas de la interfaz. Son evidencias pendientes, no fallos ocultos del software. Los nombres de imágenes siguientes son propuestas para archivos futuros: no se presentan como archivos ya existentes.

## Documentos y datos administrativos

| Evidencia | Qué debe contener | Uso | Estado |
|---|---|---|---|
| Guía original del profesor | Word completo con rúbrica, requisitos, preguntas y condiciones de exposición | Contrastar matriz y guiones | Pendiente: copiar a la raíz `Olist/`. |
| Autorización de adaptación logística | Correo, mensaje, acta o documento auténtico del docente donde conste la aceptación y su alcance | Respaldar el uso de tanques virtuales | Aprobación informada por el estudiante; respaldo pendiente de archivo. |
| Datos de portada | Nombres de ambos integrantes y fecha de sustentación confirmada | Diapositiva 1 | Pendiente; no completar con datos inferidos. |
| Duración y preguntas de sustentación | Texto exacto de la guía o instrucción docente | Ensayo y guion oral | Pendiente; las preguntas actuales son preparatorias. |

## Procedencia del dataset

Conservar la [publicación Olist/Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) como referencia primaria. La página se identificó, pero la herramienta no obtuvo texto legible de su ficha; no se certificaron por esa vía condiciones de licencia ni una versión remota específica.

Archivar una captura o exportación real de la ficha con título, autor/publicador, URL y condiciones de uso visibles. Guardar versión y fecha de descarga si existe el registro original; si no se conoce la fecha, dejarla como no documentada. Un archivo nuevo de evidencia debe registrar su fecha de captura real, sin atribuirle retroactivamente la descarga del ZIP.

El ZIP local sí está conservado y se leyó sin modificar. Su SHA-256 es:

```text
967e41e04fc306fe604e2a693f488995a8b41e5047418f8a5c8e4abd6deca784
```

Contiene `olist_orders_dataset.csv`, con 99.441 filas e identificadores únicos. La cohorte local contiene 95.082 filas. La auditoría y los archivos `exclusiones.csv`, `calidad_fechas.csv` y `anomalias_cronologicas.csv` documentan la transformación. Estas comprobaciones prueban trazabilidad interna; no sustituyen un registro de procedencia externa ni una comparación de hashes con el publicador.

Los registros son históricos y observacionales. No describirlos como experimentos realizados por los integrantes ni como mediciones propias con sensores. No inventar constancias de autenticidad, autoría, licencia o descarga.

## Capturas reales que deben obtenerse

Guardar preferiblemente en una carpeta nueva `reports/evidencias_streamlit/`, junto con un índice que registre archivo, versión de la aplicación, fecha real de captura, pantalla, ventana, escenario e índice. No hace falta cambiar código para obtenerlas.

| Nombre propuesto — aún no creado | Pantalla y configuración | Qué debe verse | Destino recomendado |
|---|---|---|---|
| `simulacion_inicio_E0_h0.png` | Simulación; principal; E0; hora 0; pausa | X0=(113,586,3005,53963), incremento de T4=0, fecha 2018-03-02 22:00 y ausencia de intervalo previo | Respaldo de inicialización y demostración. |
| `simulacion_intermedia_E0_h168.png` | Simulación; principal; E0; hora 168; pausa | Fecha 2018-03-09 22:00, cuatro tanques y conexiones, entrada/salida, controles y escala relativa | Captura obligatoria de diapositiva 7. |
| `comparacion_escenarios_principal_5488h.png` | Escenarios; principal; horizonte 5488 h; variable área | E0/E1/E2, áreas 13.339.474,31 / 12.860.070,72 / 11.660.143,58 pedidos·hora, horizonte y leyenda | Respaldo de diapositivas 10–11; usar el PNG de área existente como figura principal para no duplicar. |
| `datos_vs_modelo_X3_principal.png` | Datos y validación; ventana principal; X3; cobertura ventana actual | Observado frente a E0, fechas y unidad pedidos | Respaldo de diapositiva 9; el PNG `graficas_validacion/X3.png` ya existe y puede usarse en ella. |
| `validacion_metricas_detalle.png` | Datos y validación; detalle técnico abierto | NRMSE 0,995 / 0,559 / 0,666; criterio ≤0,30; categoría C interna y explicación | Evidencia de transparencia y límites. |
| `metodologia_ecuaciones_parametros.png` | Metodología | Cuatro EDO, conservación, unidades y tres coeficientes | Respaldo de diapositivas 5–8. Si hace falta desplazamiento, capturar dos vistas reales con nombres distintos. |
| `pruebas_188_aprobadas.png` | Terminal con la ejecución correspondiente o informe real abierto | Comando, resultado «188 passed», ausencia de fallos y contexto de archivo | Diapositivas 7 y 13 y expediente de ejecución. El registro textual ya existe. |

Las pruebas no tienen una pantalla propia en Streamlit: capturar su evidencia desde la terminal o desde el informe real. No simular una pantalla de aplicación ni generar una terminal falsa. Si se decide ejecutar de nuevo la suite, guardar ese resultado como un registro nuevo, sin reemplazar el histórico ni presentar una captura antigua como actual.

## Grabación para confirmar la versión vigente

Preparar una grabación real de aproximadamente 20–30 segundos, o varias si hace falta, que muestre reproducción a 168 horas simuladas por segundo real, pausa/reanudación, cambio E0→E1→E2 en el mismo instante y cambio a enero con reinicio. Incluir una secuencia alrededor de las horas 1217–1301 para verificar que fecha, niveles, progreso, indicadores y marcador pertenecen al mismo fotograma. En principal, esos índices corresponden a 2018-04-22 15:00 y 2018-04-26 03:00.

Comprobar también final 5488 en principal y 744 en enero, sin desbordamiento; ausencia de movimiento en conexiones de flujo cero; T4 total separado de incremento; legibilidad a 1920×1080 y 1366×768. En una ventana estrecha, verificar desplazamiento horizontal y nombres completos. Los controles, la captura y la grabación deben corresponder a la misma versión de código.

Las pruebas de API y de JavaScript con DOM simulado no comprueban la apariencia, las transiciones CSS ni posibles solapamientos. No marcar esta revisión visual como completada hasta observar la ejecución real.

## Evidencias ya disponibles y cómo usarlas

| Archivo o conjunto | Qué acredita | Qué no acredita |
|---|---|---|
| ZIP y [auditoría](auditoria_dataset.md) | Archivo local, conteos, depuración y reconstrucción | Mediciones propias o representación de todos los pedidos operativos. |
| `parametros_calibrados.json` y `calibracion_modelo.md` | Método, período y tasas estimadas | Capacidades físicas o precisión futura garantizada. |
| `resumen_validacion.json` y `metricas_validacion.csv` | Evaluación posterior al ajuste y errores finales | Pronóstico de compras futuras o eliminación del sesgo retrospectivo. |
| `indicadores_horizontes.csv` y `comparacion_escenarios.json` | Comparación interna con entradas e inicio comunes | Mejoras reales de costos, personal, energía o retrasos. |
| `graficas_validacion/` y `graficas_escenarios/` | Resultados graficados desde los experimentos registrados | Capturas de la aplicación interactiva actual. |
| [Registro de 188 pruebas](pruebas_refinamiento.txt) | Suite aprobada, revisión de tipos y 36 interacciones API registradas | Exactitud estadística suficiente ni inspección visual del navegador. |
| `integridad_redisenio.json` | Huellas de 119 archivos científicos anteriores | Autorización docente o procedencia externa del ZIP. |

## Antes de elaborar el PowerPoint

1. Copiar la guía, archivar la aprobación y completar los campos administrativos. Cotejar las preguntas originales con el guion oral.
2. Obtener las capturas y la grabación auténticas. Revisar que las cifras y etiquetas coincidan con los CSV y la ventana elegida.
3. Revisar con el equipo el guion de 13 diapositivas y la conclusión limitada a E2 dentro del modelo. Mantener los errores de validación visibles.
4. Confirmar las condiciones de uso de la fuente Olist y preparar una bibliografía breve con vínculos a los documentos completos.
5. Verificar tamaño de letra, unidades, leyendas y la escala de millones en la figura de área. No comprimir todo el guion oral en las diapositivas.
6. Ensayar ambos integrantes todas las secciones. Conservar un respaldo local del proyecto, figuras y evidencias; no ejecutar calibración o validación nueva para preparar la exposición.

Estas tareas documentales y visuales son el cierre pendiente. No requieren alterar el dataset, parámetros, ecuaciones, motores o resultados científicos.
