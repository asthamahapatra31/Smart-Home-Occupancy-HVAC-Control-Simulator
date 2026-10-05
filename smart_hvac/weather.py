"""Synthetic outdoor temperature generator."""
import math
import random
from typing import List

from .config import SCENARIOS, SimConfig


def generate_outdoor(cfg: SimConfig, rng: random.Random) -> List[float]:
    """Diurnal sine wave (coolest ~03:00, warmest ~15:00) + daily offset + AR(1) noise."""
    sc = SCENARIOS[cfg.scenario]
    day_offsets = [rng.gauss(0.0, 2.0) for _ in range(cfg.days + 1)]
    noise = 0.0
    out: List[float] = []
    for k in range(cfg.n_steps):
        t = k * cfg.dt_s
        hour = (t / 3600.0) % 24.0
        day = int(t // 86400)
        frac = (t % 86400) / 86400.0
        offset = day_offsets[day] * (1 - frac) + day_offsets[day + 1] * frac
        noise = 0.999 * noise + rng.gauss(0.0, 0.03)
        base = sc.outdoor_mean_c + sc.outdoor_swing_c * math.sin(2 * math.pi * (hour - 9.0) / 24.0)
        out.append(base + offset + noise)
    return out
