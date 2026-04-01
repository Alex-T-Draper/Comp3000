"""Completion Time Figures for Dissertation.

Generates a bar chart of total completion time per condition
and overall average, plus time-to-bottom for each condition.

Figures produced
----------------
- completion_time_per_condition.png  – Mean completion time with average line
- time_to_bottom.png                 – Mean time to reach 100% scroll

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
    "control": "C1\nPlain Text",
    "scroll-gate": "C2\nScroll-Gated",
    "formatted": "C3\nFormatted",
    "ai-summary": "C4\nAI Summary",
    "ai-enhanced": "C5\nAI Enhanced",
    "ai-hover": "C6\nAI Hover",
}
CONDITION_COLOURS = {
    "control": "#78909C",
    "scroll-gate": "#5C6BC0",
    "formatted": "#26A69A",
    "ai-summary": "#FFA726",
    "ai-enhanced": "#EF5350",
    "ai-hover": "#AB47BC",
}
CONDITION_ORDER = {
    "control": 1, "scroll-gate": 2, "formatted": 3,
    "ai-summary": 4, "ai-enhanced": 5, "ai-hover": 6,
}


def _anonymise(user_name: str, mapping: dict) -> str:
    if user_name not in mapping:
        mapping[user_name] = f"P{len(mapping) + 1:02d}"
    return mapping[user_name]


def _load_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT u.name AS user_name,
               s.condition_group,
               s.total_reading_time,
               s.time_to_bottom
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.total_reading_time IS NOT NULL
        ORDER BY s.condition_group, u.name
    """)
    rows = cur.fetchall()
    conn.close()

    anon = {}
    completion = {}   # condition -> list of seconds
    time_to_btm = {}  # condition -> list of seconds
    for r in rows:
        cond = str(r["condition_group"])
        _anonymise(r["user_name"], anon)
        t = r["total_reading_time"]
        completion.setdefault(cond, []).append(t)
        if r["time_to_bottom"] is not None:
            ttb = r["time_to_bottom"]
            time_to_btm.setdefault(cond, []).append(ttb)

    return completion, time_to_btm, anon


def _fmt_time(seconds: float) -> str:
    """Format seconds as mm:ss."""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def generate():
    completion, time_to_btm, anon_map = _load_data()
    n = len(anon_map)

    if not completion:
        print("[SKIP] No completion-time data in database.")
        return []

    outputs = []
    conditions = sorted(completion.keys(),
                        key=lambda c: CONDITION_ORDER.get(c, 99))
    labels = [CONDITION_LABELS.get(c, c) for c in conditions]
    colours = [CONDITION_COLOURS.get(c, "#999") for c in conditions]
    values = [completion[c] for c in conditions]

    # ── 1. Completion time per condition with overall average ────────
    means = [np.mean(v) for v in values]
    sems = [sp_stats.sem(v) if len(v) > 1 else 0 for v in values]
    overall_avg = np.mean([t for v in values for t in v])

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(conditions))
    bars = ax.bar(x, means, yerr=sems, capsize=5, width=0.55,
                  color=colours, alpha=0.8, edgecolor="white", linewidth=1.2,
                  error_kw={"lw": 1.5})

    # Overlay individual data points
    rng = np.random.default_rng(42)
    for i, v in enumerate(values):
        jitter = rng.uniform(-0.15, 0.15, len(v))
        ax.scatter(x[i] + jitter, v, color="black", alpha=0.4, s=18,
                   zorder=5)

    # Value labels on bars
    for i, (m, se) in enumerate(zip(means, sems)):
        ax.text(x[i], m + se + max(means) * 0.02, _fmt_time(m),
                ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Overall average line
    ax.axhline(overall_avg, color="#E53935", linestyle="--", linewidth=1.5,
               label=f"Overall avg: {_fmt_time(overall_avg)}")
    ax.legend(fontsize=10, loc="upper right")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Completion Time (seconds)", fontsize=11)
    ax.set_title("Task Completion Time per Condition", fontsize=13,
                 fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    fig.text(
        0.5, -0.03,
        f"Figure: Mean task completion time per condition (N={n}). "
        f"Error bars show ± SE. Dashed red line = overall average "
        f"({_fmt_time(overall_avg)}). Black dots = individual participants.",
        ha="center", fontsize=9, style="italic", wrap=True,
    )
    out1 = OUTPUT_DIR / "completion_time_per_condition.png"
    fig.savefig(out1, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out1}")
    outputs.append(out1)

    # ── 2. Time to bottom per condition ──────────────────────────────
    if time_to_btm:
        conds_b = sorted(time_to_btm.keys(),
                         key=lambda c: CONDITION_ORDER.get(c, 99))
        labels_b = [CONDITION_LABELS.get(c, c) for c in conds_b]
        colours_b = [CONDITION_COLOURS.get(c, "#999") for c in conds_b]
        vals_b = [time_to_btm[c] for c in conds_b]
        means_b = [np.mean(v) for v in vals_b]
        sems_b = [sp_stats.sem(v) if len(v) > 1 else 0 for v in vals_b]

        fig, ax = plt.subplots(figsize=(10, 6))
        xb = np.arange(len(conds_b))
        ax.bar(xb, means_b, yerr=sems_b, capsize=5, width=0.55,
               color=colours_b, alpha=0.8, edgecolor="white", linewidth=1.2,
               error_kw={"lw": 1.5})

        for i, v in enumerate(vals_b):
            jitter = rng.uniform(-0.15, 0.15, len(v))
            ax.scatter(xb[i] + jitter, v, color="black", alpha=0.4, s=18,
                       zorder=5)

        for i, (m, se) in enumerate(zip(means_b, sems_b)):
            ax.text(xb[i], m + se + max(means_b) * 0.02, _fmt_time(m),
                    ha="center", va="bottom", fontsize=9, fontweight="bold")

        ax.set_xticks(xb)
        ax.set_xticklabels(labels_b)
        ax.set_ylabel("Time to Bottom (seconds)", fontsize=11)
        ax.set_title("Time to Reach Document Bottom per Condition",
                     fontsize=13, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)

        fig.text(
            0.5, -0.03,
            f"Figure: Mean time until participants first scrolled to "
            f"100% depth (N varies per condition — only sessions that "
            "reached bottom). Error bars show ± SE.",
            ha="center", fontsize=9, style="italic", wrap=True,
        )
        out2 = OUTPUT_DIR / "time_to_bottom.png"
        fig.savefig(out2, dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"[OK] {out2}")
        outputs.append(out2)

    return outputs


if __name__ == "__main__":
    generate()
