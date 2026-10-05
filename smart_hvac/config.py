"""Configuration dataclasses. All temperatures in deg C, power in W, time in s."""
from dataclasses import dataclass, field


@dataclass
class ThermalConfig:
    """Single-zone lumped RC building model."""
    ua_w_per_k: float = 150.0          # envelope heat-loss coefficient (W/K)
    capacity_j_per_k: float = 8.0e6    # effective thermal mass (J/K)
    base_gain_w: float = 200.0         # appliances / lighting (W)
    gain_per_person_w: float = 100.0   # metabolic heat per occupant (W)


@dataclass
class HVACConfig:
    """Heat-pump style HVAC unit with a thermostat."""
    heat_capacity_w: float = 6000.0    # thermal output when heating
    cool_capacity_w: float = 4500.0    # thermal output when cooling
    cop_heat: float = 3.0
    cop_cool: float = 3.2
    deadband_c: float = 0.5            # half-width hysteresis band
    min_on_s: float = 300.0            # short-cycle protection
    min_off_s: float = 300.0


@dataclass
class Scenario:
    name: str
    outdoor_mean_c: float
    outdoor_swing_c: float             # half of day/night swing


SCENARIOS = {
    "winter": Scenario("winter", outdoor_mean_c=5.0, outdoor_swing_c=5.0),
    "summer": Scenario("summer", outdoor_mean_c=32.0, outdoor_swing_c=6.0),
    "mild": Scenario("mild", outdoor_mean_c=15.0, outdoor_swing_c=6.0),
}


@dataclass
class SimConfig:
    scenario: str = "winter"
    days: int = 7
    dt_s: int = 60
    seed: int = 42
    residents: int = 2
    initial_temp_c: float = 21.0
    # Comfort band used for *scoring* (not control).
    comfort_low_c: float = 20.0
    comfort_high_c: float = 25.0
    # Sensor model
    sensor_miss_prob: float = 0.02     # per-step chance an occupied home reads "no motion"
    sensor_false_prob: float = 0.001   # per-step chance an empty home reads "motion"
    # Time-of-use tariff (currency units per kWh)
    price_offpeak: float = 0.12
    price_peak: float = 0.30
    peak_start_h: int = 17
    peak_end_h: int = 21
    thermal: ThermalConfig = field(default_factory=ThermalConfig)
    hvac: HVACConfig = field(default_factory=HVACConfig)

    @property
    def n_steps(self) -> int:
        return int(self.days * 24 * 3600 // self.dt_s)
