"""Coordinate Transformation Diagram for Dissertation.

Illustrates how raw normalised Tobii gaze coordinates (0-1) are converted
to document-space pixel coordinates using scroll position:

    x_px = gaze_x × SCREEN_W
    y_px = gaze_y × SCREEN_H + scroll_position

Output: output/dissertation/coordinate_transformation.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "dissertation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCREEN_W = 2560
SCREEN_H = 1440


def generate():
    fig, axes = plt.subplots(1, 3, figsize=(16, 7),
                             gridspec_kw={"width_ratios": [1, 0.3, 1]})

    # ── Panel 1: Raw normalised gaze ─────────────────────────────────
    ax1 = axes[0]
    ax1.set_xlim(0, 1)
    ax1.set_ylim(1, 0)  # y goes down
    ax1.set_xlabel("Normalised X (0–1)", fontsize=10)
    ax1.set_ylabel("Normalised Y (0–1)", fontsize=10)
    ax1.set_title("(a) Raw Tobii Gaze", fontsize=12, fontweight="bold")
    ax1.set_aspect("equal")

    # Simulated gaze points
    rng = np.random.default_rng(42)
    gx = rng.normal(0.5, 0.12, 60).clip(0.02, 0.98)
    gy = rng.normal(0.45, 0.15, 60).clip(0.02, 0.98)
    ax1.scatter(gx, gy, c="#1976D2", alpha=0.6, s=25, zorder=3)

    # Viewport box
    viewport = mpatches.Rectangle((0, 0), 1, 1, linewidth=2,
                                  edgecolor="#333", facecolor="none",
                                  linestyle="--", label="Viewport (screen)")
    ax1.add_patch(viewport)
    ax1.legend(loc="lower right", fontsize=8)

    # ── Panel 2: Transformation arrow ────────────────────────────────
    ax2 = axes[1]
    ax2.axis("off")
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)

    ax2.annotate(
        "", xy=(0.85, 0.5), xytext=(0.15, 0.5),
        arrowprops=dict(arrowstyle="-|>", lw=3, color="#455A64"),
    )
    ax2.text(0.5, 0.62,
             r"$x_{px} = g_x \times W$" + "\n"
             r"$y_{px} = g_y \times H + s$",
             ha="center", va="bottom", fontsize=10,
             fontfamily="monospace",
             bbox=dict(boxstyle="round,pad=0.4", fc="#FFF9C4", ec="#F9A825"))
    ax2.text(0.5, 0.38, "scroll adjustment", ha="center", va="top",
             fontsize=9, style="italic", color="#666")

    # ── Panel 3: Document-space coordinates ──────────────────────────
    ax3 = axes[2]
    doc_height = 5000  # example document height in px
    ax3.set_xlim(0, SCREEN_W)
    ax3.set_ylim(doc_height, 0)
    ax3.set_xlabel("X (pixels)", fontsize=10)
    ax3.set_ylabel("Y (document pixels, scroll-adjusted)", fontsize=10)
    ax3.set_title("(b) Document-Space Coordinates", fontsize=12,
                  fontweight="bold")

    # Simulate two viewport positions (scroll=0 and scroll=2000)
    scroll_positions = [0, 2000]
    colours = ["#1976D2", "#E53935"]
    labels = ["Viewport @ scroll=0", "Viewport @ scroll=2000"]

    for scroll, colour, label in zip(scroll_positions, colours, labels):
        px = gx * SCREEN_W
        py = gy * SCREEN_H + scroll
        ax3.scatter(px, py, c=colour, alpha=0.55, s=20, label=label, zorder=3)

        # Draw viewport rectangle
        vp = mpatches.Rectangle(
            (0, scroll), SCREEN_W, SCREEN_H,
            linewidth=1.5, edgecolor=colour, facecolor=colour,
            alpha=0.07, linestyle="--",
        )
        ax3.add_patch(vp)

    ax3.legend(loc="lower right", fontsize=8)

    # ── Caption ──────────────────────────────────────────────────────
    fig.text(
        0.5, -0.02,
        "Figure: Coordinate transformation pipeline. "
        "Raw normalised Tobii gaze (a) is mapped to document-space "
        "pixel coordinates (b) by scaling to screen resolution "
        f"({SCREEN_W}×{SCREEN_H}) and adding the current scroll offset.",
        ha="center", fontsize=9, style="italic", wrap=True,
    )

    fig.tight_layout()
    out = OUTPUT_DIR / "coordinate_transformation.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out}")
    return out


if __name__ == "__main__":
    generate()
