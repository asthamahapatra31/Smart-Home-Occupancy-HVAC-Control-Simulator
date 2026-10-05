"""Simulation loop. Every controller is run against identical weather and occupancy."""
import random
from dataclasses import dataclass, field
from typing import List

from .config import SimConfig
from .controllers import Controller, Observation
from .hvac import HVACUnit, Thermostat
from .occupancy import generate_motion, generate_occupancy
from .thermal import ThermalModel
from .weather import generate_outdoor


@dataclass
class Scenario:
    """Pre-generated exogenous inputs shared by all controllers."""
    outdoor: List[float]
    occupancy: List[int]
    motion: List[bool]


@dataclass
class Result:
    controller: str
    cfg: SimConfig
    time_s: List[float] = field(default_factory=list)
    indoor: List[float] = field(default_factory=list)
    outdoor: List[float] = field(default_factory=list)
    occupancy: List[int] = field(default_factory=list)
    mode: List[int] = field(default_factory=list)
    heat_sp: List[float] = field(default_factory=list)
    cool_sp: List[float] = field(default_factory=list)
    power_w: List[float] = field(default_factory=list)


def build_scenario(cfg: SimConfig) -> Scenario:
    rng = random.Random(cfg.seed)
    outdoor = generate_outdoor(cfg, rng)
    occupancy = generate_occupancy(cfg, rng)
    motion = generate_motion(occupancy, cfg, rng)
    return Scenario(outdoor, occupancy, motion)


def run_simulation(controller: Controller, cfg: SimConfig, scenario: Scenario) -> Result:
    thermal = ThermalModel(cfg.thermal, cfg.initial_temp_c)
    unit = HVACUnit(cfg.hvac)
    thermostat = Thermostat(cfg.hvac)
    res = Result(controller=controller.name, cfg=cfg)

    for k in range(cfg.n_steps):
        t = k * cfg.dt_s
        obs = Observation(t, thermal.temp_c, scenario.motion[k], cfg.dt_s)
        heat_sp, cool_sp = controller.update(obs)
        mode = thermostat.step(t, thermal.temp_c, heat_sp, cool_sp)

        res.time_s.append(t)
        res.indoor.append(thermal.temp_c)
        res.outdoor.append(scenario.outdoor[k])
        res.occupancy.append(scenario.occupancy[k])
        res.mode.append(int(mode))
        res.heat_sp.append(heat_sp)
        res.cool_sp.append(cool_sp)
        res.power_w.append(unit.electric_power_w(mode))

        thermal.step(scenario.outdoor[k], unit.thermal_power_w(mode),
                     scenario.occupancy[k], cfg.dt_s)
    return res
