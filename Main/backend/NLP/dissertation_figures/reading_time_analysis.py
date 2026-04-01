"""Reading Time Analysis Figures for Dissertation.

Generates boxplots and bar charts of total_reading_time across the six
conditions, with anonymised participant IDs.

Figures produced
----------------
- reading_time_boxplot.png   – Boxplot per condition
- reading_time_bars.png      – Mean ± SE bar chart with individual data points

Output: output/dissertation/
"""

import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats as sp_stats

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "dissertation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(__file__).parent.parent / "tos_research.db"

CONDITION_LABELS = {
    "1": "C1\nPlain Text",
    "2": "C2\nScroll-Gated",
    "3": "C3\nFormatted",
    "4": "C4\nAI Summary",
    "5": "C5\nAI Enhanced",
    "6": "C6\nAI Hover",
    "control": "C1\nPlain Text",
    "scroll-gate": "C2\nScroll-Gated",
    "formatted": "C3\nFormatted",
    "ai-summary": "C4\nAI Summary",
    "ai-enhanced": "C5\nAI Enhanced",
    "ai-hover": "C6\nAI Hover",
}

CONDITION_COLOURS = {
    "1": "#78909C",
    "2": "#5C6BC0",
    "3": "#26A69A",
    "4": "#FFA726",
    "5": "#EF5350",
    "6": "#AB47BC",
    "control": "#78909C",
    "scroll-gate": "#5C6BC0",
    "formatted": "#26A69A",
    "ai-summary": "#FFA726",
    "ai-enhanced": "#EF5350",
    "ai-hover": "#AB47BC",
}

# Canonical sort order for conditions
CONDITION_ORDER = {
    "1": 1, "control": 1,
    "2": 2, "scroll-gate": 2,
    "3": 3, "formatted": 3,
    "4": 4, "ai-summary": 4,
    "5": 5, "ai-enhanced": 5,
    "6": 6, "ai-hover": 6,
}


def _anonymise(user_name: str, mapping: dict) -> str:
    """Return a stable anonymised ID like P01, P02, ..."""
    if user_name not in mapping:
        mapping[user_name] = f"P{len(mapping) + 1:02d}"
    return mapping[user_name]


def _load_data():
    """Load reading time data from the database, grouped by condition."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT u.name AS user_name, s.condition_group, s.total_reading_time
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.total_reading_time IS NOT NULL
        ORDER BY s.condition_group, u.name
    """)
    rows = cur.fetchall()
    conn.close()

    anon = {}
    data = {}  # condition -> list of (participant_id, reading_time_s)
    for r in rows:
        cond = str(r["condition_group"])
        pid = _anonymise(r["user_name"], anon)
        time_s = r["total_reading_time"] / 1000.0  # ms → seconds
        data.setdefault(cond, []).append((pid, time_s))

    return data, anon


def generate():
    data, anon_map = _load_data()
    n_participants = len(anon_map)

    if not data:
        print("[SKIP] No reading-time data in database.")
        return []

    conditions = sorted(data.keys(), key=lambda c: CONDITION_ORDER.get(c, 99))
    labels = [CONDITION_LABELS.get(c, c) for c in conditions]
    colours = [CONDITION_COLOURS.get(c, "#999") for c in conditions]
    values = [[t for _, t in data[c]] for c in conditions]

    outputs = []

    # ── 1. Boxplot ───────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    bp = ax.boxplot(values, labels=labels, patch_artist=True, widths=0.5)
    for patch, col in zip(bp["boxes"], colours):
        patch.set_facecolor(col)
        patch.set_alpha(0.75)
    ax.set_ylabel("Reading Time (seconds)", fontsize=11)
    ax.set_title("Total Reading Time per Condition", fontsize=13,
                 fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    fig.text(
        0.5, -0.03,
        f"Figure: Distribution of total reading time across conditions "
        f"(N={n_participants}). Each box shows the median, IQR, and "
        "whiskers at 1.5×IQR. Outliers shown as circles.",
        ha="center", fontsize=9, style="italic", wrap=True,
    )

    out1 = OUTPUT_DIR / "reading_time_boxplot.png"
    fig.savefig(out1, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out1}")
    outputs.append(out1)

    # ── 2. Bar chart (Mean ± SE) with jittered points ────────────────
    means = [np.mean(v) for v in values]
    sems = [sp_stats.sem(v) if len(v) > 1 else 0 for v in values]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(conditions))
    bars = ax.bar(x, means, yerr=sems, capsize=5, width=0.55,
                  color=colours, alpha=0.8, edgecolor="white", linewidth=1.2,
                  error_kw={"lw": 1.5})

    # Overlay individual participant points (jittered)
    rng = np.random.default_rng(7)
    for i, v in enumerate(values):
        jitter = rng.uniform(-0.15, 0.15, len(v))
        ax.scatter(x[i] + jitter, v, color="black", alpha=0.4, s=18,
                   zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Reading Time (seconds)", fontsize=11)
    ax.set_title("Mean Reading Time per Condition (± SE)", fontsize=13,
                 fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    fig.text(
        0.5, -0.03,
        f"Figure: Mean total reading time across conditions with standard "
        f"error bars (N={n_participants}). Individual participant data points "
        "shown in black. Axes: x = experimental condition, y = time in seconds.",
        ha="center", fontsize=9, style="italic", wrap=True,
    )

    out2 = OUTPUT_DIR / "reading_time_bars.png"
    fig.savefig(out2, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out2}")
    outputs.append(out2)

    return outputs


if __name__ == "__main__":
    generate()
