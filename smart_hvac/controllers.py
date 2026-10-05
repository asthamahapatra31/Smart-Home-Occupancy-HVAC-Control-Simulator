"""Control strategies. Each maps an Observation to (heat_setpoint, cool_setpoint)."""
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class Observation:
    t_s: float
    temp_c: float
    motion: bool            # raw (noisy) occupancy sensor reading
    dt_s: float = 60.0

    @property
    def hour(self) -> float:
        return (self.t_s / 3600.0) % 24.0

    @property
    def weekday(self) -> bool:
        return int(self.t_s // 86400) % 7 < 5


COMFORT = (21.0, 24.0)      # (heat, cool) when people are home
SETBACK = (17.0, 28.0)      # energy-saving setpoints when away
NIGHT = (18.5, 26.0)        # sleeping setpoints for the scheduled controller


class Controller:
    name = "base"

    def update(self, obs: Observation) -> Tuple[float, float]:
        raise NotImplementedError


class FixedController(Controller):
    """Baseline: constant comfort setpoints 24/7, ignores occupancy."""
    name = "fixed"

    def update(self, obs):
        return COMFORT


class ScheduleController(Controller):
    """Programmable thermostat: fixed weekly schedule, ignores real occupancy."""
    name = "schedule"

    def update(self, obs):
        h = obs.hour
        if obs.weekday:
            if 6.0 <= h < 8.5 or 17.0 <= h < 22.5:
                return COMFORT
            return SETBACK if 8.5 <= h < 17.0 else NIGHT
        return COMFORT if 7.5 <= h < 23.0 else NIGHT


class OccupancyController(Controller):
    """Reactive: comfort while motion was seen within `hold_s`, otherwise setback."""
    name = "occupancy"

    def __init__(self, hold_s: float = 45 * 60):
        self.hold_s = hold_s
        self._last_motion = float("-inf")

    def _occupied(self, obs: Observation) -> bool:
        if obs.motion:
            self._last_motion = obs.t_s
        return obs.t_s - self._last_motion <= self.hold_s

    def update(self, obs):
        return COMFORT if self._occupied(obs) else SETBACK


class PredictiveController(OccupancyController):
    """Occupancy-aware + learns typical arrival times and pre-conditions the home.

    Keeps an exponentially-weighted occupancy probability for each 15-minute bin of the
    day (separately for weekdays / weekends). If any bin within the next `lead_s` is
    likely occupied, it switches to comfort setpoints early so the house is ready.
    """
    name = "predictive"
    BIN_S = 900

    def __init__(self, hold_s: float = 45 * 60, lead_s: float = 90 * 60,
                 threshold: float = 0.5, learn_rate: float = 0.02):
        super().__init__(hold_s)
        self.lead_s = lead_s
        self.threshold = threshold
        self.learn_rate = learn_rate
        n = 86400 // self.BIN_S
        self.prob: Dict[bool, List[float]] = {True: [0.0] * n, False: [0.0] * n}

    def _bin(self, t_s: float) -> int:
        return int((t_s % 86400) // self.BIN_S)

    def update(self, obs):
        occupied = self._occupied(obs)
        table = self.prob[obs.weekday]
        b = self._bin(obs.t_s)
        a = self.learn_rate * obs.dt_s / 60.0
        table[b] += a * ((1.0 if occupied else 0.0) - table[b])

        if occupied:
            return COMFORT
        # Look ahead; past midnight use the next day's table (weekday/weekend aware)
        look = int(self.lead_s // self.BIN_S) + 1
        n = len(table)
        for i in range(1, look + 1):
            nb = b + i
            tbl = table
            if nb >= n:
                nb -= n
                next_weekday = (int(obs.t_s // 86400) + 1) % 7 < 5
                tbl = self.prob[next_weekday]
            if tbl[nb] >= self.threshold:
                return COMFORT
        return SETBACK


def all_controllers() -> List[Controller]:
    return [FixedController(), ScheduleController(), OccupancyController(), PredictiveController()]
