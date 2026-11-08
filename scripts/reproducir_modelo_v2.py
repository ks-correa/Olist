"""Re-run all experiments in a new directory, preserving delivered evidence."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse
import shutil
from scripts import experimentar_modelo_v2 as first
from scripts import experimentar_mezcla_v2 as second
from scripts import diagnosticar_modelo_v2 as diagnostics


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,help='Directorio NUEVO para resultados')
    target=Path(parser.parse_args().output).resolve()
    if target.exists():raise SystemExit('El destino ya existe: se conserva sin cambios')
    target.mkdir(parents=True)
    for name in ['protocolo.md','protocolo_mezcla.md','auditoria_previa.json']:
        shutil.copy2(first.OUT/name,target/name)
    first.OUT=target;second.OUT=target;diagnostics.OUT=target
    first.main();second.main();diagnostics.main()
