"""HVAC unit and hysteresis thermostat with short-cycle protection."""
from enum import IntEnum

from .config import HVACConfig


class Mode(IntEnum):
    OFF = 0
    HEAT = 1
    COOL = 2


class HVACUnit:
    def __init__(self, cfg: HVACConfig):
        self.cfg = cfg

    def thermal_power_w(self, mode: Mode) -> float:
        """Signed heat delivered to the zone (+ heating, - cooling)."""
        if mode == Mode.HEAT:
            return self.cfg.heat_capacity_w
        if mode == Mode.COOL:
            return -self.cfg.cool_capacity_w
        return 0.0

    def electric_power_w(self, mode: Mode) -> float:
        if mode == Mode.HEAT:
            return self.cfg.heat_capacity_w / self.cfg.cop_heat
        if mode == Mode.COOL:
            return self.cfg.cool_capacity_w / self.cfg.cop_cool
        return 0.0


class Thermostat:
    """Turns (temperature, heat/cool setpoints) into an HVAC mode."""

    def __init__(self, cfg: HVACConfig):
        self.cfg = cfg
        self.mode = Mode.OFF
        self._last_change = float("-inf")

    def step(self, t_s: float, temp_c: float, heat_sp: float, cool_sp: float) -> Mode:
        db = self.cfg.deadband_c
        held = t_s - self._last_change
        new = self.mode
        if self.mode == Mode.HEAT:
            if temp_c >= heat_sp + db and held >= self.cfg.min_on_s:
                new = Mode.OFF
        elif self.mode == Mode.COOL:
            if temp_c <= cool_sp - db and held >= self.cfg.min_on_s:
                new = Mode.OFF
        else:
            if held >= self.cfg.min_off_s:
                if temp_c <= heat_sp - db:
                    new = Mode.HEAT
                elif temp_c >= cool_sp + db:
                    new = Mode.COOL
        if new != self.mode:
            self.mode = new
            self._last_change = t_s
        return self.mode
