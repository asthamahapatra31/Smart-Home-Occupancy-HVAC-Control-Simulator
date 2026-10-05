"""Optional matplotlib plots (pip install matplotlib)."""
import os
from typing import Dict, List

from .simulator import Result


def plot_results(results: List[Result], metrics: Dict[str, Dict[str, float]], out_dir: str) -> List[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:  # pragma: no cover
        print("matplotlib not installed - skipping plots (pip install matplotlib)")
        return []

    os.makedirs(out_dir, exist_ok=True)
    paths = []
    cfg = results[0].cfg
    hours = [t / 3600.0 for t in results[0].time_s]

    # 1) Timeline: indoor temperature per controller with occupancy shading
    fig, ax = plt.subplots(figsize=(13, 5))
    occ = results[0].occupancy
    away_start = None
    for h, o in zip(hours + [hours[-1]], occ + [cfg.residents]):
        if o == 0 and away_start is None:
            away_start = h
        elif o > 0 and away_start is not None:
            ax.axvspan(away_start, h, color="grey", alpha=0.18, lw=0)
            away_start = None
    for r in results:
        ax.plot(hours, r.indoor, label=r.controller, lw=1.1)
    ax.plot(hours, results[0].outdoor, "k--", lw=0.8, alpha=0.5, label="outdoor")
    ax.axhspan(cfg.comfort_low_c, cfg.comfort_high_c, color="green", alpha=0.07)
    ax.set_xlabel("time (h)")
    ax.set_ylabel("temperature (°C)")
    ax.set_title("Indoor temperature by controller (grey = house empty, green = comfort band)")
    ax.legend(ncol=5, fontsize=8)
    fig.tight_layout()
    p = os.path.join(out_dir, f"{cfg.scenario}_temperature_timeline.png")
    fig.savefig(p, dpi=130)
    plt.close(fig)
    paths.append(p)

    # 2) Trade-off bars
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    names = [r.controller for r in results]
    for ax, key, title in zip(
        axes,
        ["energy_kwh", "cost", "discomfort_deg_h"],
        ["Energy (kWh)", "Cost", "Discomfort while occupied (°C·h)"],
    ):
        ax.bar(names, [metrics[n][key] for n in names], color=["#888", "#4c72b0", "#55a868", "#c44e52"])
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    p = os.path.join(out_dir, f"{cfg.scenario}_comparison.png")
    fig.savefig(p, dpi=130)
    plt.close(fig)
    paths.append(p)
    return paths
