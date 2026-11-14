"""Opt-in, offline AI experiment design research prototypes for Paper2Simu.

Importing this package does not connect to or alter any commercial solver.
"""
from .contracts import DesignError, validate_space, assess_design
from .selector import select_next_simulation

__all__ = ("DesignError", "validate_space", "assess_design", "select_next_simulation")
