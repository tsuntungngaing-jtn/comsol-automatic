"""Calibration provenance. Fitted values never become reported. LITERATURE_ADAPTED."""
from __future__ import annotations

from typing import Any


class CalibrationLedger:
    def __init__(self):
        self._params: dict[str, dict[str, Any]] = {}

    def fit(self, *, parameter_id: str, value, unit: str, target_claim_id: str,
            method: str, run_id: str, bounds=None, uncertainty=None,
            model_discrepancy=None) -> dict:
        rec = {
            'parameter_id': parameter_id, 'value': value, 'unit': unit,
            'origin': 'fitted', 'certainty': 'estimated',
            'target_claim_id': target_claim_id, 'fitting_method': method,
            'parameter_bounds': bounds, 'uncertainty': uncertainty,
            'model_discrepancy': model_discrepancy, 'run_identities': [run_id],
        }
        self._params[parameter_id] = rec
        return dict(rec)

    def get(self, parameter_id: str) -> dict:
        return dict(self._params[parameter_id])

    def may_independently_validate(self, parameter_id: str, claim_id: str) -> bool:
        rec = self._params[parameter_id]
        return claim_id != rec['target_claim_id']

    def final_status(self, parameter_id: str, independent_claim_ids: list[str]) -> str:
        rec = self._params[parameter_id]
        independent = [c for c in independent_claim_ids if c != rec['target_claim_id']]
        if independent:
            return 'VALIDATED'
        return 'CALIBRATED_NOT_INDEPENDENTLY_VALIDATED'
