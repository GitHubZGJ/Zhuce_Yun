"""图表绘制公共组件：统一配色、字体、画布与图元。"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon

BG = "#fffdf8"
INK = "#1b2c3a"
NAVY = "#123a57"
NAVY_LIGHT = "#1d4a6b"
BLUE = "#2f6690"
TEAL = "#2d6a73"
GOLD = "#d9a441"
ACCENT = "#c06a3c"
RED = "#a53d33"
GREEN = "#2e7d5b"
MUTED = "#6c777e"
LINE = "#cfc7b8"
SOFT = "#f4efe4"
SOFT_BLUE = "#eaf1f6"
SOFT_GREEN = "#eaf4ee"
SOFT_GOLD = "#fbf1dc"
SOFT_RED = "#f8e9e6"
SOFT_TEAL = "#e8f1f1"
WHITE = "#ffffff"

DIAGRAM_DIR = Path(__file__).resolve().parents[1] / "diagrams"
DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["svg.fonttype"] = "none"


def new_canvas(width=160, height=100, dpi=250):
    fig = plt.figure(figsize=(width / 16, height / 16), dpi=dpi, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def add_title(ax, kicker, title, subtitle=None, width=160, y=93.5):
    ax.text(7, y, kicker, fontsize=8.2, color=ACCENT, fontweight="bold", va="center")
    ax.text(7, y - 6.3, title, fontsize=18, color=NAVY, fontweight="bold", va="center")
    ax.plot([7, 18], [y - 10.3, y - 10.3], color=GOLD, lw=1.6, solid_capstyle="round")
    if subtitle:
        ax.text(19.5, y - 10.4, subtitle, fontsize=8.4, color=MUTED, va="center")


def rounded_box(
    ax,
    x,
    y,
    w,
    h,
    heading="",
    lines=None,
    fc=WHITE,
    ec=LINE,
    heading_fs=9.2,
    body_fs=7.8,
    heading_color=NAVY,
    body_color=INK,
    accent=None,
    lw=1.0,
    align="center",
    header_line=True,
    padding=1.6,
    zorder=3,
):
    shadow = FancyBboxPatch(
        (x + 0.55, y - 0.55),
        w,
        h,
        boxstyle="round,pad=0,rounding_size=1.2",
        facecolor="#e9e2d4",
        edgecolor="none",
        alpha=0.55,
        zorder=zorder - 1,
    )
    ax.add_patch(shadow)
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0,rounding_size=1.2",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        zorder=zorder,
    )
    ax.add_patch(patch)
    if accent:
        ax.plot([x + 1.4, x + w - 1.4], [y + h - 0.9, y + h - 0.9], color=accent, lw=2.2, zorder=zorder + 1)

    if heading:
        if align == "left":
            ax.text(
                x + padding,
                y + h - 2.6,
                heading,
                fontsize=heading_fs,
                color=heading_color,
                fontweight="bold",
                va="top",
                ha="left",
                zorder=zorder + 1,
            )
            if header_line:
                ax.plot(
                    [x + padding, x + w - padding],
                    [y + h - 4.5, y + h - 4.5],
                    color=ec,
                    lw=0.7,
                    alpha=0.8,
                    zorder=zorder + 1,
                )
        else:
            ax.text(
                x + w / 2,
                y + h / 2 + (1.4 if lines else 0),
                heading,
                fontsize=heading_fs,
                color=heading_color,
                fontweight="bold",
                va="center",
                ha="center",
                zorder=zorder + 1,
            )

    if lines:
        if align == "left":
            start_y = y + h - 6.2 if heading else y + h - 2.4
            ax.text(
                x + padding,
                start_y,
                "\n".join(lines),
                fontsize=body_fs,
                color=body_color,
                va="top",
                ha="left",
                linespacing=1.55,
                zorder=zorder + 1,
            )
        else:
            ax.text(
                x + w / 2,
                y + h / 2 - (1.4 if heading else 0),
                "\n".join(lines),
                fontsize=body_fs,
                color=body_color,
                va="center",
                ha="center",
                linespacing=1.5,
                zorder=zorder + 1,
            )
    return patch


def arrow(
    ax,
    start,
    end,
    color=NAVY_LIGHT,
    lw=1.1,
    style="-|>",
    ls="-",
    rad=0.0,
    mutation=9,
    zorder=2,
    label=None,
    label_offset=(0, 1.2),
    label_color=MUTED,
    label_fs=7,
):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle=style,
        mutation_scale=mutation,
        color=color,
        linewidth=lw,
        linestyle=ls,
        connectionstyle=f"arc3,rad={rad}",
        shrinkA=1.5,
        shrinkB=1.5,
        zorder=zorder,
    )
    ax.add_patch(patch)
    if label:
        ax.text(
            (start[0] + end[0]) / 2 + label_offset[0],
            (start[1] + end[1]) / 2 + label_offset[1],
            label,
            fontsize=label_fs,
            color=label_color,
            ha="center",
            va="center",
            zorder=zorder + 1,
            bbox=dict(facecolor=BG, edgecolor="none", pad=1.0, alpha=0.9),
        )


def actor(ax, x, y, label, color=NAVY, scale=1.0):
    s = scale
    head = Circle((x, y + 10.5 * s), 2.2 * s, facecolor=WHITE, edgecolor=color, linewidth=1.2, zorder=5)
    ax.add_patch(head)
    ax.plot([x, x], [y + 8.2 * s, y + 3.6 * s], color=color, lw=1.4, zorder=5)
    ax.plot([x - 3.2 * s, x + 3.2 * s], [y + 6.7 * s, y + 6.7 * s], color=color, lw=1.4, zorder=5)
    ax.plot([x, x - 2.6 * s], [y + 3.6 * s, y - 0.6 * s], color=color, lw=1.4, zorder=5)
    ax.plot([x, x + 2.6 * s], [y + 3.6 * s, y - 0.6 * s], color=color, lw=1.4, zorder=5)
    ax.text(x, y - 4.2 * s, label, fontsize=9, color=color, ha="center", va="top", fontweight="bold")


def use_case(ax, x, y, label, w=24, h=8, fc=SOFT_BLUE, ec=BLUE):
    ellipse = Ellipse((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=1.0, zorder=4)
    ax.add_patch(ellipse)
    ax.text(x, y, label, fontsize=7.8, color=INK, ha="center", va="center", linespacing=1.35, zorder=5)


def diamond(ax, cx, cy, w, h, label, fc=SOFT_GOLD, ec=GOLD, fontsize=7.8):
    points = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    patch = Polygon(points, closed=True, facecolor=fc, edgecolor=ec, linewidth=1.1, zorder=4)
    ax.add_patch(patch)
    ax.text(cx, cy, label, fontsize=fontsize, color=INK, ha="center", va="center", linespacing=1.3, zorder=5)


def save(fig, name):
    png = DIAGRAM_DIR / f"{name}.png"
    svg = DIAGRAM_DIR / f"{name}.svg"
    fig.savefig(png, dpi=300, facecolor=BG, bbox_inches="tight", pad_inches=0.12)
    fig.savefig(svg, facecolor=BG, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print("saved", png.name, svg.name)
