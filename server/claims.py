"""Claim contracts. A claim cannot be both calibration and independent validation."""
from __future__ import annotations

ROLES = ('calibration', 'validation', 'qualitative_reference', 'not_comparable')


class ClaimContract:
    @staticmethod
    def validate(document: dict) -> dict:
        role = document.get('validation_role')
        roles = role if isinstance(role, (list, tuple, set)) else [role]
        if 'calibration' in roles and 'validation' in roles:
            raise ValueError('A claim cannot be both calibration and independent validation')
        unknown = [r for r in roles if r not in ROLES]
        if unknown:
            raise ValueError(f'Unknown validation_role: {unknown}')
        return dict(document, validation_role=role)
