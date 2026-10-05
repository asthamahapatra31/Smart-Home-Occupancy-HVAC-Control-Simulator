"""Lumped-capacitance (1R1C) thermal model:  C dT/dt = UA (To - Ti) + Q_hvac + Q_internal."""
from .config import ThermalConfig


class ThermalModel:
    def __init__(self, cfg: ThermalConfig, initial_temp_c: float):
        self.cfg = cfg
        self.temp_c = initial_temp_c

    def internal_gain_w(self, n_occupants: int) -> float:
        return self.cfg.base_gain_w + self.cfg.gain_per_person_w * n_occupants

    def step(self, outdoor_c: float, hvac_thermal_w: float, n_occupants: int, dt_s: float) -> float:
        q_env = self.cfg.ua_w_per_k * (outdoor_c - self.temp_c)
        q_total = q_env + hvac_thermal_w + self.internal_gain_w(n_occupants)
        self.temp_c += q_total * dt_s / self.cfg.capacity_j_per_k
        return self.temp_c
