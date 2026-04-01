"""Study Procedure Timeline for Dissertation.

Generates a horizontal timeline diagram showing the study session
flow, suitable for §3.6.2 Session Timeline.

Figures produced
----------------
- study_procedure_timeline.png – Horizontal step-by-step procedure

Output: output/dissertation/
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "dissertation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate():
    steps = [
        ("Welcome &\nConsent", "#78909C", "~2 min"),
        ("Calibration\n(Eye Tracker)", "#5C6BC0", "~3 min"),
        ("C1: Plain\nText", "#26A69A", "Self-paced"),
        ("Distractor\nTask", "#BDBDBD", "~2 min"),
        ("C2: Scroll-\nGated", "#26A69A", "Self-paced"),
        ("Distractor\nTask", "#BDBDBD", "~2 min"),
        ("C3:\nFormatted", "#26A69A", "Self-paced"),
        ("Distractor\nTask", "#BDBDBD", "~2 min"),
        ("C4: AI\nSummary", "#FFA726", "Self-paced"),
        ("Distractor\nTask", "#BDBDBD", "~2 min"),
        ("C5: AI\nEnhanced", "#FFA726", "Self-paced"),
        ("Distractor\nTask", "#BDBDBD", "~2 min"),
        ("C6: AI\nHover", "#FFA726", "Self-paced"),
        ("Comprehension\nTest", "#EF5350", "~5 min"),
        ("Post-Study\nQuestionnaire", "#AB47BC", "~5 min"),
    ]

    fig, ax = plt.subplots(figsize=(18, 4))
    ax.set_xlim(-0.5, len(steps) - 0.5)
    ax.set_ylim(-1.5, 2.5)
    ax.axis("off")
    ax.set_title("Study Session Procedure", fontsize=15, fontweight="bold",
                 pad=20)

    box_w = 0.7
    box_h = 1.2

    for i, (label, colour, dur) in enumerate(steps):
        # Box
        rect = mpatches.FancyBboxPatch(
            (i - box_w / 2, -box_h / 2), box_w, box_h,
            boxstyle="round,pad=0.1", facecolor=colour,
            edgecolor="white", linewidth=2, alpha=0.85)
        ax.add_patch(rect)

        # Label
        ax.text(i, 0.05, label, ha="center", va="center", fontsize=7.5,
                fontweight="bold", color="white")

        # Duration below
        ax.text(i, -box_h / 2 - 0.25, dur, ha="center", va="top",
                fontsize=7, color="#555")

        # Arrow between boxes
        if i < len(steps) - 1:
            ax.annotate("", xy=(i + 1 - box_w / 2 - 0.05, 0),
                        xytext=(i + box_w / 2 + 0.05, 0),
                        arrowprops=dict(arrowstyle="->", color="#999",
                                        lw=1.5))

    # Step numbers
    for i in range(len(steps)):
        ax.text(i, box_h / 2 + 0.15, f"{i + 1}", ha="center", va="bottom",
                fontsize=8, fontweight="bold", color="#333")

    # Legend
    legend_items = [
        mpatches.Patch(facecolor="#78909C", label="Setup"),
        mpatches.Patch(facecolor="#26A69A", label="Non-AI Conditions"),
        mpatches.Patch(facecolor="#FFA726", label="AI Conditions"),
        mpatches.Patch(facecolor="#BDBDBD", label="Distractor Task"),
        mpatches.Patch(facecolor="#EF5350", label="Comprehension"),
        mpatches.Patch(facecolor="#AB47BC", label="Questionnaire"),
    ]
    ax.legend(handles=legend_items, loc="lower center",
              bbox_to_anchor=(0.5, -0.35), ncol=6, fontsize=8,
              frameon=False)

    fig.text(
        0.5, -0.05,
        "Figure: Study session procedure. Each participant completed all "
        "six conditions in order, with distractor tasks between conditions "
        "to reduce carryover effects. Total session duration: ~45–60 min.",
        ha="center", fontsize=9, style="italic", wrap=True,
    )

    out = OUTPUT_DIR / "study_procedure_timeline.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out}")
    return [out]


if __name__ == "__main__":
    generate()
