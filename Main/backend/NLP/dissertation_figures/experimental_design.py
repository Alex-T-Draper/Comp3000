"""Experimental Design Flowchart for Dissertation.

Generates a within-subjects study design diagram showing the six
conditions each participant experienced, with the counterbalanced order.

Conditions
----------
C1  Plain Text            – BazaarBox (e-commerce)
C2  Scroll-Gated          – VaultDrive (cloud storage)
C3  Formatted/Highlighted – ConnectSphere (social media)
C4  AI Summary            – LearnVault (education)
C5  AI Enhanced           – PulseFit (fitness)
C6  AI Hover              – SonicWave (music streaming)

Output: output/dissertation/experimental_design.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "dissertation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONDITIONS = [
    ("C1", "Plain Text",           "BazaarBox\n(e-commerce)",    "#78909C"),
    ("C2", "Scroll-Gated",         "VaultDrive\n(cloud)",        "#5C6BC0"),
    ("C3", "Formatted/Highlighted","ConnectSphere\n(social)",    "#26A69A"),
    ("C4", "AI Summary",           "LearnVault\n(education)",    "#FFA726"),
    ("C5", "AI Enhanced",          "PulseFit\n(fitness)",        "#EF5350"),
    ("C6", "AI Hover",             "SonicWave\n(music)",         "#AB47BC"),
]


def _box(ax, x, y, w, h, text, colour, fontsize=9, bold=False):
    box = mpatches.FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.12", facecolor=colour,
        edgecolor="white", linewidth=1.5, alpha=0.9,
    )
    ax.add_patch(box)
    weight = "bold" if bold else "normal"
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, color="white")


def _arrow_down(ax, x, y_from, y_to):
    ax.annotate(
        "", xy=(x, y_to), xytext=(x, y_from),
        arrowprops=dict(arrowstyle="-|>", lw=1.5, color="#455A64"),
    )


def generate():
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(-1, 13)
    ax.set_ylim(-1, 10)
    ax.axis("off")
    fig.patch.set_facecolor("#FAFAFA")

    # ── Title ────────────────────────────────────────────────────────
    ax.text(6, 9.5, "Within-Subjects Experimental Design (N=10)",
            ha="center", fontsize=14, fontweight="bold")

    # ── Recruitment ──────────────────────────────────────────────────
    _box(ax, 6, 8.5, 4, 0.7,
         "Participant Recruitment\n(N=10, within-subjects)", "#37474F",
         fontsize=10, bold=True)
    _arrow_down(ax, 6, 8.15, 7.65)

    # ── Pre-study ────────────────────────────────────────────────────
    _box(ax, 6, 7.3, 4, 0.6,
         "Eye-Tracker Calibration + Demographics", "#607D8B")
    _arrow_down(ax, 6, 7.0, 6.4)

    # ── Conditions row ───────────────────────────────────────────────
    ax.text(6, 6.2, "6 Conditions (counterbalanced Latin-square order)",
            ha="center", fontsize=10, style="italic", color="#555")

    bw, bh = 1.8, 1.3
    y_cond = 4.8
    x_positions = [1.2, 3.3, 5.4, 7.5, 9.6, 11.7]

    for i, (cid, cond_name, service, colour) in enumerate(CONDITIONS):
        x = x_positions[i]
        _box(ax, x, y_cond, bw, bh,
             f"{cid}\n{cond_name}\n\n{service}", colour, fontsize=8, bold=True)
        # arrow from condition label area
        _arrow_down(ax, x, 5.95, y_cond + bh / 2)

    # ── Per-condition flow (below conditions) ────────────────────────
    y_flow = 3.2
    flow_steps = [
        "Read ToS\n(eye-tracking active)",
        "Distractor Task\n(math / pattern)",
        "Comprehension\nTest (3 Qs)",
    ]
    flow_colours = ["#1565C0", "#6A1B9A", "#2E7D32"]
    flow_x = [3.0, 6.0, 9.0]

    ax.text(6, 3.85, "Per-condition procedure (repeated ×6)",
            ha="center", fontsize=9, style="italic", color="#777")

    for j, (step, col) in enumerate(zip(flow_steps, flow_colours)):
        _box(ax, flow_x[j], y_flow, 2.5, 0.8, step, col, fontsize=9)
        if j > 0:
            ax.annotate(
                "", xy=(flow_x[j] - 1.25, y_flow),
                xytext=(flow_x[j - 1] + 1.25, y_flow),
                arrowprops=dict(arrowstyle="-|>", lw=1.5, color="#455A64"),
            )

    # ── Post-study ───────────────────────────────────────────────────
    _arrow_down(ax, 6, 2.8, 2.1)
    _box(ax, 6, 1.7, 4.5, 0.7,
         "Post-Study Questionnaire\n(preference ranking + confidence)",
         "#37474F", fontsize=10)

    # ── Arrow from last comprehension to post ────────────────────────
    # (already handled by global arrow above)

    # ── Footer caption ───────────────────────────────────────────────
    fig.text(
        0.5, 0.01,
        "Figure: Experimental procedure. Each participant completed all six "
        "conditions in a counterbalanced order.\n"
        "Eye tracking was active during ToS reading. A distractor task "
        "separated reading from the comprehension test to reduce recency bias.",
        ha="center", fontsize=9, style="italic",
    )

    out = OUTPUT_DIR / "experimental_design.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] {out}")
    return out


if __name__ == "__main__":
    generate()
