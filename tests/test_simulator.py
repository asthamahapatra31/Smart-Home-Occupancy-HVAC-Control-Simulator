import random
import unittest

from smart_hvac.config import HVACConfig, SimConfig, ThermalConfig
from smart_hvac.controllers import (COMFORT, SETBACK, FixedController, Observation,
                                    OccupancyController, PredictiveController)
from smart_hvac.hvac import HVACUnit, Mode, Thermostat
from smart_hvac.metrics import compute_metrics
from smart_hvac.occupancy import generate_occupancy
from smart_hvac.simulator import build_scenario, run_simulation
from smart_hvac.thermal import ThermalModel


class ThermalTests(unittest.TestCase):
    def test_converges_to_steady_state(self):
        cfg = ThermalConfig(base_gain_w=0.0, gain_per_person_w=0.0)
        m = ThermalModel(cfg, 20.0)
        for _ in range(60 * 24 * 10):               # 10 days at outdoor = 0 C
            m.step(0.0, 0.0, 0, 60)
        self.assertAlmostEqual(m.temp_c, 0.0, delta=0.05)

    def test_heating_raises_temperature(self):
        m = ThermalModel(ThermalConfig(), 15.0)
        t0 = m.temp_c
        m.step(10.0, 6000.0, 2, 60)
        self.assertGreater(m.temp_c, t0)

    def test_people_add_heat(self):
        a, b = ThermalModel(ThermalConfig(), 20.0), ThermalModel(ThermalConfig(), 20.0)
        a.step(20.0, 0.0, 0, 60)
        b.step(20.0, 0.0, 4, 60)
        self.assertGreater(b.temp_c, a.temp_c)


class HVACTests(unittest.TestCase):
    def test_heats_when_cold_and_cools_when_hot(self):
        th = Thermostat(HVACConfig())
        self.assertEqual(th.step(0, 15.0, 21, 24), Mode.HEAT)
        th = Thermostat(HVACConfig())
        self.assertEqual(th.step(0, 30.0, 21, 24), Mode.COOL)

    def test_min_on_time_prevents_short_cycling(self):
        th = Thermostat(HVACConfig(min_on_s=300))
        th.step(0, 15.0, 21, 24)                         # starts heating
        self.assertEqual(th.step(60, 25.0, 21, 24), Mode.HEAT)    # too early to stop
        self.assertEqual(th.step(301, 25.0, 21, 24), Mode.OFF)

    def test_electric_power_uses_cop(self):
        u = HVACUnit(HVACConfig(heat_capacity_w=6000, cop_heat=3.0))
        self.assertAlmostEqual(u.electric_power_w(Mode.HEAT), 2000.0)
        self.assertEqual(u.electric_power_w(Mode.OFF), 0.0)


class OccupancyTests(unittest.TestCase):
    def test_seeded_and_bounded(self):
        cfg = SimConfig(days=3)
        a = generate_occupancy(cfg, random.Random(1))
        b = generate_occupancy(cfg, random.Random(1))
        self.assertEqual(a, b)
        self.assertTrue(all(0 <= n <= cfg.residents for n in a))
        self.assertEqual(len(a), cfg.n_steps)

    def test_weekday_daytime_is_mostly_empty(self):
        cfg = SimConfig(days=5, residents=2)
        occ = generate_occupancy(cfg, random.Random(3))
        noon = [occ[d * 1440 + 12 * 60] for d in range(5)]
        self.assertLess(sum(noon), 5 * cfg.residents)


class ControllerTests(unittest.TestCase):
    def test_fixed_ignores_motion(self):
        c = FixedController()
        self.assertEqual(c.update(Observation(0, 20, False)), COMFORT)

    def test_occupancy_setback_after_hold(self):
        c = OccupancyController(hold_s=600)
        self.assertEqual(c.update(Observation(0, 20, True)), COMFORT)
        self.assertEqual(c.update(Observation(300, 20, False)), COMFORT)   # still held
        self.assertEqual(c.update(Observation(1000, 20, False)), SETBACK)

    def test_predictive_preheats_after_learning(self):
        c = PredictiveController(hold_s=0, lead_s=3600, learn_rate=0.5)
        arrival = 17 * 3600
        for day in range(2):                                # Mon, Tue
            for h in range(24):
                t = day * 86400 + h * 3600 + 1
                c.update(Observation(t, 18, h >= 17))
        # Wed 16:30 - nobody home yet, but arrival learned within lead time
        sp = c.update(Observation(2 * 86400 + 16.5 * 3600, 18, False))
        self.assertEqual(sp, COMFORT)


class EndToEndTests(unittest.TestCase):
    def test_occupancy_control_saves_energy_in_winter(self):
        cfg = SimConfig(days=5)
        sc = build_scenario(cfg)
        fixed = compute_metrics(run_simulation(FixedController(), cfg, sc))
        occ = compute_metrics(run_simulation(OccupancyController(), cfg, sc))
        self.assertLess(occ["energy_kwh"], fixed["energy_kwh"])

    def test_deterministic(self):
        cfg = SimConfig(days=2)
        r1 = run_simulation(FixedController(), cfg, build_scenario(cfg))
        r2 = run_simulation(FixedController(), cfg, build_scenario(cfg))
        self.assertEqual(r1.indoor, r2.indoor)

    def test_energy_accounting(self):
        cfg = SimConfig(days=1)
        res = run_simulation(FixedController(), cfg, build_scenario(cfg))
        m = compute_metrics(res)
        self.assertAlmostEqual(m["energy_kwh"], sum(res.power_w) * cfg.dt_s / 3.6e6, places=6)


if __name__ == "__main__":
    unittest.main()
