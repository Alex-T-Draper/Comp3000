"""Engagement Metrics Figures for Dissertation.

Generates figures for AI-condition engagement metrics:
- Pause/dwell time per condition
- Time before generating summary (C4/C5/C6)
- Summary view duration (C4/C5/C6)

Figures produced
----------------
- pause_time_per_condition.png   – Total dwell/pause time per condition
- time_before_summary.png        – Time before clicking Generate (AI conditions)
- summary_view_duration.png      – Time spent viewing summary after generation

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

AI_CONDITIONS = {"ai-summary", "ai-enhanced", "ai-hover"}


def _anonymise(user_name: str, mapping: dict) -> str:
    if user_name not in mapping:
        mapping[user_name] = f"P{len(mapping) + 1:02d}"
    return mapping[user_name]


def _fmt_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _load_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT u.name AS user_name,
               s.condition_group,
               s.total_pause_time,
               s.time_before_summary,
               s.summary_view_duration,
               s.summary_generated
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.condition_group, u.name
    """)
    rows = cur.fetchall()
    conn.close()

    anon = {}
    pause = {}       # condition -> [seconds]
    pre_summary = {} # AI condition -> [seconds]
    view_dur = {}    # AI condition -> [seconds]

    for r in rows:
        cond = str(r["condition_group"])
        _anonymise(r["user_name"], anon)

        if r["total_pause_time"] is not None:
            pause.setdefault(cond, []).append(r["total_pause_time"])

        if cond in AI_CONDITIONS and r["summary_generated"]:
            if r["time_before_summary"] is not None:
                pre_summary.setdefault(cond, []).append(
                    r["time_before_summary"])
            if r["summary_view_duration"] is not None:
                view_dur.setdefault(cond, []).append(
                    r["summary_view_duration"])

    return pause, pre_summary, view_dur, anon


def _bar_chart(data, title, ylabel, caption, filename, label_map, colour_map,
               order_map, n):
    conditions = sorted(data.keys(), key=lambda c: order_map.get(c, 99))
    labels = [label_map.get(c, c) for c in conditions]
    colours = [colour_map.get(c, "#999") for c in conditions]
    values = [data[c] for c in conditions]
    means = [np.mean(v) for v in values]
    sems = [sp_stats.sem(v) if len(v) > 1 else 0 for v in values]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(conditions))
    ax.bar(x, means, yerr=sems, capsize=5, width=0.55,
           color=colours, alpha=0.8, edgecolor="white", linewidth=1.2,
           error_kw={"lw": 1.5})

    rng = np.random.default_rng(42)
    for i, v in enumerate(values):
        jitter = rng.uniform(-0.15, 0.15, len(v))
        ax.scatter(x[i] + jitter, v, color="black", alpha=0.4, s=18,
                   zorder=5)

    for i, (m, se) in enumerate(zip(means, sems)):
        ax.text(x[i], m + se + max(means) * 0.02, _fmt_time(m),
                ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    fig.text(0.5, -0.03, caption, ha="center", fontsize=9, style="italic",
             wrap=True)
    out = OUTPUT_DIR / filename
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out}")
    return out


def generate():
    pause, pre_summary, view_dur, anon_map = _load_data()
    n = len(anon_map)
    outputs = []

    # ── 1. Pause/dwell time per condition ────────────────────────────
    if pause:
        out = _bar_chart(
            pause,
            "Total Pause (Dwell) Time per Condition",
            "Pause Time (seconds)",
            f"Figure: Mean total pause/dwell time per condition (N={n}). "
            "A pause is recorded when scrolling stops for ≥ 3 s. "
            "Error bars show ± SE.",
            "pause_time_per_condition.png",
            CONDITION_LABELS, CONDITION_COLOURS, CONDITION_ORDER, n,
        )
        outputs.append(out)

    # ── 2. Time before generating summary (AI conditions) ────────────
    if pre_summary:
        out = _bar_chart(
            pre_summary,
            "Time Before Generating AI Summary",
            "Time (seconds)",
            f"Figure: Mean time participants read before clicking "
            f"'Generate AI Summary' (AI conditions only). "
            "Error bars show ± SE.",
            "time_before_summary.png",
            CONDITION_LABELS, CONDITION_COLOURS, CONDITION_ORDER, n,
        )
        outputs.append(out)

    # ── 3. Summary view duration (AI conditions) ─────────────────────
    if view_dur:
        out = _bar_chart(
            view_dur,
            "Time Spent Viewing AI Summary",
            "Duration (seconds)",
            f"Figure: Mean time participants spent viewing the AI summary "
            "after generation (AI conditions only). "
            "Error bars show ± SE.",
            "summary_view_duration.png",
            CONDITION_LABELS, CONDITION_COLOURS, CONDITION_ORDER, n,
        )
        outputs.append(out)

    if not outputs:
        print("[SKIP] No engagement data in database.")

    return outputs


if __name__ == "__main__":
    generate()
