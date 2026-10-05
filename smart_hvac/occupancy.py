"""Stochastic household occupancy and a noisy PIR-style motion sensor."""
import random
from typing import List, Tuple

from .config import SimConfig


def _intervals_away(day: int, rng: random.Random) -> List[Tuple[float, float]]:
    """Return list of (leave_h, return_h) away intervals for one resident-day."""
    weekday = day % 7 < 5            # day 0 is a Monday
    if weekday:
        if rng.random() < 0.85:      # goes to work/school
            leave = max(6.0, rng.gauss(8.0, 0.5))
            back = min(22.0, max(leave + 4, rng.gauss(17.75, 0.75)))
            return [(leave, back)]
        return []
    away = []
    for _ in range(rng.choice([0, 1, 1, 2])):          # weekend errands
        start = rng.uniform(10.0, 17.0)
        away.append((start, start + rng.uniform(0.5, 3.0)))
    return away


def generate_occupancy(cfg: SimConfig, rng: random.Random) -> List[int]:
    """True number of people at home at every time step."""
    counts = [cfg.residents] * cfg.n_steps
    steps_per_hour = 3600.0 / cfg.dt_s
    for _ in range(cfg.residents):
        for day in range(cfg.days):
            for leave_h, back_h in _intervals_away(day, rng):
                a = int((day * 24 + leave_h) * steps_per_hour)
                b = int((day * 24 + back_h) * steps_per_hour)
                for k in range(max(a, 0), min(b, cfg.n_steps)):
                    counts[k] -= 1
    return counts


def generate_motion(occupancy: List[int], cfg: SimConfig, rng: random.Random) -> List[bool]:
    """Noisy binary sensor: misses motion sometimes (e.g. sleeping), rare false triggers."""
    motion = []
    for n in occupancy:
        if n > 0:
            motion.append(rng.random() >= cfg.sensor_miss_prob)
        else:
            motion.append(rng.random() < cfg.sensor_false_prob)
    return motion
