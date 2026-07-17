"""Generate the English-language figures used by sn-article.tex.

The script reads the demand generator from the executable project and uses the
version-comparison results documented in So_sanh_v2_vs_v3.md. It writes only
derived PDF figures into this report repository.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


POLICIES = ["Random", "Q-learning", "SARSA", "SAC-AlphaLR"]
V2_PROFIT = np.array([-73.68, -53.49, -35.87, -27.88])
V3_COST = np.array([183.03, 158.35, 161.36, 156.78])
V3_REVENUE = np.array([119.69, 174.41, 170.20, 181.55])
V3_PROFIT = np.array([-63.34, 16.06, 8.84, 24.77])
V3_STOCKOUTS = np.array([4973, 2365, 2472, 2039])


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


def save_policy_performance_figure(output_dir: Path) -> None:
    x = np.arange(len(POLICIES))
    width = 0.36
    colors = ["#4472C4", "#ED7D31", "#70AD47", "#A5A5A5"]

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.2), constrained_layout=True)
    axes[0].bar(x - width / 2, V3_COST, width, label="Total cost", color="#ED7D31")
    axes[0].bar(x + width / 2, V3_REVENUE, width, label="Revenue", color="#4472C4")
    axes[0].set_title("Annual Cost and Revenue")
    axes[0].set_ylabel("Billion VND")
    axes[0].set_xticks(x, POLICIES, rotation=24, ha="right")
    axes[0].set_ylim(0, max(V3_COST.max(), V3_REVENUE.max()) * 1.18)
    axes[0].legend(frameon=False, loc="upper center", ncol=2)
    axes[0].grid(axis="y", alpha=0.25)

    profit_bars = axes[1].bar(x, V3_PROFIT, color=colors)
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_title("Annual Net Profit")
    axes[1].set_ylabel("Billion VND")
    axes[1].set_xticks(x, POLICIES, rotation=24, ha="right")
    axes[1].set_ylim(V3_PROFIT.min() * 1.18, V3_PROFIT.max() * 1.35)
    axes[1].bar_label(profit_bars, fmt="%.2f", padding=2, fontsize=8)
    axes[1].grid(axis="y", alpha=0.25)

    stockout_bars = axes[2].bar(x, V3_STOCKOUTS, color=colors)
    axes[2].set_title("Annual Stockout Units")
    axes[2].set_ylabel("Unmet demand (units)")
    axes[2].set_xticks(x, POLICIES, rotation=24, ha="right")
    axes[2].set_ylim(0, V3_STOCKOUTS.max() * 1.20)
    axes[2].bar_label(stockout_bars, fmt="%d", padding=2, fontsize=8)
    axes[2].grid(axis="y", alpha=0.25)

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


def save_version_comparison_figure(output_dir: Path) -> None:
    x = np.arange(len(POLICIES))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    old_bars = ax.bar(x - width / 2, V2_PROFIT, width, label="v2: cost-based reward", color="#A5A5A5")
    new_bars = ax.bar(x + width / 2, V3_PROFIT, width, label="v3: profit-based reward", color="#70AD47")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Net Profit Before and After the v3 Reward Revision")
    ax.set_ylabel("Net profit (billion VND)")
    ax.set_xticks(x, POLICIES)
    ax.set_ylim(min(V2_PROFIT.min(), V3_PROFIT.min()) * 1.18, V3_PROFIT.max() * 1.45)
    ax.bar_label(old_bars, fmt="%.2f", padding=2, fontsize=8)
    ax.bar_label(new_bars, fmt="%.2f", padding=2, fontsize=8)
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "version_profit_comparison.pdf")
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
    save_policy_performance_figure(output_dir)
    save_demand_profile_figure(HolidayDemandGenerator, output_dir)
    save_version_comparison_figure(output_dir)


if __name__ == "__main__":
    main()
