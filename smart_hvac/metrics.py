"""Scoring: energy, cost, comfort and equipment wear."""
from typing import Dict

from .simulator import Result


def compute_metrics(res: Result) -> Dict[str, float]:
    cfg = res.cfg
    dt_h = cfg.dt_s / 3600.0
    energy_kwh = cost = discomfort = occupied_h = comfortable_h = 0.0
    cycles = 0
    prev = 0
    for t, T, occ, mode, p in zip(res.time_s, res.indoor, res.occupancy, res.mode, res.power_w):
        kwh = p * dt_h / 1000.0
        hour = (t / 3600.0) % 24.0
        price = cfg.price_peak if cfg.peak_start_h <= hour < cfg.peak_end_h else cfg.price_offpeak
        energy_kwh += kwh
        cost += kwh * price
        if occ > 0:
            occupied_h += dt_h
            dev = max(cfg.comfort_low_c - T, T - cfg.comfort_high_c, 0.0)
            discomfort += dev * dt_h
            if dev == 0.0:
                comfortable_h += dt_h
        if mode != 0 and prev == 0:
            cycles += 1
        prev = mode
    return {
        "energy_kwh": energy_kwh,
        "cost": cost,
        "discomfort_deg_h": discomfort,
        "comfort_pct": 100.0 * comfortable_h / occupied_h if occupied_h else 100.0,
        "cycles": cycles,
        "occupied_h": occupied_h,
        "avg_indoor_c": sum(res.indoor) / len(res.indoor),
    }
