"""System Architecture Diagram for Dissertation.

Generates a high-level architecture diagram showing the components of the
ToS readability research platform: Angular frontend, FastAPI backend,
NLP pipeline, Tobii eye-tracker, and SQLite database.

Output: output/dissertation/architecture_diagram.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "dissertation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Colour palette ───────────────────────────────────────────────────
C_FRONTEND = "#4FC3F7"   # light blue
C_BACKEND  = "#81C784"   # green
C_NLP      = "#FFB74D"   # orange
C_DB       = "#CE93D8"   # purple
C_TOBII    = "#EF5350"   # red
C_ARROW    = "#455A64"   # grey-blue


def _rounded_box(ax, xy, w, h, label, sub_label, colour, fontsize=11):
    """Draw a rounded rectangle with a title and subtitle."""
    box = mpatches.FancyBboxPatch(
        xy, w, h,
        boxstyle="round,pad=0.15",
        facecolor=colour, edgecolor="white", linewidth=2, alpha=0.92,
    )
    ax.add_patch(box)
    cx, cy = xy[0] + w / 2, xy[1] + h / 2
    ax.text(cx, cy + 0.15, label, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color="white")
    if sub_label:
        ax.text(cx, cy - 0.22, sub_label, ha="center", va="center",
                fontsize=8, color="white", style="italic")


def _arrow(ax, start, end, label="", curved=False):
    """Draw an annotated arrow between two points."""
    props = dict(arrowstyle="-|>", lw=1.8, color=C_ARROW)
    if curved:
        props["connectionstyle"] = "arc3,rad=0.15"
    ax.annotate(
        "", xy=end, xytext=start,
        arrowprops=props,
    )
    if label:
        mx = (start[0] + end[0]) / 2
        my = (start[1] + end[1]) / 2
        ax.text(mx, my + 0.15, label, ha="center", va="bottom",
                fontsize=7.5, color=C_ARROW, style="italic")


def generate():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 8)
    ax.axis("off")
    fig.patch.set_facecolor("#F5F5F5")

    # ── Layer labels ─────────────────────────────────────────────────
    ax.text(5, 7.6, "System Architecture", ha="center", fontsize=16,
            fontweight="bold")

    # ── Boxes ────────────────────────────────────────────────────────
    # Frontend
    _rounded_box(ax, (0.5, 5.5), 3.5, 1.3,
                 "Angular 19 Frontend",
                 "ToS Reader · Conditions 1-6 · Scroll/Gaze Capture",
                 C_FRONTEND)

    # Tobii
    _rounded_box(ax, (6, 5.5), 3.5, 1.3,
                 "Tobii Eye Tracker",
                 "Stream Engine SDK · USB · 90 Hz Gaze",
                 C_TOBII)

    # Backend
    _rounded_box(ax, (0.5, 3.0), 3.5, 1.3,
                 "FastAPI Backend",
                 "REST API · WebSocket · Session Metrics",
                 C_BACKEND)

    # NLP Pipeline
    _rounded_box(ax, (6, 3.0), 3.5, 1.3,
                 "NLP Pipeline",
                 "DistilBART · TextRank · Clause Detection",
                 C_NLP)

    # Database
    _rounded_box(ax, (3, 0.8), 4, 1.3,
                 "SQLite Database",
                 "Sessions · Gaze Samples · Comprehension · Scroll Events",
                 C_DB)

    # ── Arrows ───────────────────────────────────────────────────────
    _arrow(ax, (2.25, 5.5), (2.25, 4.3), "REST / metrics")
    _arrow(ax, (7.75, 5.5), (7.75, 4.3), "gaze stream")
    _arrow(ax, (4.0, 3.6), (6.0, 3.6), "ToS text")
    _arrow(ax, (6.0, 3.3), (4.0, 3.3), "summaries / risk")
    _arrow(ax, (2.25, 3.0), (4.0, 2.1), "save data")
    _arrow(ax, (7.75, 3.0), (7.0, 2.1), "save gaze")

    # WebSocket arrow (curved)
    _arrow(ax, (4.0, 6.2), (6.0, 6.2), "WebSocket", curved=True)

    # ── Legend ────────────────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(color=C_FRONTEND, label="Presentation Layer"),
        mpatches.Patch(color=C_BACKEND, label="Application Layer"),
        mpatches.Patch(color=C_NLP, label="NLP / AI Layer"),
        mpatches.Patch(color=C_TOBII, label="Eye Tracking Hardware"),
        mpatches.Patch(color=C_DB, label="Persistence Layer"),
    ]
    ax.legend(handles=legend_items, loc="lower left", fontsize=9,
              framealpha=0.9, edgecolor="grey")

    out = OUTPUT_DIR / "architecture_diagram.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] {out}")
    return out


if __name__ == "__main__":
    generate()
