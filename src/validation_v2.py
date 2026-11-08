"""Verify frozen experiment provenance before loading its selected parameters."""
from pathlib import Path
import hashlib
import json
import numpy as np
from .model_v2 import ModelSpec
from .validation import FROZEN_SCALES


def load_frozen_v2(root):
    root=Path(root);out=root/'reports/modelo_v2'
    record=json.loads((out/'congelado.json').read_text(encoding='utf8'))
    if hashlib.sha256((out/'protocolo.md').read_bytes()).hexdigest()!=record['protocolo_sha256']:
        raise ValueError('Protocolo modificado después de congelar')
    for name,digest in record['source_hashes'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Código modificado después de congelar: {name}')
    if not np.array_equal(record['scales'],FROZEN_SCALES):
        raise ValueError('Escalas históricas modificadas')
    spec=ModelSpec(record['modelo'],tuple(record['theta']),tuple(record['phases']))
    return spec,record
