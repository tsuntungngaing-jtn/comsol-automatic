"""Immutable observation records bound to spec/model/run identities."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid


class ObservationCollector:
    version = '0.1.0'

    def __init__(self):
        self._items: dict[str, dict[str, Any]] = {}

    def record(self, *, case_id: str, run_id: str, spec_revision: int, model_revision: int,
               expression: str, value, unit: str, study: str, solver: str, solution: str,
               dataset: str, parameter_state: dict | None = None, selection: str | None = None,
               mph_hash: str | None = None, spec_hash: str | None = None,
               warnings: list | None = None) -> dict:
        observation_id = 'obs-' + uuid.uuid4().hex[:12]
        rec = {
            'observation_id': observation_id, 'case_id': case_id, 'run_id': run_id,
            'spec_revision': spec_revision, 'model_revision': model_revision,
            'study': study, 'solver': solver, 'solution': solution, 'dataset': dataset,
            'parameter_state': parameter_state or {}, 'expression': expression,
            'selection': selection, 'unit': unit, 'value': value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'mph_hash': mph_hash, 'spec_hash': spec_hash, 'warnings': warnings or [],
            'collector_version': self.version,
        }
        self._items[observation_id] = rec
        return dict(rec)

    def admissible_for(self, observation: dict, *, spec_revision: int, model_revision: int,
                       run_id: str) -> bool:
        return (observation.get('spec_revision') == spec_revision
                and observation.get('model_revision') == model_revision
                and observation.get('run_id') == run_id)
