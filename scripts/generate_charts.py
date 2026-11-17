"""生成可行性雷达图、缺陷帕累托图与 AI 可靠性图。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon

from diagram_lib import (
    ACCENT,
    BG,
    BLUE,
    GOLD,
    GREEN,
    LINE,
    MUTED,
    NAVY,
    RED,
    SOFT_BLUE,
    TEAL,
    WHITE,
    save,
)

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = json.loads((ROOT / "evidence" / "api_snapshot.json").read_text(encoding="utf-8"))

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False


def radar():
    labels = ["经济可行性", "技术可行性", "操作可行性", "人员可行性", "时间可行性"]
    values = [4.5, 4.3, 4.2, 3.8, 3.6]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values_closed = values + [values[0]]
    angles_closed = angles + [angles[0]]

    fig = plt.figure(figsize=(8.6, 7.9), dpi=300, facecolor=BG)
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor(BG)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=11.5, color=NAVY, fontweight="bold")
    ax.tick_params(axis="x", pad=18)

    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=8.5, color=MUTED)
    ax.set_rlabel_position(0)
    ax.grid(color=LINE, linewidth=0.8, alpha=0.8)
    ax.spines["polar"].set_color(LINE)

    baseline = [3.5] * len(labels) + [3.5]
    ax.plot(angles_closed, baseline, color=MUTED, lw=1.0, ls=(0, (3, 3)), zorder=3)
    ax.fill(angles_closed, baseline, color=MUTED, alpha=0.05, zorder=2)

    ax.plot(angles_closed, values_closed, color=BLUE, lw=2.2, zorder=4)
    ax.fill(angles_closed, values_closed, color=BLUE, alpha=0.18, zorder=3)
    ax.scatter(angles, values, s=48, color=GOLD, edgecolor=WHITE, linewidth=1.4, zorder=6)

    for angle, value in zip(angles, values):
        dx = 0.18 * np.sin(angle)
        dy = 0.18 * np.cos(angle)
        ax.text(
            angle + dx,
            value + 0.32 + dy,
            f"{value:.1f}",
            ha="center",
            va="center",
            fontsize=10.5,
            color=NAVY,
            fontweight="bold",
            zorder=7,
        )

    fig.text(0.07, 0.94, "FEASIBILITY · FIVE-DIMENSION REVIEW", fontsize=9, color=ACCENT, fontweight="bold")
    fig.text(0.07, 0.885, "五维可行性雷达图", fontsize=21, color=NAVY, fontweight="bold")
    fig.text(0.07, 0.845, "5 分制 · 虚线为 3.5 分评审基准 · 数据源：项目可行性评审记录", fontsize=9, color=MUTED)

    ax.text(
        1.22,
        1.08,
        "综合 4.08 / 5",
        transform=ax.transAxes,
        fontsize=11,
        color=NAVY,
        fontweight="bold",
        ha="right",
        va="center",
        bbox=dict(boxstyle="round,pad=0.45", facecolor=SOFT_BLUE, edgecolor=LINE),
    )

    legend_lines = [
        plt.Line2D([0], [0], color=BLUE, lw=2.2, marker="o", markerfacecolor=GOLD, markeredgecolor=WHITE, label="项目评分"),
        plt.Line2D([0], [0], color=MUTED, lw=1.0, ls=(0, (3, 3)), label="评审基准 3.5"),
    ]
    ax.legend(handles=legend_lines, loc="lower center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False, fontsize=9)
    save(fig, "01_feasibility_radar")


def pareto():
    rows = SNAPSHOT["ai_stats"]["pareto"]
    categories = [row["category"] for row in rows]
    occurrences = [row["occurrences"] for row in rows]
    cumulative = [row["cumulative"] for row in rows]
    shares = [row["share"] for row in rows]

    def wrap(text):
        if len(text) > 5:
            mid = len(text) // 2
            return text[:mid] + "\n" + text[mid:]
        return text

    fig, ax = plt.subplots(figsize=(10.6, 5.9), dpi=300, facecolor=BG)
    ax.set_facecolor(BG)
    fig.subplots_adjust(left=0.07, right=0.9, top=0.76, bottom=0.15)

    bars = ax.bar(
        range(len(rows)),
        occurrences,
        color=[NAVY if index % 2 == 0 else BLUE for index in range(len(rows))],
        width=0.58,
        edgecolor=WHITE,
        linewidth=0.8,
        zorder=3,
    )
    for bar, value in zip(bars, occurrences):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.5, str(value), ha="center", va="bottom", fontsize=10, color=NAVY, fontweight="bold")

    ax.set_ylim(0, max(occurrences) * 1.22)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels([wrap(item) for item in categories], fontsize=9.6, color="#3f4c55", linespacing=1.45)
    ax.set_ylabel("发生次数", fontsize=10, color=MUTED, labelpad=8)
    ax.tick_params(axis="y", colors=MUTED, labelsize=9)
    ax.tick_params(axis="x", length=0, pad=8)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(LINE)
    ax.spines["bottom"].set_color(LINE)
    ax.grid(axis="y", color=LINE, linestyle=(0, (2, 3)), linewidth=0.8, alpha=0.65, zorder=0)

    ax2 = ax.twinx()
    ax2.plot(range(len(rows)), cumulative, color=GOLD, marker="o", markersize=5, linewidth=2.0, zorder=5, label="累计占比")
    for index, value in enumerate(cumulative):
        ax2.annotate(f"{value:.1f}%", (index, value), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8.6, color="#8a641c")
    ax2.set_ylim(0, 108)
    ax2.set_ylabel("累计占比（%）", fontsize=10, color=MUTED, labelpad=8)
    ax2.tick_params(axis="y", colors=MUTED, labelsize=9)
    for spine in ["top", "left"]:
        ax2.spines[spine].set_visible(False)
    ax2.spines["right"].set_color(LINE)
    ax2.axhline(80, color=RED, lw=1.2, ls=(0, (4, 3)), zorder=2)
    ax2.text(len(rows) - 0.42, 81.5, "80% 参考线", color=RED, fontsize=8.8, ha="right")

    ax.axvspan(-0.45, 3.45, color=GOLD, alpha=0.055, zorder=0)
    ax.text(1.45, max(occurrences) * 1.13, "主要改进区（前四类，累计 76.5%）", fontsize=9.2, color="#8a641c", ha="center")

    fig.text(0.07, 0.93, "DEFECT PARETO · MAINTENANCE", fontsize=9, color=ACCENT, fontweight="bold")
    fig.text(0.07, 0.875, "缺陷帕累托图", fontsize=21, color=NAVY, fontweight="bold")
    fig.text(0.07, 0.835, f"25 条缺陷记录 / 累计发生 {sum(occurrences)} 次 · AI 相关占 {SNAPSHOT['ai_stats']['summary']['ai_related_rate']}% · 待修复占 {SNAPSHOT['ai_stats']['summary']['open_rate']}%", fontsize=9, color=MUTED)

    save(fig, "06_defect_pareto")


def reliability():
    rows = SNAPSHOT["ai_stats"]["by_phase"]
    labels = [f"{row['phase_name']}\n通过 {row['success_rate']:.0f}%" for row in rows]
    reliability_values = [row["reliability"] for row in rows]
    failure_values = [row["avg_failure_score"] for row in rows]

    colors = []
    for value in reliability_values:
        if value >= 90:
            colors.append(GREEN)
        elif value >= 80:
            colors.append(BLUE)
        elif value >= 70:
            colors.append(GOLD)
        else:
            colors.append(ACCENT)

    fig, ax = plt.subplots(figsize=(10.4, 5.8), dpi=300, facecolor=BG)
    ax.set_facecolor(BG)
    fig.subplots_adjust(left=0.08, right=0.94, top=0.74, bottom=0.18)

    positions = list(range(len(rows)))
    reliability_bars = ax.bar(
        [pos - 0.19 for pos in positions], reliability_values, width=0.34,
        color=colors, edgecolor=WHITE, linewidth=0.8, zorder=3, label="综合可靠性"
    )
    failure_bars = ax.bar(
        [pos + 0.19 for pos in positions], failure_values, width=0.34,
        color=ACCENT, alpha=0.9, edgecolor=WHITE, linewidth=0.8, zorder=3, label="平均失效分 FS"
    )
    for bar, value in zip(reliability_bars, reliability_values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 2, f"{value:.1f}", ha="center", va="bottom", fontsize=9.6, color=NAVY, fontweight="bold")
    for bar, value in zip(failure_bars, failure_values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 2, f"{value:.1f}", ha="center", va="bottom", fontsize=8.6, color="#8f4c2b")

    ax.axhline(80, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=1, label="可靠性目标线 80")
    ax.set_ylim(0, 112)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=9.3, color="#3f4c55", linespacing=1.5)
    ax.set_ylabel("分数", fontsize=9.8, color=MUTED)
    ax.tick_params(axis="y", colors=MUTED, labelsize=9)
    ax.tick_params(axis="x", length=0, pad=8)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(LINE)
    ax.spines["bottom"].set_color(LINE)
    ax.grid(axis="y", color=LINE, linestyle=(0, (2, 3)), linewidth=0.8, alpha=0.7, zorder=0)

    fig.text(0.08, 0.93, "AGENT RELIABILITY · BY PHASE", fontsize=9, color=ACCENT, fontweight="bold")
    fig.text(0.08, 0.875, "各阶段 AI 协作可靠性", fontsize=21, color=NAVY, fontweight="bold")
    fig.text(0.08, 0.835, "综合可靠性 = 0.6×(100−平均 FS) + 0.4×一次通过率×100；柱下为一次通过率", fontsize=9, color=MUTED)

    ax.legend(loc="upper right", bbox_to_anchor=(0.99, 1.04), frameon=False, fontsize=8.8, ncol=3)
    save(fig, "08_ai_reliability")


if __name__ == "__main__":
    radar()
    pareto()
    reliability()
