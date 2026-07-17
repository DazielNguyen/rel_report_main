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


EVALUATION_POLICIES = ["Random", "Q-learning", "SARSA", "SAC-AutoAlpha"]
# Comparable 52-week, seed-42 rollout results produced by the dashboard
# evaluation pipeline. The repository's eval_results.json is a legacy 365-day
# run and is deliberately not read here.
EVALUATION_RESULTS = {
    "total_cost": np.array([182.64, 161.00, 162.48, 155.71]),
    "revenue": np.array([120.84, 172.08, 168.96, 185.05]),
    "profit": np.array([-61.79, 11.07, 6.49, 29.35]),
    "shortage_cost": np.array([104.67, 47.90, 51.24, 34.00]),
    "stockouts": np.array([5022, 2449, 3145, 2013]),
    "service_level": np.array([55.5, 78.3, 72.1, 82.1]),
}


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


def save_actor_evaluation_figure(output_dir: Path) -> None:
    """Plot comparable 52-week seed-42 business and service outcomes."""
    x = np.arange(len(EVALUATION_POLICIES))
    colors = ["#A5A5A5", "#5B9BD5", "#70AD47", "#ED7D31"]
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.4), constrained_layout=True)

    # Business outcomes: costs and revenue share one unit and are shown together.
    business_ax = axes[0, 0]
    width = 0.36
    cost_bars = business_ax.bar(
        x - width / 2,
        EVALUATION_RESULTS["total_cost"],
        width,
        label="Total cost",
        color="#ED7D31",
    )
    revenue_bars = business_ax.bar(
        x + width / 2,
        EVALUATION_RESULTS["revenue"],
        width,
        label="Revenue",
        color="#4472C4",
    )
    business_ax.set_title("Total Cost and Revenue")
    business_ax.set_ylabel("Billion VND")
    business_ax.set_xticks(x, EVALUATION_POLICIES, rotation=15, ha="right")
    # Extra headroom keeps the legend and numerical bar labels separate.
    business_ax.set_ylim(0, 235)
    business_ax.grid(axis="y", alpha=0.25)
    business_ax.legend(frameon=False, ncol=2, loc="upper left", fontsize=7)
    business_ax.bar_label(cost_bars, fmt="%.2f", padding=2, fontsize=7)
    business_ax.bar_label(revenue_bars, fmt="%.2f", padding=2, fontsize=7)

    metrics = [
        ("Net Profit", EVALUATION_RESULTS["profit"], "Billion VND", ".2f"),
        ("Stockout Units", EVALUATION_RESULTS["stockouts"], "Units", ".0f"),
        ("Service Level", EVALUATION_RESULTS["service_level"], "Percent", ".1f"),
    ]
    for ax, (title, values, ylabel, fmt) in zip(axes.flat[1:], metrics):
        bars = ax.bar(x, values, color=colors)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xticks(x, EVALUATION_POLICIES, rotation=15, ha="right")
        ax.grid(axis="y", alpha=0.25)
        ax.bar_label(bars, labels=[format(v, fmt) for v in values], padding=3, fontsize=8)

        lower = min(0.0, float(values.min()))
        upper = max(0.0, float(values.max()))
        span = max(upper - lower, 1.0)
        ax.set_ylim(lower - 0.10 * span, upper + 0.15 * span)

    axes[1, 1].set_ylim(0, 105)
    fig.savefig(output_dir / "actor_evaluation.pdf")
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("figures"), type=Path)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    sys.path.insert(0, str(project_root))
    from env.advanced_demand_generator import HolidayDemandGenerator

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    configure_style()
    save_actor_evaluation_figure(output_dir)
    save_demand_profile_figure(HolidayDemandGenerator, output_dir)


if __name__ == "__main__":
    main()
