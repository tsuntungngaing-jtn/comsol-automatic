"""Opt-in, offline AI experiment design research prototypes for Paper2Simu.

Importing this package does not connect to or alter any commercial solver.
"""
from .contracts import DesignError, validate_space, assess_design
from .selector import select_next_simulation
from .observations import admit_observations
from .surrogate import fit_idw_baseline, predict_idw
from .discovery_loop import screen_and_rank

__all__ = ("DesignError", "validate_space", "assess_design", "select_next_simulation",
           "admit_observations", "fit_idw_baseline", "predict_idw", "screen_and_rank")
