"""Command line interface:  python -m smart_hvac --scenario winter --days 7 --plot"""
import argparse
import csv
import os

from .config import SCENARIOS, SimConfig
from .controllers import all_controllers
from .metrics import compute_metrics
from .plotting import plot_results
from .simulator import build_scenario, run_simulation


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Smart Home Occupancy & HVAC Control Simulator")
    ap.add_argument("--scenario", choices=sorted(SCENARIOS), default="winter")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--residents", type=int, default=2)
    ap.add_argument("--dt", type=int, default=60, help="time step in seconds")
    ap.add_argument("--out", default="results", help="output directory for CSV/plots")
    ap.add_argument("--plot", action="store_true", help="save PNG plots (needs matplotlib)")
    ap.add_argument("--no-csv", action="store_true")
    args = ap.parse_args(argv)

    cfg = SimConfig(scenario=args.scenario, days=args.days, seed=args.seed,
                    residents=args.residents, dt_s=args.dt)
    if args.scenario == "summer":
        cfg.initial_temp_c = 24.0
    scenario = build_scenario(cfg)

    results, metrics = [], {}
    for ctrl in all_controllers():
        res = run_simulation(ctrl, cfg, scenario)
        results.append(res)
        metrics[res.controller] = compute_metrics(res)

    base = metrics["fixed"]["energy_kwh"]
    print(f"\nScenario: {cfg.scenario} | days: {cfg.days} | seed: {cfg.seed} | residents: {cfg.residents}")
    print(f"Occupied time: {metrics['fixed']['occupied_h']:.1f} h of {cfg.days * 24} h\n")
    header = f"{'controller':<11}{'energy kWh':>11}{'saving %':>10}{'cost':>8}{'discomf C.h':>13}{'comfort %':>11}{'cycles':>8}"
    print(header)
    print("-" * len(header))
    for name, m in metrics.items():
        saving = 100.0 * (base - m["energy_kwh"]) / base if base else 0.0
        print(f"{name:<11}{m['energy_kwh']:>11.1f}{saving:>10.1f}{m['cost']:>8.2f}"
              f"{m['discomfort_deg_h']:>13.1f}{m['comfort_pct']:>11.1f}{m['cycles']:>8d}")

    if not args.no_csv or args.plot:
        os.makedirs(args.out, exist_ok=True)
    if not args.no_csv:
        for r in results:
            path = os.path.join(args.out, f"{cfg.scenario}_{r.controller}.csv")
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["time_s", "indoor_c", "outdoor_c", "occupants", "mode",
                            "heat_sp", "cool_sp", "power_w"])
                w.writerows(zip(r.time_s, r.indoor, r.outdoor, r.occupancy, r.mode,
                                r.heat_sp, r.cool_sp, r.power_w))
        print(f"\nCSV traces written to {args.out}/")
    if args.plot:
        for p in plot_results(results, metrics, args.out):
            print("saved", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
