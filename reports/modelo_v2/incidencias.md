# Incidencias de ejecución

Primera ejecución: `python scripts/experimentar_modelo_v2.py` terminó con
ValueError: Initial guess is outside of provided bounds, al iniciar B.
El segundo inicio 1.5*alpha histórico excedía por 2% la cota 0.15 del
intercepto. Se proyectaron únicamente las inicializaciones dentro de las
cotas fijadas. No se cambiaron cotas, objetivo, selección ni criterios.
No se habían calculado resultados de B/C ni de la reserva reutilizada.

Primera ejecución de las 17 pruebas iniciales V2: 16 aprobadas y una fallida.
La prueba de orden de convergencia comparaba solo el extremo a 240 h,
donde el error ya era del orden del redondeo (6e-11 pedidos). Se corrigió
el diagnóstico para contrastar toda la trayectoria transitoria frente a
expm independiente, conservando la exigencia de reducción de cuarto orden.
No se modificó el motor para resolver este fallo. Reejecución: 17 aprobadas.

Suite completa: 207 aprobadas y un fallo en test_scientific_files_unchanged.
La huella inicial y actual de data/processed/pedidos_limpios.csv es
b1f9244029f850affbafb7ea95450ec9ab5cd361face59b07242f29f873164d4;
el manifiesto histórico espera
138dc6efb6b028321aa49c8b606ccc1789cd276a53c30794cdfce81c83e4ba46.
La discrepancia es anterior al trabajo. No se editó ese CSV ni se alteró
la prueba o su manifiesto para hacerla pasar.

Un intento de invocar varias interacciones HTTP mediante python -c falló
por comillas de PowerShell (SyntaxError). Se reemplazó por el script
verificar_interfaz_v2.py: seis interacciones ready sin excepciones. Los
mensajes NativeCommandError en el registro del servidor corresponden a
PowerShell representando stderr informativo de Uvicorn; no son excepciones
de la aplicación. Las advertencias Pandas4Warning de dayofweek se conservan;
no se alteró el código congelado después de ver resultados para silenciarlas.
