"""Smart Home Occupancy & HVAC Control Simulator."""

from .config import HVACConfig, SimConfig, ThermalConfig
from .simulator import Result, build_scenario, run_simulation
from .metrics import compute_metrics

__all__ = [
    "HVACConfig",
    "SimConfig",
    "ThermalConfig",
    "Result",
    "build_scenario",
    "run_simulation",
    "compute_metrics",
]
__version__ = "1.0.0"
