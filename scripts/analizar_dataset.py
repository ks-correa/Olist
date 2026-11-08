"""Ejecutar desde cualquier directorio: python scripts/analizar_dataset.py."""
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.data_processing import *


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zip', type=Path, default=ROOT/'Brazilian_E-Commerce_Public_Dataset_by_Olist.zip')
    args = parser.parse_args()
    if not args.zip.is_file():
        parser.error('No se encontró el ZIP. Indique su ubicación exacta mediante --zip.')
    out, reports = ROOT/'data/processed', ROOT/'reports'
    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    raw, members = read_orders(args.zip)
    df, clean, quality, exclusions, chronology, stats = audit_and_clean(raw)
    flows, levels = reconstruct(clean)
    statuses = raw.order_status.value_counts(dropna=False).rename_axis('estado').reset_index(name='pedidos')
    for name, table in [('pedidos_limpios',clean), ('eventos_por_hora',flows.reset_index()), ('niveles_reales_4_tanques',levels.reset_index()), ('calidad_fechas',quality), ('exclusiones',exclusions), ('duraciones_etapas_horas',stats.reset_index(names='etapa')), ('distribucion_estados',statuses)]:
        table.to_csv(out/f'{name}.csv', index=False, date_format='%Y-%m-%d %H:%M:%S')
    flags = chronology.copy()
    flags.insert(0, 'order_id', df.order_id)
    flags.loc[chronology.any(axis=1)].to_csv(out/'anomalias_cronologicas.csv', index=False)
    fig, axes = plt.subplots(4, 1, figsize=(13, 11), sharex=True)
    for ax, col in zip(axes, ['X1','X2','X3','X4']):
        ax.plot(levels.index, levels[col], linewidth=.8)
        ax.set_ylabel(f'{col} (pedidos)')
        ax.grid(alpha=.25)
    fig.suptitle('Cohorte entregada: niveles históricos a cortes horarios')
    fig.tight_layout()
    fig.savefig(reports/'niveles_observados.png', dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(13,5))
    for col in FLOWS:
        ax.plot(flows.index, flows[col], label=col, alpha=.65, linewidth=.6)
    ax.legend(); ax.set_ylabel('Pedidos/hora'); ax.set_title('Flujos históricos observados, intervalos de una hora')
    fig.tight_layout(); fig.savefig(reports/'flujos_historicos.png', dpi=150); plt.close(fig)
    def table(frame):
        return frame.to_string(index=False)
    text = f'''# Auditoría del dataset Olist — fase 1

## Fuente y reproducibilidad
ZIP original leído directamente, sin modificar. SHA-256: `{sha256(args.zip)}`.
CSV del archivo:\n\n''' + '\n'.join('- '+n for n in members) + f'''

## Población
Originales: **{len(raw):,}**. Identificadores únicos no nulos: **{raw.order_id.nunique():,}**.
Incluidos: **{len(clean):,}**. Excluidos: **{len(raw)-len(clean):,}**.
Referencia de 99.441 originales y 95.082 incluidos: **{'coincide' if len(raw)==99441 and len(clean)==95082 else 'NO coincide; revisar las tablas de criterios y la fuente'}**.

Se modela exclusivamente la cohorte retrospectiva de pedidos delivered con cuatro fechas completas, válidas y no decrecientes. La igualdad entre fechas es válida.

### Estados
```
{table(statuses)}
```
### Calidad y rango temporal (dataset completo)
```
{table(quality)}
```
### Exclusiones
```
{table(exclusions)}
```
Los conteos independientes pueden solaparse. Los secuenciales son disjuntos y suman el total excluido. Se excluyen identificadores ausentes/duplicados para contar pedidos una sola vez, estados distintos de delivered por definición de cohorte, fechas principales incompletas por falta de eventos verificables y cronología inversa por incompatibilidad con transferencias causales. La fecha estimada no determina la inclusión.

### Inversiones cronológicas (pares adyacentes, dataset completo)
```
{chronology.sum().to_string()}
```
### Duraciones de la cohorte (horas)
```
{stats.to_string()}
```
Estas duraciones no se convierten en tasas de servicio. Los percentiles describen tiempos observados entre marcas de eventos.

## Reconstrucción y conservación
{len(levels):,} cortes horarios desde {levels.index.min()} hasta {levels.index.max()}.
Los eventos originales se conservan en pedidos_limpios.csv. Cada acumulado cuenta eventos con fecha <= t; cada flujo cuenta eventos en (t−1 hora, t]. Se incluye un corte inicial vacío y el final posterior o igual al último evento. No se interpola ni se cambia la hora de los eventos; no se atribuye una zona horaria no documentada.

X1=A−B, X2=B−C, X3=C−D, X4=D. Por cancelación algebraica, X1+X2+X3+X4=A.
Verificación ejecutada sobre todos los cortes: niveles no negativos, conservación exacta y ΔX=(compras−aprobaciones, aprobaciones−despachos, despachos−entregas, entregas).
Estado final: {levels.iloc[-1][['X1','X2','X3','X4']].to_dict()}.
Cada transferencia se resta de un depósito y se añade al siguiente en el mismo intervalo. X4 es terminal acumulado.
Las columnas *_por_hora son conteos divididos por intervalos de exactamente una hora: observaciones históricas, no parámetros calibrados.

## Archivos y gráficas
Los CSV de data/processed incluyen cohorte, flujos y tasas horarias, niveles y acumulados, calidad de fechas, exclusiones, anomalías, estados y estadísticas de duración.
- niveles_observados.png: cuatro paneles con X1–X4; X4 crece con las entregas.
- flujos_historicos.png: compras, aprobaciones, despachos y entregas por hora; se mantienen picos y horas sin actividad.

## Limitaciones y decisiones antes de las EDO
Hay sesgo de selección por exigir entrega y fechas completas: esta cohorte no es el inventario operativo completo ni representa automáticamente los pedidos pendientes de Olist. No existen aquí fechas explícitas de cancelación que permitan reconstruir sus salidas. Los estados finales no sustituyen eventos fechados.
La precisión horaria oculta variaciones dentro del intervalo; las marcas originales permanecen disponibles. Los extremos de la ventana sufren efectos de cohorte y no describen una operación estacionaria.
Antes de las EDO deben definirse población objetivo, condiciones iniciales, tratamiento de cancelaciones y censura, ventana de calibración/validación y método estadístico de estimación de transferencias. No asumir capacidad de servicio como el inverso del tiempo medio de etapa.
No se implementan simulación, EDO, RK4, AgentPy, escenarios ni interfaz.
'''
    (reports/'auditoria_dataset.md').write_text(text, encoding='utf-8')
    print(f'Originales={len(raw)}; incluidos={len(clean)}; excluidos={len(raw)-len(clean)}')
    print(exclusions.to_string(index=False)); print(stats.to_string())

if __name__ == '__main__':
    main()
