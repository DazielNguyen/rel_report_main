"""Generate the English-language figures used by sn-article.tex.

The script reads the executable inventory project passed with --project-root,
runs the same seeded dashboard rollouts used for the report, and writes only
derived PDF figures into this report repository.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


POLICIES = ["Random", "Q-learning", "SARSA", "SAC-AlphaLR"]
POLICY_KEYS = ["random", "q_learning", "sarsa", "sac"]
BASE_DEMAND = np.array([6, 4, 2, 4, 10], dtype=np.float32)
DEMAND_SCALES = [0.8, 1.0, 1.2]
HOLIDAY_SCALES = [0.5, 1.0, 1.5]


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "figure.dpi": 150,
            "savefig.bbox": "tight",
        }
    )


def save_cost_and_stockout_figure(run_rollout, output_dir: Path) -> None:
    results = []
    for key in POLICY_KEYS:
        records = run_rollout(key, seed=42)
        results.append(
            {
                "procurement": sum(row["procurement"] for row in records) / 1e9,
                "storage": sum(row["storage"] for row in records) / 1e9,
                "shortage": sum(row["shortage"] for row in records) / 1e9,
                "stockouts": sum(row["stockout_units"] for row in records),
            }
        )

    x = np.arange(len(POLICIES))
    procurement = np.array([row["procurement"] for row in results])
    storage = np.array([row["storage"] for row in results])
    shortage = np.array([row["shortage"] for row in results])
    stockouts = np.array([row["stockouts"] for row in results])

    fig = plt.figure(figsize=(7.2, 4.1), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, width_ratios=[1.25, 1.0])
    cost_ax = fig.add_subplot(grid[:, 0])
    stockout_ax = fig.add_subplot(grid[0, 1])
    storage_ax = fig.add_subplot(grid[1, 1])

    cost_ax.bar(x, procurement, label="Procurement", color="#4472C4")
    cost_ax.bar(x, storage, bottom=procurement, label="Storage", color="#70AD47")
    cost_ax.bar(
        x,
        shortage,
        bottom=procurement + storage,
        label="Shortage",
        color="#ED7D31",
    )
    totals = procurement + storage + shortage
    cost_ax.set_title("Annual Cost Composition", pad=28)
    cost_ax.set_ylabel("Cost (billion VND)")
    cost_ax.set_xticks(x, POLICIES, rotation=18, ha="right")
    cost_ax.set_ylim(0, totals.max() * 1.08)
    cost_ax.grid(axis="y", alpha=0.25)
    cost_ax.legend(
        frameon=False,
        ncol=3,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
        columnspacing=0.8,
        handlelength=1.3,
    )

    policy_colors = ["#A5A5A5", "#5B9BD5", "#FFC000", "#70AD47"]
    bars = stockout_ax.bar(x, stockouts, color=policy_colors)
    stockout_ax.set_title("Annual Stockout Units")
    stockout_ax.set_ylabel("Unmet demand (units)")
    stockout_ax.set_xticks(x, POLICIES, rotation=18, ha="right")
    stockout_ax.set_ylim(0, stockouts.max() * 1.18)
    stockout_ax.grid(axis="y", alpha=0.25)
    stockout_ax.bar_label(bars, fmt="%d", padding=2, fontsize=8)

    storage_bars = storage_ax.bar(x, storage, color=policy_colors)
    storage_ax.set_title("Annual Storage Cost")
    storage_ax.set_ylabel("Cost (billion VND)")
    storage_ax.set_xticks(x, POLICIES, rotation=18, ha="right")
    storage_ax.set_ylim(0, storage.max() * 1.28)
    storage_ax.grid(axis="y", alpha=0.25)
    storage_ax.bar_label(storage_bars, fmt="%.2f", padding=2, fontsize=8)

    fig.savefig(output_dir / "policy_performance.pdf")
    plt.close(fig)


def save_demand_profile_figure(HolidayDemandGenerator, output_dir: Path) -> None:
    generator = HolidayDemandGenerator(seed=42)
    demand = np.array([generator.generate(day) for day in range(365)])
    labels = ["iPhone", "iPad", "MacBook", "Apple Watch", "AirPods"]

    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    for idx, label in enumerate(labels):
        ax.plot(np.arange(1, 366), demand[:, idx], linewidth=0.9, label=label)
    for day, holiday in generator.holidays.items():
        ax.axvline(day + 1, color="black", linewidth=0.45, alpha=0.25)
    ax.set_title("Seeded Daily Demand Profile with Seasonal and Holiday Effects")
    ax.set_xlabel("Day of year")
    ax.set_ylabel("Demand (units/day)")
    ax.set_xlim(1, 365)
    ax.grid(alpha=0.2)
    ax.legend(ncol=5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.20))
    fig.tight_layout()
    fig.savefig(output_dir / "annual_demand_profile.pdf")
    plt.close(fig)


def save_sensitivity_figure(run_rollout, output_dir: Path) -> None:
    costs = np.zeros((len(DEMAND_SCALES), len(HOLIDAY_SCALES)))
    stockouts = np.zeros_like(costs)
    for i, demand_scale in enumerate(DEMAND_SCALES):
        scenario_demand = np.maximum(1, BASE_DEMAND * demand_scale)
        for j, holiday_scale in enumerate(HOLIDAY_SCALES):
            records = run_rollout(
                "sac",
                seed=42,
                demand=scenario_demand,
                holiday_scale=holiday_scale,
            )
            costs[i, j] = sum(row["total_cost"] for row in records) / 1e9
            stockouts[i, j] = sum(row["stockout_units"] for row in records)

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    panels = [
        (costs, "Total Cost (billion VND)", ".1f", "YlOrRd"),
        (stockouts, "Stockout Units", ".0f", "Blues"),
    ]
    for ax, (values, title, fmt, cmap) in zip(axes, panels):
        image = ax.imshow(values, cmap=cmap, aspect="auto")
        ax.set_title(title)
        ax.set_xlabel("Holiday intensity multiplier")
        ax.set_ylabel("Baseline demand multiplier")
        ax.set_xticks(range(len(HOLIDAY_SCALES)), [f"{v:.1f}x" for v in HOLIDAY_SCALES])
        ax.set_yticks(range(len(DEMAND_SCALES)), [f"{v:.1f}x" for v in DEMAND_SCALES])
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                threshold = (values.min() + values.max()) / 2
                color = "white" if values[i, j] > threshold else "black"
                ax.text(j, i, format(values[i, j], fmt), ha="center", va="center", color=color, fontsize=8)
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

    fig.suptitle("SAC-AlphaLR Sensitivity to Configurable Demand Scenarios", y=1.02)
    fig.tight_layout()
    fig.savefig(output_dir / "configuration_sensitivity.pdf")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("figures"), type=Path)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    sys.path.insert(0, str(project_root))
    from dashboard.backend.rollout import run_rollout
    from env.advanced_demand_generator import HolidayDemandGenerator

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    configure_style()
    save_cost_and_stockout_figure(run_rollout, output_dir)
    save_demand_profile_figure(HolidayDemandGenerator, output_dir)
    save_sensitivity_figure(run_rollout, output_dir)


if __name__ == "__main__":
    main()
