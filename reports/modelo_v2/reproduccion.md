# Ejecución y evidencias reproducibles

Entorno exacto, versiones, fecha UTC real y hashes de CSV/ZIP en entorno.json.
La fecha local de trabajo es 2026-11-08, America/Bogota; los timestamps
históricos se conservan tal como fueron suministrados, sin inventar zona.

Comandos ejecutados con .venv/Scripts/python.exe:

```powershell
.venv/Scripts/python.exe scripts/experimentar_modelo_v2.py
.venv/Scripts/python.exe scripts/experimentar_mezcla_v2.py
.venv/Scripts/python.exe scripts/diagnosticar_modelo_v2.py
.venv/Scripts/python.exe scripts/informar_modelo_v2.py
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m pytest tests/test_model_v2.py tests/test_model_mixture.py tests/test_model_v2_ui.py -q
.venv/Scripts/python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8503 --server.enableAgentApi true
.venv/Scripts/python.exe scripts/verificar_interfaz_v2.py
```

Los scripts de ajuste rechazan sobrescribir una congelación existente.
Para repetir todos los experimentos preservando estos resultados:

```powershell
.venv/Scripts/python.exe scripts/reproducir_modelo_v2.py --output reports/reproduccion_v2_nueva
```

El destino debe ser nuevo. Protocolos, ventanas, pesos y cotas permanecen
idénticos. La selección local debe reproducirse hasta tolerancia numérica;
fecha, tiempos de ejecución y diferencias de versión no son invariantes.
Las rutas de hashes del experimento apuntan al código fuente usado. Las
congelaciones verifican código/protocolo y escalas; el manifiesto previo
permite comprobar que entradas y resultados históricos no cambiaron.

pruebas_completas.txt: 207 passed, 1 failed (discrepancia anterior).
pruebas_nuevas.txt: 20 passed. Los errores iniciales de implementación y
la discrepancia del manifiesto se describen en incidencias.md y
discrepancias_integridad_preexistentes.json. No se descartaron fallos.
api_verificacion.json registra seis interacciones con status ready.
No se hizo inspección completa de renderizado en navegador ni comprobación
de tipos estática con mypy/ty (no disponibles en el entorno). La sintaxis y
el comportamiento de los módulos se verifican por importación y pruebas.
No se cambiaron dependencias Python ni los tests históricos.

Los histogramas de duración solo describen completadas y se etiquetan así;
la supervivencia incluye todas las censuras al corte. No hay datos sintéticos
en evaluaciones empíricas. Los datos artificiales se usan solo en unitarias.

Se repitieron A/B/C/M en un directorio separado: selección B y seis tablas
idénticas byte a byte. Evidencia en reproducibilidad_verificada.json y
reproduccion_ejecucion.txt. No se sobrescribió ningún resultado entregado.
