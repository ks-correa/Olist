# Matriz de cumplimiento académico — OLIST / LAB

## Alcance de esta revisión

No se encontró `Guia_Proyecto_Simulacion_Tanques_Parejas (1).docx` al buscar documentos Word en el proyecto. Debe copiarse a la raíz de Olist. Esta matriz verifica los requisitos del Prompt 11 y su estructura provisional de 13 diapositivas; no certifica requisitos adicionales, rúbrica, duración ni preguntas que sólo aparezcan en la guía ausente.

La aprobación de la adaptación logística fue comunicada por el estudiante. Se registra como antecedente declarado, sin convertirlo en evidencia documental del docente. El guion conserva exactamente el orden solicitado; no se crea aún el PowerPoint.

**Estados:** verificado = existe evidencia concreta inspeccionada; limitado = implementación o procedimiento comprobado con restricciones científicas; declarado = informado por el estudiante sin respaldo archivado localizado; pendiente = falta el entregable o la comprobación. Una prueba informática aprobada no acredita por sí sola validez predictiva.

## Requisitos y evidencia

| Requisito revisado | Archivo o evidencia | Cumplimiento funcional/documental | Cumplimiento científico y pendiente |
|---|---|---|---|
| Contrastar la guía original completa | Búsqueda local de `*.docx`: sin resultados | Pendiente | Copiar la guía y cotejar rúbrica, preguntas y exigencias físicas originales. |
| Autorización docente para tanques virtuales | Declaración expresa del estudiante en el Prompt 11 | Declarado; no se encontró acta, correo o mensaje archivado | Archivar la aprobación y su alcance. No afirmar homologación documental completa. |
| Problema y pregunta de decisión | [Guion, diapositiva 2](../docs/guion_presentacion_13_diapositivas.md#diapositiva-2-problema-y-pregunta-de-decisión) | Documentado | Pregunta limitada a qué tasa acelerar en este modelo; no optimización operacional real de Olist. |
| Fuente de datos reales | ZIP original; [auditoría](auditoria_dataset.md); [publicación Olist en Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) | ZIP y conteos verificados; URL de publicación identificada | Falta archivar ficha, condiciones de uso y registro de descarga. El hash local no prueba por sí solo identidad con una versión remota. No son mediciones propias. |
| Depuración trazable | `src/data_processing.py`; `data/processed/pedidos_limpios.csv`, `exclusiones.csv`, `calidad_fechas.csv`, `anomalias_cronologicas.csv` | Verificado: 99.441 originales; 95.082 incluidos | Cohorte retrospectiva de entregados completos; excluye otras situaciones y no representa todo el inventario operativo. |
| Reconstrucción temporal de niveles | `data/processed/niveles_reales_4_tanques.csv`, `eventos_por_hora.csv`; [modelo](../docs/modelo_matematico.md) | Verificado: 18.292 cortes y 18.291 intervalos; balances por eventos | La agregación horaria aproxima la variación intrahoraria. No se presupone zona horaria no documentada. |
| Cuatro tanques y límites del sistema | [Modelo matemático](../docs/modelo_matematico.md); `ui/tanks.py` | Cuatro estados y representación interconectada implementados | Analogía de balance con pedidos. No se modelan agua, capacidades físicas ni ley hidráulica de caudal. T4 es terminal sin salida. |
| Variables, unidades e inicialización | [Modelo](../docs/modelo_matematico.md); `reports/resumen_validacion.json` | Verificado: estados en pedidos; tiempo en horas; tasas en h⁻¹ | Estado inicial observado una sola vez. En la ventana principal: [113, 586, 3005, 53963]. |
| Cuatro EDO y conservación | `src/rk4_solver.py`, funciones `rhs` y `transfer_rates`; [formulación](../docs/modelo_matematico.md) | Verificado: flujos internos se cancelan en la suma | Primer orden y tasas constantes son hipótesis; conservar el total no garantiza acertar cada etapa. |
| Implementación RK4 | `src/rk4_solver.py`, `src/simulation_engine.py`; [implementación](../docs/implementacion_rk4_agentpy.md) | Verificado: integración vectorial, cuatro subpasos de 0,25 h por hora | Convergencia y conservación verificadas con parámetros finales. No atribuir errores grandes de validación al integrador sin evidencia. |
| Exactamente cuatro agentes AgentPy | `src/agent_model.py`, `DepositAgent`, `FourDepositModel`; `resumen_validacion.json` | Cuatro agentes de depósitos; equivalencia exacta de estados y transferencias con RK4 independiente | Organización agregada determinista. No hay agente por pedido, geografía ni decisiones autónomas modeladas. |
| Calibración mediante datos | `src/calibration.py`; [informe](calibracion_modelo.md); `parametros_calibrados.json` | Verificado: mínimos cuadrados normalizados y 12.803 intervalos de desarrollo | Tasas efectivas estimadas; no capacidades medidas. Propagador auxiliar de las mismas EDO durante optimización; trayectorias finales con RK4. |
| Selección de estructura antes de reserva | [Comparación de modelos](comparacion_modelos.md); `modelo_seleccionado_desarrollo.json` | Base seleccionado en desarrollo; candidato de aprobación rápida no adoptado | No confundir ese candidato con E1/E2. No se evaluó como modelo alternativo en validación final. |
| Validación cronológica independiente del ajuste | [Validación final](validacion_final.md); `resumen_validacion.json`; `metricas_validacion.csv` | Procedimiento verificado: 5.488 intervalos posteriores, parámetros congelados, sin correcciones posteriores | Independiente del ajuste temporal, condicionada a compras conocidas y cohorte retrospectiva. El período ya se usó: no es una reserva nueva para futuras decisiones. |
| Precisión suficiente según criterio interno | `metricas_validacion.csv`, `criterios_validacion.csv`; [plan](../docs/plan_calibracion_validacion.md) | Métricas y criterio disponibles | **No alcanzada:** X1, X2 y X3 superan NRMSE 0,30. Categoría C interna; no es una calificación oficial de Olist. |
| Tres escenarios comparables | `src/scenarios.py`; `comparacion_escenarios.json`; [resultados](escenarios_resultados.md) | E0, E1 y E2 comparten entradas, inicio, horizonte, motor y paso; sólo cambia una tasa según diseño | Comparación hipotética retrospectiva. Enero es sensibilidad, no nueva validación independiente. |
| Recomendación cuantitativa | `indicadores_horizontes.csv`, `diferencias_escenarios.csv` | E2 tiene menor área principal; diferencia de 12,59 % frente a E0 | Recomendación académica dentro del modelo. No demuestra beneficio real, ahorro ni causalidad operacional. |
| Traslado de acumulación entre etapas | `graficas_escenarios/principal_X3.png`; `comparacion_escenarios.json`, campo `shift_X3` | E1 puede aumentar X3: máximo diferencial +73,46 pedidos | Transferir antes a T3 no crea pedidos; no confundir reducción en T2 con mejora uniforme de todo el proceso. |
| Reproducción y aplicación | `app.py`, `app_pages/`, `ui/`; [guía](../docs/guia_uso_streamlit.md) | Cinco pantallas, escenarios y modo personalizado implementados | Modo libre no validado. Las animaciones son presentación, sin interpretación individual ni física. |
| Verificación informática y sincronización | [Registro de 188 pruebas](pruebas_refinamiento.txt); [protocolo](../docs/refinamiento_interfaz.md) | 188 pruebas registradas; API real y renderer JavaScript en DOM simulado | Verifica funcionamiento. No sustituye validación estadística ni inspección visual de navegador. |
| Capturas y demostración real | [Plan de evidencias](evidencias_pendientes.md) | Pendiente: no se localizaron capturas actuales archivadas de Streamlit | La aplicación no fue inspeccionada visualmente en esta revisión. Obtener capturas y grabación reales, sin recrearlas. |
| Presentación de exactamente 13 diapositivas | [Guion de diapositivas](../docs/guion_presentacion_13_diapositivas.md) | Guion completo y orden verificado; PowerPoint pendiente por instrucción | Contrastar contra el Word original antes de maquetar. Completar integrantes y fecha. |
| Sustentación de ambos integrantes | [Guion oral](../docs/guion_sustentacion.md) | Explicaciones para las 13 diapositivas y preguntas preparatorias | Ensayo conjunto pendiente. Las preguntas originales de la guía no se pueden transcribir sin el archivo. |
| Referencias y registros históricos | Diapositiva 13; auditoría, ZIP, CSV, informes, requisitos de entorno | Referencias primarias y archivos identificados | Completar evidencia de procedencia y licencia. Los registros son observacionales, no ensayos propios con sensores. |

## Resultados definitivos cotejados

Los conteos se comprobaron leyendo `olist_orders_dataset.csv` dentro del ZIP y `pedidos_limpios.csv`. Los coeficientes coinciden en `parametros_calibrados.json`, `modelo_seleccionado_desarrollo.json` y `resumen_validacion.json`.

| Magnitud | Valor comprobado | Fuente |
|---|---|---|
| Pedidos originales | 99.441 | CSV original dentro del ZIP |
| Cohorte depurada | 95.082 | `data/processed/pedidos_limpios.csv` |
| Excluidos | 4.359 | `data/processed/exclusiones.csv`; auditoría |
| α | 0.10202378368368686 h⁻¹ | `parametros_calibrados.json` |
| β | 0.013240792867426554 h⁻¹ | mismo archivo |
| γ | 0.004071911987908591 h⁻¹ | mismo archivo |
| Integración final | RK4; h=0,25 horas; cuatro subpasos por hora | `resumen_validacion.json` |
| Entrenamiento | 12.803 intervalos; 2016-09-15 11:00 a 2018-03-02 22:00 | `parametros_calibrados.json` |
| Validación | 5.488 intervalos; 2018-03-02 22:00 a 2018-10-17 14:00 | `resumen_validacion.json` |
| Estados/agentes | Cuatro/cuatro | código y comprobaciones de ejecución |

| Etapa | MAE (pedidos) | RMSE (pedidos) | NRMSE | NRMSE ≤ 0,30 |
|---|---:|---:|---:|---|
| X1 · aprobación | 24,50 | 44,17 | 0,995 | No |
| X2 · despacho | 138,87 | 184,66 | 0,559 | No |
| X3 · entrega | 546,73 | 669,10 | 0,666 | No |

Fuente: `metricas_validacion.csv`; los redondeos son sólo de presentación. Las escalas NRMSE proceden de entrenamiento y no se reajustaron usando validación.

| Escenario | Intervención | Área principal (pedidos·hora) | Reducción frente a E0 |
|---|---|---:|---:|
| E0 | Tasas calibradas | 13.339.474,31 | Referencia |
| E1 | β × 1,20 | 12.860.070,72 | 3,59 % |
| E2 | γ × 1,20 | 11.660.143,58 | 12,59 % |

Fuente: `indicadores_horizontes.csv`, filtro ventana=`principal`, horizonte=5488. Porcentajes cotejados con 100·(área_E0−área_Ej)/área_E0. Las áreas se obtienen por trapecios sobre estados horarios; no son costos monetarios ni horas de espera individuales medidas.

SHA-256 del ZIP inspeccionado: `967e41e04fc306fe604e2a693f488995a8b41e5047418f8a5c8e4abd6deca784`.

## Problemas que pueden afectar la evaluación y acciones previas al PowerPoint

| Prioridad | Problema | Acción concreta |
|---|---|---|
| Alta | Guía ausente: no se puede certificar cumplimiento íntegro ni preguntas originales | Copiar el Word, cotejar cada requisito y actualizar esta matriz antes de maquetar. |
| Alta | Autorización de adaptación no archivada | Guardar el mensaje o acta real del docente; no reconstruir ni inventar el respaldo. |
| Alta | Precisión insuficiente según criterio | Mostrar la tabla completa de X1–X3 y decir que la decisión es exploratoria. No ocultar el resultado detrás de las 188 pruebas. |
| Alta | Captura actual y revisión visual pendientes | Obtener capturas de la versión vigente, revisar sincronización a 168 h/s y guardar grabación breve. |
| Media | Cadena de procedencia externa incompleta | Archivar ficha Olist/Kaggle, condiciones de uso y registro de descarga si existe; conservar el ZIP y su hash. |
| Media | Riesgo de confundir salida logística con salida del sistema | Dibujar entrega hacia X4. No añadir un flujo externo después de X4 en las ecuaciones. |
| Media | Documentos de fases anteriores usan futuro o dicen que no existe interfaz | Presentarlos como registros fechados de desarrollo; para el estado final usar la guía de Streamlit y el refinamiento. No modificar los informes históricos. |
| Media | Figura de área usa notación 1e7 y título técnico | En la futura diapositiva aclarar «millones de pedidos·hora» o construir un gráfico editable desde el CSV, sin alterar el original ni sus valores. |
| Media | Portada y tiempo de exposición incompletos | Confirmar integrantes, fecha y duración exigida al consultar la guía. Ensayar ambos todas las secciones. |

El cierre acredita una implementación trazable y una comparación interna cuantitativa, con limitaciones científicas explícitas. No certifica exactitud operacional ni da por cumplidos los requisitos desconocidos de la guía original.
